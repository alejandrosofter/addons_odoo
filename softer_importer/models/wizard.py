from odoo import models, fields, api
import firebase_admin
from firebase_admin import credentials, firestore
from odoo.modules.module import get_module_resource
import re
from datetime import datetime, date


class FirebaseImportWizard(models.TransientModel):
    _name = "importer.wizard"
    _description = "Importar registros desde Firebase"

    fechaHoraComienzo = fields.Datetime(string="Comienzo", default=fields.Datetime.now)
    fechaHoraFinal = fields.Datetime(string="Final")
    coleccion = fields.Selection(
        [
            ("pacientes", "Pacientes"),
            ("compras", "Compras"),
        ]
    )
    registrosProcesados = fields.Integer(string="Registros procesados", default=0)
    actualIdImport = fields.Char(string="Actual ID")
    totalImportar = fields.Integer(string="Total a importar", default=0)
    journal_pay_default = fields.Many2one("account.journal", string="Cuenta Pagos")
    journal_item_default = fields.Many2one(
        "account.account",
        string="Cuenta Items Default",
    )
    estado = fields.Selection(
        [
            ("detenido", "Detenido"),
            ("procesando", "Procesando"),
            ("finalizado", "Finalizado"),
        ],
        string="Estado",
        default="detenido",
    )

    def action_resume(self):
        for record in self:
            self.write({"estado": "procesando"})
            journal = self.env["account.journal"].search([("type", "=", "purchase")])
            currency = self.env["res.currency"].search([("name", "=", "ARS")])
            defProveedor = self.getDefProveedor()
            last_document = self.findDocId(record.actualIdImport)

            print(f"ARRANCANDO CON: {last_document}")
            self.with_delay().importar_job(
                journal,
                currency,
                defProveedor,
                limit=1,
                last_document=last_document,
                journal_pay_default=self.journal_pay_default,
                journal_item_default=self.journal_item_default,
            )

    @api.model
    def create(self, vals):
        """Sobreescribe el método create para iniciar el job en segundo plano al crear un registro."""
        record = super(FirebaseImportWizard, self).create(vals)
        record.importar()  # Llama a la función para iniciar el job
        return record

    def importar(self):
        """Programa el job de importación en segundo plano."""
        self.write({"estado": "procesando"})
        journal = self.env["account.journal"].search([("type", "=", "purchase")])

        currency = self.env["res.currency"].search([("name", "=", "ARS")])
        defProveedor = self.getDefProveedor()

        self.with_delay().importar_job(
            journal,
            currency,
            defProveedor,
            isBegin=True,
            journal_pay_default=self.journal_pay_default,
            journal_item_default=self.journal_item_default,
        )

    @api.model
    def connect_to_firebase(self):
        """Configura y establece la conexión a Firebase."""
        cred_path = get_module_resource(
            "softer_importer", "static/configs", "firebaseConfig.json"
        )
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        return firestore.client()

    def getDefProveedor(self):
        defProveedor = self.env["res.partner"].search(
            [("name", "=", "CONSUMIDOR FINAL")], limit=1
        )
        if not defProveedor:
            defProveedor = self.env["res.partner"].create({"name": "CONSUMIDOR FINAL"})

        return defProveedor

    def getNroFactura(self, nro, id):
        ramdomId = datetime.now().strftime("%H%M%S")[-4:]
        idNro = re.sub(r"\D", "", id)
        subNro = f"{ramdomId}"
        if not nro:
            return [f"FA-sinNro", subNro]
        arr = nro.split("-")
        if len(arr) > 1:
            return [f"FA-{arr[0]}", subNro]
        return [f"FA-{nro}", subNro]

    def getProveedorFirebase(self, data):
        db = self.connect_to_firebase()
        # Obtén el ID de la entidad y elimina cualquier barra diagonal al final
        id_entidad = data.get("idEntidad").rstrip("/")
        if not id_entidad or id_entidad == "":
            return None
        collection_ref = db.collection("proveedores")

        doc = collection_ref.document(id_entidad).get()

        if doc.exists:
            return doc.to_dict()
        return None

    def getProveedor(self, data, defaultProveedor):

        res = self.env["res.partner"].search([("ref", "=", data.get("idEntidad"))])
        if res:
            return res[0]

        # 4 es CUIT
        # 5 es DNI
        proveedor = self.getProveedorFirebase(data)
        if not data.get("idEntidad") or data.get("idEntidad") == "" or not proveedor:
            return defaultProveedor
        if proveedor.get("cuit"):

            res = self.env["res.partner"].search([("vat", "=", proveedor.get("cuit"))])
            # BUSCO PRIMERO QUIZAS SE CARGO CON EL MISMO CUIT
            if res:
                return res[0]
        aux = {
            "name": proveedor.get("razonSocial").upper().strip(),
            "ref": data.get("idEntidad"),
            "l10n_latam_identification_type_id": 4,
            "vat": proveedor.get("cuit"),
            "email": proveedor.get("email"),
            "supplier_rank": 1,
            "l10n_ar_afip_responsibility_type_id": 1,
        }
        try:
            proveedor = self.env["res.partner"].create(aux)

            return proveedor

        except Exception as e:
            print(f"No encontre proveedor por error")
            return defaultProveedor

    def getFecha(self, fecha):
        try:
            # Si la fecha es un objeto datetime (o tipo timestamp de Firebase que se convierte en datetime)
            if isinstance(fecha, datetime):
                year = fecha.year
                if fecha.year < 25:
                    year = 2000 + fecha.year
                formatted_date = fecha.strftime(f"{year}-%m-%d")
                print("es datetime")

            # Si es un timestamp (segundos desde la época Unix, común en Firebase)
            elif isinstance(fecha, int) or isinstance(fecha, float):
                # Convertir el timestamp a datetime
                fecha_obj = datetime.fromtimestamp(fecha)
                year = fecha_obj.year
                if fecha.year < 25:
                    year = 2000 + fecha_obj.year
                newDate = datetime(fecha_obj.year, fecha_obj.month, fecha_obj.day)
                formatted_date = newDate.strftime(f"{year}-%m-%d")
                print(f"es timestamp YEAR {formatted_date}")

            # Si es un string en el formato 'yy-mm-dd'
            elif isinstance(fecha, str):
                # Convertir la cadena 'yy-mm-dd' a un objeto datetime
                fecha_obj = datetime.strptime(fecha, "%y-%m-%d")
                year = fecha_obj.year
                if fecha.year < 25:
                    year = 2000 + fecha_obj.year
                formatted_date = fecha_obj.strftime(f"{year}-%m-%d")
                print("es string")

            else:
                formatted_date = None  # Si no es un tipo válido de fecha

        except ValueError as e:
            # Si ocurre un error de conversión, manejarlo
            formatted_date = None
            print(f"Error de conversión: {e}")

        print(f"FECHA {formatted_date}")
        return formatted_date

    def loadCompra(self, data, id, journal, currency, defaultProveedor):
        auxInvoice = self.env["account.move"].search([("ref", "=", id)])
        if auxInvoice:
            return auxInvoice
        formatted_date = self.getFecha(data.get("fecha"))
        nroFactura = self.getNroFactura(data.get("nro"), id)
        proveedor = self.getProveedor(data, defaultProveedor)
        if not proveedor:
            proveedor = defaultProveedor
        importeTotal = (
            0
            if not data.get("importeTotal") or data.get("importeTotal") == ""
            else float(data.get("importeTotal"))
        )
        invoice = {
            "partner_id": proveedor.id,
            "sequence_prefix": nroFactura[0],
            "sequence_number": nroFactura[1],
            "currency_id": currency.id,
            "journal_id": journal.id,
            "state": "draft",
            "ref": f"{id}",
            "l10n_latam_document_type_id": 1,
            "l10n_ar_afip_responsibility_type_id": 1,
            # "l10n_ar_latam_document_number": data.get("nro"),
            "payment_state": "paid",
            "l10n_ar_currency_rate": 1,
            "to_check": False,
            "posted_before": True,
            "is_storno": False,
            "move_type": "in_invoice",
            "name": f"{nroFactura[0]}{nroFactura[1]}",
            "auto_post": "no",
            "payment_state": "paid",
            "invoice_partner_display_name": data.get("label_idEntidad"),
            "date": formatted_date,
            "invoice_date": formatted_date,
            "invoice_date_due": formatted_date,
            "amount_untaxed": importeTotal,
            "amount_total": importeTotal,
            "amount_untaxed_signed": -importeTotal,
            "amount_total_signed": -importeTotal,
            "amount_total_in_currency_signed": -importeTotal,
        }
        print(f"invoice {invoice}")
        invoice = self.env["account.move"].create(invoice)

        return invoice

    def getProductoItem(self, item):
        producto = self.env["product.product"].search(
            [("default_code", "=", item.get("_id"))]
        )
        if producto:
            return producto[0]

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
        producto = self.env["product.template"].create(aux)

        return self.env["product.product"].search(
            [("default_code", "=", item.get("_id"))]
        )

    def getItemsCompra(self, data, currency, proveedor, journal, invoice, centroCosto):
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
                    "name": item.get("detalle"),
                    "display_type": "product",
                    "move_id": invoice.id,
                    "product_id": producto.id,
                    "quantity": item.get("cantidad"),
                    "price_unit": float(item.get("importe")),
                    "account_id": centroCosto.id,
                    # "analytic_distribution": {f"{centroCosto.id}": 100},
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
                    "_id": invoice.id,
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
                    "name": data.get("detalle"),
                    "display_type": "product",
                    "move_id": invoice.id,
                    "product_id": producto.id,
                    "quantity": 1,
                    "price_unit": float(total),
                    "account_id": centroCosto.id,
                    # "analytic_distribution": {f"{centroCosto.id}": 100},
                }
            ]

    def loadItemsCompra(self, data, invoice, centroCosto, proveedor, journal, currency):
        items = self.getItemsCompra(
            data, currency, proveedor, journal, invoice, centroCosto
        )

        for item in items:
            self.env["account.move.line"].create(item)

    def getCentroCosto2(self, data, id):
        cc = self.env["account.analytic.account"].search(
            [("code", "=", data.get("idCentroCosto"))]
        )
        if cc:
            return cc[0]
        plan_id = 1
        nombre = (
            "s/n"
            if not data.get("label_idCentroCosto")
            or data.get("label_idCentroCosto") == ""
            else data.get("label_idCentroCosto")
        )
        aux = {
            "name": nombre,
            "plan_id": plan_id,
            "root_plan_id": plan_id,
            "code": id,
        }
        cc = self.env["account.analytic.account"].create(aux)

        return cc

    def getCentroCosto(self, data, id, journal_default_compra):
        nombre = (
            "s/n"
            if not data.get("label_idCentroCosto")
            or data.get("label_idCentroCosto") == ""
            else data.get("label_idCentroCosto")
        )
        idNro = re.sub(r"\D", "", id)
        code = f"5.1.1.10.{idNro}"

        if nombre == "s/n":
            return journal_default_compra
        print(f"BUSCANDO CENTRO DE COSTO: {data.get('idCentroCosto')}")
        cc = self.env["account.account"].search([("code", "=", code)])
        if cc:
            return cc[0]

        aux = {
            "name": f"GASTOS {nombre}",
            "account_type": "expense",
            "company_id": 1,
            "code": code,
        }
        print(f"CREAR Centro de costo: {aux}")
        cc = self.env["account.account"].create(aux)

        return cc

    def findByRef(self, ref):
        docs = self.env["account.move"].search([("ref", "=", ref)])
        if len(docs) > 0:
            return docs[0]

    def findDocId(self, id):
        db = self.connect_to_firebase()
        collection_ref = db.collection(self.coleccion)
        doc = collection_ref.document(id).get()
        if doc.exists:
            return doc.to_dict()

    def getData(
        self, last_document, limit=25, fieldOrder="fecha_timestamp", isBegin=False
    ):
        db = self.connect_to_firebase()
        collection_ref = db.collection(self.coleccion)
        query = collection_ref.order_by(fieldOrder).limit(limit)
        if last_document and not isBegin:
            query = query.start_after(last_document)
        # Referencia a la colección de Firebase

        all_records = query.get()
        return all_records

    def loadPago(self, data, invoice, journal, currency, company):
        payment_method = self.env["account.payment.method"].search(
            [("code", "=", "manual")]
        )[0]

        aux = {
            # "invoice_ids": [[4, invoice.id, "None"]],
            # "default_invoice_ids": [[4, invoice.id, "None"]],
            "amount": float(data.get("importeTotal")),
            # "payment_date": ,
            "payment_type": "outbound",
            "has_invoices": True,
            "currency_id": 1,
            "journal_id": journal.id,
            "payment_method_id": 1,
            "partner_id": invoice.partner_id.id,
            "partner_type": "supplier",
            "communication": "INV/2019/0141/44",
            "name": "INV/2019/0141/44",
        }
        print(aux)
        try:
            pay = self.env["account.payment"].create(aux)
            print("Pago registrado correctamente.")
        except Exception as e:
            print("Error al registrar el pago:", e)

    def importar_job(
        self,
        journal,
        currency,
        defProveedor,
        last_document=None,
        limit=10,
        fieldOrder="fecha_timestamp",
        isBegin=False,
        journal_item_default=None,
        journal_pay_default=None,
        company=None,
    ):
        """Job en segundo plano para importar datos de Firebase."""
        # Conectar a Firebase
        # print(f"ARRANCO DESDE: {last_document}")
        # Crea una referencia a la colección de Firebase
        all_records = self.getData(last_document, limit, fieldOrder, isBegin)
        # todos = self.getData(None, None, fieldOrder)
        # print(f"todos: {len(todos)}")

        # Actualiza el campo totalImportar con el total de registros

        i = 0
        # Procesa e importa cada documento
        for doc in all_records:
            i = i + 1

            data = doc.to_dict()
            invoice = self.findByRef(doc.id)
            if invoice is not None:
                print(f"El documento {data.get('ref')} ya ha sido importado")
                continue
            self.actualIdImport = doc.id
            centroCosto = self.getCentroCosto(
                data, doc.get("idCentroCosto"), journal_item_default
            )
            print(f"CENTRO DE COSTO: {centroCosto}")
            # try:
            invoice = self.loadCompra(data, doc.id, journal, currency, defProveedor)

            self.loadItemsCompra(
                data, invoice, centroCosto, defProveedor, journal, currency
            )
            # publicar factura
            # invoice.action_post()
            # inputar pago
            # self.loadPago(data, invoice, journal_pay_default, currency, company)

            self.registrosProcesados += 1
            self.env.cr.commit()

            print(f"Importando registro {i}")

            # except Exception as e:
            #     print(f"Error al procesar el registro {doc.id}: {e}")
            #     continue

        self.totalImportar = self.totalImportar + i
        if len(all_records) == limit:
            print(f"Vuelvo a importar {limit} registros")
            last_document = all_records[-1].to_dict()
            self.with_delay().importar_job(
                journal,
                currency,
                defProveedor,
                last_document,
                limit,
                fieldOrder,
                journal_item_default=journal_item_default,
                journal_pay_default=journal_pay_default,
            )
        else:
            print("Todos los registros han sido importados. Proceso finalizado.")
            # Opcional: Cambiar el estado a "finalizado" si es necesario
            # self.write({"estado": "finalizado"})
