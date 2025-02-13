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
{
    "name": "Softer Asistencias",
    "version": "17.0.1.2.2",
    "category": "Human Resources",
    "summary": "Integracion para biometricos ZTK y hikvision",
    "description": "Integracion para biometricos ZTK y hikvision",
    "author": "Softer",
    "company": "Softer",
    "maintainer": "Softer",
    "website": "https://Softer.com.ar",
    "depends": ["base_setup", "hr_attendance", "softer_dispositivos", "resource"],
    "external_dependencies": {
        "python": ["pyzk"],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/biometric_device_details_views.xml",
        "views/hr_employee_views.xml",
        "views/daily_attendance_views.xml",
        "views/biometric_device_attendance_menus.xml",
        "views/res_config_settings_view.xml",
        "data/download_data.xml",
        "views/cron_sync.xml",
        "views/resource_calendar_leaves_views.xml",
        "views/resource_calendar_views.xml",
        "views/hr_attendance_menu.xml",
        "views/hr_attendance.xml",
        "views/assets.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
