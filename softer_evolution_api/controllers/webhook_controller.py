from odoo import http
from odoo.http import request
import json
import logging
from odoo.fields import Datetime

_logger = logging.getLogger(__name__)


class EvolutionWebhookController(http.Controller):
    @http.route(
        "/evolution_api/webhook",
        type="http",
        auth="public",
        csrf=False,
        methods=["POST"],
    )
    def handle_webhook(self, **post):
        try:
            _logger.info("=== INICIO PROCESAMIENTO WEBHOOK ===")
            _logger.info("POST data: %s", post)
            _logger.info("Headers: %s", request.httprequest.headers)

            # Obtener los datos del webhook del body del request
            raw_data = request.httprequest.data
            _logger.info("Raw data: %s", raw_data)

            if not raw_data:
                _logger.error("No se recibieron datos en el body")
                return json.dumps(
                    {"status": "error", "message": "No hay datos en el body"}
                )

            try:
                webhook_data = json.loads(raw_data.decode())
                _logger.info("Datos decodificados: %s", json.dumps(webhook_data))
            except json.JSONDecodeError as e:
                _logger.error("Error decodificando JSON: %s", str(e))
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Error decodificando JSON: {str(e)}",
                    }
                )

            # Validar que tengamos los datos necesarios
            if not webhook_data:
                _logger.error("webhook_data está vacío")
                return json.dumps(
                    {
                        "status": "error",
                        "message": "Datos inválidos - webhook_data vacío",
                    }
                )

            # Validar evento
            event = webhook_data.get("event", "")
            if not event:
                _logger.error("No se encontró 'event' en webhook_data")
                _logger.error("Contenido recibido: %s", webhook_data)
                return json.dumps(
                    {"status": "error", "message": "Datos inválidos - falta event"}
                )

            _logger.info("Evento recibido: %s", event)

            # Crear el registro del webhook
            webhook_vals = {
                "event_type": event.upper().replace(".", "_"),
                "raw_data": json.dumps(webhook_data),
                "processed": False,
            }

            # Buscar la instancia por el apikey
            api_key = webhook_data.get("apikey")
            if api_key:
                _logger.info("Buscando instancia por apikey: %s", api_key)
                instance = (
                    request.env["evolution.api.numbers"]
                    .sudo()
                    .search([("token", "=", api_key)], limit=1)
                )
                if instance:
                    _logger.info("Instancia encontrada con ID: %s", instance.id)
                    webhook_vals["instance_id"] = instance.id
                else:
                    _logger.warning("No se encontró instancia con apikey: %s", api_key)

            # Crear el registro del webhook
            webhook = request.env["evolution.api.webhook"].sudo().create(webhook_vals)
            _logger.info("Webhook creado con ID: %s", webhook.id)

            # Procesar el evento según su tipo
            self._process_webhook_event(webhook)
            _logger.info("Webhook procesado exitosamente")

            return json.dumps({"status": "success", "webhook_id": webhook.id})

        except Exception as e:
            _logger.error("Error al procesar webhook: %s", str(e))
            _logger.error("Traceback:", exc_info=True)
            return json.dumps({"status": "error", "message": str(e)})

    def _process_webhook_event(self, webhook):
        """
        Procesa el evento del webhook según su tipo
        """
        try:
            _logger.info(
                "Iniciando procesamiento de evento tipo: %s", webhook.event_type
            )

            data = json.loads(webhook.raw_data)
            _logger.info("Datos del evento: %s", json.dumps(data))

            # Manejadores para cada tipo de evento
            event_handlers = {
                "MESSAGES_UPSERT": self._handle_message_upsert,
                "CHATS_UPDATE": self._handle_chats_update,
                "CONNECTION_UPDATE": self._handle_connection_update,
                "QRCODE_UPDATED": self._handle_qrcode_update,
            }

            handler = event_handlers.get(webhook.event_type)
            if handler:
                _logger.info("Ejecutando handler para: %s", webhook.event_type)
                handler(data, webhook)
                _logger.info("Handler ejecutado exitosamente")
            else:
                _logger.warning("No hay handler para el evento: %s", webhook.event_type)

            webhook.sudo().write({"processed": True})
            _logger.info("Evento marcado como procesado")

        except Exception as e:
            _logger.error("Error al procesar evento %s: %s", webhook.event_type, str(e))
            _logger.error("Traceback:", exc_info=True)
            raise

    def _handle_message_upsert(self, data, webhook):
        """
        Maneja eventos de nuevos mensajes
        """
        try:
            _logger.info("Procesando mensaje upsert")

            if not data.get("data"):
                _logger.warning("No hay datos de mensaje en el evento")
                return

            message_data = data["data"]
            key_data = message_data.get("key", {})

            _logger.info("Datos del mensaje: %s", json.dumps(message_data))

            # Crear mensaje en Odoo
            message_vals = {
                "number_id": (webhook.instance_id.id if webhook.instance_id else False),
                "numeroDestino": key_data.get("remoteJid"),
                "text": (
                    message_data.get("message", {}).get("conversation")
                    or json.dumps(message_data.get("message", {}))
                ),
                "type": "text",  # Por ahora solo manejamos texto
                "estado": "enviado",  # El mensaje ya fue enviado
                "fechaHora": Datetime.now(),  # Usamos la hora actual
            }

            message = request.env["evolution.api.message"].sudo().create(message_vals)
            _logger.info("Mensaje creado con ID: %s", message.id)

        except Exception as e:
            _logger.error("Error procesando mensaje: %s", str(e))
            _logger.error("Traceback:", exc_info=True)
            raise

    def _handle_chats_update(self, data, webhook):
        """
        Maneja eventos de actualización de chats
        """
        try:
            _logger.info("Procesando actualización de chats")
            if not data.get("data"):
                _logger.warning("No hay datos de chat en el evento")
                return

            chat_data = data["data"]
            _logger.info("Datos del chat: %s", json.dumps(chat_data))
            # Aquí puedes implementar la lógica específica para
            # actualización de chats

        except Exception as e:
            _logger.error("Error procesando chat update: %s", str(e))
            _logger.error("Traceback:", exc_info=True)
            raise

    def _handle_connection_update(self, data, webhook):
        """
        Maneja eventos de actualización de conexión
        """
        try:
            _logger.info("Procesando actualización de conexión")

            if webhook.instance_id and "connection_state" in data:
                status = data["connection_state"]
                _logger.info(
                    "Actualizando estado de instancia %s a: %s",
                    webhook.instance_id.id,
                    status,
                )
                webhook.instance_id.sudo().write({"estado": status})
                _logger.info("Estado actualizado exitosamente")
            else:
                _logger.warning("Datos insuficientes para actualizar estado")

        except Exception as e:
            _logger.error("Error actualizando conexión: %s", str(e))
            _logger.error("Traceback:", exc_info=True)
            raise

    def _handle_qrcode_update(self, data, webhook):
        """
        Maneja eventos de actualización de código QR
        """
        try:
            _logger.info("Procesando actualización de QR")

            if webhook.instance_id and "qrcode" in data:
                _logger.info("QR recibido para instancia: %s", webhook.instance_id.id)
                # Implementar lógica para QR
                pass
            else:
                _logger.warning("Datos insuficientes para procesar QR")

        except Exception as e:
            _logger.error("Error procesando QR: %s", str(e))
            _logger.error("Traceback:", exc_info=True)
            raise
