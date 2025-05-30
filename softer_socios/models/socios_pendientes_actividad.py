# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SociosPendientesActividad(models.Model):
    _name = "socios.pendientes.actividad"
    _description = "Socios Pendientes de Actividad"
    _order = "socio asc"

    name = fields.Char(
        string="Nombre",
        compute="_compute_name",
        store=True,
    )
    es_debito_automatico = fields.Boolean(
        string="Abona Debito Automatico",
        store=True,
    )
    integrante_id = fields.Many2one(
        "softer.actividades.integrantes",
        string="Integrante",
        required=False,
        ondelete="set null",
    )
    categoria_suscripcion = fields.Many2one(
        "softer.suscripcion.categoria",
        string="Categoría de Suscripción",
        help="Categoría que se asignará a las suscripciones generadas",
        default=lambda self: int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("socios.categoria_suscripcion", default=False)
        )
        or False,
    )
    cliente_facturacion = fields.Many2one(
        "res.partner",
        string="Cliente Facturación",
        required=False,
        ondelete="set null",
    )
    socio = fields.Many2one(
        "res.partner",
        string="Socio",
        required=False,
        ondelete="set null",
    )
    dni = fields.Char(
        string="DNI",
        compute="_compute_fields_from_partner",
        inverse="_inverse_fields_to_partner",
        store=True,
    )
    fecha_nacimiento = fields.Date(
        string="Fecha de Nacimiento",
        compute="_compute_fields_from_partner",
        inverse="_inverse_fields_to_partner",
        store=True,
    )
    telefono = fields.Char(
        string="Teléfono",
        compute="_compute_fields_from_partner",
        inverse="_inverse_fields_to_partner",
        store=True,
    )
    email = fields.Char(
        string="Email",
        compute="_compute_fields_from_partner",
        inverse="_inverse_fields_to_partner",
        store=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Producto",
        default=lambda self: int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("socios.default_product_id", default=False)
        )
        or False,
    )
    genero = fields.Selection(
        selection=[("M", "Masculino"), ("F", "Femenino")],
        string="Género",
        default="M",
    )
    nro_socio = fields.Char(
        string="Número de Socio",
    )
    categoria_socio = fields.Many2one(
        "socios.categoria",
        string="Categoría de Socio",
        ondelete="set null",
        required=False,
    )
    domicilio = fields.Char(
        string="Domicilio",
        compute="_compute_fields_from_partner",
        inverse="_inverse_fields_to_partner",
        store=True,
    )
    cbu_contacto_facturacion = fields.Many2one(
        "res.partner.bank",
        string="CBU Facturación",
        required=False,
        store=True,
        domain="[('partner_id', '=', cliente_facturacion)]",
        help="CBU asociado al contacto de facturación",
    )
    fecha_creacion = fields.Datetime(
        string="Fecha de Creación",
        default=fields.Datetime.now,
    )
    estado = fields.Selection(
        selection=[
            ("pendiente", "Pendiente"),
            ("procesado", "Procesado"),
            ("error", "Error"),
        ],
        string="Estado",
        default="pendiente",
    )
    mensaje_error = fields.Text(string="Mensaje de Error")

    def _compute_name(self):
        """Computa el nombre del registro con el nombre del socio y el que paga"""
        for record in self:
            if record.cliente_facturacion and record.socio:
                socio = record.cliente_facturacion.name
                pagador = record.socio.name
                record.name = f"{socio} - {pagador}"

    @api.depends("cliente_facturacion")
    def _compute_fields_from_partner(self):
        """Computa todos los campos que dependen del cliente_facturacion"""
        for record in self:
            partner = record.cliente_facturacion
            record.dni = partner.vat
            record.telefono = partner.phone
            record.email = partner.email
            record.domicilio = partner.street
            record.name = partner.name

    def _inverse_fields_to_partner(self):
        """Actualiza los campos en el partner cuando se modifican en el registro"""
        for record in self:
            partner = record.cliente_facturacion
            partner.vat = record.dni
            partner.phone = record.telefono
            partner.email = record.email
            partner.street = record.domicilio

    @api.depends("cliente_facturacion")
    def _compute_nameSocio(self):
        for record in self:
            record.nameSocio = record.cliente_facturacion.name

    @api.depends("cliente_facturacion", "socio")
    def _compute_name(self):
        """Computa el nombre del registro con el nombre del socio y el que paga"""
        for record in self:
            if record.cliente_facturacion and record.socio:
                socio = record.cliente_facturacion.name
                pagador = record.socio.name
                record.name = f"{socio} - {pagador}"
            else:
                record.name = False

    def procesar_pendiente(self):
        """Procesa un registro pendiente creando un socio"""
        self.ensure_one()
        try:
            if self.estado != "pendiente" and self.estado != "error":
                _logger.info(f"Registro {self.id} no está pendiente")
                return

            # Verificar si ya existe un socio
            socio = self.env["res_partner.socio"].search(
                [("partner_id", "=", self.cliente_facturacion.id)], limit=1
            )

            if socio:
                _logger.info(
                    f"Ya existe socio {socio.id} para cliente {self.cliente_facturacion.id}"
                )
                self.estado = "procesado"
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "res_partner.socio",
                    "res_id": socio.id,
                    "view_mode": "form",
                    "target": "current",
                    "context": {
                        "default_estado": (
                            "activa" if socio.estado != "activa" else "suspendida"
                        )
                    },
                }

            # Obtener valores por defecto de configuración
            config = self.env["ir.config_parameter"].sudo()
            default_zip = config.get_param("socios.default_zip", default="")
            default_city = config.get_param("socios.default_city", default="")
            default_state_id = config.get_param(
                "socios.default_state_id", default=False
            )
            default_country_id = config.get_param(
                "socios.default_country_id", default=False
            )
            default_product_id = config.get_param(
                "socios.default_product_id", default=False
            )

            # Crear nuevo socio
            vals = {
                "cliente_facturacion": self.cliente_facturacion.id,
                "partner_id": self.socio.id,
                "fechaNacimiento": self.fecha_nacimiento,
                "phone": self.telefono,
                "email": self.email,
                "genero": self.genero,
                "street": self.domicilio,
                "zip": default_zip,
                "city": default_city,
                "cbu_contacto_facturacion": self.cbu_contacto_facturacion.id,
                "paga_debito_automatico": self.es_debito_automatico,
                "state_id": int(default_state_id) if default_state_id else False,
                "country_id": int(default_country_id) if default_country_id else False,
                "product_id": int(default_product_id) if default_product_id else False,
                "categoria_suscripcion": self.categoria_suscripcion.id,
                "tipoSocio": "participante",
                "estado": "activa",
                "esActivo": True,
                "fechaAlta": fields.Date.context_today(self),
                "categoria_id": self.categoria_socio.id,
                "member_number": (
                    self.categoria_socio.next_nroSocio()
                    if not self.nro_socio
                    else self.nro_socio
                ),
            }

            _logger.info(f"Creando socio con valores: {vals}")

            try:
                nuevo_socio = self.env["res_partner.socio"].create(vals)
                _logger.info(f"Socio creado exitosamente: {nuevo_socio.id}")
            except Exception as e:
                self.env.cr.rollback()
                self.estado = "error"
                self.mensaje_error = self.geterror(str(e))
                _logger.error(f"Error al crear socio: {str(e)}")
                return

            self.estado = "procesado"
            _logger.info(
                f"Se creó socio {nuevo_socio.id} para integrante "
                f"{self.integrante_id.id}"
            )

            return {
                "type": "ir.actions.act_window",
                "res_model": "res_partner.socio",
                "res_id": nuevo_socio.id,
                "view_mode": "form",
                "target": "current",
            }

        except Exception as e:
            self.env.cr.rollback()
            self.estado = "error"
            self.mensaje_error = self.geterror(str(e))
            _logger.error(f"Error al procesar pendiente {self.id}: {str(e)}")

    def geterror(self, error):
        """Retorna un mensaje de error legible para el usuario"""
        if "duplicate key value violates unique constraint" in str(error):
            if "socios_socio_member_number_categoria_uniq" in str(error):
                return _(
                    "No se pudo crear el socio porque ya existe otro socio con el mismo número "
                    "en la misma categoría.\n\n"
                    "Por favor, verifique que el número de socio sea único para esta categoría."
                )
            return _(
                "No se pudo crear el socio porque ya existe un registro con los mismos datos.\n\n"
                "Por favor, verifique que los datos sean únicos."
            )

        return (
            _(
                "Ocurrió un error al procesar el socio pendiente. "
                "Por favor, intente nuevamente o contacte al administrador.\n\n"
                "Error técnico: %s"
            )
            % error
        )

    def action_buscar_pendientes(self):
        """Abre un wizard para confirmar la búsqueda de socios pendientes"""
        return {
            "type": "ir.actions.act_window",
            "name": "Buscar Socios Pendientes",
            "res_model": "socios.pendientes.actividad.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_message": "¿Desea buscar socios pendientes en las actividades activas?"
            },
        }
