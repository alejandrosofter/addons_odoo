from odoo import models, fields, tools


class SuscripcionProductReport(models.Model):
    _name = "softer.suscripcion.product.report"
    _description = "Reporte de Productos Suscritos"
    _auto = False

    product_id = fields.Many2one("product.product", string="Producto", readonly=True)
    cliente_id = fields.Many2one("res.partner", string="Cliente", readonly=True)
    suscripcion_id = fields.Many2one(
        "softer.suscripcion", string="Suscripción", readonly=True
    )
    estado = fields.Selection(
        [("activa", "Activa"), ("suspendida", "Suspendida"), ("baja", "Baja")],
        string="Estado",
        readonly=True,
    )
    fecha_inicio = fields.Date(string="Fecha Inicio", readonly=True)
    proxima_factura = fields.Date(string="Próxima Factura", readonly=True)
    company_id = fields.Many2one("res.company", string="Compañía", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # Verificar si las tablas base existen
        self.env.cr.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'softer_suscripcion'
            )
        """
        )
        if not self.env.cr.fetchone()[0]:
            return

        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () AS id,
                    p.id as product_id,
                    s.cliente_id,
                    s.id as suscripcion_id,
                    s.estado,
                    s.fecha_inicio,
                    s.proxima_factura,
                    s.company_id
                FROM 
                    softer_suscripcion s
                    JOIN """
            + rel_table
            + """ rel ON rel.softer_suscripcion_id = s.id
                    JOIN product_product p ON p.id = rel.product_product_id
                WHERE 
                    s.active = true 
                    AND s.estado = 'activa'
            )
        """
            % self._table
        )
