from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = "res.config.settings"

    userIdNotificaciones = fields.Many2one("res.users", string="Notificar a...")
    userAdministrador = fields.Many2one("res.users", string="Administrador Asistencias")
    active = fields.Boolean(string="Notificacion activa", default=False)
    quioskoActive = fields.Boolean(string="Quiosko activo", default=False)

    # Guarda la configuración en ir.config_parameter
    def set_values(self):
        super(ResConfigSettingsInherit, self).set_values()
        ir_config = self.env["ir.config_parameter"].sudo()

        ir_config.set_param(
            "asistencias.userIdNotificaciones",
            str(self.userIdNotificaciones.id) if self.userIdNotificaciones else "",
        )
        ir_config.set_param(
            "asistencias.userAdministrador",
            str(self.userAdministrador.id) if self.userAdministrador else "",
        )
        ir_config.set_param("asistencias.quioskoActive", self.quioskoActive)
        ir_config.set_param("asistencias.active", self.active)

        # Activar/desactivar menú según `quioskoActive`
        menu = self.env.ref("hr_attendance.menu_hr_attendance_kiosk_no_user_mode")
        menu.active = self.quioskoActive

    @api.constrains("active", "userIdNotificaciones", "userAdministrador")
    def _check_required_users(self):
        for record in self:
            if record.active and (
                not record.userIdNotificaciones or not record.userAdministrador
            ):
                raise ValidationError(
                    "Si la notificación está activa, debes seleccionar un usuario para notificaciones y un administrador."
                )

    @api.model
    def get_values(self):
        res = super(ResConfigSettingsInherit, self).get_values()
        ir_config = self.env["ir.config_parameter"].sudo()
        user_id = ir_config.get_param("asistencias.userIdNotificaciones")
        userAdmin = ir_config.get_param("asistencias.userAdministrador")

        res.update(
            {
                "userIdNotificaciones": (
                    self.env["res.users"].browse(int(user_id)) if user_id else False
                ),
                "userAdministrador": (
                    self.env["res.users"].browse(int(userAdmin)) if userAdmin else False
                ),
                "quioskoActive": ir_config.get_param(
                    "asistencias.quioskoActive", default=False
                ),
                "active": ir_config.get_param("asistencias.active", default=False),
            }
        )
        return res
