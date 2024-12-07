# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Apps(models.Model):
    _name = "instancias.apps"
    _description = "Apps"

    name = fields.Char(string="Nombre", required=True)
    version = fields.Char(string="Version")
    tieneDb = fields.Boolean(string="Tiene DB")
    userDb = fields.Char(string="Usuario DB")
    passwordDb = fields.Char(string="Password DB")
    nameDb = fields.Char(string="Nombre DB")
    portDb = fields.Char(string="Puerto DB")
    portAppExpose = fields.Char(string="Puerto App Expose")

    imagenDb_id = fields.Many2one("instancias.imagenes", string="Imagen DB")
    imagenApp_id = fields.Many2one(
        "instancias.imagenes", string="Imagen App", required=True
    )

    @api.constrains(
        "tieneDb", "userDb", "passwordDb", "nameDb", "portDb", "imagenDb_id"
    )
    def _check_db_fields_required(self):
        for record in self:
            if record.tieneDb:
                if not record.userDb:
                    raise ValidationError(
                        "El campo Usuario DB es obligatorio cuando Tiene DB está marcado."
                    )
                if not record.passwordDb:
                    raise ValidationError(
                        "El campo Password DB es obligatorio cuando Tiene DB está marcado."
                    )
                if not record.nameDb:
                    raise ValidationError(
                        "El campo Nombre DB es obligatorio cuando Tiene DB está marcado."
                    )
                if not record.portDb:
                    raise ValidationError(
                        "El campo Puerto DB es obligatorio cuando Tiene DB está marcado."
                    )
                if not record.imagenDb_id:
                    raise ValidationError(
                        "El campo Imagen DB es obligatorio cuando Tiene DB está marcado."
                    )

    def get_docker_image_info(self):
        """
        Obtiene la información de las imágenes Docker asociadas a esta aplicación.
        """
        for record in self:
            imagen_db = record.imagenDb_id
            imagen_db_nombre = imagen_db.nombreImagenDocker if imagen_db else "N/A"

            imagen_app = record.imagenApp_id
            imagen_app_nombre = imagen_app.nombreImagenDocker if imagen_app else "N/A"

            return {
                "imagen_db_nombre": imagen_db_nombre,
                "imagen_app_nombre": imagen_app_nombre,
            }
