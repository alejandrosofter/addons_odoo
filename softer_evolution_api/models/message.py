from odoo import models, fields, api
import requests
import base64
import logging
import mimetypes
import re

_logger = logging.getLogger(__name__)


class EvolutionApiMessage(models.Model):
    _name = "evolution.api.message"
    _description = "Evolution API Messages"
    _rec_name = "number_id"
    _order = "fechaHora desc"

    number_id = fields.Many2one(
        "evolution.api.numbers",
        string="WhatsApp Number",
        required=True,
        help="WhatsApp number used to send the message",
    )

    numeroDestino = fields.Char(
        string="Número Destino",
        required=True,
        help="Número de WhatsApp del destinatario",
    )

    fechaHora = fields.Datetime(
        string="Fecha y Hora",
        required=True,
        default=fields.Datetime.now,
        help="Fecha y hora del mensaje",
    )

    type = fields.Selection(
        [
            ("text", "Texto"),
            ("image", "Imagen"),
            ("video", "Video"),
            ("audio", "Audio"),
            ("document", "Documento"),
            ("sticker", "Sticker"),
        ],
        string="Tipo",
        required=True,
        default="text",
    )

    text = fields.Text(
        string="Texto", help="Contenido del mensaje de texto o pie de imagen"
    )

    file = fields.Binary(
        string="Archivo",
        attachment=True,
        help="Archivo adjunto (para mensajes tipo media, audio o sticker)",
    )

    file_name = fields.Char(string="Nombre del archivo")

    estado = fields.Selection(
        [("pendiente", "Pendiente"), ("enviado", "Enviado")],
        string="Estado",
        required=True,
        default="pendiente",
    )

    def _format_phone_number(self, number):
        """Formatea el número de teléfono al formato requerido por Evolution API.

        Args:
            number: Número telefónico (ej: +54 297 544-7771)
        Returns:
            str: Número formateado (ej: 549297544771)
        """
        # Eliminar el signo +, espacios, guiones y otros caracteres no numéricos
        clean_number = re.sub(r"[^\d]", "", number)

        # Si empieza con 54, agregar el 9 después del 54
        if clean_number.startswith("54"):
            if len(clean_number) > 2 and clean_number[2] != "9":
                clean_number = "54" + "9" + clean_number[2:]
        # Si no empieza con 54, agregar 549 al inicio
        else:
            clean_number = "549" + clean_number

        return clean_number

    def _send_message_to_api(self):
        self.ensure_one()
        if not self.number_id:
            raise models.ValidationError("Debe seleccionar una instancia de WhatsApp")

        # Obtener configuraciones globales
        ir_config = self.env["ir.config_parameter"].sudo()
        base_url = ir_config.get_param("evolution_api.url")
        api_token = ir_config.get_param("evolution_api.token")

        if not base_url or not api_token:
            raise models.ValidationError(
                "La URL y el Token de Evolution API deben estar configurados"
            )

        base_url = base_url.rstrip("/")
        instance = self.number_id.name
        headers = {"Content-Type": "application/json", "apikey": api_token}

        # Formatear número de destino
        formatted_number = self._format_phone_number(self.numeroDestino)

        # Log para depuración
        _logger.info(
            "Enviando mensaje - URL: %s, Instance: %s, Número: %s",
            base_url,
            instance,
            formatted_number,
        )

        # Preparar el endpoint y payload según el tipo de mensaje
        if self.type == "text":
            endpoint = f"{base_url}/message/sendText/{instance}"
            payload = {"number": formatted_number, "text": self.text, "delay": 1200}

            # Log del payload
            _logger.info("Payload para mensaje de texto: %s", payload)

        elif self.type in ["image", "video", "document", "sticker"]:
            endpoint = f"{base_url}/message/sendMedia/{instance}"

            if not self.file:
                raise models.ValidationError("Debe seleccionar un archivo para enviar")

            # Detectar el tipo MIME
            mime_type = mimetypes.guess_type(self.file_name)[0]
            if not mime_type:
                mime_type = {
                    "image": "image/png",
                    "video": "video/mp4",
                    "document": "application/pdf",
                    "sticker": "image/webp",
                }.get(self.type, "application/octet-stream")

            # Convertir archivo a base64
            media_data = (
                self.file.decode() if isinstance(self.file, bytes) else self.file
            )

            payload = {
                "number": formatted_number,
                "mediatype": self.type,
                "mimetype": mime_type,
                "media": media_data,
                "fileName": self.file_name,
                "delay": 1200,
                "caption": self.text if self.text else "",
            }

        elif self.type == "audio":
            endpoint = f"{base_url}/message/sendWhatsAppAudio/{instance}"
            raise models.ValidationError("El envío de audio aún no está implementado")
        else:
            raise models.ValidationError(f"Tipo de mensaje no soportado: {self.type}")

        try:
            # Log de la petición
            _logger.info("Haciendo petición a: %s con headers: %s", endpoint, headers)

            response = requests.post(
                endpoint, headers=headers, json=payload, timeout=10
            )

            # Log de la respuesta
            _logger.info(
                "Respuesta del servidor: Status: %s, Contenido: %s",
                response.status_code,
                response.text,
            )

            response.raise_for_status()
            self.write({"estado": "enviado"})
            return True
        except requests.exceptions.RequestException as e:
            error_msg = f"Error al enviar mensaje: {str(e)}"
            _logger.error(error_msg)
            raise models.ValidationError(error_msg)

    def action_send_message(self):
        """Botón para enviar mensaje manualmente"""
        return self._send_message_to_api()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            try:
                record._send_message_to_api()
            except Exception as e:
                _logger.error("Error al enviar mensaje automáticamente: %s", str(e))
        return records
