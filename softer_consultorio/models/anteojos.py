# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AnteojosOpciones(models.Model):
    _name = "consultorio.anteojos_opciones"
    _description = "Opciones de Anteojos"
    name = fields.Char(string="Opcion")


class AnteojosRecetasOpciones(models.Model):
    _name = "consultorio.recetas.opciones"
    _description = "Opciones de Anteojos"
    opcion = fields.Many2one("consultorio.anteojos_opciones", string="Opcion")
    anteojo_id = fields.Many2one("consultorio.anteojos", string="Anteojo")  # Agregado


class AnteojosGraduaciones(models.Model):
    _name = "consultorio.anteojos_graduaciones"
    _description = "Graduaciones de Anteojos"

    name = fields.Char(string="Graduacion")
    anteojo_id = fields.Many2one("consultorio.anteojos", string="Anteojo")

    tipoAnteojo = fields.Selection(
        [
            ("cerca", "Para Cerca"),
            ("lejos", "Para Lejos"),
            ("intermedio", "Para Intermedio"),
        ],
        string="Tipo Anteojo",
    )

    # Campos para el ojo izquierdo
    izquierdo_esNeutro = fields.Boolean(string="Es neutro")
    izquierdo_sinCambio = fields.Boolean(string="Sin Cambio")
    izquierdo_adicionar = fields.Boolean(string="Adicionar")
    izquierdo_adicion = fields.Integer(string="Cantidad Adicion")
    izquierdo_adicionEsferico = fields.Integer(string="Adicion Esferico")
    izquierdo_esfera = fields.Integer(string="Esfera")
    izquierdo_cilindro = fields.Integer(string="Cilindro")
    izquierdo_eje = fields.Integer(string="Eje")
    izquierdo_piso = fields.Integer(string="Piso")

    # Campos para el ojo derecho
    derecho_esNeutro = fields.Boolean(string="Es neutro")
    derecho_sinCambio = fields.Boolean(string="Sin Cambio")
    derecho_adicionar = fields.Boolean(string="Adicionar")
    derecho_adicion = fields.Integer(string="Cantidad Adicion")
    derecho_adicionEsferico = fields.Integer(string="Adicion Esferico")
    derecho_esfera = fields.Integer(string="Esfera")
    derecho_cilindro = fields.Integer(string="Cilindro")
    derecho_eje = fields.Integer(string="Eje")
    derecho_piso = fields.Integer(string="Piso")


# class AnteojosGraduaciones(models.Model):
#     _name = "consultorio.anteojos_graduaciones"
#     _description = "Graduaciones de Anteojos"
#     name = fields.Char(string="Graduacion")
#     anteojo_id = fields.Many2one("consultorio.anteojos", string="Anteojo")  # Agregado

#     tipoAnteojo = fields.Selection(
#         [
#             ("cerca", "Para Cerca"),
#             ("lejos", "Para Lejos"),
#             ("intermedio", "Para Intermedio"),
#         ],
#         string="Tipo Anteojo",
#     )
#     ojo = fields.Selection(
#         [("izquierda", "Izquierda"), ("derecha", "Derecha"), ("ambos", "Ambos")]
#     )
#     esNeutro = fields.Boolean(string="Es neutro")
#     sinCambio = fields.Boolean(string="Sin Cambio")
#     adicionar = fields.Boolean(string="Adicionar")
#     adicion = fields.Integer(string="Cantidad Adicion")
#     adicionEsferico = fields.Integer(string="Adicion Esferico")
#     esfera = fields.Integer(string="Esfera")
#     cilindro = fields.Integer(string="Cilindro")
#     eje = fields.Integer(string="Eje")
#     piso = fields.Integer(string="Piso")


class Anteojos(models.Model):
    _name = "consultorio.anteojos"
    _description = "Anteojos"
    receta_id = fields.Many2one(
        "consultorio.recetas", string="Receta", ondelete="cascade"
    )
    observaciones = fields.Text(string="Observaciones")

    graduaciones = fields.One2many(
        "consultorio.anteojos_graduaciones", "anteojo_id", string="Lentes"
    )
    opciones = fields.One2many(
        "consultorio.recetas.opciones", "anteojo_id", string="Opciones"
    )
