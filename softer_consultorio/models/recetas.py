# -*- coding: utf-8 -*-
from odoo import models, fields, api


class RecetasAnteojos(models.Model):
    _name = "consultorio.recetas.anteojos"
    _description = "Anteojos en Receta"

    receta_id = fields.Many2one(
        "consultorio.recetas", string="Receta", ondelete="cascade"
    )
    anteojo_id = fields.Many2one(
        "consultorio.anteojos", string="Anteojo", required=True
    )
    cantidad = fields.Integer(string="Cantidad", default=1)
    detalle = fields.Text(string="Nota")


class RecetasPrestaciones(models.Model):
    _name = "consultorio.recetas.prestaciones"
    _description = "Prestaciones en Receta"

    receta_id = fields.Many2one(
        "consultorio.recetas", string="Receta", ondelete="cascade"
    )
    prestacion_id = fields.Many2one(
        "consultorio.prestaciones", string="Prestacion", required=True
    )
    cantidad = fields.Integer(string="Cantidad", default=1)
    detalle = fields.Text(string="Nota")


class RecetasDiagnosticos(models.Model):
    _name = "consultorio.recetas.diagnosticos"
    _description = "Indicaciones en Receta"

    receta_id = fields.Many2one(
        "consultorio.recetas", string="Receta", ondelete="cascade"
    )
    diagnostico_id = fields.Many2one(
        "consultorio.diagnosticos", string="Diagnostico", required=True
    )
    detalle = fields.Text(string="Detalle")

    @api.onchange("diagnostico_id")
    def _onchange_diagnostico(self):
        if self.diagnostico_id:
            self.detalle = self.diagnostico_id.detalle


class RecetasIndicaciones(models.Model):
    _name = "consultorio.recetas.indicaciones"
    _description = "Indicaciones en Receta"

    receta_id = fields.Many2one(
        "consultorio.recetas", string="Receta", ondelete="cascade"
    )
    indicacion_id = fields.Many2one(
        "consultorio.indicaciones", string="Indicacion", required=True
    )
    detalle = fields.Text(string="Detalle")

    @api.onchange("indicacion_id")
    def _onchange_indicacion(self):
        if self.indicacion_id:
            self.detalle = self.indicacion_id.detalle


class RecetasMedicamentos(models.Model):
    _name = "consultorio.recetas.medicamentos"
    _description = "Medicamentos en Receta"

    receta_id = fields.Many2one(
        "consultorio.recetas", string="Receta", ondelete="cascade"
    )
    medicamento_id = fields.Many2one(
        "consultorio.medicamentos", string="Medicamento", required=True
    )
    cantidad = fields.Integer(string="Cantidad", default=1)
    posologia_ids = fields.Many2one("consultorio.posologia", string="Posología")


class Recetas(models.Model):
    _name = "consultorio.recetas"
    _description = "Recetas"

    paciente = fields.Many2one("consultorio.pacientes", string="Paciente")
    ref = fields.Char(string="Referencia", hide=True)
    fecha = fields.Date(string="Fecha")
    name = fields.Char(string="Receta", related="paciente.name", store=True)
    esParticular = fields.Boolean(string="Particular")  # Campo independiente y editable
    obraSocial = fields.Many2one("consultorio.obrasociales", string="Obra Social")
    medicamentos_ids = fields.One2many(
        "consultorio.recetas.medicamentos", "receta_id", string="Medicamentos"
    )
    indicaciones_ids = fields.One2many(
        "consultorio.recetas.indicaciones", "receta_id", string="Indicaciones"
    )
    diagnosticos_ids = fields.One2many(
        "consultorio.recetas.diagnosticos", "receta_id", string="Diagnosticos"
    )
    prestaciones_ids = fields.One2many(
        "consultorio.recetas.prestaciones", "receta_id", string="Prestaciones"
    )
    anteojos_ids = fields.One2many(
        "consultorio.anteojos", "receta_id", string="Anteojos"
    )

    def getObraSocialDefault(self, obrasSociales):
        if not obrasSociales:
            return False
        for record in obrasSociales:
            if record.esDefault:
                return record
        return obrasSociales[0] if obrasSociales else False

    @api.onchange("paciente")
    def _onchange_paciente(self):
        if self.paciente:
            # Asigna el valor de esParticular del paciente seleccionado
            default_obrasocial = self.getObraSocialDefault(self.paciente.obrasSociales)
            self.esParticular = self.paciente.esParticular
            self.obraSocial = (
                default_obrasocial.obrasocial if default_obrasocial else False
            )
