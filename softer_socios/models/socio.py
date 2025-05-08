# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)


class ClubMember(models.Model):
    _name = "socios.socio"
    _description = "Socios"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    partner_id = fields.Many2one(
        "res.partner",
        string="Contacto Socio",
        required=True,
        ondelete="cascade",
        index=True,
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
    )
    contactoPrimario = fields.Many2one(
        "res.partner",
        string="Contacto Primario",
        required=False,
        store=True,
    )
    contactoSecundario = fields.Many2one(
        "res.partner",
        string="Contacto Secundario",
        required=False,
        store=True,
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
        help="Categoría que se asignará a las suscripciones generadas",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Producto",
        help="Producto que se asignará a la suscripcion generadas",
    )
    name = fields.Char(
        related="partner_id.name", string="Nombre", store=True, readonly=False
    )
    phone = fields.Char(
        related="partner_id.phone", string="Teléfono", store=True, readonly=False
    )
    mobile = fields.Char(
        related="partner_id.mobile", string="Móvil", store=True, readonly=False
    )
    email = fields.Char(
        related="partner_id.email", string="Email", store=True, readonly=False
    )
    street = fields.Char(
        related="partner_id.street", string="Domicilio", store=True, readonly=False
    )
    dni = fields.Char(
        related="partner_id.vat",
        string="DNI",
        store=True,
        readonly=False,
        help="Documento Nacional de Identidad",
    )
    profesion = fields.Char(string="Profesión", store=True)
    street2 = fields.Char(
        related="partner_id.street2", string="Domicilio 2", store=True, readonly=False
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
    )
    member_number = fields.Char(string="Nro de Socio", copy=False, index=True)
    fechaNacimiento = fields.Date(string="Fecha de Nacimiento")
    genero = fields.Selection(
        selection=[("M", "Masculino"), ("F", "Femenino")],
        string="Género",
    )
    tipoSocio = fields.Selection(
        selection=[
            ("participante", "Participante"),
            ("adherente", "Adherente"),
        ],
        string="Tipo de Socio",
    )
    categoria_id = fields.Many2one(
        "socios.categoria",
        string="Categoría",
        required=True,
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
    edad = fields.Integer(string="Edad", compute="_compute_edad")

    integrante_ids = fields.One2many(
        "softer.actividades.integrantes",
        "cliente_id",
        string="Actividades",
        help="Registros de actividades en las que participa este socio",
    )

    suscripcion_ids = fields.One2many(
        "softer.suscripcion",
        "cliente_id",
        string="Suscripciones",
        help="Suscripciones asociadas a este socio (por contacto)",
    )

    integrantes_facturacion_ids = fields.Many2many(
        "softer.actividades.integrantes",
        compute="_compute_integrantes_facturacion_ids",
        string="Integrantes (por Cliente Facturación)",
        help="Integrantes donde el cliente_id es igual al cliente_facturacion del socio",
    )

    suscripciones_facturacion_ids = fields.Many2many(
        "softer.suscripcion",
        compute="_compute_suscripciones_facturacion_ids",
        string="Suscripciones (por Cliente Facturación)",
        help="Suscripciones donde el cliente_id es igual al cliente_facturacion del socio",
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
        _logger.info(f"Socio creado: {nuevosocio.id}")

        # Intentar crear la suscripción
        try:
            _logger.info("Iniciando creación de suscripción")
            nuevosocio.subscription_upsert()
        except Exception as e:
            _logger.error(f"Error al crear suscripción: {str(e)}")
            raise

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

    def subscription_upsert(self):
        """Crea o actualiza suscripciones para los socios"""
        _logger.info(f"Iniciando subscription_upsert para socio {self.id}")
        _logger.info(f"Estado actual del socio: {self.estado}")
        _logger.info(
            f"Producto asignado: {self.product_id.id if self.product_id else 'No'}"
        )

        # Mapeo de estados del socio a estados de suscripción
        estado_suscripcion = {
            "activa": "activa",
            "suspendida": "suspendida",
            "baja": "finalizada",
            "finalizada": "finalizada",
        }.get(self.estado, "finalizada")

        _logger.info(f"Estado de suscripción mapeado: {estado_suscripcion}")

        # Buscar suscripción existente por idSocio
        subscription = self.env["softer.suscripcion"].search(
            [
                ("idSocio", "=", self.id),
                ("estado", "in", ["activa", "suspendida"]),
            ],
            limit=1,
        )

        if subscription:
            _logger.info(f"Suscripción existente encontrada: {subscription.id}")
            # Actualizar suscripción existente
            subscription.cambiarEstado(
                estado_suscripcion,
                f"Cambio de estado desde socio {self.id}",
                self.env.user.id,
            )
            _logger.info("Suscripción actualizada")
        elif self.estado == "activa" and self.product_id:
            _logger.info("Creando nueva suscripción")
            # Crear nueva suscripción solo si el estado es activa
            subscription = self.env["softer.suscripcion"].create(
                {
                    "cliente_id": self.partner_id.id,
                    "cliente_facturacion": self.cliente_facturacion.id,
                    "estado": "activa",
                    "fecha_inicio": fields.Date.context_today(self),
                    "idSocio": self.id,
                    "tieneSocio": True,
                    "paga_debito_automatico": self.paga_debito_automatico,
                    "categoria_id": self.categoria_suscripcion.id,
                    "tipo_temporalidad": "mensual",
                    "cantidad_recurrencia": 1,
                    "usoSuscripcion": True,
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product_id.id,
                                "cantidad": 1,
                            },
                        )
                    ],
                }
            )
            _logger.info(f"Nueva suscripción creada: {subscription.id}")
            # Registrar el cambio de estado inicial
            subscription.cambiarEstado(
                "activa",
                f"Creación desde socio {self.id}",
                self.env.user.id,
            )
            _logger.info("Estado inicial de suscripción registrado")
        else:
            _logger.warning(
                f"No se creó suscripción. Estado: {self.estado}, "
                f"Producto: {self.product_id.id if self.product_id else 'No'}"
            )

        _logger.info(
            f"Suscripción {'actualizada' if subscription else 'creada'} "
            f"para socio {self.id}"
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Éxito",
                "message": "Suscripciones actualizadas correctamente.",
                "type": "success",
                "sticky": True,
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
                    [("cliente_id", "=", socio.cliente_facturacion.id)]
                )
                socio.integrantes_facturacion_ids = integrantes
            else:
                socio.integrantes_facturacion_ids = False

    @api.depends("cliente_facturacion")
    def _compute_suscripciones_facturacion_ids(self):
        for socio in self:
            if socio.cliente_facturacion:
                suscripciones = self.env["softer.suscripcion"].search(
                    [("cliente_id", "=", socio.cliente_facturacion.id)]
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
