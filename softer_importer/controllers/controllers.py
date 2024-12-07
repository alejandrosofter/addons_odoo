# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.modules.module import get_module_resource
import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime


class Importaciones(http.Controller):
    def __init__(self):
        print("inicializando importer!")
        # Crear instancia de ImportacionConsultorios para manejar la lógica de importación
        # self.import_consultorios = ImportacionConsultorios()
        # self.import_ohm = ImportarOhm()

    def chageToDraftAllInvoices(self):
        invoices = request.env["account.move"].sudo().search([])
        for invoice in invoices:
            invoice.sudo().write({"state": "draft"})

    def index(self, **kw):
        token = kw.get("token")
        coleccion = kw.get("coleccion")
        data = self.getData(None, limit=1)
        ret = ""
        for doc in data:
            print(doc.to_dict())
            ret = doc.to_dict()
            fecha = self.getFecha(ret.get("fecha"))
        return fecha

    @http.route("/ejecutar", auth="public", methods=["GET"], csrf=False)
    def test(self, **kw):
        return self.chageToDraftAllInvoices()

    def importar(self, coleccion):
        # Llamar los métodos de importación desde la instancia de ImportacionConsultorios
        if coleccion == "pacientes":
            # self.import_consultorios.importPacientes()
            return "Importación de pacientes exitosa"

        if coleccion == "compras":
            db = self.connect_to_firebase()
            collection_ref = db.collection("compras")
            data = collection_ref.order_by("fecha_timestamp").get()

            print(f"Cantidad de registros {len(data)}")
            return "Importación de compras exitosa"
