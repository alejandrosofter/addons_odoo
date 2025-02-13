from odoo import http
from odoo.http import request, Response
from odoo import fields
import json
import logging
from datetime import datetime, timedelta
import pytz
from collections import defaultdict

_logger = logging.getLogger(__name__)


class AttendanceAPI(http.Controller):
    @http.route("/api/empleados", auth="none", methods=["GET"], csrf=False)
    def submit_attendance(self, **kwargs):
        _logger.info(f"API DE EMPLEADOSS Token")

        token = request.httprequest.headers.get("Authorization")
        _logger.info(f"API DE EMPLEADOSS Token: {token}")
        # Validar el token
        dispositivo = (
            request.env["dispositivos.dispositivos"]
            .sudo()
            .search([("tokenApi", "=", token), ("conexion", "=", "api")], limit=1)
        )
        if not dispositivo:
            return Response(
                json.dumps({"error": "No encuentro o token invalido"}),
                status=401,
                content_type="application/json",
            )
        jsonData = self.getEmployees()
        _logger.info(jsonData)
        return Response(
            json.dumps({"status": "success", "employees": jsonData}),
            status=200,
            content_type="application/json",
        )

    @http.route("/api/asistencias", auth="none", methods=["POST"], csrf=False)
    def load_attendance(self, **kwargs):
        _logger.info(f"API DE ASISTENCIAS Token")

        token = request.httprequest.headers.get("Authorization")
        dispositivo = (
            request.env["dispositivos.dispositivos"]
            .sudo()
            .search([("tokenApi", "=", token), ("conexion", "=", "api")], limit=1)
        )
        if not dispositivo:
            return Response(
                json.dumps({"error": "No encuentro o token invalido"}),
                status=401,
                content_type="application/json",
            )
        raw_data = request.httprequest.data

        # Parsear los datos como JSON
        data = json.loads(raw_data)
        asistencias = data.get("asistencias", [])
        deviceAttendance = (
            request.env["biometric.device.details"]
            .sudo()
            .search([("id", "=", dispositivo.id)], limit=1)
        )

        if deviceAttendance:

            employees = self.getEmployees()
            _logger.info(asistencias)
            attendances = self.getDataDeviceDB(asistencias, employees, deviceAttendance)

            self.syncTableBase(attendances)
            inout = self.agrupar_simulando_salidas(attendances)
            self.syncTableAttendance(inout)
            # orderData = sorted(
            #     attendances,
            #     key=lambda x: x.get("punching_time"),
            # )
            # filterData = _self.filtrar_registros_por_tiempo(
            #     orderData, self.minutes_delete_repeat
            # )
            # groupData = _self.agrupar_simulando_salidas(filterData)
        return Response(
            json.dumps({"status": "success", "asistencias": asistencias}),
            status=200,
            content_type="application/json",
        )

    def getEmployees(self):
        employees = request.env["hr.employee"].sudo().search([])
        jsonData = []
        for employee in employees:
            jsonData.append(
                {
                    "device_id_num": employee.device_id_num,
                    "name": employee.name,
                    "pin": employee.pin,
                    "id": employee.id,
                }
            )
        return jsonData

    def syncTableAttendance(self, data):
        hr_attendance = request.env["hr.attendance"].sudo()
        _logger.info(f"SYNC DATA ATTENDENCE cant registros {len(data)}")
        # truncate model

        for line in data:
            dateIn = line.get("in", None).replace(tzinfo=None)
            dateOut = line.get("out", None).replace(tzinfo=None)
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

    def agrupar_simulando_salidas(self, registros):
        # Diccionario para agrupar los registros por empleado y día
        registros_agrupados = defaultdict(list)

        # Iteramos por cada registro para agruparlo por employeeNro y día
        for registro in registros:
            fecha = registro.get("punching_time")
            dia = fecha.date()  # Extraemos solo la fecha sin la hora
            clave = (registro.get("employee_id"), dia)  # Clave de agrupación

            # Agrupamos por employeeNro y día
            registros_agrupados[clave].append(registro)

        # Modificamos la estructura para cada grupo
        registros_modificados = []
        for (employeeNro, dia), entradas in registros_agrupados.items():
            # Ordenamos los registros por la fecha y hora
            entradas.sort(key=lambda x: x.get("punching_time"))

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
                    "in": entrada_in["punching_time"],
                    "out": entrada_out["punching_time"],
                    "employeeNro": employeeNro,
                    "employee_id": entrada_in["employee_id"],
                }
                registros_modificados.append(registro_modificado)
                i += 2  # Saltar al siguiente par

        return registros_modificados

    def getDate(self, fecha):
        local_tz = pytz.timezone(
            "America/Argentina/Buenos_Aires"
        )  # Cambia a la zona horaria correspondiente
        fecha_local = local_tz.localize(datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S"))

        # Convertir a UTC
        return fecha_local.astimezone(pytz.utc)

    def getEmployeDevice(self, employees, userID):
        for employee in employees:
            if int(employee.get("device_id_num", None)) == int(userID):
                return employee

    def getDataDeviceDB(self, data, employees, device):
        dataParsed = []
        zk_attendance = request.env["zk.machine.attendance"].sudo()
        for line in data:
            newDate = self.getDate(line.get("fecha", None))
            employee = self.getEmployeDevice(employees, line.get("user_id", None))
            if not employee:
                _logger.info(f"No hay empleado con id {line.get('user_id',None)}")
                continue
            duplicate_atten_ids = zk_attendance.search(
                [
                    ("employee_id", "=", employee.get("id", None)),
                    ("punching_time", "=", newDate),
                ]
            )
            if not duplicate_atten_ids:
                dataParsed.append(
                    {
                        "employee_id": employee.get("id", None),
                        "device_id_num": device.id,
                        # 'attendance_type': str(line.get("type","")),
                        # 'punch_type': str(line.get("type","")),
                        "punching_time": newDate,
                        "address_id": device.company_id.id,
                        "id": line.get("id", None),
                    }
                )
        return dataParsed

    def syncTableBase(self, data):
        zk_attendance = request.env["zk.machine.attendance"].sudo()

        for line in data:
            zk_attendance.create(
                {
                    "employee_id": line.get("employee_id", None),
                    "device_id_num": line.get("device_id_num", None),
                    "punching_time": fields.Datetime.to_string(
                        line.get("punching_time", None)
                    ),
                    "address_id": line.get("address_id", None),
                    "id": line.get("id", None),
                }
            )
