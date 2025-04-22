# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SociosPendientesActividadWizard(models.TransientModel):
    _name = "socios.pendientes.actividad.wizard"
    _description = "Wizard para buscar socios pendientes"

    message = fields.Text(
        string="Mensaje",
        readonly=True,
    )

    def action_confirm(self):
        """Ejecuta la búsqueda de socios pendientes"""
        self.ensure_one()
        _logger.info("Iniciando búsqueda de socios pendientes")

        # Buscar actividades activas
        actividades = self.env["softer.actividades"].search([("estado", "=", "activa")])
        _logger.info(f"Se encontraron {len(actividades)} actividades activas")

        contador = 0
        contador_existentes = 0
        contador_pendientes = 0
        for actividad in actividades:
            _logger.info(f"Procesando actividad: {actividad.id} - {actividad.name}")

            # Buscar integrantes de la actividad
            integrantes = self.env["softer.actividades.integrantes"].search(
                [("actividad_id", "=", actividad.id)]
            )
            _logger.info(
                f"Se encontraron {len(integrantes)} integrantes en la actividad"
            )

            for integrante in integrantes:
                _logger.info(f"Procesando integrante: {integrante.id}")
                _logger.info(
                    f"Cliente socio: {integrante.cliente_id.id} - "
                    f"{integrante.cliente_id.name}"
                )
                if integrante.excluir_socio:
                    _logger.info(f"Integrante {integrante.id} tiene excluido el socio")
                    continue

                # Verificar si ya existe un socio
                socio = self.env["socios.socio"].search(
                    [("partner_id", "=", integrante.cliente_id.id)],
                    limit=1,
                )

                if socio:
                    _logger.info(
                        f"Ya existe socio {socio.id} para el integrante "
                        f"{integrante.id} ({integrante.cliente_id.name})"
                    )
                    contador_existentes += 1
                    continue

                # Verificar si ya existe un registro pendiente
                pendiente = self.env["socios.pendientes.actividad"].search(
                    [
                        ("socio", "=", integrante.cliente_id.id),
                        ("estado", "=", "pendiente"),
                    ],
                    limit=1,
                )

                if pendiente:
                    _logger.info(
                        f"Ya existe registro pendiente {pendiente.id} para el "
                        f"integrante {integrante.id} ({integrante.cliente_id.name})"
                    )
                    contador_pendientes += 1
                    continue
                vals = {
                    "integrante_id": integrante.id,
                    "cliente_facturacion": integrante.cliente_contacto.id,
                    "socio": integrante.cliente_id.id,
                    "es_debito_automatico": integrante.es_debito_automatico,
                    "dni": integrante.cliente_id.vat,
                    "fecha_nacimiento": integrante.fechaNacimiento,
                    "telefono": integrante.telefono_whatsapp,
                    "email": integrante.cliente_contacto.email,
                    "domicilio": integrante.cliente_id.street,
                    "categoria_suscripcion": actividad.categoria_suscripcion.id,
                }
                # Crear registro pendiente
                self.env["socios.pendientes.actividad"].create(vals)
                contador += 1

        _logger.info(
            f"Proceso completado. Se crearon {contador} registros pendientes, "
            f"se encontraron {contador_existentes} socios existentes y "
            f"{contador_pendientes} registros pendientes existentes"
        )

        # Cerrar el wizard y redirigir a la vista de socios pendientes
        return {
            "type": "ir.actions.act_window",
            "name": "Socios Pendientes",
            "res_model": "socios.pendientes.actividad",
            "view_mode": "tree,form",
            "target": "current",
            "context": {
                "search_default_estado": "pendiente",
            },
            "domain": [("estado", "=", "pendiente")],
        }
