from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SofterSyncronizerDestino(models.Model):
    _name = "softer.syncronizer.destino"
    _description = "Destino de Sincronización"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name asc"

    name = fields.Char(string="Nombre", required=True, tracking=True)
    model_id = fields.Many2one(
        "ir.model",
        string="Modelo",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    active = fields.Boolean(default=True, string="Activo", tracking=True)
    description = fields.Text(string="Descripción", tracking=True)
    create_date = fields.Datetime(
        string="Fecha de Creación", readonly=True, default=fields.Datetime.now
    )
    script_transformer = fields.Text(
        string="Script de Transformación",
        help="""Código Python para transformar los datos del origen al modelo destino.
        El script debe definir una función transform(data, nroRegistroProcesado) que recibe:
        - data: los datos del origen
        - nroRegistroProcesado: el número de registro que se está procesando

        Opcionalmente puede definir una función postCreateEdit(record_original, record_odoo) que recibe:
        - record_original: el registro original del JSON
        - record_odoo: el registro creado/actualizado en Odoo

        Ejemplo:
        def transform(data, nroRegistroProcesado):
            return {
                'name': data.get('nombre'),
                'email': data.get('correo'),
                'phone': data.get('telefono'),
                'sequence': nroRegistroProcesado
            }

        def postCreateEdit(record_original, record_odoo):
            # Acciones adicionales después de crear/editar
            if 'actividad' in record_original:
                self.env['softer.actividades'].agregar_cliente_a_actividad(
                    cliente_id=record_odoo.id,
                    nombre_actividad=record_original['actividad']
                )
        """,
        tracking=True,
    )

    def transform_data(self, data, nroRegistroProcesado, existing={}):
        """Ejecuta el script de transformación sobre los datos"""
        if not self.script_transformer:
            return data

        try:
            # Crear un diccionario local para ejecutar el script
            local_dict = {"self": self}
            # Ejecutar el script
            exec(self.script_transformer, {}, local_dict)

            # Obtener la función transform
            transform_func = local_dict.get("transform")
            if not transform_func or not callable(transform_func):
                raise Exception(
                    "El script debe definir una función 'transform(data, nroRegistroProcesado, existing)'"
                )

            # Ejecutar la transformación pasando self como primer argumento
            return transform_func(self, data, nroRegistroProcesado, existing)

        except Exception as e:
            _logger.error("Error en el script de transformación: %s", str(e))
            raise Exception(f"Error en el script de transformación: {str(e)}")

    def postCreateEdit(self, record_original, record_odoo):
        """Ejecuta la función postCreateEdit del script si existe"""
        if not self.script_transformer:
            return

        try:
            # Crear un diccionario local para ejecutar el script
            local_dict = {"self": self}
            # Ejecutar el script
            exec(self.script_transformer, {}, local_dict)

            # Obtener la función postCreateEdit
            post_edit_func = local_dict.get("postCreateEdit")
            if post_edit_func and callable(post_edit_func):
                post_edit_func(self, record_original, record_odoo)

        except Exception as e:
            _logger.error("Error en postCreateEdit: %s", str(e))
            raise Exception(f"Error en postCreateEdit: {str(e)}")
