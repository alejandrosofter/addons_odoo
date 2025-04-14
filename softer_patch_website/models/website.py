from odoo import models
from odoo.http import request


class Website(models.Model):
    _inherit = "website"

    def _is_canonical_url(self, canonical_url=None, canonical_params=None):
        try:
            environ = request.httprequest.environ
            request_uri = environ.get("REQUEST_URI")
            if not request_uri:
                request_uri = (
                    request.httprequest.full_path
                    if hasattr(request.httprequest, "full_path")
                    else request.httprequest.path
                )
            current_url = request.httprequest.url_root[:-1] + request_uri
        except Exception:
            current_url = request.httprequest.url
        return current_url == self._canonical_url(canonical_url, canonical_params)
