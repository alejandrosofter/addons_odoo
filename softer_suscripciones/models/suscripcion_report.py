from odoo import fields, models, tools


class SuscripcionProductReport(models.Model):
    _name = "softer.suscripcion.product.report"
    _description = "Reporte de Productos Suscritos"
    _auto = False
    _rec_name = "product_id"

    product_id = fields.Many2one("product.product", string="Producto", readonly=True)
    cliente_id = fields.Many2one("res.partner", string="Cliente", readonly=True)
    suscripcion_id = fields.Many2one(
        "softer.suscripcion", string="Suscripción", readonly=True
    )
    estado = fields.Selection(
        [
            ("borrador", "Borrador"),
            ("activa", "Activa"),
            ("suspendida", "Suspendida"),
            ("baja", "Baja"),
        ],
        string="Estado",
        readonly=True,
    )
    fecha_inicio = fields.Date(string="Fecha de Inicio", readonly=True)
    proxima_factura = fields.Date(string="Próxima Factura", readonly=True)
    company_id = fields.Many2one("res.company", string="Compañía", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute(
            """
            CREATE OR REPLACE VIEW %s AS (
                WITH RECURSIVE numbers AS (
                    SELECT 1 as n
                    UNION ALL
                    SELECT n + 1 FROM numbers WHERE n < 1000000
                )
                SELECT
                    n.n as id,
                    sl.product_id,
                    s.cliente_id,
                    s.id as suscripcion_id,
                    s.estado,
                    s.fecha_inicio,
                    s.proxima_factura,
                    s.company_id
                FROM softer_suscripcion s
                JOIN softer_suscripcion_line sl ON sl.suscripcion_id = s.id
                CROSS JOIN numbers n
                WHERE s.active = true
                LIMIT 1
            )
        """
            % self._table
        )
