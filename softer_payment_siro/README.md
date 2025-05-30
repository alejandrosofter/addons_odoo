# Proveedor de Pagos SIRO para Odoo

Este módulo implementa la integración con el sistema de pagos SIRO para Odoo 17.0.

## Características

- Integración completa con la API de SIRO
- Soporte para pagos en Pesos Argentinos (ARS)
- Notificaciones de estado de pago en tiempo real
- Interfaz de usuario intuitiva para la configuración
- Manejo de errores y estados de transacción

## Instalación

1. Copie este módulo a su carpeta de addons de Odoo
2. Actualice la lista de módulos en Odoo
3. Busque e instale el módulo "Payment Provider: Siro"

## Configuración

1. Vaya a Facturación > Configuración > Proveedores de Pago
2. Active el proveedor de pagos SIRO
3. Configure los siguientes campos:
   - Usuario SIRO
   - Contraseña SIRO
   - ID Convenio SIRO
   - CUIT Administrador SIRO

## Uso

Una vez configurado, SIRO aparecerá como opción de pago en:

- Portal de cliente
- Facturas en línea
- Órdenes de venta

## Soporte

Para soporte técnico, por favor contacte a:

- Email: soporte@softer.com.ar
- Teléfono: +54 11 XXXX-XXXX

## Licencia

Este módulo está licenciado bajo LGPL-3.
Vea el archivo LICENSE para más detalles.

# Siro

## Technical details

https://onlinesiro.com.ar/wp-content/uploads/_pda/2025/05/SIRO-Developers-API-SIRO-Version-1.3-04.25.pdf
APIs:

Homologación https://apisesionh.bancoroela.com.ar/auth/Sesion
Producción https://apisesion.bancoroela.com.ar/auth/Sesion
