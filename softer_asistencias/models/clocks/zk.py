import datetime
import logging
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")


class ZkClock:

    def __init__(self, device_ip, port_number, device_password):
        self.device_ip = device_ip
        self.port_number = port_number
        self.device_password = device_password
        self.device = ZK(self.device_ip, self.port_number)

    def sync_device(_self, self):
        _self.sync_data(self)
        self.last_sync_time = datetime.now()

    def sync_data(_self, self):
        """Function to download attendance records from the device"""
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
        zk_attendance = self.env["zk.machine.attendance"]
        hr_attendance = self.env["hr.attendance"]

        machine_ip = _self.device_ip
        zk_port = _self.port_number
        try:
            # Connecting with the device with the ip and port provided
            zk = ZK(
                machine_ip,
                port=zk_port,
                timeout=15,
                password=0,
                force_udp=False,
                ommit_ping=False,
            )
        except NameError:
            raise UserError(
                _(
                    "Pyzk module not Found. Please install it"
                    "with 'pip3 install pyzk'."
                )
            )
        conn = self.device_connect(zk)
        self.action_set_timezone()
        if conn:
            conn.disable_device()  # Device Cannot be used during this time.
            user = conn.get_users()
            attendance = conn.get_attendance()
            if attendance:
                for each in attendance:
                    atten_time = each.timestamp
                    local_tz = pytz.timezone(self.env.user.partner_id.tz or "GMT")
                    local_dt = local_tz.localize(atten_time, is_dst=None)
                    utc_dt = local_dt.astimezone(pytz.utc)
                    utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                    atten_time = datetime.datetime.strptime(utc_dt, "%Y-%m-%d %H:%M:%S")
                    atten_time = fields.Datetime.to_string(atten_time)
                    for uid in user:
                        if uid.user_id == each.user_id:
                            get_user_id = self.env["hr.employee"].search(
                                [("device_id_num", "=", each.user_id)]
                            )
                            if get_user_id:
                                duplicate_atten_ids = zk_attendance.search(
                                    [
                                        ("device_id_num", "=", each.user_id),
                                        ("punching_time", "=", atten_time),
                                    ]
                                )
                                if not duplicate_atten_ids:
                                    zk_attendance.create(
                                        {
                                            "employee_id": get_user_id.id,
                                            "device_id_num": each.user_id,
                                            "attendance_type": str(each.status),
                                            "punch_type": str(each.punch),
                                            "punching_time": atten_time,
                                            "address_id": _self.device_ip,
                                        }
                                    )
                                    att_var = hr_attendance.search(
                                        [
                                            ("employee_id", "=", get_user_id.id),
                                            ("check_out", "=", False),
                                        ]
                                    )
                                    if each.punch == 0:  # check-in
                                        if not att_var:
                                            hr_attendance.create(
                                                {
                                                    "employee_id": get_user_id.id,
                                                    "check_in": atten_time,
                                                }
                                            )
                                    if each.punch == 1:  # check-out
                                        if len(att_var) == 1:
                                            att_var.write({"check_out": atten_time})
                                        else:
                                            att_var1 = hr_attendance.search(
                                                [("employee_id", "=", get_user_id.id)]
                                            )
                                            if att_var1:
                                                att_var1[-1].write(
                                                    {"check_out": atten_time}
                                                )
                            else:
                                employee = self.env["hr.employee"].create(
                                    {"device_id_num": each.user_id, "name": uid.name}
                                )
                                zk_attendance.create(
                                    {
                                        "employee_id": employee.id,
                                        "device_id_num": each.user_id,
                                        "attendance_type": str(each.status),
                                        "punch_type": str(each.punch),
                                        "punching_time": atten_time,
                                        "address_id": _self.address_id,
                                    }
                                )
                                hr_attendance.create(
                                    {"employee_id": employee.id, "check_in": atten_time}
                                )
                conn.disconnect
                return True
            else:
                raise UserError(
                    _("Unable to get the attendance log, please" "try again later.")
                )
        else:
            raise UserError(
                _(
                    "Unable to connect, please check the"
                    "parameters and network connections."
                )
            )

    def device_connect(self, zk):
        """Function for connecting the device with Odoo"""
        try:
            conn = zk.connect()
            return conn
        except Exception:
            return False

    def test(self):
        _logger.info(f"Testeando ZK {self.device_ip} port {self.port_number}")
        zk = ZK(
            self.device_ip,
            self.port_number,
            timeout=5,
            password=self.device_password,
            force_udp=False,
            ommit_ping=False,
        )
        # zk = ZK(
        #     self.device_ip,
        #     port=self.port_number,
        #     timeout=30,
        #     password=self.device_password,
        #     ommit_ping=False,
        # )
        try:
            if zk.connect():
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "message": "Successfully Connected",
                        "type": "success",
                        "sticky": False,
                    },
                }
        except Exception as error:
            raise ValidationError(f"upsss {error}")
