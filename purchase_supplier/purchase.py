# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2012 Vauxoo - http://www.vauxoo.com/
#    All Rights Reserved.
#    info Vauxoo (info@vauxoo.com)
############################################################################
#    Coded by: moylop260 (moylop260@vauxoo.com)
#              Isaac Lopez (isaac@vauxoo.com)
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

import time
import netsvc
from osv import fields, osv
from mx import DateTime
from tools import config
from tools.translate import _

class purchase_order(osv.osv):
    _inherit = "purchase.order"
    
    def wkf_confirm_order(self, cr, uid, ids, context = None):
        product_supp_obj = self.pool.get('product.supplierinfo')
        company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id

        if super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context = context):
            for po in self.browse(cr, uid, ids, context = context):
                partner_id = po.partner_id.id
                for line in po.order_line:
                    product_id = line.product_id.id
                    #~ print 'y sus lineas de producto',line.product_id.id,'el producto es',line.product_id.name
                    if not product_supp_obj.search(cr, uid, [('product_id', '=', product_id), ('name', '=', partner_id)]):
                        #~ print '-------el supplier no existe, se va agregar'
                        product_supp_obj.create(cr, uid, {'name': partner_id, 'min_qty': 1.0, 'delay': 1, 'sequence': 10, 'product_id': product_id, 'company_id': company_id})
                    #~ product_obj.write(cr, uid,[product_id], {'seller_ids': partner_id})
                    
            return True
        else:
            return False

purchase_order()
