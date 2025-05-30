# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _

# API URLs
API_AUTH_PRODUCCION = (
    "https://apisesion.bancoroela.com.ar/"  # Ajustar según documentación de SIRO
)
API_AUTH_HOMOLOGACION = "https://apisesionh.bancoroela.com.ar/"

API_SIRO_PRODUCCION = "https://apisiro.bancoroela.com.ar/"
API_SIRO_HOMOLOGACION = "https://apisiroh.bancoroela.com.ar/"

API_PAGOS_PRODUCCION = "https://siropagos.bancoroela.com.ar/"
API_PAGOS_HOMOLOGACION = "https://siropagosh.bancoroela.com.ar/"

# Monedas soportadas
SUPPORTED_CURRENCIES = [
    "ARS",  # Peso Argentino
]

# Decimales por moneda
CURRENCY_DECIMALS = {
    "ARS": 2,  # Peso Argentino - 2 decimales
}

# Métodos de pago por defecto
DEFAULT_PAYMENT_METHOD_CODES = [
    "siro",
]

# Mapeo de estados de transacción
TRANSACTION_STATUS_MAPPING = {
    "pending": ["PENDIENTE", "EN_PROCESO"],
    "done": ["PAGADO", "ACREDITADO"],
    "canceled": ["CANCELADO", "RECHAZADO"],
    "error": ["ERROR", "FALLO"],
}

# Mapeo de mensajes de error
ERROR_MESSAGE_MAPPING = {
    "error_autenticacion": _(
        "Error de autenticación. Por favor verifique sus credenciales."
    ),
    "error_conexion": _(
        "Error de conexión con el servicio de pagos. Por favor intente más tarde."
    ),
    "error_datos": _(
        "Error en los datos enviados. Por favor verifique la información."
    ),
    "error_fondos": _("Fondos insuficientes para realizar el pago."),
    "error_general": _("Error general. Por favor contacte al soporte técnico."),
}

CONCEPTOS_COMPROBANTE = [
    ("0", "Mensualidad"),
    ("1", "Intereses"),
    ("2", "Morosidad"),
    ("3", "Otros pagos"),
    ("4", "Pago parcial"),
    ("5", "Refinanciación"),
    ("6", "Bonificación"),
    ("7", "Ajuste"),
    ("8", "Recargo"),
    ("9", "Otro concepto"),
]
