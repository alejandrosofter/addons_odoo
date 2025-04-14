from odoo import models
from odoo.http import request
from werkzeug.urls import url_parse, url_encode


class Website(models.Model):
    _inherit = "website"

    def _get_request_url(self):
        """Método auxiliar para obtener la URL actual de manera segura"""
        try:
            environ = request.httprequest.environ
            # Intentar obtener la URL de diferentes fuentes
            request_uri = environ.get("REQUEST_URI")
            if not request_uri:
                # Intentar con PATH_INFO y QUERY_STRING
                request_uri = environ.get("PATH_INFO", "")
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

            return request_uri
        except Exception:
            return request.httprequest.path

    def _is_canonical_url(self, canonical_url=None, canonical_params=None):
        try:
            request_uri = self._get_request_url()
            # Construir la URL actual
            url_root = request.httprequest.url_root.rstrip("/")
            current_url = f"{url_root}{request_uri}"
        except Exception:
            # Si todo falla, usar la URL base
            current_url = request.httprequest.url

        return current_url == self._canonical_url(canonical_url, canonical_params)

    def _get_alternate_languages(self, canonical_params=None):
        """Sobrescribe el método para manejar mejor la obtención de URLs"""
        if not self.env["res.language"].search_count([("active", "=", True)]) > 1:
            return []

        try:
            request_path = self._get_request_url()
            if not request_path:
                return []

            if not self._is_canonical_url(canonical_params=canonical_params):
                return []

            languages = self.env["res.language"].get_sorted()
            current_lang = request.lang
            result = []

            for lg in languages:
                if lg.code == current_lang.code:
                    continue
                url_params = dict(request.httprequest.args)
                url_params["edit_translations"] = None
                url_params["enable_editor"] = None

                for key, val in canonical_params.items() if canonical_params else []:
                    url_params[key] = val

                url = f"{request.httprequest.url_root.rstrip('/')}{request_path}"
                parsed = url_parse(url)
                path = parsed.path
                fragment = parsed.fragment

                if lg.url_code:
                    path = f"/{lg.url_code}{path}"

                result.append(
                    {
                        "hreflang": lg.iso_code,
                        "short_name": lg.code.split("_")[0],
                        "href": f"{parsed.scheme}://{parsed.netloc}{path}"
                        f"{'?' + url_encode(url_params) if url_params else ''}"
                        f"{'#' + fragment if fragment else ''}",
                    }
                )

            return result
        except Exception:
            return []
