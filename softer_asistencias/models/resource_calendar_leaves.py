from odoo import models, fields, api
import locale
import re
import pytz
from datetime import datetime, timedelta


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    tipo = fields.Selection(
        [
            ("otro", "Otros"),
            ("feriado", "Feriado (*)"),
            ("vacaciones", "Vacaciones (*)"),
            ("pedido_dias", "Pedido de Dias (*)"),
            ("enfermedad", "Enfermedad (*)"),
            ("llegada_tarde", "Llegada Tarde (**)"),
            ("salida_temprana", "Salida Temprana (**)"),
            ("inasistencia", "Inasistencia (**)"),
        ],
        string="Tipo",
        required=True,
    )
    assistance_id = fields.Many2one(
        "hr.assistance",
        string="Asistencia Referencia",
        # ondelete="cascade",
    )

    @api.onchange("tipo")
    def _onchange_tipo(self):
        if self.tipo and self.tipo in dict(self._fields["tipo"].selection):
            self.name = dict(self._fields["tipo"].selection)[self.tipo]
        else:
            self.name = ""

    def getDate(self, atten_time):

        utc_dt = atten_time.astimezone(pytz.utc)

        # Convertir la fecha UTC a formato de cadena
        utc_dt_str = utc_dt.strftime("%Y-%m-%d %H:%M:%S")

        # Convertir la cadena a un objeto datetime
        return datetime.strptime(utc_dt_str, "%Y-%m-%d %H:%M:%S")

        # return fields.Datetime.to_string(atten_time)

    def create(self, vals):
        print("vals", vals)
        leave = super(ResourceCalendarLeaves, self).create(vals)
        if (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("asistencias.notificarAlinputFalta")
        ):
            print("Notificar al cargar falta (esta activo el parm config sistema)")
            if leave.tipo in ["llegada_tarde", "salida_temprana", "inasistencia"]:
                # envio notificacion por wsap
                print(
                    "Enviando notificacion por wsap por que es una inasistencia infustificada"
                )
                ir_config = self.env["ir.config_parameter"].sudo()
                user_id = ir_config.get_param("asistencias.userIdNotificaciones")
                user = self.env["res.users"].browse(int(user_id)) if user_id else False
                if user:
                    print(f"Enviando notificacion a {user.partner_id.name}")
                    locale.setlocale(locale.LC_TIME, "es_ES.utf8")
                    tz = pytz.timezone(
                        "America/Argentina/Buenos_Aires"
                    )  # Ajusta según tu zona horaria
                    fecha = leave.date_from.replace(tzinfo=pytz.utc).astimezone(tz)
                    hora = fecha.strftime("%H:%M")
                    diaMes = fecha.strftime("%d")
                    weekDay = fecha.strftime("%A").capitalize()
                    tipo_label = (
                        dict(leave._fields["tipo"].selection)
                        .get(leave.tipo, "Desconocido")
                        .replace("(**)", "")
                        .strip()
                    )
                    empleado = leave.resource_id.name
                    user.partner_id.send_whatsapp_message(
                        f"*{empleado}* tiene una _{tipo_label}_ el {weekDay} {diaMes} a las *{hora}*"
                    )
                else:
                    print("No hay usuario para notificar")
        return leave
