# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _generate_pos_order_invoice(self):
        """
        Sobrescribe el método para validar automáticamente la factura con AFIP
        si el diario tiene configuración AFIP.

        Cuando se crea una factura desde el punto de venta, Odoo la crea en
        estado 'draft' y no la valida automáticamente. Este método asegura que
        si el diario tiene configuración AFIP, la factura se valide
        inmediatamente para que se impute en AFIP sin necesidad de validarla
        manualmente.

        Returns:
            dict: Diccionario de acción de ventana (ir.actions.act_window)
        """
        invoice_action = super(PosOrder, self)._generate_pos_order_invoice()

        # Verificar que se haya creado una acción válida
        if not invoice_action:
            return invoice_action

        # El método original devuelve un diccionario de acción
        # (ir.actions.act_window) con res_id que contiene el ID de la factura
        # creada
        if not isinstance(invoice_action, dict):
            # Si no es un diccionario, devolverlo tal cual
            return invoice_action

        # Verificar que sea una acción de ventana para account.move
        if invoice_action.get("res_model") != "account.move" or not invoice_action.get(
            "res_id"
        ):
            # No es una acción de factura válida, devolver tal cual
            return invoice_action

        # Obtener la factura real usando el res_id
        invoice_id = invoice_action.get("res_id")
        invoice = self.env["account.move"].browse(invoice_id)

        # Verificar que la factura exista y tenga un diario asignado
        if not invoice.exists() or not invoice.journal_id:
            return invoice_action

        journal = invoice.journal_id

        # Verificar si el diario tiene configuración AFIP
        # RLI_RLM = Régimen de Liquidación Inmediata /
        #           Régimen de Liquidación Mensual
        # FEERCEL = Facturación Electrónica E-Commerce
        has_afip_config = bool(
            journal.l10n_ar_afip_pos_system in ["RLI_RLM", "FEERCEL"]
            and journal.afip_ws
        )

        # Debug: imprimir valores de invoice y has_afip_config
        print("=" * 80)
        print("DEBUG línea 65:")
        print("  invoice:", invoice)
        print("  invoice.id:", invoice.id if invoice else "None")
        print("  invoice.state:", invoice.state if invoice else "None")
        print(
            "  invoice.afip_auth_code:", invoice.afip_auth_code if invoice else "None"
        )
        print(
            "  invoice.journal_id:",
            invoice.journal_id.name if invoice.journal_id else "None",
        )
        print(
            "  journal.l10n_ar_afip_pos_system:",
            journal.l10n_ar_afip_pos_system if journal else "None",
        )
        print("  journal.afip_ws:", journal.afip_ws if journal else "None")
        print("  has_afip_config:", has_afip_config)
        print("=" * 80)

        # Validar si tiene configuración AFIP
        # Si la factura está en draft, validarla completamente
        # Si la factura ya está posted pero no tiene CAE, solicitar el CAE
        if has_afip_config:
            try:
                if invoice.state == "draft":
                    # Validar la factura completamente (action_post llama a do_pyafipws_request_cae)
                    invoice.action_post()
                    _logger.info(
                        "Factura %s (ID: %s) validada automáticamente en AFIP "
                        "desde POS. CAE: %s"
                        % (
                            invoice.name or "N/A",
                            invoice.id,
                            invoice.afip_auth_code or "Pendiente",
                        )
                    )
                elif invoice.state == "posted" and not invoice.afip_auth_code:
                    # La factura ya está validada pero no tiene CAE
                    # Llamar directamente a do_pyafipws_request_cae()
                    invoice.do_pyafipws_request_cae()
                    _logger.info(
                        "CAE solicitado para factura %s (ID: %s) desde POS. "
                        "CAE: %s"
                        % (
                            invoice.name or "N/A",
                            invoice.id,
                            invoice.afip_auth_code or "Pendiente",
                        )
                    )
            except Exception as e:
                _logger.error(
                    "Error al validar factura %s (ID: %s) en AFIP desde POS: "
                    "%s. La factura quedará sin validar en AFIP."
                    % (invoice.name or "N/A", invoice.id, str(e))
                )
                # No levantamos la excepción para no interrumpir el flujo
                # del POS pero logueamos el error para diagnóstico
                # El usuario podrá validar manualmente desde el módulo de
                # facturación

        # Devolver el diccionario de acción original sin modificar
        return invoice_action
