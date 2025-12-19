# Patch POS Facturación Electrónica

## Descripción

Este módulo soluciona el problema donde las facturas creadas desde el punto de venta (POS) se generan correctamente pero no se validan automáticamente en AFIP, quedando en estado "borrador" hasta que se validan manualmente desde el módulo de facturación.

## Problema que resuelve

Cuando se crea una factura desde el punto de venta con un diario configurado para facturación electrónica AFIP:

- La factura se crea correctamente con todos los datos
- Sin embargo, no se imputa automáticamente en AFIP
- El usuario debe ir al módulo de facturación, pasar la factura a borrador y luego validarla manualmente
- Al validar manualmente, funciona correctamente

## Solución

Este módulo intercepta la creación de facturas desde el POS y automáticamente valida la factura con AFIP si:

- El diario tiene configuración AFIP (`l10n_ar_afip_pos_system` en `["RLI_RLM", "FEERCEL"]`)
- El diario tiene un webservice AFIP configurado (`afip_ws`)
- La factura está en estado "draft" (borrador)

## Funcionamiento

Cuando se crea una factura desde el POS:

1. Se llama al método original `_generate_pos_order_invoice()` que crea la factura
2. Se verifica si el diario tiene configuración AFIP
3. Si tiene configuración AFIP, se llama automáticamente a `action_post()`
4. `action_post()` internamente llama a `do_pyafipws_request_cae()` que valida la factura en AFIP
5. La factura queda validada y con CAE asignado

## Instalación

1. Reiniciar el servidor de Odoo
2. Actualizar la lista de módulos
3. Instalar el módulo "Patch POS Facturación Electrónica"

## Dependencias

- `point_of_sale`: Módulo de punto de venta
- `l10n_ar_afipws_fe`: Módulo de facturación electrónica AFIP para Argentina

## Logs

El módulo registra en los logs:

- **INFO**: Cuando una factura se valida exitosamente en AFIP desde el POS
- **ERROR**: Cuando hay un error al validar la factura (la factura quedará en borrador para validación manual)

Los logs incluyen:

- Nombre/número de la factura
- ID de la factura
- CAE obtenido (si fue exitoso)
- Mensaje de error (si hubo problema)

## Notas

- Si hay un error al validar con AFIP, la factura quedará en borrador y podrá validarse manualmente
- El error se registra en los logs pero no interrumpe el flujo del POS
- Solo se valida automáticamente si el diario tiene configuración AFIP completa

## Autor

Softer - https://softer.com.ar


