from odoo import models, fields, api


class SofterSyncronizerFile(models.Model):
    _name = "softer.syncronizer.file"
    _description = "Archivo de Sincronización"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nombre", required=True)
    origen_id = fields.Many2one(
        "softer.syncronizer.origen", string="Origen", required=True, ondelete="cascade"
    )
    fecha_sincronizacion = fields.Datetime(
        string="Fecha de Sincronización", required=True
    )
    estado = fields.Selection(
        [
            ("pendiente", "Pendiente"),
            ("procesando", "Procesando"),
            ("completado", "Completado"),
            ("error", "Error"),
        ],
        string="Estado",
        default="pendiente",
        required=True,
    )
    datos = fields.Text(string="Datos")
    error = fields.Text(string="Error")
    active = fields.Boolean(string="Activo", default=True)

    @api.depends("file_name")
    def _compute_name(self):
        for record in self:
            record.name = record.file_name or "Sin nombre"

    @api.depends("file_data")
    def _compute_file_size(self):
        for record in self:
            if record.file_data:
                try:
                    # El tamaño real es 3/4 del tamaño base64 (porque base64 usa 4 caracteres por cada 3 bytes)
                    record.file_size = len(record.file_data) * 3 // 4
                except (binascii.Error, TypeError):
                    record.file_size = 0
            else:
                record.file_size = 0

    def action_process_file(self):
        self.write({"state": "processing", "message": "Procesando archivo..."})
        try:
            # TODO: Implementar lógica de procesamiento del archivo
            self.write(
                {
                    "state": "done",
                    "message": "Archivo procesado exitosamente",
                    "last_sync_date": fields.Datetime.now(),
                }
            )
        except Exception as e:
            self.write(
                {"state": "error", "message": f"Error al procesar el archivo: {str(e)}"}
            )
