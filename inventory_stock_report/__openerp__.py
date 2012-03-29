#!/usr/bin/python
# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) Vauxoo (<http://vauxoo.com>).
#    All Rights Reserved
###############Credits######################################################
#    Coded by: Vauxoo C.A.           
#    Planified by: Nhomar Hernandez
#    Audited by: Vauxoo C.A.
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

{
    "name" : "l10n-co-stock-count"                                  ,
    "version" : "0.1"                                               ,
    "depends" : ['base'                                             ,
                 'stock'                                            ,
                 'product'                                          ,
                ]                                                   ,
    "author" : "Vauxoo"                                  ,
    "description" : """
                - Reporte de la Hoja de Conteo de Inventario.
                - Reporte del Total de Invenatrio.
                    """                                             ,
    "website" : "http://wiki.openerp.org.ve/"                       ,
    "category" : "Generic Modules"                                  ,
    "init_xml" : [
    ]                                                               ,
    "demo_xml" : [
    ]                                                               ,
    "update_xml" : [
                'stock_report.xml'                           ,  
                'wizard/stock_count_view.xml'                           ,  
                'wizard/stock_qty_view.xml'                       ,
                
    ]                                                               ,
    "active": False                                                 ,
    "installable": True                                             ,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
