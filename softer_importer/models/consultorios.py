# -*- coding: utf-8 -*-
import firebase_admin
from firebase_admin import credentials, firestore
from odoo.modules.module import get_module_resource
from odoo.http import request
import hashlib


class ImportacionConsultorios:
    def __init__(self):
        # Inicializar Firebase solo si no está ya inicializado
        if not firebase_admin._apps:
            cred_path = get_module_resource(
                "softer_importer", "static/configs", "firebaseConfig.json"
            )
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def importObrasSociales(self):
        # Retrieve data from Firebase
        users_ref = self.db.collection("obrasSociales")
        docs = users_ref.stream()

        for doc in docs:
            self.upgradeObrasocial(doc.to_dict(), doc.id)

    def convertIdInt(self, id):
        return int(id, 36)

    def upgradeObrasocial(self, data, id):
        aux = {
            "name": data.get("nombre"),
            "ref": id,
        }
        request.env["consultorio.obrasociales"].sudo().create(aux)

    def upgradeOsPaciente(self, idOdoo, data, id):
        aux = {
            "paciente": idOdoo,
            "obraSocial": self.convertIdInt(id),
        }
        request.env["consultorio.pacientes.obrasSociales"].sudo().create(aux)

    def importOsPaciente(self, idOdoo, idFirebase):
        users_ref = self.db.collection(f"pacientes/{idFirebase}/obrasSociales")
        docs = users_ref.stream()

        for doc in docs:
            self.upgradeOsPaciente(idOdoo, doc.to_dict(), doc.id)

    def upgradePaciente(self, paciente, id):
        aux = {
            "ref": id,
            "name": paciente.get("nombre"),
            "apellido": paciente.get("apellido"),
            "email": paciente.get("email"),
            "dni": paciente.get("dni"),
            "fechaNacimiento": paciente.get("fechaNacimiento"),
            "nroTelefono": paciente.get("telefono"),
            "esParticular": paciente.get("esParticular"),
        }
        res = request.env["consultorio.pacientes"].sudo().create(aux)
        self.importOsPaciente(res.id, id)

    def importPacientes(self):
        users_ref = self.db.collection("pacientes")
        docs = users_ref.stream()

        for doc in docs:
            self.upgradePaciente(doc.to_dict(), doc.id)
