from odoo import models, api
import logging
import google.generativeai as genai
import os
import json

import pytesseract

from PIL import Image

API_KEY = "AIzaSyC863_nDfEy0GEAiJ_Uk71GN6xQkVLg0J8"


# apt update && pip3 install docker pdfplumber pytesseract && apt install tesseract-ocr
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """
        Método que captura nuevos correos electrónicos entrantes y procesa el contenido y adjuntos.
        """
        res = super(AccountMove, self).message_new(msg_dict, custom_values)
        # self.env.cr.commit()
        # Agrega un log para verificar el ID del comprobante
        print(f"CUSTOM VALUES {res.id}")
        print(custom_values)
        # Obtener los adjuntos asociados con esta factura
        attachments = msg_dict.get("attachments")
        # Log de la cantidad de adjuntos encontrados
        print(f"PROCESANDO COMPROBANTE {res.id} con {len(attachments)} adjuntos")
        if attachments:
            return self.procesarAttachments(attachments, res)

    def procesarAttachments(self, attachments, res):
        for attachment in attachments:

            file_content = attachment.get("content")
            name = attachment.get("fname")
            # file_content = attachment.content
            # name = attachment.fname
            file_name = f"/tmp/{name}"
            print(f"procesando attachments file_name {file_name} ")
            if file_content:
                try:
                    # Guardar el archivo en el sistema
                    with open(file_name, "wb") as f:
                        f.write(file_content)

                    if not os.path.isfile(file_name):
                        logger.error(f"Error al guardar el archivo: {file_name}")
                        continue
                    result = self.procesarFactura(file_name)
                    # result = self.extractInfo(file_name)

                    print("RESULTADO DEL PROCESAMIENTO!")
                    print(result)

                    print("UPDATE FACTURA")
                    self.updateFactura(res, result)
                except Exception as e:
                    logger.error(f"Error al guardar el archivo {file_name}: {e}")
            else:
                logger.warning(f"Adjunto con estructura inesperada: {attachment}")

        return res

    def getPartner(self, proveedor):
        partner = self.env["res.partner"].search(
            [
                ("vat", "=", proveedor.get("cuit")),
            ],
            limit=1,
        )

        if partner:
            return partner[0]
        else:
            # Crear un nuevo partner

            try:
                data = {
                    "name": proveedor.get("razon_social"),
                    "complete_name": proveedor.get("razon_social"),
                    "vat": proveedor.get("cuit"),
                    # "type": "company",
                    # "company_type": "company",
                    "email": proveedor.get("email"),
                    "phone": proveedor.get("telefono"),
                    "mobile": proveedor.get("celular"),
                    "supplier_rank": 1,
                    "l10n_latam_identification_type_id": 4,
                    "l10n_ar_afip_responsibility_type_id": 1,
                }
                partner = self.env["res.partner"].sudo().create(data)
                print(f"Partner creado con éxito: {partner}")
                return partner
            except Exception as e:
                print(f"Error al crear el partner: {e}")
                return None

    def getTax(self, porcentajeIva):
        if porcentajeIva is None or porcentajeIva == "":
            return None
        return self.env["account.tax"].search(
            [
                ("amount", "=", float(porcentajeIva)),
            ],
            limit=1,
        )

    def getItems(self, items):
        lines = []
        for item in items:
            tax = self.getTax(item.get("porcentajeIva"))
            taxes = [] if tax is None else [tax.id]
            print("PASO")
            lines.append(
                (
                    0,
                    0,
                    {
                        "name": item.get("descripcion"),
                        "tax_ids": [(6, 0, taxes)],
                        "price_unit": self.parseImporte(item.get("importeUnitario")),
                        "quantity": (
                            1
                            if item.get("cantidad") is None
                            else float(item.get("cantidad"))
                        ),
                    },
                )
            )

        return lines

    def parseImporte(self, importe):
        if importe is None:
            return 0
        # verificar tipo dato string o float
        if type(importe) == str:
            return float(importe.replace(",", "").strip())
        else:
            return importe

    def updateFactura(self, invoice, result):
        print("PARTNER ")
        partner = self.getPartner(result.get("proveedor"))
        try:
            print(partner)
            nombre = (
                "S/N"
                if not result.get("nroFactura") or result.get("nroFactura") == ""
                else result.get("nroFactura")
            )
            items = self.getItems(result.get("items"))
            data = {
                "partner_id": partner.id,
                "move_type": "in_invoice",
                "invoice_date": result.get("fecha"),
                "invoice_date_due": result.get("fechaVto"),
                "name": nombre,
                "invoice_line_ids": items,
            }
            print("DATA")
            print(data)

            invoice.sudo().write(data)
        except Exception as e:
            print(f"Error al actualizar la factura: {e}")

    def extractInfo(self, file_path):

        image = Image.open(file_path)

        # Usar pytesseract para extraer texto
        return pytesseract.image_to_string(image, lang="spa")

    def procesarFactura(self, file_path):

        genai.configure(api_key=API_KEY)

        # Prepare file to upload to GenAI File API
        display_name = "fact1"
        file_response = genai.upload_file(path=file_path, display_name=display_name)
        print(f"Uploaded file {file_response.display_name} as: {file_response.uri}")

        # Make Gemini 1.5 API LLM call
        prompt = "me das la info de esta factura"
        model_name = "models/gemini-1.5-flash"
        model = genai.GenerativeModel(
            model_name,
            generation_config={"response_mime_type": "application/json"},
            system_instruction=(
                "Eres un asistente que analiza facturas de compra y extrae la información extraída con un OCR. "
                "Chequea la información para separarla en los siguientes campos en formato JSON (las fechas en formato aaaa-mm-dd): "
                f"proveedor: razon_social, condicion_iva, cuit (sin guiones), telefono, direccion, email, celular"
                "destinatario: razon_social, condicion_iva, cuit (sin guiones)"
                "fecha, nroFactura, fechaVto, fechaDesde (opcional), fechaHasta (opcional), "
                "items: [{descripcion, cantidad, importeUnitario, porcentajeIva, importeTotal, codigoProducto}]. "
                "En la columna FACTURA se encuentran los datos de la factura y el cuit del proveedor!"
                "El porcentajeIva suele estar en una columna (%IVA) y los items con la forma (10.50) o (21.00). "
                "En caso de que algún item no tenga cantidad, debe ser 1. Si no se encuentra la cantidad, debe ser 1, "
                "y en caso de no tener precio unitario, debe ser el total del item. "
                "En el caso de los ticket factura, los datos del proveedor suelen estar en la parte superior con datos como "
                "Dom.com (domicilio comercial), Dom.Leg, C.U.I.T, y el IVA RESPONSABLE INSCRIPTO se refiere a que el proveedor es inscripto."
            ),
        )
        try:
            response = model.generate_content([prompt, file_response])
        except Exception as e:
            logger.error(f"ERROR AL GENERAR CON GEMINI: {e}")

        genai.delete_file(name=file_response.name)
        return json.loads(response.text)
