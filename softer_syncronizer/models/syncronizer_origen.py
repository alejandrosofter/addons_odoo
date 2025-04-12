# tiene los datos:
# - name
# - descripcion
# - plataforma (firebase,api)
# - url (url de la plataforma)
# - token (token de la plataforma)
# - tipoAuth (Barer, Basic)
# - tokenAuth (token de autenticacion)
# - username (username de la plataforma)
# -pssword

from odoo import models, fields, api


class SofterSyncronizerOrigen(models.Model):
    _name = "softer.syncronizer.origen"
    _description = "Origen de Sincronización"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nombre", required=True)
    url = fields.Char(string="URL", required=True)
    auth_type = fields.Selection(
        [
            ("none", "Sin Autenticación"),
            ("basic", "Autenticación Básica"),
            ("bearer", "Token Bearer"),
        ],
        string="Tipo de Autenticación",
        default="none",
        required=True,
    )

    # Campos de autenticación
    auth_user = fields.Char(string="Usuario")
    auth_password = fields.Char(string="Contraseña")
    auth_token = fields.Char(string="Token")
    auth_header = fields.Char(string="Header de Autenticación")

    # Campos de tarea
    esConTask = fields.Boolean(string="Es con Tarea", default=False)
    task_status_url = fields.Char(string="URL de Estado")
    task_status_field = fields.Char(string="Campo de Estado")
    task_status_value = fields.Char(string="Valor de Estado")
    task_interval = fields.Integer(string="Intervalo (segundos)", default=30)
    task_timeout = fields.Integer(string="Timeout (segundos)", default=300)
    urlResultados = fields.Char(string="URL de Resultados")

    # Campos adicionales
    active = fields.Boolean(string="Activo", default=True)
    param_ids = fields.One2many(
        "softer.syncronizer.origen.param", "origen_id", string="Parámetros"
    )

    method = fields.Selection(
        [
            ("post", "POST"),
            ("get", "GET"),
        ],
        string="Método HTTP",
        required=True,
        default="post",
        tracking=True,
    )

    @api.onchange("auth_type")
    def _onchange_auth_type(self):
        if self.auth_type == "none":
            self.auth_user = False
            self.auth_password = False
            self.auth_token = False
            self.auth_header = False
        elif self.auth_type == "basic":
            self.auth_token = False
            self.auth_header = False
        elif self.auth_type == "bearer":
            self.auth_user = False
            self.auth_password = False
