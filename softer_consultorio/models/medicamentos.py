# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Medicamentos(models.Model):
    _name = "consultorio.medicamentos"
    _description = "Medicamentos"
    name = fields.Char(string="Nombre Comercial")

    nameGenerico = fields.Char(string="Nombre Generico")
    presentacion = fields.Char(string="Presentación")
    laboratorio = fields.Char(string="Laboratorio")
    accionTerapeutica = fields.Many2one(
        "consultorio.accionterapeutica", string="Accion Terapeutica"
    )
    posologia_ids = fields.Many2one("consultorio.posologia", string="Posología")


class MedicamentosAccionTerapeurica(models.Model):
    _name = "consultorio.accionterapeutica"
    _description = "Accion Terapeutica"
    name = fields.Char(string="Nombre")


class Posologias(models.Model):
    _name = "consultorio.posologia"
    _description = "Posología"
    name = fields.Char(string="Posología")
    cantidad = fields.Integer(string="Cantidad")
    presentacion = fields.Char(string="Presentación")
    horas = fields.Integer(string="Horas")
    dias = fields.Integer(string="Dias")
