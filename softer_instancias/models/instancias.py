from odoo import models, fields, api
import docker
import time
from odoo.exceptions import UserError
import psycopg2
from psycopg2 import OperationalError
import requests
import logging
from .dominios import Dominios
from odoo.exceptions import ValidationError


# Configurar el logger
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Instancias(models.Model):
    _name = "instancias.instancias"
    _description = "Instancias"

    cliente = fields.Many2one("res.partner", string="Contacto")
    user_id = fields.Many2one("res.users", string="Usuario", required=True)

    app_id = fields.Many2one("instancias.apps", string="App", required=True)
    fecha = fields.Date(string="Fecha")

    dominios_id = fields.Many2one("instancias.dominios", string="Dominio")
    subdominio = fields.Char(string="Subdominio")
    ref = fields.Char(string="Referencia", required=True, unique=True)
    name = fields.Char(string="Nombre de Instancia", required=True)
    suscription_id = fields.Many2one("subscription.package", string="Suscripción")
    estado = fields.Selection(
        [
            ("running", "Corriendo"),
            ("stop", "Detenida"),
            ("error", "Error"),
            ("procesando", "Procesando"),
            ("suspendido", "Suspendido"),
            ("porsuspender", "Por suspender"),
        ],
        string="Estado",
        default="stop",
    )

    # @api.model
    # def create(self, vals):
    #     # Llamamos al método create original para crear el registro
    #     record = super(Instancias, self).create(vals)
    #     if not record.ref or record.ref == "":
    #         record.ref = record.id

    @api.constrains("suscription_id")
    def _check_unique_suscription(self):
        for record in self:
            if record.suscription_id:
                existing = self.search(
                    [
                        ("suscription_id", "=", record.suscription_id.id),
                        ("ref", "!=", record.ref),
                    ]
                )
                if existing:
                    raise ValidationError(
                        "Al parecer ya esta asignada la suscripcio a una instancia."
                    )

    @api.constrains("subdominio", "dominios_id")
    def _check_unique_subdominio_per_dominio(self):
        for record in self:
            if record.subdominio and record.dominios_id:
                existing = self.search(
                    [
                        ("subdominio", "=", record.subdominio),
                        ("dominios_id", "=", record.dominios_id.id),
                        ("id", "!=", record.ref),
                    ]
                )
                if existing:
                    raise ValidationError("El subdominio debe ser único por dominio.")

    def action_suspend(self):
        for record in self:
            record.estado = "procesando"
            self.stop_services(service_id=record.ref)
            record.estado = "suspendido"

    def action_initialize(self):
        for record in self:
            self.with_delay().startInstancia(record)

    def action_start(self):
        for record in self:
            self.startInstancia(record)

    def startInstancia(self, record):
        logger.info("COMENZADO INSTANCIA")

        self.estado = "procesando"
        subdominio = f"{record.subdominio}." if record.subdominio else ""
        dominio = f"{subdominio}{record.dominios_id.name}"
        logger.info(f"COMENZANDO CON {dominio} id {record.ref}")
        self.create_services(
            service_id=record.ref,
            dominio=dominio,
        )
        self.estado = "running"

    def action_stop(self):
        network = "traefik"
        for record in self:
            record.estado = "procesando"
            self.stop_services(service_id=record.ref)
            # self.disconect_network(container=container, network_name=network)
            record.estado = "stop"

    def action_delete(self):
        for record in self:
            record.estado = "procesando"
            self.action_deleteAll(service_id=record.ref)

            record.estado = "stop"

    def action_deleteAll(self, service_id):
        client = docker.from_env()
        try:
            container_db = client.containers.get(f"db_{service_id}")
            container_db.stop()
            container_db.remove()
        except docker.errors.NotFound:
            pass

        try:
            container_odoo = client.containers.get(f"app_{service_id}")
            container_odoo.stop()
            container_odoo.remove()
        except docker.errors.NotFound:
            pass
        self.delete_volumes(service_id)

    def stop_service(self, service_id):
        client = docker.from_env()
        try:
            container_db = client.containers.get(f"{service_id}")
            container_db.stop()
            container_db.remove()
        except docker.errors.NotFound:
            pass

    def delete_volumes(self, service_id):
        client = docker.from_env()
        try:
            data = client.volumes.get(f"{service_id}_data")
            data.remove()
            files = client.volumes.get(f"{service_id}_files")
            files.remove()
        except docker.errors.NotFound:
            pass

    def stop_services(self, service_id):
        client = docker.from_env()
        try:
            container_db = client.containers.get(f"db_{service_id}")
            container_db.stop()
        except docker.errors.NotFound:
            pass

        try:
            container_odoo = client.containers.get(f"app_{service_id}")
            container_odoo.stop()
            return container_odoo
        except docker.errors.NotFound:
            pass

    def create_apps(self, service_id, dominio):
        client = docker.from_env()
        app = self.app_id

        # Obtener la información de la imagen Docker para la aplicación
        imagen_app = (
            app.imagenApp_id.nombreImagenDocker if app.imagenApp_id else "default_image"
        )

        # Obtener la configuración de la aplicación
        env_vars = {
            "HOST": f"db_{service_id}",
            "USER": app.userDb or "default_user",
            "PASSWORD": app.passwordDb or "default_password",
            "DB": app.nameDb or "main",
        }

        # Configurar puertos
        # expose_ports = (
        #     {f"{self.exposePortAppDesde}/tcp": self.exposePortAppHasta}
        #     if self.exposePortAppDesde and self.exposePortAppHasta
        #     else {}
        # )
        portApp = f"{app.portAppExpose}" if app.portAppExpose else "80"
        labels = {
            "traefik.enable": "true",
            f"traefik.http.routers.app_{service_id}.rule": f"Host(`{dominio}`)",
            f"traefik.http.services.app_{service_id}.loadbalancer.server.port": portApp,
            f"traefik.http.routers.app_{service_id}.entrypoints": "websecure",
            f"traefik.http.routers.app_{service_id}.tls": "true",
            f"traefik.http.routers.app_{service_id}.tls.certresolver": "myresolver",
        }
        self.stop_service(service_id=f"app_{service_id}")
        return client.containers.run(
            image=imagen_app,
            name=f"app_{service_id}",
            user="root",
            tty=True,
            command="--",
            environment=env_vars,
            # ports=expose_ports,
            volumes={
                # "/mnt/privateAddons/softer_instancias/static/config/odoo.conf": {
                #     "bind": "/etc/odoo/odoo.conf",
                #     "mode": "ro",
                # },
                f"{service_id}_files": {"bind": "/var/lib/odoo", "mode": "rw"},
            },
            detach=True,
            labels=labels,
            network="traefik",
        )

    def create_db(self, service_id):
        client = docker.from_env()

        app = self.app_id

        # Obtener la información de la imagen Docker para la base de datos
        imagen_db = (
            app.imagenDb_id.nombreImagenDocker
            if app.imagenDb_id
            else "default_db_image"
        )

        # Obtener la configuración de la base de datos
        env_vars = {
            "POSTGRES_USER": app.userDb or "default_user",
            "POSTGRES_PASSWORD": app.passwordDb or "default_password",
            "POSTGRES_DB": app.nameDb or "main",
        }

        # # Configurar puertos
        # expose_ports = (
        #     {f"{self.exposePortDbDesde}/tcp": self.exposePortDbHasta}
        #     if self.exposePortDbDesde and self.exposePortDbHasta
        #     else {}
        # )
        self.stop_service(service_id=f"db_{service_id}")
        return client.containers.run(
            image=imagen_db,
            name=f"db_{service_id}",
            user="root",
            environment=env_vars,
            # ports=expose_ports,
            volumes={
                f"{service_id}_data": {"bind": "/var/lib/postgresql/data", "mode": "rw"}
            },
            detach=True,
            network="traefik",
        )

    def wait_for_db(self, service_id, app):
        host = f"db_{service_id}"
        port = app.portDb
        user = app.userDb
        password = app.passwordDb
        dbname = app.nameDb
        timeout = 300
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                conn = psycopg2.connect(
                    host=host, port=port, user=user, password=password, dbname=dbname
                )
                conn.close()
                print("Base de datos lista para conexiones.")
                return
            except OperationalError:
                print("Esperando a que la base de datos esté lista...")
                time.sleep(5)
        print("Tiempo de espera agotado. No se pudo conectar a la base de datos.")

    def container_start(self, service_id):
        client = docker.from_env()
        container = client.containers.get(service_id)
        try:
            container.start()
        except docker.errors.APIError as e:
            print(f"Error al iniciar el contenedor {service_id}: {e}")

    def conect_network(self, container, network_name):
        client = docker.from_env()
        network = client.networks.get(network_name)

        try:
            if container:
                network.connect(container.id)
        except docker.errors.APIError as e:
            print(f"Error al conectar los contenedores a la red {network_name}: {e}")

        print(f"Contenedores conectados a la red {network_name}.")
        return network

    def disconect_network(self, container, network_name):
        client = docker.from_env()
        network = client.networks.get(network_name)
        try:
            if container:
                network.disconnect(container.id)
        except docker.errors.APIError as e:
            print(
                f"Error al desconectar los contenedores de la red {network_name}: {e}"
            )

        print(f"Contenedores desconectados de la red {network_name}.")
        return network

    def create_appInstance(self, service_id, dominio, network_name):
        try:
            self.create_apps(service_id=service_id, dominio=dominio)
            # self.conect_network(container, network_name)
        except docker.errors.APIError as e:
            print(f"Error al crear el contenedor app_{service_id}: {e}")
            raise UserError(f"Fallo crítico al crear e iniciar ODOO {e}")

    def create_dbInstance(self, service_id, network_name):
        try:
            self.create_db(service_id=service_id)
            # self.conect_network(container, network_name)
        except docker.errors.APIError as e:
            print(f"Error al crear el contenedor db_{service_id}: {e}")
            raise UserError(f"Fallo crítico al crear e iniciar DB ODOO {e}")

    def create_services(self, service_id, dominio, network="traefik"):
        app = self.app_id

        self.create_dbInstance(service_id=service_id, network_name=network)
        self.wait_for_db(service_id=service_id, app=app)

        self.create_appInstance(
            service_id=service_id,
            dominio=dominio,
            network_name=network,
        )
