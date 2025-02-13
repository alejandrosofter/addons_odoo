import datetime
import logging
from requests.auth import HTTPDigestAuth
from requests import Session
import json
from types import SimpleNamespace
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from collections import defaultdict
import pytz

_logger = logging.getLogger(__name__)


class HikvisionClocks:

    def __init__(self, device_ip, port_number, device_password, device_user, is_https):
        self.device_ip = device_ip
        self.port_number = port_number
        self.device_password = device_password
        self.device_user = device_user
        self.is_https = is_https

    def getUserAttendance(self, users, line):
        for user in users:
            if user.user_id == line.user_id:
                return user

    def resetAll(self):
        auth = HTTPDigestAuth(self.device_user, self.device_password)

        path = self.getUrl() + "/ISAPI/System/factoryReset?mode=full"

    def updateUser(self, employee):
        auth = HTTPDigestAuth(self.device_user, self.device_password)

        _logger.info(f"UPDATE USER {employee.name}")
        path = self.getUrl() + "/ISAPI/AccessControl/UserInfo/Modify?format=json"
        body = {"UserInfo": self.parseDataUserClock(employee)}
        r = requests.put(path, json=body, auth=auth)
        return r

    def addUser(self, employee):
        data = self.parseDataUserClock(employee)
        _logger.info(f"CREATE USER {employee.name}")
        _logger.info(data)
        auth = HTTPDigestAuth(self.device_user, self.device_password)

        path = self.getUrl() + "/ISAPI/AccessControl/UserInfo/Record?format=json"
        body = {"UserInfo": data}
        response = requests.post(path, data=json.dumps(body), auth=auth)
        return response.json()

    def parseDataUserClock(self, employee):

        return {
            "employeeNo": employee.device_id_num,
            "name": employee.name,
            "userType": "normal",
            "gender": "female" if employee.gender == "female" else "male",
            "localUIRight": False,
            "password": employee.pin,
            "maxOpenDoorTime": 0,
            "Valid": {
                "enable": True,
                "beginTime": "2020-08-23T00:00:00",
                "endTime": "2036-08-23T23:59:59",
                "timeType": "local",
            },
            "doorRight": "1",
            "RightPlan": [{"doorNo": 1, "planTemplateNo": "1"}],
            "roomNumber": 1,
            "floorNumber": 1,
            "userVerifyMode": "",
            "groupId": 1,
        }

    def syncEmployee(self, selfModel):
        hr_employee = selfModel.env["hr.employee"]
        employees = hr_employee.search([])
        usersClock = self.getAllUsers()

        salida = ""
        for employee in employees:
            if not employee.device_id_num:
                salida += f"El empleado {employee.name} no tiene seteado el Device ID (Ajustes de RR HH en empleado)  \n"
                continue
            user = self.getUserClock(usersClock, employee)
            if user:
                res = self.updateUser(employee)
                salida += f"{employee.name} UPDATE OK! \n"
            else:
                res = self.addUser(employee)
                salida += f"{employee.name} NUEVO OK! \n"
        return salida

    def setDate(self, date):
        auth = HTTPDigestAuth(self.device_user, self.device_password)
        path = self.getUrl() + "/ISAPI/System/time"

    def getUserClock(self, users, employee):
        for user in users["UserInfo"]:
            if (user["employeeNo"]) == str(employee.device_id_num):
                return user

    def syncDbData(_self, self, registros, groupData):
        _self.syncTableBase(self, registros)
        _self.syncTableAttendance(self, groupData)

    def getDate(self, fecha):
        # Parsear la fecha en formato ISO 8601 con la zona horaria incluida
        atten_time = datetime.fromisoformat(fecha)

        # Definir la zona horaria local
        local_tz = pytz.timezone("GMT")  # Asegúrate de usar la zona horaria correcta

        # Convertir la fecha al tiempo UTC
        utc_dt = atten_time.astimezone(pytz.utc)

        # Convertir la fecha UTC a formato de cadena
        utc_dt_str = utc_dt.strftime("%Y-%m-%d %H:%M:%S")

        # Convertir la cadena a un objeto datetime
        atten_time = datetime.strptime(utc_dt_str, "%Y-%m-%d %H:%M:%S")

        return fields.Datetime.to_string(atten_time)

    def syncTableAttendance(_self, self, data):
        hr_attendance = self.env["hr.attendance"]
        _logger.info(f"SYNC DATA ATTENDENCE cant registros {len(data)}")
        # truncate model

        for line in data:
            dateIn = _self.getDate(line.get("in", None))
            dateOut = _self.getDate(line.get("out", None))
            duplicate_atten_ids = hr_attendance.search(
                [
                    ("employee_id", "=", line.get("employee_id", None)),
                    ("check_in", "=", dateIn),
                ]
            )
            if not duplicate_atten_ids:
                hr_attendance.create(
                    {
                        "employee_id": line.get("employee_id", None),
                        "check_in": dateIn,
                        "check_out": dateOut,
                    }
                )

    def syncTableBase(_self, self, data):
        zk_attendance = self.env["zk.machine.attendance"]
        _logger.info(f"SYNC DATA 2122 BASE cant registros {len(data)}")
        # truncate model

        for line in data:
            newDate = _self.getDate(line.get("date", None))
            _logger.info(line)
            _logger.info(newDate)
            duplicate_atten_ids = zk_attendance.search(
                [
                    ("employee_id", "=", line.get("employee_id", None)),
                    ("punching_time", "=", newDate),
                ]
            )
            if not duplicate_atten_ids:
                zk_attendance.create(
                    {
                        "employee_id": line.get("employee_id", None),
                        "device_id_num": self.id,
                        # 'attendance_type': str(line.get("type","")),
                        # 'punch_type': str(line.get("type","")),
                        "punching_time": newDate,
                        "address_id": self.company_id.id,
                        "id": line.get("id", None),
                    }
                )

    def sync_data(_self, self):
        hr_employee = self.env["hr.employee"]
        employees = hr_employee.search([])
        allData = []
        for employee in employees:
            _logger.info(f"Verificando marcadas de {employee.name}")
            if employee.device_id_num:
                partialData = _self.getAllData(self, employee.device_id_num, employees)
                allData += partialData

        orderData = sorted(allData, key=lambda x: x["date"])
        filterData = _self.filtrar_registros_por_tiempo(
            orderData, self.minutes_delete_repeat
        )
        groupData = _self.agrupar_simulando_salidas(filterData)
        _self.syncDbData(self, filterData, groupData)
        for data in groupData:
            _logger.info(data)
        return ""

    def agrupar_simulando_salidas(self, registros):
        # Diccionario para agrupar los registros por empleado y día
        registros_agrupados = defaultdict(list)

        # Iteramos por cada registro para agruparlo por employeeNro y día
        for registro in registros:
            fecha = datetime.strptime(registro["date"], "%Y-%m-%dT%H:%M:%S%z")
            dia = fecha.date()  # Extraemos solo la fecha sin la hora
            clave = (registro["employeeNro"], dia)  # Clave de agrupación

            # Agrupamos por employeeNro y día
            registros_agrupados[clave].append(registro)

        # Modificamos la estructura para cada grupo
        registros_modificados = []
        for (employeeNro, dia), entradas in registros_agrupados.items():
            # Ordenamos los registros por la fecha y hora
            entradas.sort(
                key=lambda x: datetime.strptime(x["date"], "%Y-%m-%dT%H:%M:%S%z")
            )

            # Agrupamos en pares consecutivos (in - siguiente entrada como out)
            i = 0
            while i < len(entradas) - 1:
                entrada_in = entradas[i]
                entrada_out = entradas[
                    i + 1
                ]  # Siguiente entrada será simulada como salida

                # Simulamos el par in-out
                registro_modificado = {
                    "id": entrada_in["id"],
                    "in": entrada_in["date"],
                    "out": entrada_out["date"],
                    "type": entrada_in["type"],
                    "name": entrada_in["name"],
                    "employeeNro": employeeNro,
                    "employee_id": entrada_in["employee_id"],
                }
                registros_modificados.append(registro_modificado)
                i += 2  # Saltar al siguiente par

        return registros_modificados

    def filtrar_registros_por_tiempo(self, registros, minutos):
        # Si el array tiene menos de 2 registros, no hay necesidad de filtrar
        if len(registros) < 2:
            return registros
        if minutos == 0:
            return registros
        # Convertimos la variable 'minutos' en un objeto timedelta
        delta_minutos = timedelta(minutes=minutos)

        # Creamos un nuevo array para almacenar los registros filtrados
        registros_filtrados = [
            registros[0]
        ]  # Añadimos el primer registro automáticamente

        # Iteramos sobre los registros comenzando por el segundo
        for i in range(1, len(registros)):
            # Obtenemos las fechas de los registros actual y anterior
            fecha_actual = datetime.strptime(
                registros[i]["date"], "%Y-%m-%dT%H:%M:%S%z"
            )
            ultimo_registro_filtrado = registros_filtrados[-1]
            fecha_anterior = datetime.strptime(
                ultimo_registro_filtrado["date"], "%Y-%m-%dT%H:%M:%S%z"
            )

            # Comparamos la diferencia de tiempo solo si es el mismo 'employeeNro'
            if registros[i]["employeeNro"] == ultimo_registro_filtrado["employeeNro"]:
                if fecha_actual - fecha_anterior >= delta_minutos:
                    registros_filtrados.append(registros[i])
            else:
                # Si no es el mismo 'employeeNro', agregamos el registro
                registros_filtrados.append(registros[i])

        return registros_filtrados

    def getEmployeeId(self, employeeNro, employes):
        for employee in employes:
            if employee.device_id_num == employeeNro:
                return employee.id
        return False

    def getAllData(_self, self, device_id_num, employes=[]):
        desde = 0
        SIZE_PAGE = 20
        attendance = _self.getData(desde, SIZE_PAGE, device_id_num, self.last_sync)
        _logger.info(attendance)
        total = attendance["totalMatches"]
        _logger.info(f"Total: {total}")
        # check InfoList exists
        if "InfoList" not in attendance:
            return []
        data = attendance["InfoList"]
        totalData = []
        while desde < total:
            for line in data:
                _logger.info(line)
                id = line["serialNo"]
                date = line["time"]
                name = line.get("name", None)
                type = line["type"]
                employeeNro = line.get("employeeNoString", None)
                if name:

                    totalData.append(
                        {
                            "id": id,
                            "date": date,
                            "type": type,
                            "name": name,
                            "employeeNro": employeeNro,
                            "employee_id": _self.getEmployeeId(employeeNro, employes),
                        }
                    )
                desde += 1

            # Llamar a getData nuevamente si aún hay más datos por procesar
            if desde < total:
                attendance = _self.getData(
                    desde, SIZE_PAGE, device_id_num, self.last_sync
                )
                data = attendance["InfoList"]

        return totalData

    def sync_device(_self, self):

        salida = _self.syncEmployee(self)
        salida += _self.sync_data(self)
        self.last_sync_time = datetime.now()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"message": salida, "type": "success", "sticky": True},
        }

    def getAllUsers(self):
        auth = HTTPDigestAuth(self.device_user, self.device_password)
        path = self.getUrl() + "/ISAPI/AccessControl/UserInfo/Search?format=json"
        body = {
            "UserInfoSearchCond": {
                "searchID": "4",
                "searchResultPosition": 0,
                "maxResults": 32,
            }
        }
        response = requests.post(path, data=json.dumps(body), auth=auth)
        return response.json()["UserInfoSearch"]

    def getUrl(self):
        protocol = "http" if self.is_https is False else "https"
        return protocol + "://" + self.device_ip

    def getUser(self, id=""):
        auth = HTTPDigestAuth(self.device_user, self.device_password)

        path = self.getUrl() + "/ISAPI/AccessControl/UserInfo/Search?format=json"
        body = {
            "UserInfoSearchCond": {
                "searchID": "4",
                "searchResultPosition": 0,
                "maxResults": 32,
                "EmployeeNoList": [{"employeeNo": str(id)}],
            }
        }
        if id == "":
            body = {
                "UserInfoSearchCond": {
                    "searchID": "4",
                    "searchResultPosition": 0,
                    "maxResults": 32,
                }
            }
        response = requests.post(path, data=json.dumps(body), auth=auth)
        _logger.info(response.json())
        return response.json()["UserInfoSearch"]

    def getData(self, desde=0, hasta=10, id="", last_sync=datetime.now()):

        auth = HTTPDigestAuth(self.device_user, self.device_password)

        path = self.getUrl() + "/ISAPI/AccessControl/AcsEvent?format=json"
        _logger.info(f"desde {desde}")
        body = {
            "AcsEventCond": {
                "searchID": "3",
                "searchResultPosition": desde,
                "startTime": last_sync.isoformat() + "T00:00:00+08:00",
                "maxResults": hasta,
                "employeeNoString": str(id),
                "major": 0,
                "minor": 0,
            }
        }
        response = requests.post(path, data=json.dumps(body), auth=auth)

        data = response.json().get("AcsEvent", None)

        if not data:
            _logger.info(response.json())
            raise UserError(_("No se encontraron eventos en esta fecha"))

        return data

    def test(self):
        _logger.info("Testeando Hikvision")

        try:
            testData = self.getUser()
            _logger.info(testData)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "message": "Conecta ok!",
                    "type": "success",
                    "sticky": False,
                },
            }
        except Exception as error:
            _logger.info(error)
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "message": f"Ups no puedo conectar a esta ip {self.device_ip}",
                    "type": "danger",
                    "sticky": False,
                },
            }
