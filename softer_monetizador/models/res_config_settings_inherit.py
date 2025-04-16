from odoo import models, fields, api


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = "res.config.settings"

    fecha_inicio = fields.Date(string="Fecha Inicio")
    tipo_servicio_cobro = fields.Selection(
        [("por_cobro", "Por Cobro"), ("importe_fijo", "Importe Fijo")],
        string="Tipo Servicio Cobro",
    )
    estado = fields.Selection(
        [("activo", "Activo"), ("suspendido", "Suspendido")], string="Estado"
    )
    tipo_operador = fields.Selection(
        [("host", "HOST"), ("cliente", "CLIENTE")], string="Tipo Operador"
    )
    importe_fijo = fields.Float(string="Importe Fijo")
    importe_por_cobro = fields.Float(string="Importe Por Cobro")
    url_host = fields.Char(string="URL Host")

    # Guarda la configuración en ir.config_parameter
    def set_values(self):
        super(ResConfigSettingsInherit, self).set_values()
        config = self.env["ir.config_parameter"].sudo()

        config.set_param("monetizador.fecha_inicio", self.fecha_inicio)
        config.set_param("monetizador.tipo_servicio_cobro", self.tipo_servicio_cobro)
        config.set_param("monetizador.estado", self.estado)
        config.set_param("monetizador.tipo_operador", self.tipo_operador)
        config.set_param("monetizador.importe_fijo", self.importe_fijo)
        config.set_param("monetizador.importe_por_cobro", self.importe_por_cobro)
        config.set_param("monetizador.url_host", self.url_host)

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsInherit, self).get_values()
        config = self.env["ir.config_parameter"].sudo()
        res.update(
            {
                "fecha_inicio": config.get_param(
                    "monetizador.fecha_inicio", default=False
                ),
                "tipo_servicio_cobro": config.get_param(
                    "monetizador.tipo_servicio_cobro", default="por_cobro"
                ),
                "estado": config.get_param("monetizador.estado", default="activo"),
                "tipo_operador": config.get_param(
                    "monetizador.tipo_operador", default="host"
                ),
                "importe_fijo": float(
                    config.get_param("monetizador.importe_fijo", default=0.0)
                ),
                "importe_por_cobro": float(
                    config.get_param("monetizador.importe_por_cobro", default=0.0)
                ),
                "url_host": config.get_param("monetizador.url_host", default=""),
            }
        )
        return res
