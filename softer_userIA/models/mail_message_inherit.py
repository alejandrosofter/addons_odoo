from odoo import models, api


class MailMessageInherit(models.Model):
    _inherit = "mail.message"

    @api.model
    def create(self, vals):
        # Creamos el mensaje
        message = super(MailMessageInherit, self).create(vals)
        print("CHECK MENSAJE")

        # Verificamos si el mensaje es enviado a un canal de chat
        if message.model == "discuss.channel" and message.record_name:
            # Buscamos el canal basado en el campo `name` de discuss.channel
            discuss_channel = self.env["discuss.channel"].search(
                [("name", "=", message.record_name)], limit=1
            )

            if discuss_channel:
                # Obtenemos el usuario write_uid asociado al canal
                recipient_user = discuss_channel.write_uid
                if recipient_user and recipient_user.es_virtual:
                    # en response hago la consulta chatgpt y respondo
                    response = "apaaa bien!"

                    print(
                        f"Receptor del mensaje: {recipient_user.name} (ID: {recipient_user.id})"
                    )
                    # Creamos un nuevo mensaje en el mismo canal con la respuesta
                    self.create(
                        {
                            "body": response,
                            "model": "discuss.channel",
                            "res_id": discuss_channel.id,
                            "message_type": "comment",
                            "subtype_id": self.env.ref("mail.mt_comment").id,
                        }
                    )

        return message
