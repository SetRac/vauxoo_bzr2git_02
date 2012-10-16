# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import fields, osv
from tools.translate import _
import decimal_precision as dp

class product_product(osv.osv):
    _inherit = "product.product"
    _columns = {
        'date_to': fields.dummy(string='Date To', type='datetime'),
        'date_from_to': fields.dummy(string='Date From-To', type='datetime'),
        'date_from': fields.dummy(string='Date From', type='datetime'),
    }

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        for lin in args:
            if len(lin) == 3:
                for field, operator, value in [tuple(lin)]:
                    if field == 'date_from_to':
                        if '>' in operator:
                            context['from_date']=value
                        if '<' in operator:
                            context['to_date']=value
        res = super(product_product, self).search(cr, user, args, offset=offset, limit=limit, order=order, context=context, count=count)
        return res
product_product()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
