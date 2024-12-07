# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Imagenes(models.Model):
    _name = "instancias.imagenes"
    _description = "Imagenes"

    lastUpdate = fields.Date(string="Ultimas Actualizaciones")
    name = fields.Char(string="Nombre Imagen")
    nombreImagenDocker = fields.Char(string="Nombre de Imagen Docker")
    tipo = fields.Selection(
        [
            ("dockerfile", "Dockerfile"),
            ("dockerhub", "Dockerhub"),
        ],
        string="Tipo de Imagen",
        default="dockerhub",
    )
    version = fields.Char(string="Version")
    esDockerhub = fields.Boolean(string="Es Dockerhub")
    dockerfile = fields.Text(string="Dockerfile")
    # lista estado
    estado = fields.Selection(
        [
            ("activa", "Activa"),
            ("inactiva", "Inactiva"),
        ],
        string="Estado",
        default="activa",
    )
