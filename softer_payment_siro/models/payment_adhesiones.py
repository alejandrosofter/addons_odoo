from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import re
from datetime import datetime
import logging
from ..const import (
    API_SIRO_PRODUCCION,
    API_SIRO_HOMOLOGACION,
)

_logger = logging.getLogger(__name__)


class PaymentAdhesiones(models.Model):
    _name = "payment.adhesiones"
    _description = "Adhesiones de Pago SIRO"
    _order = "fecha_alta desc"

    name = fields.Char(
        string="Nombre",
        compute="_compute_name",
        store=True,
    )

    provider_id = fields.Many2one(
        "payment.provider",
        string="Proveedor de Pago",
        required=True,
        domain="[('code', '=', 'siro')]",
        ondelete="restrict",
        help="Proveedor de pago SIRO para realizar las operaciones",
        default=lambda self: self.env["payment.provider"]
        .search([("code", "=", "siro")], limit=1)
        .id,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        required=True,
        ondelete="restrict",
        help="Cliente asociado a la adhesión",
    )

    numero_adhesion = fields.Char(
        string="Número de Adhesión",
        size=22,
        required=True,
        help="Número de adhesión del cliente. Puede ser CBU Bancario "
        "(22 dígitos) o número de tarjeta de crédito (16 dígitos).",
    )

    numero_cliente_empresa = fields.Char(
        string="Código de Pago Electrónico",
        size=19,
        required=True,
        readonly=True,
        help="Código de Pago Electrónico (19 dígitos). "
        "Primeros 9 dígitos: identificador del cliente y los 10 dígitos restantes: convenio del proveedor siro",
    )

    fecha_alta = fields.Datetime(
        string="Fecha de Alta",
        readonly=True,
        help="Fecha y hora del alta de la adhesión para el CPE.",
    )

    fecha_baja = fields.Datetime(
        string="Fecha de Baja",
        help="Fecha y hora de la baja de la adhesión para el CPE.",
        readonly=True,
    )

    tipo_adhesion = fields.Selection(
        [("VS", "VISA"), ("MC", "MASTERCARD"), ("DD", "Débito Directo (cbu)")],
        string="Tipo de Adhesión",
        size=2,
        required=True,
        help="Tipo de adhesión del cliente: VISA, MASTERCARD o Débito Directo",
    )

    active = fields.Boolean(
        default=True, help="Permite archivar/desarchivar la adhesión"
    )

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("confirmed", "Confirmado"),
            ("baja", "Baja"),
            ("error", "Error"),
        ],
        string="Estado",
        default="draft",
        required=True,
        readonly=True,
    )

    error_message = fields.Text(
        string="Mensaje de Error",
        readonly=True,
    )

    def _call_siro_api(self, endpoint, data):
        """Realiza la llamada a la API de SIRO usando el provider."""
        self.ensure_one()
        try:
            response = self.provider_id.callSiroApi(
                endpoint=endpoint, payload=data, method="POST", api="siro"
            )
            return response.json()
        except Exception as e:
            _logger.error("Error al llamar a la API de SIRO: %s", str(e))
            return {"Message": str(e)}

    def _convert_iso_datetime(self, iso_date_str):
        """Convierte una fecha ISO 8601 al formato de Odoo."""
        if not iso_date_str:
            return False
        try:
            from datetime import datetime
            from dateutil import parser

            # Parsear la fecha ISO
            dt = parser.parse(iso_date_str)
            # Convertir a UTC si tiene zona horaria
            if dt.tzinfo:
                dt = dt.astimezone(datetime.now().astimezone().tzinfo)
            # Formatear al formato que Odoo espera
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            _logger.error("Error al convertir fecha: %s", str(e))
            return False

    def _generate_cliente_id_empresa(self, partner):
        """Genera un ID de cliente empresa de 9 dígitos a partir del ID del partner.

        Args:
            partner (res.partner): Partner del cual generar el ID

        Returns:
            str: ID de cliente empresa de 9 dígitos

        Raises:
            UserError: Si no se puede generar un ID válido
        """
        if not partner:
            raise UserError(_("El cliente es requerido."))

        # Convertir el ID del partner a string y rellenar con ceros a la izquierda
        partner_id_str = str(partner.id).zfill(9)

        # Si el ID es mayor a 9 dígitos, usar los últimos 9
        if len(partner_id_str) > 9:
            partner_id_str = partner_id_str[-9:]

        return partner_id_str

    @api.onchange("partner_id", "provider_id")
    def _onchange_partner_provider(self):
        if self.partner_id and self.provider_id and self.provider_id.id_convenio:
            try:
                cliente_id = self._generate_cliente_id_empresa(self.partner_id)
                self.numero_cliente_empresa = (
                    f"{cliente_id}{self.provider_id.id_convenio}"
                )
            except UserError as e:
                return {"warning": {"title": _("Advertencia"), "message": str(e)}}
        else:
            self.numero_cliente_empresa = False

    @api.model
    def create(self, vals):
        """Sobrescribe el método create para validar con la API de SIRO."""
        # Obtener el provider y partner para poder hacer la llamada
        provider = self.env["payment.provider"].browse(vals.get("provider_id"))
        partner = self.env["res.partner"].browse(vals.get("partner_id"))

        if not provider:
            raise UserError(_("Debe seleccionar un proveedor de pago SIRO."))

        if not provider.id_convenio:
            raise UserError(_("El proveedor no tiene configurado el ID de convenio."))

        # Generar numero_cliente_empresa
        cliente_id = self._generate_cliente_id_empresa(partner)
        numero_cliente_empresa = f"{cliente_id}{provider.id_convenio}"
        vals["numero_cliente_empresa"] = numero_cliente_empresa

        # Preparar datos para la API
        api_data = {
            "numeroAdhesion": vals.get("numero_adhesion"),
            "numeroClienteEmpresa": numero_cliente_empresa,
            "tipoAdhesion": vals.get("tipo_adhesion"),
        }

        # Llamar a la API antes de crear el registro
        try:
            response = provider.callSiroApi(
                endpoint="siro/Adhesiones", payload=api_data, method="POST", api="siro"
            ).json()

            if "fechaAlta" in response:
                fecha_alta = self._convert_iso_datetime(response.get("fechaAlta"))
                if not fecha_alta:
                    raise UserError(_("Error al procesar la fecha de alta."))

                vals.update(
                    {
                        "state": "confirmed",
                        "fecha_alta": fecha_alta,
                    }
                )
                return super().create(vals)
            else:
                raise UserError(_("Error al crear la adhesión en SIRO."))

        except Exception as e:
            if "La adhesión ya existe" in str(e):
                response = provider.callSiroApi(
                    endpoint=f"siro/Adhesiones/Desactivar/{numero_cliente_empresa}",
                    payload={},
                    method="POST",
                    api="siro",
                ).json()
                raise UserError(
                    _(
                        "La adhesion existia, hizo la baja. Vuelve a intentar por favor..."
                    )
                )
            raise UserError(str(e))

    @api.constrains("numero_adhesion", "tipo_adhesion")
    def _check_numero_adhesion_format(self):
        for record in self:
            if (
                record.tipo_adhesion in ["VS", "MC"]
                and len(record.numero_adhesion) != 16
            ):
                raise ValidationError(
                    "Para tarjetas de crédito, el número de adhesión debe "
                    "tener 16 dígitos."
                )
            elif record.tipo_adhesion == "DD" and len(record.numero_adhesion) != 22:
                raise ValidationError(
                    "Para Débito Directo, el número de adhesión (CBU) debe "
                    "tener 22 dígitos."
                )
            if not record.numero_adhesion.isdigit():
                raise ValidationError(
                    "El número de adhesión debe contener solo dígitos " "numéricos."
                )

    @api.depends("partner_id", "tipo_adhesion", "numero_adhesion")
    def _compute_name(self):
        selection_dict = dict(self._fields["tipo_adhesion"].selection)
        for record in self:
            if record.partner_id and record.tipo_adhesion:
                name = (
                    f"{record.partner_id.name} | {selection_dict[record.tipo_adhesion]}"
                )
                if record.numero_adhesion:
                    name = f"{name} ({record.numero_adhesion})"
                record.name = name
            else:
                record.name = record.numero_adhesion or ""

    def action_baja(self):
        """Da de baja la adhesión en SIRO."""
        self.ensure_one()

        if self.state != "confirmed":
            raise UserError("Solo se pueden dar de baja adhesiones confirmadas.")

        # Preparar datos para la API
        api_data = {}

        try:
            response = self.provider_id.callSiroApi(
                endpoint=f"siro/Adhesiones/Desactivar/{self.numero_cliente_empresa}",
                payload=api_data,
                method="POST",
                api="siro",
            ).json()
            print("BAJA!!")
            print(response)
            # La respuesta es un array, tomamos el primer elemento
            if response and isinstance(response, list) and len(response) > 0:
                adhesion_data = response[0]
                if adhesion_data.get("numeroAdhesion"):
                    self.write(
                        {
                            "state": "baja",
                            "fecha_baja": datetime.now(),
                        }
                    )
                    return True

            raise UserError("No se pudo procesar la baja de la adhesión.")

        except Exception as e:
            raise UserError(str(e))
