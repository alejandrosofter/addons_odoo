# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SociosCategoria(models.Model):
    _name = "socios.categoria"
    _description = "Categorías de Socios"
    _order = "name"

    name = fields.Char(string="Nombre", required=True, index=True)
    proximoNroSocio = fields.Integer(
        string="Próximo Número de Socio", default=1, required=True
    )
    descripcion = fields.Text(string="Descripción")

    def next_nroSocio(self):
        """Busca el próximo número de socio disponible para esta categoría"""
        self.ensure_one()
        # Buscar el número más alto usado en esta categoría
        max_nro = (
            self.env["socios.socio"]
            .search(
                [("categoria_id", "=", self.id)],
                order="member_number desc",
                limit=1,
            )
            .member_number
        )

        if max_nro:
            # Convertir a número y sumar 1
            try:
                next_nro = int(max_nro) + 1
            except ValueError:
                # Si no es un número válido, usar el próximo configurado
                next_nro = self.proximoNroSocio
        else:
            # Si no hay socios, usar el próximo configurado
            next_nro = self.proximoNroSocio if self.proximoNroSocio else 1

        # Actualizar el próximo número en la categoría
        self.proximoNroSocio = next_nro
        return str(next_nro)
