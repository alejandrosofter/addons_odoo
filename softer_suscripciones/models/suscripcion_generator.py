# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError


class SuscripcionGenerator(models.Model):
    _name = "softer.suscripcion.generator"
    _description = "Generador de Suscripciones"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    fecha = fields.Date(
        string="Fecha",
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    forzar_generacion = fields.Boolean(
        string="Forzar generación",
        help="Si está tildado, se generarán ítems y órdenes de venta sin "
        "realizar chequeos de exclusión ni periodicidad. Solo se respeta el "
        "estado de la suscripción y los flags de línea.",
        default=False,
    )
    item_ids = fields.One2many(
        "softer.suscripcion.generator.item",
        "generator_id",
        string="Items de Suscripción",
        required=True,
    )
    log = fields.Text(
        string="Log de generación",
        readonly=True,
        help="Resumen de la operación de generación de órdenes.",
    )

    def logear(self, data_registro):
        """
        Guarda un resumen de la operación de generación en el campo log.
        data_registro: dict con claves:
            - total_chequeadas
            - total_generadas
            - total_existentes
            - ordenes_generadas (lista de str)
            - ordenes_existentes (lista de str)
        """
        from datetime import datetime

        log_lines = [
            (
                "Fecha/hora de ejecución: "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ),
            f"Suscripciones chequeadas: {data_registro.get('total_chequeadas', 0)}",
            f"Órdenes generadas: {data_registro.get('total_generadas', 0)}",
            f"Órdenes ya existentes: {data_registro.get('total_existentes', 0)}",
        ]
        if data_registro.get("ordenes_generadas"):
            log_lines.append("\nÓrdenes generadas:")
            log_lines.extend([f"- {o}" for o in data_registro["ordenes_generadas"]])
        if data_registro.get("ordenes_existentes"):
            log_lines.append("\nÓrdenes ya existentes:")
            log_lines.extend([f"- {o}" for o in data_registro["ordenes_existentes"]])
        self.log = "\n".join(log_lines)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            forzar = record.forzar_generacion
            hoy = record.fecha or date.today()
            suscripciones = self.env["softer.suscripcion"].search(
                [("estado", "!=", "baja")]
            )
            items_to_create = []
            total_chequeadas = 0
            total_generadas = 0
            total_existentes = 0
            ordenes_generadas = []
            ordenes_existentes = []
            for suscripcion in suscripciones:
                total_chequeadas += 1
                existe_orden = suscripcion.sale_order_ids.filtered(
                    lambda o, hoy=hoy: (o.date_order and o.date_order.date() == hoy)
                )
                order_id = False
                if not existe_orden:
                    order = suscripcion.create_sale_order(forzar_generacion=forzar)
                    if order:
                        order_id = order.id
                        total_generadas += 1
                        ordenes_generadas.append(
                            f"{order.name} (Cliente: " f"{suscripcion.cliente_id.name})"
                        )
                else:
                    order_id = existe_orden[0].id
                    total_existentes += 1
                    ordenes_existentes.append(
                        f"{existe_orden[0].name} (Cliente: "
                        f"{suscripcion.cliente_id.name})"
                    )
                items_to_create.append(
                    {
                        "generator_id": record.id,
                        "suscripcion_id": suscripcion.id,
                        "order_id": order_id,
                    }
                )
            if items_to_create:
                self.env["softer.suscripcion.generator.item"].create(items_to_create)
            # Usar la función logear
            record.logear(
                {
                    "total_chequeadas": total_chequeadas,
                    "total_generadas": total_generadas,
                    "total_existentes": total_existentes,
                    "ordenes_generadas": ordenes_generadas,
                    "ordenes_existentes": ordenes_existentes,
                }
            )
        return records

    def unlink(self):
        for record in self:
            orders = record.item_ids.mapped("order_id")
            try:
                orders.unlink()
            except Exception as e:
                msg = str(e)
                if (
                    "violates foreign key constraint" in msg
                    and "payment_pendientes_pago_item_order_id_fkey" in msg
                ):
                    raise UserError(
                        "DEUDA/PENDIENTES DE PAGO: \n\n"
                        "No se pueden eliminar las órdenes de venta porque "
                        "existen registros de pagos pendientes asociados. "
                        "Elimine primero los pagos pendientes relacionados "
                    )
                raise UserError(
                    "Error inesperado al eliminar las órdenes de venta: %s" % msg
                )
        return super().unlink()


class SuscripcionGeneratorItem(models.Model):
    _name = "softer.suscripcion.generator.item"
    _description = "Item de Generador de Suscripción"

    generator_id = fields.Many2one(
        "softer.suscripcion.generator",
        string="Generador",
        required=True,
        ondelete="cascade",
    )
    suscripcion_id = fields.Many2one(
        "softer.suscripcion",
        string="Suscripción",
        required=True,
        ondelete="cascade",
    )
    order_id = fields.Many2one(
        "sale.order",
        string="Orden de Venta",
        readonly=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        compute="_compute_partner_id",
        store=True,
        readonly=True,
    )
    importe = fields.Float(
        string="Importe",
        compute="_compute_importe",
        store=True,
        readonly=True,
    )

    @api.depends("suscripcion_id")
    def _compute_partner_id(self):
        for record in self:
            record.partner_id = record.suscripcion_id.cliente_id

    @api.depends("suscripcion_id")
    def _compute_importe(self):
        for record in self:
            # Suma de los importes de las líneas de la suscripción
            record.importe = sum(
                line.product_id.list_price * line.cantidad
                for line in record.suscripcion_id.line_ids
            )
