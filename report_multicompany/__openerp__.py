# -*- encoding: utf-8 -*-
#
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Vauxoo - http://www.vauxoo.com/
#    All Rights Reserved.
#    info Vauxoo (info@vauxoo.com)
#
#    Coded by: Jorge Angel Naranjo (jorge_nr@vauxoo.com)
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
{
    "name": "Report Multicompany",
    "version": "1.0",
    "depends": [
        "base",
    ],
    "author": "Vauxoo",
    "description": """
Report Multicompany
===================

This module adds a model report_multicompany which helps to have a report
relationship with company (similar to a property).

    """,
    "website": "http://vauxoo.com",
    "category": "Addons Vauxoo",
    "data": [
    "security/ir.model.access.csv",
    "view/report_multicompany_view.xml",
    "security/report_multicompany_security.xml"
    ],
    "test": [],
    "active": False,
    "installable": True,
}
