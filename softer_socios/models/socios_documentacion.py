# -*- coding: utf-8 -*-

from odoo import models, fields


class TipoDocumento(models.Model):
    _name = "softer.tipo_documento"
    _description = "Tipo de Documento para Socios"

    name = fields.Char("Nombre", required=True)
    detalle = fields.Text("Detalle")


class SociosDocumentacion(models.Model):
    _name = "softer.socios_documentacion"
    _description = "Documentación de Socios"

    tipo_documento_id = fields.Many2one(
        "softer.tipo_documento", string="Tipo de Documento", required=True
    )
    socio_id = fields.Many2one(
        "res_partner.socio", string="Socio", required=True, ondelete="cascade"
    )
    fecha = fields.Date("Fecha", required=True)
    fecha_vto = fields.Date("Fecha Vencimiento")
    archivo = fields.Binary("Archivo")
    archivo_filename = fields.Char("Nombre del Archivo")
