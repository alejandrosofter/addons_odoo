# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)


class ClubMember(models.Model):
    _name = "res_partner.socio"
    _description = "Socios"
    _order = "name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    fecha_nacimiento = fields.Date(
        string="Fecha de Nacimiento",
        help="Fecha de nacimiento del contacto",
        tracking=True,
        store=True,
    )
    genero = fields.Selection(
        selection=[("M", "Masculino"), ("F", "Femenino")],
        string="Género",
        tracking=True,
    )

    cbu_contacto_facturacion = fields.Many2one(
        "res.partner.bank",
        string="CBU Facturación",
        required=False,
        store=True,
        domain="[('partner_id', '=', cliente_facturacion)]",
        help="CBU asociado al contacto de facturación",
    )
    cliente_facturacion = fields.Many2one(
        "res.partner",
        string="Facturación",
        required=True,
        store=True,
        tracking=True,
    )
    contactoPrimario = fields.Many2one(
        "res.partner",
        string="Contacto Primario",
        required=False,
        store=True,
        tracking=True,
    )
    contactoSecundario = fields.Many2one(
        "res.partner",
        string="Contacto Secundario",
        required=False,
        store=True,
        tracking=True,
    )
    paga_debito_automatico = fields.Boolean(
        string="Abona Debito Automatico",
        default=False,
        tracking=True,
        help="Indica si el socio abona mediante débito automático",
    )
    categoria_suscripcion = fields.Many2one(
        "softer.suscripcion.categoria",
        string="Categoría de Suscripción",
        tracking=True,
        help="Categoría que se asignará a las suscripciones generadas",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Producto",
        help="Producto que se asignará a la suscripcion generadas",
    )
    name = fields.Char(
        related="partner_id.name",
        string="Nombre",
        store=True,
        readonly=False,
        tracking=True,
    )
    phone = fields.Char(
        related="partner_id.phone",
        string="Teléfono",
        store=True,
        readonly=False,
        tracking=True,
    )
    mobile = fields.Char(
        related="partner_id.mobile", string="Móvil", store=True, readonly=False
    )
    email = fields.Char(
        related="partner_id.email", string="Email", store=True, readonly=False
    )
    street = fields.Char(
        related="partner_id.street",
        string="Domicilio",
        store=True,
        readonly=False,
    )
    dni = fields.Char(
        related="partner_id.vat",
        string="DNI",
        store=True,
        readonly=False,
        help="Documento Nacional de Identidad",
        tracking=True,
    )
    profesion = fields.Char(string="Profesión", store=True)
    street2 = fields.Char(
        related="partner_id.street2",
        string="Domicilio 2",
        store=True,
        readonly=False,
    )
    zip = fields.Char(
        related="partner_id.zip",
        string="Código Postal",
        store=True,
        readonly=False,
        default=lambda self: self.env["ir.config_parameter"]
        .sudo()
        .get_param("socios.default_zip", default=""),
    )
    city = fields.Char(
        related="partner_id.city",
        string="Ciudad",
        store=True,
        readonly=False,
        default=lambda self: self.env["ir.config_parameter"]
        .sudo()
        .get_param("socios.default_city", default=""),
    )
    state_id = fields.Many2one(
        related="partner_id.state_id",
        string="Provincia",
        store=True,
        readonly=False,
        default=lambda self: self.env["ir.config_parameter"]
        .sudo()
        .get_param("socios.default_state_id", default=False),
    )
    country_id = fields.Many2one(
        related="partner_id.country_id",
        string="País",
        store=True,
        readonly=False,
        default=lambda self: self.env["ir.config_parameter"]
        .sudo()
        .get_param("socios.default_country_id", default=False),
    )

    image_1920 = fields.Image(
        related="partner_id.image_1920",
        string="Foto",
        max_width=1920,
        max_height=1920,
        store=True,
        readonly=False,
        tracking=True,
    )
    member_number = fields.Char(string="Nro de Socio", copy=False, index=True)
    fechaNacimiento = fields.Date(string="Fecha de Nacimiento")

    tipoSocio = fields.Selection(
        selection=[
            ("participante", "Participante"),
            ("adherente", "Adherente"),
        ],
        string="Tipo de Socio",
        tracking=True,
    )
    categoria_id = fields.Many2one(
        "socios.categoria",
        string="Categoría",
        required=True,
        tracking=True,
    )
    estado = fields.Selection(
        selection=[
            ("activa", "Activa"),
            ("suspendida", "Suspendida"),
            ("baja", "Baja"),
        ],
        string="Estado",
        default="activa",
    )
    estado_ids = fields.One2many(
        "socios.estado", "socio_id", string="Historial de Estados"
    )
    fechaAlta = fields.Date(string="Fecha de Alta")
    fechaBaja = fields.Date(string="Fecha de Baja")

    esActivo = fields.Boolean(string="Es Socio Activo", default=False)
    edad = fields.Integer(string="Edad", compute="_compute_edad", store=True)

    integrantes_facturacion_ids = fields.Many2many(
        "softer.actividades.integrantes",
        compute="_compute_integrantes_facturacion_ids",
        string="Integrantes (por Cliente Facturación)",
        help=(
            "Integrantes donde el cliente_id es igual al "
            "cliente_facturacion del socio"
        ),
    )

    suscripciones_facturacion_ids = fields.Many2many(
        "softer.suscripcion",
        compute="_compute_suscripciones_facturacion_ids",
        string="Suscripciones (por Cliente Facturación)",
        help=(
            "Suscripciones donde el cliente_id es igual al "
            "cliente_facturacion del socio"
        ),
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Contacto",
        required=True,
        ondelete="cascade",
        tracking=True,
        help="Contacto asociado a este socio",
    )
    motivos_cambio_productos = fields.One2many(
        "softer.suscripcion.motivo_cambio_productos",
        compute="_compute_motivos_cambio_productos",
        string="Motivos de Cambio de Productos",
    )

    _sql_constraints = [
        (
            "member_number_categoria_uniq",
            "unique(member_number, categoria_id)",
            "Ya existe un socio con este número en la misma categoría.",
        ),
        (
            "dni_uniq",
            "unique(dni)",
            "Ya existe un socio con este DNI.",
        ),
        (
            "partner_id_uniq",
            "unique(partner_id)",
            "Cada socio debe estar vinculado a un único contacto.",
        ),
    ]

    @api.depends("fechaNacimiento")
    def _compute_edad(self):
        for record in self:
            if record.fechaNacimiento:
                today = date.today()
                edad = today.year - record.fechaNacimiento.year
                if (today.month, today.day) < (
                    record.fechaNacimiento.month,
                    record.fechaNacimiento.day,
                ):
                    edad -= 1
                record.edad = edad
            else:
                record.edad = 0

    @api.onchange("fechaNacimiento")
    def _onchange_fechaNacimiento(self):
        if self.fechaNacimiento:
            edad = self._calcular_edad(self.fechaNacimiento)
            edad_adherente = int(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("socios.default_edad_adherente", default="18")
            )
            if edad > edad_adherente:
                self.tipoSocio = "adherente"
            else:
                self.tipoSocio = "participante"

    # @api.onchange("categoria_id")
    # def _onchange_categoria_id(self):
    #     if self.categoria_id and not self.member_number:
    #         self.member_number = str(self.categoria_id.proximoNroSocio)

    @api.onchange("dni")
    def _onchange_dni(self):
        if self.dni:
            # Buscar partner con ese VAT
            partner = self.env["res.partner"].search([("vat", "=", self.dni)], limit=1)
            if partner:
                # Si existe, actualizar todos los campos relacionados
                self.partner_id = partner.id
                self.name = partner.name
                self.phone = partner.phone
                self.mobile = partner.mobile
                self.email = partner.email
                self.street = partner.street
                self.street2 = partner.street2
                self.zip = partner.zip
                self.city = partner.city
                self.state_id = partner.state_id
                self.country_id = partner.country_id

    @api.onchange("cliente_facturacion")
    def _onchange_cliente_facturacion(self):
        """Limpia el CBU cuando cambia el cliente de facturación"""
        self.cbu_contacto_facturacion = False

    def _sync_partner_fields(self, vals=None):
        """
        Sincroniza los datos básicos del socio hacia el partner relacionado.
        Si se pasa vals, solo actualiza los campos modificados.
        """
        campos = [
            ("name", "name"),
            ("phone", "phone"),
            ("mobile", "mobile"),
            ("email", "email"),
            ("street", "street"),
            ("street2", "street2"),
            ("zip", "zip"),
            ("city", "city"),
            ("state_id", "state_id"),
            ("country_id", "country_id"),
            ("vat", "dni"),
            ("fecha_nacimiento", "fecha_nacimiento"),
            ("genero", "genero"),
        ]
        for socio in self:
            partner_vals = {}
            if vals:
                for field_socio, field_partner in campos:
                    if field_socio in vals:
                        partner_vals[field_partner] = vals[field_socio]
            else:
                for field_socio, field_partner in campos:
                    partner_vals[field_partner] = getattr(socio, field_socio, False)
            if partner_vals and socio.partner_id:
                socio.partner_id.sudo().write(partner_vals)
            # Sincronizar payment_adhesion_id en cliente_facturacion
            if vals and "payment_adhesion_id" in vals and socio.cliente_facturacion:
                socio.cliente_facturacion.sudo().write(
                    {"payment_adhesion_id": vals["payment_adhesion_id"]}
                )
            elif not vals and socio.cliente_facturacion and socio.payment_adhesion_id:
                socio.cliente_facturacion.sudo().write(
                    {"payment_adhesion_id": socio.payment_adhesion_id}
                )

    @api.model
    def create(self, vals):
        _logger.info(f"Iniciando creación de socio con valores: {vals}")
        # Verificar si ya existe un socio con el mismo DNI
        dni = vals.get("dni")
        if dni:
            existing_socio = self.search([("dni", "=", dni)])
            if existing_socio:
                _logger.warning(f"Ya existe socio con DNI {dni}")
                raise ValidationError("Ya existe un socio con el DNI %s" % dni)

        # Si no hay partner_id, crear uno nuevo
        if not vals.get("partner_id"):
            _logger.info("Creando nuevo partner para el socio")
            partner_vals = {
                "name": vals.get("name", "Nuevo Socio"),
                "phone": vals.get("phone"),
                "mobile": vals.get("mobile"),
                "email": vals.get("email"),
                "street": vals.get("street"),
                "street2": vals.get("street2"),
                "zip": vals.get("zip"),
                "city": vals.get("city"),
                "state_id": vals.get("state_id"),
                "country_id": vals.get("country_id"),
                "vat": vals.get("dni"),
                "socio_id": False,
                "fecha_nacimiento": vals.get("fecha_nacimiento"),
                "genero": vals.get("genero"),
            }
            partner = self.env["res.partner"].create(partner_vals)
            vals["partner_id"] = partner.id
            _logger.info(f"Partner creado: {partner.id}")

        # Asignar número de socio si no está definido y hay categoría
        if not vals.get("member_number") and vals.get("categoria_id"):
            categoria = self.env["socios.categoria"].browse(vals["categoria_id"])
            if categoria:
                vals["member_number"] = categoria.next_nroSocio()
            else:
                _logger.warning("No se encontró la categoría especificada")

        nuevosocio = super(ClubMember, self).create(vals)
        # Sincronizar socio_id en el partner
        if nuevosocio.partner_id:
            nuevosocio.partner_id.sudo().write({"socio_id": nuevosocio.id})
        # Sincronizar datos básicos al partner
        nuevosocio._sync_partner_fields()
        _logger.info(f"Socio creado: {nuevosocio.id}")

        return nuevosocio

    @api.constrains("tipoSocio", "member_number")
    def _check_member_number_required(self):
        for record in self:
            if record.tipoSocio and not record.member_number:
                raise ValidationError(
                    "El número de socio es obligatorio si el tipo de socio "
                    "está definido."
                )

    @api.constrains("member_number", "categoria_id")
    def _check_member_number_unique(self):
        for record in self:
            if record.member_number and record.categoria_id:
                domain = [
                    ("member_number", "=", record.member_number),
                    ("categoria_id", "=", record.categoria_id.id),
                    ("id", "!=", record.id),
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        "Ya existe un socio con este número en la misma " "categoría."
                    )

    @api.constrains("dni")
    def _check_dni_unique(self):
        for record in self:
            if record.dni:
                domain = [
                    ("dni", "=", record.dni),
                    ("id", "!=", record.id),
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        "Ya existe un socio con el DNI %s" % record.dni
                    )

    def action_view_estados(self):
        self.ensure_one()
        return {
            "name": "Nuevo Estado",
            "type": "ir.actions.act_window",
            "res_model": "socios.estado",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_socio_id": self.id,
                "default_fecha": fields.Date.context_today(self),
                **self.env.context,
            },
        }

    def _calcular_edad(self, fecha_nacimiento):
        today = date.today()
        edad = today.year - fecha_nacimiento.year
        if (today.month, today.day) < (
            fecha_nacimiento.month,
            fecha_nacimiento.day,
        ):
            edad -= 1
        return edad

    @api.depends("cliente_facturacion")
    def _compute_integrantes_facturacion_ids(self):
        for socio in self:
            if socio.cliente_facturacion:
                integrantes = self.env["softer.actividades.integrantes"].search(
                    [("cliente_id", "=", socio.partner_id.id)]
                )
                socio.integrantes_facturacion_ids = integrantes
            else:
                socio.integrantes_facturacion_ids = False

    @api.depends("cliente_facturacion")
    def _compute_suscripciones_facturacion_ids(self):
        for socio in self:
            if socio.cliente_facturacion:
                suscripciones = self.env["softer.suscripcion"].search(
                    [("cliente_facturacion", "=", socio.cliente_facturacion.id)]
                )
                socio.suscripciones_facturacion_ids = suscripciones
            else:
                socio.suscripciones_facturacion_ids = False

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        config = self.env["ir.config_parameter"].sudo()
        categoria_suscripcion = config.get_param("socios.categoria_suscripcion")
        categoria_id = config.get_param("socios.default_categoria_id")
        product_id = config.get_param("socios.default_product_id")
        if categoria_suscripcion:
            res["categoria_suscripcion"] = int(categoria_suscripcion)
        if categoria_id:
            res["categoria_id"] = int(categoria_id)
        if product_id:
            res["product_id"] = int(product_id)
        return res

    def write(self, vals):
        for socio in self:
            old_partner = socio.partner_id
            res = super(ClubMember, socio).write(vals)
            new_partner = socio.partner_id
            # Si cambió el partner, limpiar el anterior
            if vals.get("partner_id") and old_partner and old_partner != new_partner:
                old_partner.sudo().write({"socio_id": False})
            # Asegurar que el nuevo partner apunte al socio
            if new_partner and new_partner.socio_id != socio:
                new_partner.sudo().write({"socio_id": socio.id})
            # Sincronizar datos básicos al partner
            socio._sync_partner_fields(vals)
        return res

    def unlink(self):
        for socio in self:
            if socio.partner_id:
                socio.partner_id.sudo().write({"socio_id": False})
        return super(ClubMember, self).unlink()

    @api.depends("partner_id")
    def _compute_motivos_cambio_productos(self):
        for socio in self:
            if socio.partner_id:
                motivos = self.env["softer.suscripcion.motivo_cambio_productos"].search(
                    [("cliente_id", "=", socio.partner_id.id)]
                )
                socio.motivos_cambio_productos = motivos
            else:
                socio.motivos_cambio_productos = False
