from odoo import models, fields, api, _
import requests
import base64

from collections import defaultdict


class AnclajesSettings(models.TransientModel):
    _inherit = "res.config.settings"
    idUserDefaultImport = fields.Many2one("res.users", string="Usuario por Defecto")
    import_status = fields.Char(string="Estado de la Importación", readonly=True)
    desdeRegistro = fields.Integer(string="Desde Registro")
    hastaRegistro = fields.Integer(string="Hasta Registro")

    def set_values(self):
        super(AnclajesSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "anclajes.idUserDefaultImport",
            self.idUserDefaultImport.id if self.idUserDefaultImport else False,
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "anclajes.desdeRegistro", self.desdeRegistro
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "anclajes.hastaRegistro", self.hastaRegistro
        )

    @api.model
    def get_values(self):
        res = super(AnclajesSettings, self).get_values()
        ir_config = self.env["ir.config_parameter"].sudo()
        user_id = ir_config.get_param("anclajes.idUserDefaultImport", default=False)
        desdeRegistro = ir_config.get_param("anclajes.desdeRegistro", default=0)
        hastaRegistro = ir_config.get_param("anclajes.hastaRegistro", default=0)
        # Verifica si user_id es un número válido antes de convertir
        try:
            user_id = int(user_id) if user_id else False
        except ValueError:
            user_id = False  # Si no es un número, establece False

        res.update(
            {
                "idUserDefaultImport": user_id,
                "desdeRegistro": desdeRegistro,
                "hastaRegistro": hastaRegistro,
            }
        )
        return res

    @api.model
    def import_anclajes(self, args=None):
        self.syncAnclajes()

    @api.model
    def import_users(self, args=None):
        self.syncUsers()

    @api.model
    def import_equipos(self, args=None):
        self.syncEquipos()

    def syncUsers(self):
        try:
            # Realiza la solicitud a la API
            response = requests.get("http://apianclajes.yavu.com.ar/users")
            response.raise_for_status()
            data = response.json()

            # Procesa los datos y cuenta las zonas
            for record in data:
                newUser = {
                    "name": record.get("username"),
                    "ref": record.get("_id"),
                    "login": record.get("username"),
                }
                self.env["res.users"].sudo().create(newUser)

        except requests.exceptions.RequestException as e:
            raise models.ValidationError(_("Error al conectar con la API: %s") % str(e))
        except Exception as e:
            raise models.ValidationError(_("Error al importar registros: %s") % str(e))

    def getCertificadoApi(self, certificado):
        try:
            response = requests.get(
                f"https://anclajes.ibero-sa.net/descargaCertificado/{certificado}"
            )
            response.raise_for_status()

            # Convertir directamente a base64 para el campo binary
            return base64.b64encode(response.content)

        except requests.exceptions.RequestException as e:
            raise models.ValidationError(_("Error al conectar con la API: %s") % str(e))
        except Exception as e:
            raise models.ValidationError(
                _("Error al importar certificado: %s") % str(e)
            )

    def syncAnclajes(self):
        try:
            # Realiza la solicitud a la API
            response = requests.get("http://apianclajes.yavu.com.ar/anclajes")
            response.raise_for_status()
            data = response.json()
            ir_config = self.env["ir.config_parameter"].sudo()
            desdeRegistro = int(
                ir_config.get_param("anclajes.desdeRegistro", default=0)
            )
            hastaRegistro = int(
                ir_config.get_param("anclajes.hastaRegistro", default=0)
            )
            i = 0
            print(
                f"Cantidad total de registros {len(data)} importando desde {desdeRegistro} hasta {hastaRegistro}"
            )
            for record in data:
                if i < desdeRegistro:
                    i = i + 1
                    continue
                if i > hastaRegistro:
                    break
                print(f"Importando registro {i}")
                i = i + 1
                # Verifica si ya existe un registro con la misma referencia (_id)
                existing_anclaje = self.env["anclajes.anclajes"].search(
                    [("ref", "=", record.get("_id"))], limit=1
                )
                user = self.idUserDefaultImport
                equipoEnsayo = self.env["anclajes.equipos"].search(
                    [("ref", "=", record.get("equipoEnsayo"))], limit=1
                )

                certificado = self.getCertificadoApi(record.get("certificado"))
                # Valores a cargar o actualizar en el modelo Odoo
                vals = {
                    "name": record.get("pozo"),  # Pozo
                    "ref": record.get("_id"),  # Referencia desde _id
                    "bateria": record.get("bateria"),  # Batería
                    "nroCertificado": record.get(
                        "certificacion"
                    ),  # Número de Certificado
                    "equipoEnsayo": equipoEnsayo.id,
                    "equipoIngresante": record.get(
                        "equipoIngresante"
                    ),  # Equipo Ingresante
                    "fechaEnsayo": (
                        record.get("fechaEnsayo")[:10]
                        if record.get("fechaEnsayo")
                        else False
                    ),  # Fecha Ensayo
                    "fechaConstruccion": (
                        record.get("fechaConstruccion")[:10]
                        if record.get("fechaConstruccion")
                        else False
                    ),  # Fecha Construcción
                    "anclaje_no": record.get("estadoNO", ""),  # Anclaje NO
                    "anclaje_ne": record.get("estadoNE", ""),  # Anclaje NE
                    "anclaje_so": record.get("estadoSO", ""),  # Anclaje SO
                    "anclaje_se": record.get("estadoSE", ""),  # Anclaje SE
                    "user_id": user,
                    "certificado": certificado,
                }

                if existing_anclaje:
                    # Actualiza el registro si ya existe
                    existing_anclaje.write(vals)
                else:
                    # Crea un nuevo registro si no existe
                    self.env["anclajes.anclajes"].create(vals)

            # Actualiza el estado
            self.import_status = _("Registros importados correctamente.")

        except requests.exceptions.RequestException as e:
            raise models.ValidationError(_("Error al conectar con la API: %s") % str(e))
        except Exception as e:
            raise models.ValidationError(_("Error al importar registros: %s") % str(e))

    def getNombrePozo(self, pozo):
        if not pozo or "-" not in pozo:
            return "DEFAULT"  # Salta registros sin pozo válido
        # en mayusculas
        return pozo.split("-")[0].upper()

    def syncZonas(self):
        try:
            # Realiza la solicitud a la API
            response = requests.get("http://apianclajes.yavu.com.ar/anclajes")
            response.raise_for_status()
            data = response.json()
            zonas = set()  # Usamos un set para evitar duplicados
            for record in data:
                zonas.add(self.getNombrePozo(record.get("pozo", "")))  # Extrae "PPP"

            # Convierte el set en una lista
            zonas_list = list(zonas)
            print(zonas_list)

            for record in zonas_list:
                self.env["anclajes.zonas"].create(
                    {
                        "name": record,
                    }
                )

        # # Actualiza el estado
        # self.import_status = _("Registros importados correctamente.")

        except requests.exceptions.RequestException as e:
            raise models.ValidationError(_("Error al conectar con la API: %s") % str(e))
        except Exception as e:
            raise models.ValidationError(_("Error al importar registros: %s") % str(e))

    def syncEquipos(self):
        try:
            # Realiza la solicitud a la API
            response = requests.get("http://apianclajes.yavu.com.ar/equipos")
            response.raise_for_status()
            data = response.json()

            # Procesa los datos y crea registros
            for record in data:
                self.env["anclajes.equipos"].create(
                    {
                        "name": record.get("nombreEquipo"),
                        "ref": record.get("_id"),
                    }
                )

            # Actualiza el estado
            self.import_status = _("Registros importados correctamente.")

        except requests.exceptions.RequestException as e:
            raise models.ValidationError(_("Error al conectar con la API: %s") % str(e))
        except Exception as e:
            raise models.ValidationError(_("Error al importar registros: %s") % str(e))
