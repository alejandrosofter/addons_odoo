# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class Actividades(models.Model):
    _name = "softer.actividades"
    _description = "Modelo de Actividades"

    name = fields.Char(
        string="Nombre",
        required=True,
    )
    genero = fields.Selection(
        selection=[
            ("M", "Masculino"),
            ("F", "Femenino"),
            ("Todos", "Todos"),
        ],
        string="Género",
        default="Todos",
    )
    estado = fields.Selection(
        [
            ("activa", "Activa"),
            ("suspendida", "Suspendida"),
            ("baja", "Baja"),
        ],
        string="Estado",
    )
    categoria_suscripcion = fields.Many2one(
        "softer.suscripcion.categoria",
        string="Categoría de Suscripción",
        help="Categoría que se asignará a las suscripciones generadas",
    )
    entrenador = fields.Many2one("res.partner", string="Entrenador")
    administrador = fields.Many2one("res.partner", string="Administrador")
    tipoRangos = fields.Selection(
        [
            ("porFechaNacimiento", "Por Fecha Nacimiento"),
            ("libre", "Libre"),
        ],
        string="Tipo de Rango",
    )

    fechaDesde = fields.Date(string="Rango Desde", tracking=True)
    fechaHasta = fields.Date(string="Rango Hasta", tracking=True)
    integrantes = fields.One2many(
        "softer.actividades.integrantes", "actividad_id", string="Integrantes"
    )
    horarios = fields.One2many(
        "softer.actividades.horarios", "actividad_id", string="Horarios"
    )
    productosAsociados = fields.One2many(
        "softer.actividades.productos", "actividad_id", string="Productos Asociados"
    )
    registroSuscripciones = fields.Text(
        string="Registro de Suscripciones",
        readonly=True,
        help="Registro histórico de suscripciones generadas",
    )
    mensajes = fields.One2many(
        "softer.actividades.mensajes", "actividad_id", string="Mensajes"
    )

    def agregar_cliente_a_actividad(self, cliente_id, nombre_actividad=False):
        """
        Agrega un cliente a una actividad existente o crea una nueva basada en el rango de fechas
        Args:
            cliente_id (int): ID del cliente a agregar
            nombre_actividad (str): Nombre opcional de la actividad a la que se quiere agregar
        Returns:
            dict: Diccionario con el resultado de la operación
        """
        try:
            print(f"agregando cliente {cliente_id} a actividad {nombre_actividad}")
            # Verificar que el cliente existe y es un jugador
            cliente = self.env["res.partner"].browse(cliente_id)
            if not cliente.exists():
                return {"success": False, "message": "El cliente no existe."}

            # Validación de género
            if nombre_actividad:
                actividad = self.search([("name", "=", nombre_actividad)], limit=1)
                if (
                    actividad
                    and actividad.genero != "Todos"
                    and actividad.genero != cliente.genero
                ):
                    return {
                        "success": False,
                        "message": f"El género del cliente no coincide con el requerido por la actividad ({actividad.genero}).",
                    }

            # Buscar el contacto del cliente (el mismo cliente en este caso)
            cliente_contacto_id = cliente.id
            # Si se proporciona nombre de actividad, buscar esa actividad
            if nombre_actividad:
                actividad = self.search([("name", "=", nombre_actividad)], limit=1)
                if not actividad:
                    # crear actividad con ese nombre

                    actividad = (
                        self.env["softer.actividades"]
                        .sudo()
                        .create(
                            {
                                "name": nombre_actividad,
                                "tipoRangos": "libre",
                            }
                        )
                    )
            else:
                # Buscar una actividad con rango por fecha de nacimiento que coincida
                domain = [
                    ("tipoRangos", "=", "porFechaNacimiento"),
                    ("fechaDesde", "<=", cliente.fechaNacimiento),
                    ("fechaHasta", ">=", cliente.fechaNacimiento),
                    ("estado", "=", "activa"),
                ]
                # Agregar filtro de género si es necesario
                domain.append("|")
                domain.append(("genero", "=", "Todos"))
                domain.append(("genero", "=", cliente.genero))

                actividad = self.search(domain, limit=1)

                if not actividad:
                    actividad = self.search(
                        [
                            ("name", "=", "Sin rango"),
                        ],
                        limit=1,
                    )
                    if not actividad:
                        actividad = (
                            self.env["softer.actividades"]
                            .sudo()
                            .create(
                                {
                                    "name": "Sin rango",
                                    "tipoRangos": "libre",
                                }
                            )
                        )

            # Agregar el cliente a la actividad
            resultado = actividad.agregar_integrante(
                cliente_id=cliente.id,
                cliente_contacto_id=cliente_contacto_id,
            )

            if resultado["success"]:
                return {
                    "success": True,
                    "message": f'Cliente agregado exitosamente a la actividad "{actividad.name}".',
                }
            else:
                return resultado

        except Exception as e:
            return {
                "success": False,
                "message": f"Error al agregar cliente a la actividad: {str(e)}",
            }

    def agregar_integrante(self, cliente_id, cliente_contacto_id):
        """
        Agrega un integrante a la actividad
        Args:
            cliente_id (int): ID del cliente (integrante)
            cliente_contacto_id (int): ID del contacto del cliente
        Returns:
            dict: Diccionario con el resultado de la operación
        """
        try:
            # Verificar si el cliente ya está en la actividad
            integrante_existente = self.env["softer.actividades.integrantes"].search(
                [("actividad_id", "=", self.id), ("cliente_id", "=", cliente_id)]
            )

            if integrante_existente:
                return {
                    "success": False,
                    "message": f"El cliente ya está registrado en esta actividad.",
                }

            # Crear el nuevo integrante
            vals = {
                "actividad_id": self.id,
                "cliente_id": cliente_id,
                "cliente_contacto": cliente_contacto_id,
                "estado": "activo",
            }

            self.env["softer.actividades.integrantes"].create(vals)

            return {"success": True, "message": "Integrante agregado exitosamente."}

        except Exception as e:
            return {
                "success": False,
                "message": f"Error al agregar integrante: {str(e)}",
            }

    def action_create_subscriptions(self):
        """Genera suscripciones para los integrantes basado en los productos asociados"""
        self.ensure_one()

        # Validar si hay productos asociados
        if not self.productosAsociados:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Advertencia",
                    "message": 'No hay productos asociados a esta actividad. Por favor, agregue productos en la pestaña "Condiciones (suscripciones)".',
                    "type": "warning",
                    "sticky": True,
                },
            }

        AltaModel = self.env["softer.suscripcion.alta"]
        altas_creadas = 0
        registro_nuevo = ""

        for integrante in self.integrantes.filtered(lambda i: i.estado == "activo"):
            # Verificar si el integrante ya tiene una alta activa
            alta_integrante = self.env["softer.suscripcion.alta"].search(
                [
                    ("idActividad", "=", self.id),
                    ("cliente_id", "=", integrante.cliente_id.id),
                    # ("state", "=", "done"),
                ],
                limit=1,
            )

            if alta_integrante:
                registro_nuevo += (
                    f"[{fields.Datetime.now()}] Cliente: {integrante.cliente_id.name} - "
                    f"Ya tiene una alta activa: {alta_integrante.name}\n"
                )
                continue

            # Crear un alta por integrante
            vals_alta = {
                "cliente_id": integrante.cliente_id.id,
                "fecha": fields.Date.today(),
                "fecha_inicio": fields.Date.today(),
                "idActividad": self.id,
                "categoria_id": (
                    self.categoria_suscripcion.id
                    if self.categoria_suscripcion
                    else False
                ),
                "product_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": producto.producto_id.id,
                            "quantity": producto.cantidad,
                            "es_indefinido": producto.esIndefinida,
                            "es_unica": producto.esUnica,
                            "fecha_fin": (
                                False if producto.esIndefinida else producto.fechaFin
                            ),
                            "es_debito_automatico": producto.paga_debito_automatico,
                        },
                    )
                    for producto in self.productosAsociados
                ],
            }

            try:
                nueva_alta = AltaModel.create(vals_alta)
                # Confirmar el alta
                nueva_alta.action_confirm()
                altas_creadas += 1

                # Registrar las altas creadas
                fecha_actual = fields.Datetime.now()
                registro_nuevo += (
                    f"[{fecha_actual}] Cliente: {integrante.cliente_id.name} - "
                    f"Alta: {nueva_alta.name}\n"
                )
            except Exception as e:
                fecha_actual = fields.Datetime.now()
                registro_nuevo += (
                    f"[{fecha_actual}] ERROR - Cliente: {integrante.cliente_id.name} - "
                    f"Error: {str(e)}\n"
                )
                _logger.error(
                    "Error al crear alta para cliente %s: %s",
                    integrante.cliente_id.name,
                    str(e),
                )
                continue

        # Actualizar el registro
        if registro_nuevo:
            registro_actual = self.registroSuscripciones or ""
            self.registroSuscripciones = registro_nuevo + registro_actual

        if altas_creadas > 0:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Éxito",
                    "message": f"Se han generado {altas_creadas} altas para los integrantes.",
                    "type": "success",
                    "sticky": False,
                },
            }
        else:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Información",
                    "message": "No se crearon nuevas altas. Todos los integrantes ya tienen altas activas.",
                    "type": "info",
                    "sticky": False,
                },
            }

    def action_grant_system_access_team(self):
        """Otorga acceso al sistema a todos los integrantes del equipo"""
        integrantes_sin_acceso = self.env["softer.actividades.integrantes"].search(
            [
                ("actividad_id", "=", self.id),
                ("tiene_acceso_sistema", "=", False),
                ("cliente_contacto.vat", "!=", False),
            ]
        )

        if not integrantes_sin_acceso:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Información",
                    "message": "No hay integrantes sin acceso al sistema en este equipo",
                    "type": "info",
                },
            }

        for integrante in integrantes_sin_acceso:
            integrante.action_grant_system_access()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Éxito",
                "message": f"Se han creado {len(integrantes_sin_acceso)} accesos al sistema para el equipo",
                "type": "success",
            },
        }


class ActividadesProductos(models.Model):
    _name = "softer.actividades.productos"
    _description = "Productos Asociados a Actividades"

    actividad_id = fields.Many2one("softer.actividades", string="Actividad")
    producto_id = fields.Many2one("product.product", string="Producto", required=True)
    cantidad = fields.Integer(string="Cantidad", default=1)
    fechaInicio = fields.Date(string="Fecha Inicio")
    fechaFin = fields.Date(string="Fecha Fin")
    esIndefinida = fields.Boolean(string="Es Indefinida", default=False)
    esUnica = fields.Boolean(string="Es Unica", default=False)
    paga_debito_automatico = fields.Boolean(
        string="Paga Débito Automático",
        default=False,
        help="Indica si este producto se paga mediante débito automático",
    )

    @api.onchange("esIndefinida")
    def _onchange_esIndefinida(self):
        if self.esIndefinida:
            self.fechaFin = False


class ActividadesMensajes(models.Model):
    _name = "softer.actividades.mensajes"
    _description = "Mensajes de WhatsApp para Actividades"
    _order = "fecha_hora desc"

    actividad_id = fields.Many2one(
        "softer.actividades", string="Actividad", required=True, ondelete="cascade"
    )
    fecha_hora = fields.Datetime(
        string="Fecha y Hora", default=lambda self: fields.Datetime.now(), required=True
    )
    tipo_mensaje = fields.Selection(
        [("text", "Texto"), ("media", "Multimedia")],
        string="Tipo de Mensaje",
        required=True,
    )
    archivo = fields.Binary(string="Archivo")
    nombre_archivo = fields.Char(string="Nombre del Archivo")
    texto = fields.Text(string="Mensaje")
    registro = fields.Text(
        string="Registro de Envío", help="Registro de a quiénes se envió el mensaje"
    )

    @api.model_create_multi
    def create(self, vals_list):
        mensajes = super().create(vals_list)
        for mensaje in mensajes:
            mensaje._enviar_mensajes_integrantes()
        return mensajes

    def _enviar_mensajes_integrantes(self):
        """Envía el mensaje a todos los integrantes de la actividad"""
        self.ensure_one()
        registro = []

        # Obtener la instancia activa de Evolution API
        instance = self.env["evolution.api.numbers"].search(
            [("estado", "=", "active")], limit=1
        )

        if not instance:
            raise ValidationError("No hay una instancia activa de Evolution API")

        # Obtener todos los integrantes activos con teléfono
        integrantes = self.actividad_id.integrantes.filtered(
            lambda i: i.estado == "activo" and i.cliente_contacto.phone
        )

        for integrante in integrantes:
            try:
                if self.tipo_mensaje == "text":
                    # Enviar mensaje de texto
                    self.env["evolution.api.message"].sudo().create(
                        {
                            "number_id": instance.id,
                            "numeroDestino": integrante.cliente_contacto.phone,
                            "type": "text",
                            "text": self.texto,
                        }
                    )
                else:
                    # Enviar mensaje multimedia
                    self.env["evolution.api.message"].sudo().create(
                        {
                            "number_id": instance.id,
                            "numeroDestino": integrante.cliente_contacto.phone,
                            "type": "media",
                            "text": self.texto or "",
                            "media": self.archivo,
                            "filename": self.nombre_archivo,
                        }
                    )

                registro.append(
                    f"{integrante.cliente_id.name} ({integrante.cliente_contacto.phone}) - Enviado"
                )
            except Exception as e:
                registro.append(
                    f"{integrante.cliente_id.name} ({integrante.cliente_contacto.phone}) - Error: {str(e)}"
                )

        # Actualizar el registro
        self.registro = "\n".join(registro)
