from odoo import models, fields, api
from datetime import datetime, time, timedelta
import pytz
from odoo.exceptions import ValidationError

ARG_TIMEZONE = pytz.timezone("America/Argentina/Buenos_Aires")


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    is_late = fields.Boolean(
        string="Llegada Tarde", compute="_compute_late_early", store=True
    )
    is_early_exit = fields.Boolean(
        string="Salida Temprana", compute="_compute_late_early", store=True
    )

    def unlink(self):
        # Eliminar leaves asociados antes de eliminar la asistencia
        leaves = self.env["resource.calendar.leaves"].search(
            [("assistance_id", "in", self.ids)]
        )
        if leaves:
            leaves.unlink()
        return super(HrAttendance, self).unlink()

    @api.model
    def get_asistencias_active(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("asistencias.active", "False")
            == "True"
        )

    def enviar_reporte_asistencias(self):
        """Genera un reporte de asistencias y lo envía al administrador."""
        admin = self.env["res.users"].search(
            [
                (
                    "id",
                    "=",
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("asistencias.userAdministrador"),
                )
            ],
            limit=1,
        )
        if not admin:
            raise ValidationError("No hay un Administrador de Asistencias configurado.")

        hoy = fields.Date.today()

        # Obtener todas las asistencias del día
        asistencias = self.env["hr.attendance"].search([("check_in", ">=", hoy)])

        # Obtener todas las ausencias justificadas del día
        ausencias = self.env["resource.calendar.leaves"].search(
            [
                ("date_from", "<=", hoy),
                ("date_to", ">=", hoy),
                (
                    "tipo",
                    "in",
                    ["feriado", "vacaciones", "pedido_dias", "enfermedad"],
                ),
            ]
        )

        empleados_presentes = asistencias.mapped("employee_id.resource_id")
        empleados_ausentes = ausencias.mapped("resource_id")

        # Determinar ausencias no justificadas
        empleados_totales = self.env["hr.employee"].search([])
        empleados_totales = empleados_totales.mapped("resource_id")
        ausencias_no_justificadas = (
            empleados_totales - empleados_presentes - empleados_ausentes
        )

        # Generar reporte
        reporte_html = """
            <h3>Reporte de Asistencias - {}</h3>
            <h4>Empleados Presentes:</h4>
            <ul>
        """.format(
            hoy
        )

        for empleado in empleados_presentes:
            reporte_html += "<li>{}</li>".format(empleado.name)

        reporte_html += """
            </ul>
            <h4>Empleados con Ausencias Justificadas:</h4>
            <ul>
        """
        for empleado in empleados_ausentes:
            reporte_html += "<li>{}</li>".format(empleado.name)

        reporte_html += """
            </ul>
            <h4>Empleados con Ausencias NO Justificadas:</h4>
            <ul>
        """
        for empleado in ausencias_no_justificadas:
            reporte_html += "<li>{}</li>".format(empleado.name)

        reporte_html += "</ul>"

        # Enviar el correo
        mail_values = {
            "subject": "Reporte de Asistencias - {}".format(hoy),
            "email_to": admin.email,
            "body_html": reporte_html,
        }
        self.env["mail.mail"].create(mail_values).send()

    @api.depends("check_in", "check_out", "employee_id")
    def _compute_late_early(self):
        for record in self:
            employee = record.employee_id
            calendar = employee.resource_calendar_id

            if not calendar or not record.check_in:
                record.is_late = False
                record.is_early_exit = False
                continue

            # Convertir check_in y check_out a la zona horaria de Argentina
            check_in = record.check_in.replace(tzinfo=pytz.utc).astimezone(ARG_TIMEZONE)
            check_out = (
                record.check_out.replace(tzinfo=pytz.utc).astimezone(ARG_TIMEZONE)
                if record.check_out
                else None
            )

            weekday = check_in.weekday()

            # Obtener el horario de trabajo esperado del empleado
            expected_attendance = calendar.attendance_ids.filtered(
                lambda a: int(a.dayofweek) == weekday
            )

            if expected_attendance:
                hour_from, min_from = divmod(expected_attendance[0].hour_from * 60, 60)
                hour_to, min_to = divmod(expected_attendance[0].hour_to * 60, 60)

                work_start = ARG_TIMEZONE.localize(
                    datetime.combine(
                        check_in.date(), time(int(hour_from), int(min_from))
                    )
                )
                work_end = (
                    ARG_TIMEZONE.localize(
                        datetime.combine(
                            check_out.date(), time(int(hour_to), int(min_to))
                        )
                    )
                    if check_out
                    else None
                )
                print(
                    f"check_in: {check_in}, check_out: {check_out}, work_start: {work_start}, work_end: {work_end}, isLate: {check_in > work_start}"
                )

                # Determinar si llegó tarde
                record.is_late = check_in > work_start

                # Determinar si salió temprano
                record.is_early_exit = (
                    check_out < work_end if check_out and work_end else False
                )
            else:
                record.is_late = False
                record.is_early_exit = False

    @api.model
    def create(self, vals):
        record = super(HrAttendance, self).create(vals)
        record._handle_late_or_early()
        return record

    def write(self, vals):
        res = super(HrAttendance, self).write(vals)
        self._handle_late_or_early()
        return res

    def _handle_late_or_early(self):
        for record in self:
            if record.is_late:
                self._create_leave(record, "Llegada Tarde", "llegada_tarde")
            else:
                self._delete_leave(record, "llegada_tarde")
            if record.is_early_exit:
                self._create_leave(record, "Salida Temprana", "salida_temprana")
            else:
                self._delete_leave(record, "salida_temprana")

    def _delete_leave(self, record, tipo):
        recordLeave = self.env["resource.calendar.leaves"].search(
            [("assistance_id", "=", record.id), ("tipo", "=", tipo)]
        )
        if recordLeave:
            recordLeave.unlink()

    def _create_leave(self, record, reason, tipo):
        """Crea un registro en resource.calendar.leaves para marcar llegadas tarde o salidas tempranas"""
        calendar = record.employee_id.resource_calendar_id
        resource = record.employee_id.resource_id

        if not calendar or not resource:
            print("No hay calendario o recurso asociado END")
            return  # Evita errores si no hay calendario o recurso asociado
        recordLeave = self.env["resource.calendar.leaves"].search(
            [("assistance_id", "=", record.id)]
        )
        if recordLeave:
            recordLeave.write(
                {
                    "name": f"{reason} ",
                    "date_from": (
                        record.check_in
                        if reason == "Llegada Tarde"
                        else record.check_out
                    ),
                    "date_to": (
                        record.check_in
                        if reason == "Llegada Tarde"
                        else record.check_out
                    ),
                }
            )
            return

        newData = {
            "name": f"{reason} ",
            "calendar_id": calendar.id,
            "resource_id": resource.id,
            "date_from": (
                record.check_in if reason == "Llegada Tarde" else record.check_out
            ),
            "date_to": (
                record.check_in if reason == "Llegada Tarde" else record.check_out
            ),
            "tipo": tipo,
            "assistance_id": record.id,
        }
        print("CREA REGISTRO LEAVE", newData)
        self.env["resource.calendar.leaves"].create(newData)

    @api.model
    def verificar_horarios_asistencias(self):
        """
        Verifica todas las asistencias y actualiza su estado de llegada tarde o salida temprana.
        Este método está diseñado para ser ejecutado manualmente a través de un cron job.
        """
        # Buscar todas las asistencias
        asistencias = self.search([])

        # Forzar el recálculo de is_late y is_early_exit
        for asistencia in asistencias:
            asistencia._compute_late_early()
            asistencia._handle_late_or_early()

        return True
