# -*- coding: utf-8 -*-
from . import res_partner_inherit
from . import socios_categoria
from . import socio
from . import socio_estados
from . import res_config_settings
from . import socios_pendientes_actividad
from . import suscripcion_inherit  # Este debe ser el último ya que depende de socio
from . import socios_pendientes_actividad_wizard
from . import socio_payment_inherit

# Estas importaciones son necesarias para que Odoo cargue los modelos
# No se pueden eliminar aunque el linter las marque como no utilizadas
