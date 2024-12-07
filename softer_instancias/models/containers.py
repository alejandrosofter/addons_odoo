from odoo import models, fields, api
import docker
import time


class Containers:
    def __init__(self):
        self.client = docker.from_env()

    def create_container(self, image, name, environment, ports, volumes, labels=None):
        try:
            container = self.client.containers.run(
                image=image,
                name=name,
                user="root",
                environment=environment,
                ports=ports,
                volumes=volumes,
                detach=True,
                labels=labels,
            )
            return container
        except docker.errors.APIError as e:
            print(f"Error al crear el contenedor {name}: {e}")
            return None

    def start_container(self, container_id):
        try:
            container = self.client.containers.get(container_id)
            container.start()
        except docker.errors.APIError as e:
            print(f"Error al iniciar el contenedor {container_id}: {e}")

    def stop_container(self, container_id):
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            pass

    def wait_for_container(self, container_id, status="running"):
        while True:
            try:
                container = self.client.containers.get(container_id)
                if container.status == status:
                    print(f"Contenedor {container_id} está listo.")
                    break
            except docker.errors.NotFound:
                pass
            time.sleep(5)  # Esperar 5 segundos antes de volver a verificar

    def connect_to_network(self, container, network_name):
        try:
            network = self.client.networks.get(network_name)
            network.connect(container.id)
            print(f"Contenedor {container.id} conectado a la red {network_name}.")
        except docker.errors.NotFound as e:
            print(
                f"Error al conectar el contenedor {container.id} a la red {network_name}: {e}"
            )
