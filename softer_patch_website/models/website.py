from odoo import models, api
from odoo.http import request


class Website(models.Model):
    _inherit = "website"

    def _get_current_website_id(self, domain_name=None, fallback=True):
        """Sobrescribe el método para evitar errores con REQUEST_URI"""
        try:
            return super()._get_current_website_id(domain_name, fallback)
        except Exception:
            if fallback:
                return self.env["website"].search([], limit=1).id
            return False

    def _get_request_url(self):
        """Método auxiliar para obtener la URL actual de forma segura"""
        try:
            if hasattr(request, "httprequest") and request.httprequest:
                # Intentamos obtener la URL completa
                if hasattr(request.httprequest, "url"):
                    return request.httprequest.url

                # Si no está disponible, construimos la URL desde sus partes
                path = request.httprequest.path
                query_string = (
                    request.httprequest.query_string.decode()
                    if request.httprequest.query_string
                    else ""
                )
                return f"{path}{'?' + query_string if query_string else ''}"
        except Exception:
            pass
        return "/"

    def _is_canonical_url(self, url):
        """Sobrescribe el método para manejar URLs de forma segura"""
        try:
            return super()._is_canonical_url(url)
        except Exception:
            return True

    def _get_alternate_languages(self, canonical_params):
        """Sobrescribe el método para manejar idiomas alternativos de forma segura"""
        try:
            return super()._get_alternate_languages(canonical_params)
        except Exception:
            return []
