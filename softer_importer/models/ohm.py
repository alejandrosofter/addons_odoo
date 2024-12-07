# -*- coding: utf-8 -*-
import firebase_admin
from firebase_admin import credentials, firestore
from odoo.modules.module import get_module_resource
from odoo.http import request
import hashlib
from datetime import datetime
import json
import csv


class ImportarOhm:
    FILEPRODUCTS = "productos.csv"

    def __init__(self):
        # Inicializar Firebase solo si no está ya inicializado
        if not firebase_admin._apps:
            cred_path = get_module_resource(
                "softer_importer", "static/configs", "firebaseConfig.json"
            )
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def importCentrosCosto(self):
        # Retrieve data from Firebase
        users_ref = self.db.collection("centroCostos")
        docs = users_ref.stream()

        for doc in docs:
            self.upgradeCentroCosto(doc.to_dict(), doc.id)

    def saveToCvs(self, items, dataCols, filename, mode="w"):
        cred_path = get_module_resource(
            "softer_consultorio", "static/configs", filename
        )

        with open(cred_path, mode=mode, newline="", encoding="utf-8") as archivo_csv:
            escritor_csv = csv.writer(archivo_csv)

            # Escribe la cabecera en el CSV usando los nombres de las columnas
            # if mode == "w":
            # headers = [col["header"] for col in dataCols]
            # escritor_csv.writerow(headers)
            # partner_id,journal_id,move_name,product_id,quantity,analytic_distribution,price_unit,move_id
            for item in items:
                row = []

                for col in dataCols:
                    # Usa el método getattr para obtener el valor del atributo
                    value = item.get(col["dataField"], "")
                    row.append(value)

                # Escribe la fila en el archivo CSV
                escritor_csv.writerow(row)

    def importCompra(self, data, id):
        print(f"Importando data {id}")

    def importAllProducts(self):
        users_ref = self.db.collection("compras")
        docs = users_ref.stream()
        i = 0
        journal = (
            request.env["account.journal"].sudo().search([("type", "=", "purchase")])
        )
        currency = request.env["res.currency"].sudo().search([("name", "=", "ARS")])
        items = []
        self.cleanFile(self.FILEPRODUCTS)

        for doc in docs:
            i = i + 1
            print(f"Imporando producto {i}")
            # res = self.upgradeCompras(doc.to_dict(), doc.id)
            arrAux = self.updateProduct(doc.to_dict(), doc.id, journal, currency)
            items = items + arrAux
        dataCols = [
            {"header": "Nombre", "dataField": "name"},
            {"header": "Referencia", "dataField": "default_code"},
            {"header": "Precio", "dataField": "list_price"},
            {
                "header": "Diario",
                "dataField": "journal_name",
            },  # Esto puede ser constante
            {
                "header": "Moneda",
                "dataField": "currency_name",
            },  # Esto también puede ser constante
        ]

        self.saveToCvs(items, dataCols, self.FILEPRODUCTS)

    def parseProduct(self, data, id, journal, currency):

        items = []
        factura = request.env["account.move"].sudo().search([("ref", "=", id)])
        if data.get("items"):
            for item in data.get("items"):
                importe = (
                    0
                    if not item.get("importe", "") or item.get("importe") == ""
                    else float(item.get("importe"))
                )
                id = self.getIdItemCompra(item, id)
                nombre = (
                    (
                        "sin nombre"
                        if not item.get("detalle") or item.get("detalle") == ""
                        else item.get("detalle")
                    )
                    .strip()
                    .upper()
                )
                items.append(
                    {
                        "name": nombre,
                        "default_code": self.getIdItemCompra(None, id),
                        "type": "consu",
                        "sale_line_warn": "no-message",
                        "purchase_line_warn": "no-message",
                        "service_type": "manual",
                        "list_price": importe,
                        "detailed_type": "consu",
                        "factura": factura.id,
                    }
                )
        else:
            importe = (
                0
                if not data.get("importeTotal", "") or data.get("importeTotal") == ""
                else float(data.get("importeTotal"))
            )
            nombre = (
                (
                    "sin nombre"
                    if not data.get("detalle") or data.get("detalle") == ""
                    else data.get("detalle")
                )
                .strip()
                .upper()
            )
            items.append(
                {
                    "name": nombre,
                    "default_code": id,
                    "type": "consu",
                    "sale_line_warn": "no-message",
                    "purchase_line_warn": "no-message",
                    "service_type": "manual",
                    "list_price": importe,
                    "detailed_type": "consu",
                    "factura": factura.id,
                }
            )
        return items

    def importItemsFactura(self):
        users_ref = self.db.collection("compras")
        docs = users_ref.stream()
        i = 0
        journal = (
            request.env["account.journal"].sudo().search([("type", "=", "purchase")])
        )
        currency = request.env["res.currency"].sudo().search([("name", "=", "ARS")])

        # self.cleanFile("facturasItems.csv")
        dataCols = [
            {"header": "partner_id", "dataField": "partner_id"},
            {"header": "journal_id", "dataField": "journal_id"},
            {"header": "move_name", "dataField": "move_name"},
            {"header": "product_id", "dataField": "product_id"},
            {"header": "quantity", "dataField": "quantity"},
            {"header": "analytic_distribution", "dataField": "analytic_distribution"},
            {"header": "price_unit", "dataField": "price_unit"},
            {"header": "move_id", "dataField": "invoice"},
        ]
        for doc in docs:
            i = i + 1
            print(f"Imporando item {i}")
            # if i <= 950:
            #     continue
            res = self.getItemsCompras(doc.to_dict(), doc.id, journal, currency)
            # "currency_id": currency.id,
            #         "partner_id": proveedor.id,
            #         "journal_id": journal.id,
            #         "parent_state": "posted",
            #         "move_name": item.get("id"),
            #         "name": item.get("detalle"),
            #         "display_type": "product",
            #         "date": invoice.get("date"),
            #         "invoice_date": invoice.get("date"),
            #         "product_id": producto.id,
            #         "quantity": item.get("cantidad"),
            #         "price_unit": float(item.get("importe")),
            #         "analytic_distribution": {
            #             f"{centroCosto.id}": float(item.get("importe"))
            self.saveToCvs(res, dataCols, "facturasItems.csv", "a")

        # self.addToFileJson(items, self.FILEPRODUCTS)

    def getDefProveedor(self):
        defProveedor = (
            request.env["res.partner"]
            .sudo()
            .search([("name", "=", "CONSUMIDOR FINAL")], limit=1)
        )
        if not defProveedor:
            defProveedor = (
                request.env["res.partner"].sudo().create({"name": "CONSUMIDOR FINAL"})
            )
        return defProveedor

    def importCompras(self):
        # Retrieve data from Firebase
        users_ref = self.db.collection("compras")
        docs = users_ref.stream()
        i = 0
        journal = (
            request.env["account.journal"].sudo().search([("type", "=", "purchase")])
        )
        currency = request.env["res.currency"].sudo().search([("name", "=", "ARS")])
        defProveedor = self.getDefProveedor()
        items = []
        for doc in docs:
            i = i + 1
            print(f"Imporando {i}")
            # "amount_untaxed": importeTotal,
            # "amount_total": importeTotal,
            # "amount_untaxed_signed": -importeTotal,
            # "amount_total_signed": -importeTotal,
            # "amount_total_in_currency_signed": -importeTotal,
            items.append(
                self.parseCompra(doc.to_dict(), doc.id, journal, currency, defProveedor)
            )
        dataCols = [
            {"header": "Nombre", "dataField": "name"},
            {"header": "Referencia", "dataField": "ref"},
            {"header": "Nro", "dataField": "name"},
            {"header": "Importe amount_untaxed", "dataField": "amount_untaxed"},
            {
                "header": "Importe amount_total_signed",
                "dataField": "amount_total_signed",
            },
            {
                "header": "Importe amount_untaxed_signeds",
                "dataField": "amount_untaxed_signed",
            },
            {
                "header": "Importe amount_total_signed",
                "dataField": "amount_total_signed",
            },
            {
                "header": "Importe amount_total_in_currency_signed",
                "dataField": "amount_total_in_currency_signed",
            },
            {
                "header": "Proveedor",
                "dataField": "partner_id",
            },  # Esto puede ser constante
            {
                "header": "Fecha",
                "dataField": "date",
            },  # Esto también puede ser constante
            {
                "header": "Divisa",
                "dataField": "divisa",
            },
            {
                "header": "Estado",
                "dataField": "estado",
            },
            {
                "header": "Tipo",
                "dataField": "tipo",
            },
            {
                "header": "Nro factura",
                "dataField": "nro",
            },
        ]

        self.saveToCvs(items, dataCols, "facturas.csv")

    def getIdItemCompra(self, item, id):
        if not item:
            return id
        return item.get("_id") if item.get("_id") else item.get("id")

    def updateProduct(self, data, id, journal, currency):

        items = []
        if data.get("items"):
            for item in data.get("items"):
                importe = (
                    0
                    if not item.get("importe", "") or item.get("importe") == ""
                    else float(item.get("importe"))
                )
                id = self.getIdItemCompra(item, id)
                nombre = (
                    (
                        "sin nombre"
                        if not item.get("detalle") or item.get("detalle") == ""
                        else item.get("detalle")
                    )
                    .strip()
                    .upper()
                )
                items.append(
                    {
                        "name": nombre,
                        "default_code": self.getIdItemCompra(None, id),
                        "type": "consu",
                        "sale_line_warn": "no-message",
                        "purchase_line_warn": "no-message",
                        "service_type": "manual",
                        "list_price": importe,
                        "detailed_type": "consu",
                    }
                )
        else:
            importe = (
                0
                if not data.get("importeTotal", "") or data.get("importeTotal") == ""
                else float(data.get("importeTotal"))
            )
            nombre = (
                (
                    "sin nombre"
                    if not data.get("detalle") or data.get("detalle") == ""
                    else data.get("detalle")
                )
                .strip()
                .upper()
            )
            items.append(
                {
                    "name": nombre,
                    "default_code": id,
                    "type": "consu",
                    "sale_line_warn": "no-message",
                    "purchase_line_warn": "no-message",
                    "service_type": "manual",
                    "list_price": importe,
                    "detailed_type": "consu",
                }
            )
        return items

    def importProveedores(self):
        # Retrieve data from Firebase
        users_ref = self.db.collection("proveedores")
        docs = users_ref.stream()

        for doc in docs:
            self.upgradeProveedores(doc.to_dict(), doc.id)

    def findByref(self, ref):
        res = request.env["res.partner"].sudo().search([("ref", "=", ref)])
        if res:
            return res
        return False

    def getNroFactura(self, nro, id):
        if not nro:
            return [f"FA-sinNro", id]
        arr = nro.split("-")
        if len(arr) > 1:
            return [f"FA-{arr[0]}", arr[1]]
        return [f"FA-{nro}", id]

    def cleanFile(self, filename):
        cred_path = get_module_resource(
            "softer_consultorio", "static/configs", filename
        )
        try:
            with open(cred_path, "w") as f:
                f.write("")
        except IOError as e:
            print(f"Error handling file: {e}")

    def addToFileJson(self, data, filename="import.json"):
        # Ensure `data` is JSON-serializable (typically a dict)
        cred_path = get_module_resource(
            "softer_consultorio", "static/configs", filename
        )

        print(f"Guardando en {cred_path}")
        try:
            with open(cred_path, "r+") as f:
                try:
                    # Load existing data; if empty, initialize as a list
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        raise ValueError("Expected file content to be a list")
                except json.JSONDecodeError:
                    existing_data = []  # Start fresh if the file is empty or invalid

                # Append new data and write back
                existing_data.append(data)
                f.seek(0)
                json.dump(existing_data, f, indent=4)
                f.truncate()  # Clean up remaining content if the new data is smaller
        except IOError as e:
            print(f"Error handling file: {e}")

    def parseCompra(self, data, id, journal, currency, defaultProveedor):
        proveedor = self.findByref(data.get("idEntidad"))
        journal = (
            request.env["account.journal"].sudo().search([("type", "=", "purchase")])
        )
        currency = request.env["res.currency"].sudo().search([("name", "=", "ARS")])
        # data.get("nombreCentroCosto") tiene la forma xxxxx-xxxxxxx

        fecha = data.get("fecha").strftime("%Y-%m-%d")
        nroFactura = self.getNroFactura(data.get("nro"), id)
        if not proveedor:
            proveedor = defaultProveedor
        importeTotal = (
            0
            if not data.get("importeTotal") or data.get("importeTotal") == ""
            else float(data.get("importeTotal"))
        )
        return {
            "partner_id": proveedor.id,
            "partner_name": proveedor.name,
            "nro": data.get("nro"),
            "sequence_prefix": nroFactura[0],
            "sequence_number": nroFactura[1],
            "currency_id": currency.id,
            "journal_id": journal.id,
            "state": "draft",
            "ref": id,
            "l10n_latam_document_type_id": 1,
            "l10n_ar_afip_responsibility_type_id": 1,
            # "l10n_ar_latam_document_number": data.get("nro"),
            "l10n_ar_currency_rate": 1,
            "to_check": False,
            "posted_before": True,
            "is_storno": False,
            "move_type": "in_invoice",
            "name": f"{nroFactura[0]}{nroFactura[1]}",
            "auto_post": "no",
            "payment_state": "paid",
            "invoice_partner_display_name": data.get("label_idEntidad"),
            "date": fecha,
            "invoice_date": fecha,
            "invoice_date_due": fecha,
            "amount_untaxed": importeTotal,
            "amount_total": importeTotal,
            "amount_untaxed_signed": -importeTotal,
            "amount_total_signed": -importeTotal,
            "amount_total_in_currency_signed": -importeTotal,
            "divisa": "ARS",
            "estado": "Pagada",
            "tipo": "Factura de proveedor",
        }

    def upgradeCompras(self, data, id):
        # 4 es CUIT
        # 5 es DNI

        proveedor = self.findByref(data.get("idEntidad"))
        journal = (
            request.env["account.journal"].sudo().search([("type", "=", "purchase")])
        )
        currency = request.env["res.currency"].sudo().search([("name", "=", "ARS")])
        # data.get("nombreCentroCosto") tiene la forma xxxxx-xxxxxxx

        fecha = data.get("fecha").strftime("%Y-%m-%d")
        nroFactura = self.getNroFactura(data.get("nro"), id)
        if not proveedor:

            return {
                "error": True,
                "message": f"no se encontro proveedor {data.get('idEntidad')}",
            }
        aux = {
            "partner_id": proveedor.id,
            "sequence_prefix": nroFactura[0],
            "sequence_number": nroFactura[1],
            "currency_id": currency.id,
            "journal_id": journal.id,
            "state": "draft",
            "ref": id,
            "l10n_latam_document_type_id": 1,
            "l10n_ar_afip_responsibility_type_id": 1,
            # "l10n_ar_latam_document_number": data.get("nro"),
            "l10n_ar_currency_rate": 1,
            "to_check": False,
            "posted_before": True,
            "is_storno": False,
            "move_type": "in_invoice",
            "name": f"{nroFactura[0]}{nroFactura[1]}",
            "auto_post": "no",
            "payment_state": "paid",
            "invoice_partner_display_name": data.get("label_idEntidad"),
            "date": fecha,
            "invoice_date": fecha,
            "invoice_date_due": fecha,
            # "amount_untaxed": importeTotal,
            # "amount_total": data.get("total"),
            # "amount_untaxed_signed": data.get("total"),
            # "amount_total_signed": data.get("total"),
            # "amount_total_in_currency_signed": data.get("total"),
        }

        # items = self.getItemsCompras(data, journal, currency, proveedor, aux)
        # importeTotal = 0
        # for item in items:
        #     importeTotal += float(item.get("price_unit", 0)) * float(
        #         item.get("quantity", 0)
        #     )
        importeTotal = float(data.get("importeTotal"))
        aux["amount_untaxed"] = importeTotal
        aux["amount_total"] = importeTotal

        aux["amount_untaxed_signed"] = -importeTotal
        aux["amount_total_signed"] = -importeTotal
        aux["amount_total_in_currency_signed"] = -importeTotal

        try:
            # factura = request.env["account.move"].sudo().search([("ref", "=", id)])
            # if not factura:
            factura = aux
            # factura = request.env["account.move"].sudo().create(aux)
            # self.cargarItemsFactura(items, factura)
            # request.env.cr.commit()
            # PUBLISH
            # factura["items"] = items
            self.addToFileJson(factura)
            # factura.sudo().action_post()
            return {"error": False, factura: factura}
            # pago = self.pagarFactura(factura)
            # factura["payment_id"] = pago.id

        except Exception as e:

            return {"error": True, "message": str(e)}

    def cargarItemsFactura(self, items, factura):
        for item in items:
            item["move_id"] = factura.id
            request.env["account.move.line"].sudo().create(item)

    def pagarFactura(self, factura):
        codeBankPay = "BNK1"
        journal = (
            request.env["account.journal"].sudo().search([("code", "=", codeBankPay)])
        )
        destination_account = (
            request.env["account.account"]
            .sudo()
            .search([("code", "=", "2.1.1.01.010")])
        )
        outstanding_account = (
            request.env["account.account"]
            .sudo()
            .search([("code", "=", "1.1.1.02.004")])
        )
        # print all fields jornal
        payment_vals = {
            "payment_type": "outbound",
            "amount": float(factura.amount_total),
            "currency_id": factura.currency_id.id,
            "journal_id": journal.id,
            "company_id": factura.company_id.id,
            "date": factura.date,
            "ref": factura.name,
            "partner_id": factura.partner_id.id,
        }
        # payment_vals = {
        #     "partner_id": factura.partner_id.id,
        #     "journal_id": journal.id,
        #     "payment_type": "outbound",
        #     "partner_type": "supplier",
        #     "amount": float(factura.amount_total),
        #     "amount_company_currency_signed": -float(factura.amount_total),
        #     "is_reconciled": True,
        #     "is_matched": False,
        #     "is_internal_transfer": False,
        #     "payment_method_line_id": 2,
        #     "payment_method_id": 2,
        #     "outstanding_account_id": outstanding_account.id,
        #     "destination_account_id": destination_account.id,
        #     "currency_id": factura.currency_id.id,
        #     "move_id": factura.id,  # Relacionar el pago con la factura
        # }

        # Crear el pago y confirmarlo
        return request.env["account.payment"].sudo().create(payment_vals)
        # pago.sudo().action_post()

    def getProductoItem(self, item):
        producto = (
            request.env["product.template"]
            .sudo()
            .search([("default_code", "=", item.get("_id"))])
        )
        if producto:
            return producto[0]
        # create product
        nombre = (
            "s/n"
            if not item.get("detalle") or item.get("detalle") == ""
            else item.get("detalle").strip().upper()
        )
        aux = {
            "name": nombre,
            "default_code": item.get("_id"),
            "type": "consu",
            "categ_id": 1,
            "uom_id": 1,
            "uom_po_id": 1,
            "sale_line_warn": "no-message",
            "purchase_line_warn": "no-message",
            "service_type": "manual",
            "list_price": item.get("importe"),
            "detailed_type": "consu",
        }
        return request.env["product.template"].sudo().create(aux)

    def getItemsCompras(self, data, id, journal, currency):
        invoice = request.env["account.move"].sudo().search([("ref", "=", id)])
        proveedor = self.findByref(data.get("idEntidad"))
        if not proveedor:
            proveedor = self.getDefProveedor()
        centroCosto = (
            request.env["account.analytic.account"]
            .sudo()
            .search([("code", "=", data.get("idCentroCosto"))])
        )

        items = []
        if data.get("items"):
            for item in data.get("items"):
                producto = self.getProductoItem(item)
                aux = {
                    # "move_id":idMove,
                    "currency_id": currency.id,
                    "partner_id": proveedor.id,
                    "journal_id": journal.id,
                    "parent_state": "posted",
                    "move_name": item.get("id"),
                    "name": item.get("detalle"),
                    "display_type": "product",
                    "invoice": invoice.id,
                    "product_id": producto.id,
                    "quantity": item.get("cantidad"),
                    "price_unit": float(item.get("importe")),
                    "analytic_distribution": {
                        f"{centroCosto.id}": float(item.get("importe"))
                    },
                }
                items.append(aux)
            return items
        else:
            total = (
                0
                if data.get("importeTotal") == "" or not data.get("importeTotal")
                else data.get("importeTotal")
            )
            producto = self.getProductoItem(
                {
                    "detalle": data.get("detalle"),
                    "_id": data.get("detalle"),
                    "importe": float(total),
                }
            )
            return [
                {
                    # "move_id":idMove,
                    "currency_id": currency.id,
                    "partner_id": proveedor.id,
                    "journal_id": journal.id,
                    "parent_state": "posted",
                    "move_name": data.get("id"),
                    "name": data.get("detalle"),
                    "display_type": "product",
                    "invoice": invoice.id,
                    "product_id": producto.id,
                    "quantity": 1,
                    "price_unit": float(total),
                    "analytic_distribution": {f"{centroCosto.id}": 100},
                }
            ]

    def upgradeCentroCosto(self, data, id):
        # 4 es CUIT
        # 5 es DNI
        plan_id = 1
        aux = {
            "name": data.get("nombreCentroCosto"),
            "plan_id": plan_id,
            "root_plan_id": plan_id,
            "code": id,
        }
        print(aux)
        try:
            request.env["account.analytic.account"].sudo().create(aux)
        except Exception as e:
            print(e)

    def upgradeProveedores(self, data, id):
        # 4 es CUIT
        # 5 es DNI
        aux = {
            "name": data.get("razonSocial"),
            "ref": id,
            "vat": data.get("cuit"),
            "supplier_rank": 1,
            "l10n_latam_identification_type_id": 4,
            "l10n_ar_afip_responsibility_type_id": 1,
        }
        print(aux)
        try:
            if not self.findByref(aux["ref"]):
                request.env["res.partner"].sudo().create(aux)
        except Exception as e:
            print(e)
