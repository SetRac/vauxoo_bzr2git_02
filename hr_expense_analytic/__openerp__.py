# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2012 Vauxoo - http://www.vauxoo.com/
#    All Rights Reserved.
#    info Vauxoo (info@vauxoo.com)
############################################################################
#    Coded by: el_rodo_1 (rodo@vauxoo.com)
############################################################################
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
##############################################################################

{
    "name" : "hr_expense_analytic",
    "version" : "1.0",
    "author" : "Vauxoo",
    "category" : "hr",
    "description" : """This module add analytic account to departament""",
    "website" : "http://www.vauxoo.com/",
    "license" : "AGPL-3",
    "depends" : ["hr","hr_expense","account"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["hr_expense_analytic_view.xml"],
    "test": [],
    "installable" : True,
    "active" : False,
}
