from odoo import models, fields, api


class EvolutionApiWebhook(models.Model):
    _name = "evolution.api.webhook"
    _description = "Eventos Webhook de Evolution API"
    _rec_name = "event_type"
    _order = "create_date desc"

    event_type = fields.Selection(
        [
            ("APPLICATION_STARTUP", "Inicio de Aplicación"),
            ("CALL", "Llamada"),
            ("CHATS_DELETE", "Eliminación de Chats"),
            ("CHATS_SET", "Configuración de Chats"),
            ("CHATS_UPDATE", "Actualización de Chats"),
            ("CHATS_UPSERT", "Inserción/Actualización de Chats"),
            ("CONNECTION_UPDATE", "Actualización de Conexión"),
            ("CONTACTS_SET", "Configuración de Contactos"),
            ("CONTACTS_UPDATE", "Actualización de Contactos"),
            ("CONTACTS_UPSERT", "Inserción/Actualización de Contactos"),
            ("GROUP_PARTICIPANTS_UPDATE", "Actualización de Participantes"),
            ("GROUP_UPDATE", "Actualización de Grupo"),
            ("GROUPS_UPSERT", "Inserción/Actualización de Grupos"),
            ("LABELS_ASSOCIATION", "Asociación de Etiquetas"),
            ("LABELS_EDIT", "Edición de Etiquetas"),
            ("LOGOUT_INSTANCE", "Cierre de Sesión de Instancia"),
            ("MESSAGES_DELETE", "Eliminación de Mensajes"),
            ("MESSAGES_SET", "Configuración de Mensajes"),
            ("MESSAGES_UPDATE", "Actualización de Mensajes"),
            ("MESSAGES_UPSERT", "Inserción/Actualización de Mensajes"),
            ("PRESENCE_UPDATE", "Actualización de Presencia"),
            ("QRCODE_UPDATED", "Actualización de Código QR"),
            ("REMOVE_INSTANCE", "Eliminación de Instancia"),
            ("SEND_MESSAGE", "Envío de Mensaje"),
            ("TYPEBOT_CHANGE_STATUS", "Cambio de Estado de Typebot"),
            ("TYPEBOT_START", "Inicio de Typebot"),
        ],
        string="Tipo de Evento",
        required=True,
    )

    instance_id = fields.Many2one(
        "evolution.api.numbers", string="Instancia de WhatsApp"
    )
    raw_data = fields.Text(string="Datos Crudos")

    state = fields.Selection(
        [
            ("nuevo", "Nuevo"),
            ("procesando", "Procesando"),
            ("procesado", "Procesado"),
            ("error", "Error"),
        ],
        string="Estado",
        default="nuevo",
        required=True,
        tracking=True,
    )

    processed = fields.Boolean(
        string="Procesado", compute="_compute_processed", store=True
    )

    create_date = fields.Datetime(string="Fecha de Creación", readonly=True)

    error_message = fields.Text(string="Mensaje de Error", readonly=True)

    @api.depends("state")
    def _compute_processed(self):
        for record in self:
            record.processed = record.state in ["procesado"]

    def action_procesar(self):
        self.write({"state": "procesando"})

    def action_marcar_procesado(self):
        self.write({"state": "procesado"})

    def action_marcar_error(self, error_message=False):
        vals = {"state": "error"}
        if error_message:
            vals["error_message"] = error_message
        self.write(vals)

    def action_reintentar(self):
        self.write({"state": "nuevo", "error_message": False})
