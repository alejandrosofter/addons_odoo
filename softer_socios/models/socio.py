# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

# Listas para selectores de fecha de facturación (ya no se usarán directamente en socio)
# MESES_SELECTION = [
#     ("1", "Enero"), ("2", "Febrero"), ("3", "Marzo"),
#     ("4", "Abril"), ("5", "Mayo"), ("6", "Junio"),
#     ("7", "Julio"), ("8", "Agosto"), ("9", "Septiembre"),
#     ("10", "Octubre"), ("11", "Noviembre"), ("12", "Diciembre"),
# ]

# DIAS_SELECTION = [(str(i), str(i)) for i in range(1, 32)]


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
    suscripcion_categoria_id = fields.Many2one(
        "softer.suscripcion.categoria",
        string="Categoría de Suscripción",
        tracking=True,
        help="Categoría que se asignará a las suscripciones generadas",
    )
    # product_id campo original, no relacionado a suscripción por plan
    product_id = fields.Many2one(
        "product.product",
        string="Producto por Defecto (Generación)",
        help="Producto que se asignará a la suscripcion " "generadas si no hay plan",
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

    suscripcion_id = fields.Many2one(
        "softer.suscripcion",
        string="Suscripción",
        help="Suscripción principal asociada al socio",
        tracking=True,
    )
    suscripcion_plan_id = fields.Many2one(
        "softer.suscripcion.plan",
        string="Plan de Suscripción",
        help="Plan de suscripción asociado al socio",
        tracking=True,
        required=True,
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
                # Si existe, actualizar los campos seleccionados
                self.partner_id = partner.id
                # No sincronizamos todos los campos aquí, solo los que se supone que _sync_partner_fields maneja.
                # Los onchange no deben modificar campos relacionados
                # que se supone que otro método sincroniza.
                # self.name = partner.name
                # self.genero = partner.genero
                # self.fechaNacimiento = partner.fecha_nacimiento
                # self.payment_adhesion_id = partner.payment_adhesion_id

    @api.onchange("cliente_facturacion")
    def _onchange_cliente_facturacion(self):
        """Limpia el CBU cuando cambia el cliente de facturación"""
        self.cbu_contacto_facturacion = False

    @api.onchange("contactoPrimario")
    def _onchange_contactoPrimario(self):
        """Sincroniza el cliente_facturacion con el contactoPrimario"""
        if self.contactoPrimario:
            self.cliente_facturacion = self.contactoPrimario
        else:
            self.cliente_facturacion = False

    def _sync_partner_fields(self, vals=None):
        """
        Sincroniza los datos básicos del socio hacia el partner relacionado.
        Si se pasa vals, solo actualiza los campos modificados.
        """
        campos = [
            ("dni", "vat"),
            ("name", "name"),
            ("genero", "genero"),
            ("payment_adhesion_id", "payment_adhesion_id"),
            ("fecha_nacimiento", "fecha_nacimiento"),
        ]
        for socio in self:
            partner_vals = {}
            if vals:
                for field_socio, field_partner in campos:
                    if field_socio in vals:
                        valor = vals[field_socio]
                        # Manejar campos Many2one específicamente
                        if field_socio == "payment_adhesion_id" and valor is not False:
                            # Si el valor es un ID, úsalo. Si es un recordset, usa su ID.
                            partner_vals[field_partner] = (
                                valor.id
                                if isinstance(valor, models.BaseModel)
                                else valor
                            )
                        else:
                            partner_vals[field_partner] = valor
            else:
                for field_socio, field_partner in campos:
                    valor = getattr(socio, field_socio, False)
                    # Manejar campos Many2one específicamente
                    if field_socio == "payment_adhesion_id" and valor is not False:
                        partner_vals[field_partner] = (
                            valor.id if isinstance(valor, models.BaseModel) else valor
                        )
                    else:
                        partner_vals[field_partner] = valor

            if partner_vals and socio.partner_id:
                socio.partner_id.sudo().write(partner_vals)

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
                # Sincronizar solo los campos especificados en _sync_partner_fields
                "vat": vals.get("dni"),
                "fecha_nacimiento": vals.get("fecha_nacimiento"),
                "genero": vals.get("genero"),
                "payment_adhesion_id": vals.get("payment_adhesion_id"),
                # otros campos del partner necesarios para la creación inicial si aplica
                "socio_id": False,
            }
            # Limpiar valores False o None antes de crear para evitar errores
            partner_vals = {
                k: v
                for k, v in partner_vals.items()
                if v is not False and v is not None
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

        # Crear registro de estado inicial 'Alta Inicial'
        try:
            self.env["socios.estado"].create(
                {
                    "socio_id": nuevosocio.id,
                    "fecha": fields.Datetime.now(),  # Usar Datetime.now() como en el modelo
                    "estado": "activa",  # Usar el campo 'estado' con valor 'activa'
                    "motivo": "Alta inicial del socio",  # Opcional: añadir un motivo
                    # 'usuario_id': self.env.user.id # Ya es el valor por defecto si no se especifica
                }
            )
            _logger.info(
                f"Estado inicial 'Alta Inicial' creado para socio {nuevosocio.id}"
            )
        except Exception as e:
            _logger.error(
                f"Error al crear estado inicial para socio {nuevosocio.id}: {e}"
            )
            # Considerar si se debe revertir la creación del socio o solo registrar el error

        # Sincronizar socio_id en el partner si el partner fue creado aquí
        if nuevosocio.partner_id and not vals.get(
            "partner_id"
        ):  # Solo si se creó un nuevo partner
            nuevosocio.partner_id.sudo().write({"socio_id": nuevosocio.id})

        # Sincronizar los datos básicos seleccionados al partner después de la creación
        nuevosocio._sync_partner_fields()
        _logger.info(f"Socio creado: {nuevosocio.id}")
        nuevosocio.subscription_upsert()
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
        """Sobrescribe el método write para verificar estado de socio y"""

        for rec in self:
            # Almacenar valores antiguos antes de la escritura
            old_partner = rec.partner_id
            old_suscripcion_plan_id = rec.suscripcion_plan_id
            old_suscripcion_categoria_id = rec.suscripcion_categoria_id
            old_cliente_facturacion = rec.cliente_facturacion
            old_paga_debito_automatico = rec.paga_debito_automatico
            old_payment_adhesion_id = rec.payment_adhesion_id

            res = super(ClubMember, rec).write(vals)
            new_partner = rec.partner_id
            # Si cambió el partner, limpiar el anterior
            if vals.get("partner_id") and old_partner and old_partner != new_partner:
                old_partner.sudo().write({"socio_id": False})
            # Asegurar que el nuevo partner apunte al socio
            # Solo si el partner_id fue cambiado en este write o si antes no tenia partner_id
            if (
                new_partner
                and (vals.get("partner_id") or not old_partner)
                and new_partner.socio_id != rec
            ):
                new_partner.sudo().write({"socio_id": rec.id})

            # Sincronizar datos básicos seleccionados al partner después de la escritura principal
            rec._sync_partner_fields(vals)

            # Chequear si suscripcion_plan_id cambió y sincronizar suscripción
            if (
                "suscripcion_plan_id" in vals
                and old_suscripcion_plan_id != rec.suscripcion_plan_id
                or "suscripcion_categoria_id" in vals
                and old_suscripcion_categoria_id != rec.suscripcion_categoria_id
                or "cliente_facturacion" in vals
                and old_cliente_facturacion != rec.cliente_facturacion
                or "paga_debito_automatico" in vals
                and old_paga_debito_automatico != rec.paga_debito_automatico
                or "payment_adhesion_id" in vals
                and old_payment_adhesion_id != rec.payment_adhesion_id
            ):
                _logger.info(
                    f"suscripcion_plan_id cambió para socio {rec.id}. "
                    "Sincronizando suscripción."
                )
                rec.subscription_upsert()

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

    def _handle_error(self, error):
        return (
            _(
                "Ocurrió un error al procesar el socio pendiente. "
                "Por favor, intente nuevamente o contacte al "
                "administrador.\n\n"
                "Error técnico: %s"
            )
            % error
        )

    # MÉTODO PARA CREAR O ACTUALIZAR SUSCRIPCIÓN Y SU LÍNEA PRINCIPAL
    def subscription_upsert(self):
        """Crea o actualiza la suscripción principal del socio y su línea."""
        self.ensure_one()  # Asegura que se ejecuta en un solo registro

        # 1. Buscar o crear la suscripción principal
        suscripcion = self.suscripcion_id

        suscripcion_header_vals = {
            "cliente_id": self.partner_id.id,
            "cliente_facturacion": self.cliente_facturacion.id,
            "suscripcion_plan_id": self.suscripcion_plan_id.id,
            "categoria_id": self.suscripcion_categoria_id.id,
            "paga_debito_automatico": self.paga_debito_automatico,
            "payment_adhesion_id": (
                self.payment_adhesion_id.id if self.payment_adhesion_id else False
            ),
            # Otros campos de encabezado si son necesarios, por ejemplo:
            # 'categoria_id': self.categoria_suscripcion.id,
            # 'suscripcion_plan_id': ... (si mapeas categoria_suscripcion a plan)
        }

        if not suscripcion:
            # Si no existe, crear una nueva suscripción
            try:
                suscripcion_header_vals["name"] = (
                    f"Suscripción Socio {self.member_number or self.name}"
                )
                # Asignar fecha de inicio si no existe
                if not suscripcion_header_vals.get("fecha_inicio"):
                    suscripcion_header_vals["fecha_inicio"] = fields.Date.today()

                suscripcion = self.env["softer.suscripcion"].create(
                    suscripcion_header_vals
                )
                self.suscripcion_id = suscripcion.id
                _logger.info(
                    f"Suscripción {suscripcion.id} creada y "
                    f"vinculada al socio {self.id}"
                )
            except Exception as e:
                _logger.error(f"Error al crear suscripción para socio {self.id}: {e}")
                # Manejar el error si la creación falla
                return

        # Si ya existía o se acaba de crear, actualizar encabezado
        if suscripcion:
            try:
                suscripcion.write(suscripcion_header_vals)
                _logger.info(
                    f"Encabezado de suscripción {suscripcion.id} "
                    f"actualizado para socio {self.id}"
                )
            except Exception as e:
                _logger.error(
                    f"Error al actualizar encabezado de suscripción "
                    f"{suscripcion.id} para socio {self.id}: {e}"
                )
                # Manejar el error si la actualización del encabezado falla

        # 2. Buscar o crear la línea principal de la suscripción
        # Asumo que hay una única línea principal para el producto del socio.
        # Podrías necesitar ajustar la lógica si un socio puede tener múltiples líneas
        # asociadas a los campos del modelo socio.
        # linea_suscripcion = suscripcion.line_ids.filtered(
        #     lambda l: l.product_id.id == self.suscripcion_product_id.id
        # )

        # Si hay múltiples líneas con el mismo producto, tomamos la primera o podrías borrarlas y crear una nueva
        # if len(linea_suscripcion) > 1:
        #     _logger.warning(
        #         f"Múltiples líneas con el mismo producto "
        #         f"{self.suscripcion_product_id.id} encontradas para "
        #         f"suscripción {suscripcion.id}. Tomando la primera.")
        #     linea_suscripcion = linea_suscripcion[0]
        # elif len(linea_suscripcion) == 1:
        #     linea_suscripcion = linea_suscripcion[0]
        # else:
        #     linea_suscripcion = False # No se encontró línea existente para este producto

        # Usar los datos del plan de suscripción para la línea
        plan = self.suscripcion_plan_id

        if not plan:
            _logger.warning(
                f"Socio {self.id} no tiene un plan de suscripción "
                "asignado. No se creará/actualizará línea de suscripción."
            )
            # Si no hay plan, y hay una suscripción, quizás deberíamos limpiar las líneas existentes?
            # Por ahora, simplemente salimos.
            return  # No se puede crear línea sin un plan

        # Eliminar líneas existentes si el plan cambió o es la primera vez que se aplica un plan
        # Podríamos ser más inteligentes y solo actualizar si el item del plan existe en las líneas
        # Pero para simplificar, borramos y creamos.
        if suscripcion.line_ids:
            _logger.info(
                f"Eliminando {len(suscripcion.line_ids)} líneas "
                f"existentes para suscripción {suscripcion.id} "
                f"antes de aplicar plan {plan.id}."
            )
            suscripcion.line_ids.unlink()

        # Llamar al método action_aplicar_plan de la suscripción para crear las líneas
        try:
            _logger.info(
                f"Llamando action_aplicar_plan para suscripción "
                f"{suscripcion.id} con plan {plan.id}"
            )
            suscripcion.action_aplicar_plan()
        except Exception as e:
            _logger.error(
                f"Error al llamar action_aplicar_plan para "
                f"suscripción {suscripcion.id}: {e}"
            )
            # Manejar error si la aplicación del plan falla

        # Después de crear/actualizar las líneas, marcar la suscripción como pendiente de aplicar plan a False si aplica
        # self.pendiente_cambio_plan = False # Esto podría hacerse si la lógica es que subscription_upsert 'aplica' el plan

    def _actualizar_estados_por_defecto(self):
        """Actualiza los registros existentes con estados incorrectos"""
        registros_a_actualizar = self.search([("estado", "!=", "activa")])
        for rec in registros_a_actualizar:
            rec.estado = "activa"
            rec.esActivo = True
        _logger.info(
            f"Se actualizaron {len(registros_a_actualizar)} registros "
            f"a estado 'activa'"
        )

    @api.model
    def init(self):
        self._actualizar_estados_por_defecto()
