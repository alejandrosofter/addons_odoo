# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import models
from . import controllers

from odoo.addons.payment import setup_provider, reset_payment_provider


def post_init_hook(env):
    """Set up payment provider."""
    setup_provider(env, "siro")


def uninstall_hook(env):
    """Remove payment provider."""
    reset_payment_provider(env, "siro")
