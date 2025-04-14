from odoo import models
from odoo.http import request


class Website(models.Model):
    _inherit = "website"

    def _is_canonical_url(self, canonical_url=None, canonical_params=None):
        try:
            environ = request.httprequest.environ
            # Intentar obtener la URL de diferentes fuentes
            request_uri = environ.get("REQUEST_URI")
            if not request_uri:
                # Intentar con PATH_INFO
                request_uri = environ.get("PATH_INFO", "")
                # Agregar query string si existe
                query_string = environ.get("QUERY_STRING")
                if query_string:
                    request_uri += "?" + query_string

            # Si aún no tenemos una URI válida, usar full_path o path
            if not request_uri:
                request_uri = (
                    request.httprequest.full_path
                    if hasattr(request.httprequest, "full_path")
                    else request.httprequest.path
                )

            # Construir la URL actual
            url_root = request.httprequest.url_root.rstrip("/")
            current_url = f"{url_root}{request_uri}"

        except Exception:
            # Si todo falla, usar la URL base
            current_url = request.httprequest.url

        return current_url == self._canonical_url(canonical_url, canonical_params)
