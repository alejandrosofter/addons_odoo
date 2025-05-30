# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
from datetime import datetime

import requests
from werkzeug import urls

from odoo import _, fields, models, api
from odoo.exceptions import ValidationError

from odoo.addons.softer_payment_siro import const

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = "payment.provider"
    nro_empresa = fields.Char(
        string="Número de Empresa",
        size=10,
        required=True,
        help="Número de empresa (10 caracteres)",
    )
    code = fields.Selection(
        selection_add=[("siro", "SIRO")],
        ondelete={"siro": "set default"},
    )
    user_id = fields.Char(
        string="Usuario SIRO",
        help="Usuario para autenticación con SIRO",
    )
    password = fields.Char(
        string="Contraseña SIRO",
        help="Contraseña para autenticación con SIRO",
    )
    id_convenio = fields.Char(
        string="ID Convenio SIRO",
        help="ID del convenio para autenticación con SIRO (10 dígitos)",
        size=10,
    )
    cuit_administrador = fields.Char(
        string="CUIT Administrador SIRO",
        help="CUIT del administrador para autenticación con SIRO",
    )
    token_access = fields.Char(
        string="Token de Acceso SIRO",
        help="Token de acceso para autenticación con SIRO",
        readonly=True,
    )

    @api.constrains("nro_empresa")
    def _check_nro_empresa_length(self):
        for record in self:
            if len(record.nro_empresa) != 10:
                raise ValidationError(
                    _("El número de empresa debe tener exactamente 10 caracteres.")
                )

    # === BUSINESS METHODS === #

    def _get_supported_currencies(self):
        """Override of `payment` to return the supported currencies."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == "siro":
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    def authenticate(self, timeout=10):
        """Authenticate with SIRO API."""
        self.ensure_one()
        # url dependiendo si es produccion o homologacion
        url = (
            const.API_AUTH_HOMOLOGACION
            if self.state == "test"
            else const.API_AUTH_PRODUCCION
        )

        payload = {
            "Usuario": self.user_id,
            "Password": self.password,
        }

        response = requests.post(f"{url}auth/Sesion", json=payload, timeout=timeout)

        if response.status_code == 200:

            response_json = response.json()
            if response_json and "access_token" in response_json:
                self.token_access = response_json["access_token"]
                print(self.token_access)
            else:
                raise ValidationError(
                    _(
                        "Error en la respuesta de autenticación: no se encontró el token."
                    )
                )
        else:
            raise ValidationError(
                _(
                    "Error al autenticar con SIRO. "
                    "Código de estado: %(status)s. "
                    "Respuesta: %(response)s",
                    status=response.status_code,
                    response=response.text,
                )
            )

        return response_json

    def _format_api_error(self, response):
        """Formatea el mensaje de error de la API."""
        if isinstance(response, dict):
            message = response.get("Message", "")
            model_state = response.get("ModelState", {})

            error_details = []
            # Procesar errores de ModelState
            if model_state:
                for field_errors in model_state.values():
                    if isinstance(field_errors, list):
                        error_details.extend(field_errors)

            # Construir mensaje final
            if error_details:
                message = f"{message}\n\nDetalles:\n" + "\n".join(
                    f"- {error}" for error in error_details
                )

            return message or "Error desconocido en la API"
        return str(response)

    def callSiroApi(
        self, endpoint, payload=None, method="POST", api="pagos", timeout=30
    ):
        """Call SIRO API."""
        self.ensure_one()
        self.authenticate(timeout=timeout)
        if api == "pagos":
            url_api = (
                const.API_PAGOS_HOMOLOGACION
                if self.state == "test"
                else const.API_PAGOS_PRODUCCION
            )
        else:
            url_api = (
                const.API_SIRO_HOMOLOGACION
                if self.state == "test"
                else const.API_SIRO_PRODUCCION
            )
        headers = {
            "Authorization": f"Bearer {self.token_access}",
            "Content-Type": "application/json",
        }
        url = urls.url_join(url_api, endpoint)
        print(
            f"URL: {url} \nPayload: {payload} \nHeaders: {headers} \nTimeout: {timeout}"
        )
        try:
            if method == "GET":
                response = requests.get(
                    url, params=payload, headers=headers, timeout=timeout
                )
            else:
                response = requests.post(
                    url, json=payload, headers=headers, timeout=timeout
                )

            # Si hay error HTTP, procesamos la respuesta
            if not response.ok:
                error_data = response.json()
                error_msg = self._format_api_error(error_data)
                raise ValidationError(error_msg)

            return response

        except requests.exceptions.HTTPError as e:
            _logger.error(
                "Error HTTP en llamada a SIRO: %s\nPayload: %s", str(e), payload
            )
            raise ValidationError(str(e))
        except requests.exceptions.RequestException as e:
            _logger.error("Error en llamada a SIRO: %s\nPayload: %s", str(e), payload)
            raise ValidationError(
                "Error de conexión con SIRO. Por favor, intente nuevamente."
            )
        except Exception as e:
            _logger.error(
                "Error inesperado en llamada a SIRO: %s\nPayload: %s", str(e), payload
            )
            raise ValidationError(str(e))

    def _format_nro_cliente_empresa(self, partner_id):
        """Formatea el número de cliente según especificación SIRO.

        Formato: 19 dígitos numéricos
        - Primeros 9 dígitos: identificador del cliente
        - Últimos 10 dígitos: número de convenio/nro_empresa

        :param int partner_id: ID del partner
        :return: Número de cliente formateado
        :rtype: str
        """
        # Asegurar que el partner_id tenga 9 dígitos con padding de ceros
        partner_str = str(partner_id).zfill(9)

        # Obtener y validar el id_convenio
        convenio = self.id_convenio or ""
        convenio = "".join(filter(str.isdigit, convenio))  # Solo dígitos

        if len(convenio) != 10:
            raise ValidationError(
                _("El ID de convenio debe tener 10 dígitos numéricos.")
            )

        nro_cliente = f"{partner_str}{convenio}"
        if not nro_cliente.isdigit() or len(nro_cliente) != 19:
            raise ValidationError(_("Error al generar número de cliente SIRO."))
        return nro_cliente

    def _format_nro_comprobante(self, reference, concept_code="0"):
        """Formatea el número de comprobante según especificación SIRO.

        Formato: 20 dígitos numéricos
        - Primeros 15 dígitos: identificador interno
        - Dígito 16: código de concepto (0-9)
        - Últimos 4 dígitos: MMAA (mes y año)

        :param str reference: Referencia de la transacción
        :param str concept_code: Código de concepto (0-9)
        :return: Número de comprobante formateado
        :rtype: str
        """
        # Limpiar referencia y tomar solo números y letras
        ref_clean = "".join(c for c in str(reference) if c.isalnum())

        # Convertir letras a números (A=1, B=2, etc) y tomar los primeros 15
        ref_nums = ""
        for c in ref_clean:
            if c.isdigit():
                ref_nums += c
            elif c.isalpha():
                ref_nums += str(ord(c.upper()) - ord("A") + 1).zfill(2)

        # Asegurar 15 dígitos con padding
        ref_str = ref_nums[:15].zfill(15)

        # Validar código de concepto (0-9)
        if not concept_code.isdigit() or len(concept_code) != 1:
            raise ValidationError(_("El código de concepto debe ser un dígito (0-9)."))

        # Obtener mes y año actual en formato MMAA
        now = datetime.now()
        period = now.strftime("%m%y")

        nro_comprobante = f"{ref_str}{concept_code}{period}"
        if not nro_comprobante.isdigit() or len(nro_comprobante) != 20:
            raise ValidationError(_("Error al generar número de comprobante SIRO."))
        return nro_comprobante

    def _validate_url(self, url, field_name):
        """Valida que la URL sea absoluta y tenga el formato correcto.

        :param str url: URL a validar
        :param str field_name: Nombre del campo para el mensaje de error
        :return: URL validada
        :rtype: str
        :raise: ValidationError si la URL no es válida
        """
        if not url:
            raise ValidationError(_(f"La URL de {field_name} es requerida."))

        # Asegurar que la URL comience con http:// o https://
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        # Validar formato básico de URL
        try:
            result = urls.url_parse(url)
            if not result.scheme or not result.netloc:
                raise ValidationError(_(f"La URL de {field_name} no es válida: {url}"))
        except Exception as e:
            raise ValidationError(_(f"Error al validar URL de {field_name}: {str(e)}"))

        return url

    def _get_concepto(self, descripcion):
        """Obtiene el concepto según la descripción. Solo Letras y numeros"""
        return "".join(c for c in str(descripcion) if c.isalnum())[:40]

    def _siro_consulta(self, endpoint, payload=None, method="POST"):
        """Consulta a SIRO API."""
        self.ensure_one()
        print("check data")

        print(endpoint)
        response = self.callSiroApi(endpoint, payload, method)
        return response.json()

    def _siro_make_request(self, endpoint, payload=None, method="POST"):
        """Make a request to SIRO API at the specified endpoint."""
        self.ensure_one()

        _logger.info("Payload original: %s", payload)

        if payload and method == "POST":
            try:
                # Extraer partner_id del payload o usar un valor por defecto
                partner_id = payload.get("partner_id", 1)

                # Formatear datos según especificación SIRO
                nro_cliente = self._format_nro_cliente_empresa(partner_id)
                concepto = self._get_concepto(payload.get("descripcion", ""))
                nro_comprobante = self._format_nro_comprobante(
                    payload.get("referencia", ""),
                    concept_code="0",  # Concepto por defecto
                )

                # Preparar el payload según especificación SIRO
                data = {
                    "concepto": concepto,
                    "importe": float(payload.get("monto", 0)),
                    "nro_comprobante": nro_comprobante,
                    "nro_cliente_empresa": nro_cliente,
                    "idReferenciaOperacion": f"{payload.get('referencia', '')}",
                    "URL_OK": (
                        "https://www.google.com/ok"
                        if self.state == "test"
                        else payload.get("urls", {}).get("webhook", "")
                    ),
                    "URL_ERROR": (
                        "https://www.google.com/error"
                        if self.state == "test"
                        else payload.get("urls", {}).get("webhook", "")
                    ),
                }

                # Validaciones adicionales
                if not data["importe"] or data["importe"] <= 0:
                    raise ValidationError(_("El importe debe ser mayor a 0."))

                if not data["concepto"]:
                    raise ValidationError(_("El concepto es requerido."))

                payload = data
                _logger.info("Payload formateado SIRO: %s", payload)

            except ValidationError:
                raise
            except Exception as e:
                _logger.exception("Error al preparar payload SIRO")
                raise ValidationError(
                    _("Error al preparar datos para SIRO: %s", str(e))
                )

        response = self.callSiroApi(endpoint, payload, method)

        # Procesar la respuesta
        if response.status_code != 200:
            try:
                error_data = response.json()
                if "Message" in error_data:
                    message = error_data["Message"]
                    details = []

                    # Procesar errores de ModelState
                    if "ModelState" in error_data:
                        for _, errors in error_data["ModelState"].items():
                            if isinstance(errors, list):
                                details.extend(errors)

                    error_msg = f"{message}\n"
                    if details:
                        error_msg += "\nDetalles:\n" + "\n".join(
                            f"- {e}" for e in details
                        )

                    raise ValidationError(_(error_msg))
            except ValueError:
                raise ValidationError(
                    _("Error en la respuesta de SIRO: %s", response.text)
                )
        print("OKK!")
        print(response.json())
        return response.json()

    def _get_default_payment_method_codes(self):
        """Override of `payment` to return the default payment method codes."""
        default_codes = super()._get_default_payment_method_codes()
        if self.code != "siro":
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES
