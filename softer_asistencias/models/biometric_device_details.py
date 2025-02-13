# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import datetime

import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from .clocks.zk import ZkClock
from .clocks.hikvision import HikvisionClocks
import logging

_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")


class BiometricDeviceDetails(models.Model):
    """Model for configuring and connect the biometric device with odoo"""

    _name = "biometric.device.details"
    _description = "Biometric Device Details"

    name = fields.Char(string="Name", required=True, help="Record Name")

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.user.company_id.id,
        help="Current Company",
    )
    dispositivo_id = fields.Many2one(
        "dispositivos.dispositivos", string="Dispositivo", help="Dispositivo"
    )
    device_password = fields.Char(string="Password", help="Clave del dispositivo")
    device_user = fields.Char(string="Usuario", help="Usuario del dispositivo")
    last_sync = fields.Date(string="Sync desde", help="Sync desde")
    last_sync_time = fields.Datetime(string="Last Sync", help="Last Sync")
    minutes_delete_repeat = fields.Integer(
        string="Mins borrar repetidos",
        default=1,
        help="Minutos entre marcadas, cero (0) para no borrar",
    )
    type_clock = fields.Selection(
        [("ZK", "ZK"), ("hikvision", "Hikvision")],
        string="Tipo de Reloj",
        default="ZK",
    )

    def testZk(self):
        device = ZkClock(
            self.dispositivo_id.host,
            self.dispositivo_id.port,
            self.dispositivo_id.password,
        )
        return device.test()

    def testHikvision(self):
        device = HikvisionClocks(
            self.dispositivo_id.host,
            self.dispositivo_id.port,
            self.dispositivo_id.password,
            self.dispositivo_id.user,
            self.dispositivo_id.is_https,
        )
        return device.test()

    def action_test_connection(self):
        """Checking the connection status"""
        _logger.info("TESTEANDO CLOCKS")
        if self.type_clock == "ZK":
            return self.testZk()
        if self.type_clock == "hikvision":
            return self.testHikvision()

    @api.model
    def cron_sync(self):

        device = self.env["biometric.device.details"].search([])
        _logger.info(
            f"Cron Sync COMENZANDO, tengo {len(device)} Dispositivos para sync"
        )
        for rec in device:
            _logger.info(f"Cron Sync device {rec.name}")
            rec.action_download_attendance()
            rec.last_sync = datetime.datetime.now(pytz.utc)

    def action_download_attendance(self):
        if self.type_clock == "ZK":
            device = ZkClock(self.device_ip, self.port_number, self.device_password)
            return device.sync_device(self)

        if self.type_clock == "hikvision":
            device = HikvisionClocks(
                self.dispositivo_id.host,
                self.dispositivo_id.port,
                self.dispositivo_id.password,
                self.dispositivo_id.user,
                self.dispositivo_id.is_https,
            )

            return device.sync_device(self)
