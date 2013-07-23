#!/usr/bin/python
# -*- encoding: utf-8 -*-
###############################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
############# Credits #########################################################
#    Coded by: Katherine Zaoral          <kathy@vauxoo.com>
#    Planified by: Humberto Arocha       <hbto@vauxoo.com>
#    Audited by: Humberto Arocha         <hbto@vauxoo.com>
###############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################
import time
from openerp.osv import fields, osv
from openerp import netsvc
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class hr_expense_expense(osv.Model):
    _inherit = "hr.expense.expense"

    def _amount(self, cr, uid, ids, field_name, arg, context=None):
        """ Overwrite method to add the sum of the invoices total amount
        (Sub total + tax amount ). """
        context = context or {}
        cur_obj = self.pool.get('res.currency')
        res = super(hr_expense_expense, self)._amount(
            cr, uid, ids, field_name, arg, context=context)
        acc_payable_ids = self.pool.get('account.account').search(
            cr, uid, [('type', '=', 'payable')], context=context)
        for expense in self.browse(cr, uid, res.keys(), context=context):
            for invoice in expense.invoice_ids:
                if invoice.move_id:
                    res[expense.id] += \
                        sum([aml.credit
                             for aml in invoice.move_id.line_id
                             if aml.account_id in acc_payable_ids])
                else:
                    res[expense.id] += cur_obj.exchange(
                        cr, uid, [],
                        from_amount=invoice.amount_total,
                        to_currency_id=expense.currency_id.id,
                        from_currency_id=invoice.currency_id.id,
                        exchange_date=invoice.date_due,
                        context=context)
        return res

    def _get_exp_from_invoice(self, cr, uid, ids, context=None):
        """ Return expense ids related to invoices that have been changed."""
        context = context or {}
        ai_obj = self.pool.get('account.invoice')
        inv_ids = ids
        exp_ids = list(set(
            [inv_brw.expense_id.id
             for inv_brw in ai_obj.browse(cr, uid, inv_ids, context=context)]))
        return exp_ids

    def _get_ail_ids(self, cr, uid, ids, field_name, arg, context=None):
        """ Returns list of invoice lines of the invoices related to the
        expense. """
        context = context or {}
        res = {}
        for exp in self.browse(cr, uid, ids, context=context):
            ail_ids = []
            for inv_brw in self.browse(
                    cr, uid, exp.id, context=context).invoice_ids:
                ail_ids.extend([line.id for line in inv_brw.invoice_line])
            res[exp.id] = ail_ids
        return res

    _columns = {
        'invoice_ids': fields.one2many('account.invoice', 'expense_id',
                                       'Invoices', help=''),
        'ail_ids': fields.function(_get_ail_ids,
                                   type="one2many",
                                   relation='account.invoice.line',
                                   string='Invoices lines',
                                   help='Deductible Expense'),
        'amount': fields.function(
            _amount,
            string='Total Amount',
            digits_compute=dp.get_precision('Account'),
            store={
                'hr.expense.expense': (lambda self, cr, uid, ids, c={}: ids,
                                       None, 50),
                'account.invoice': (_get_exp_from_invoice, None, 50)
            }),
        'advance_ids': fields.many2many(
            'account.move.line', 'expense_advance_rel',
            'expense_id', 'aml_id', string='Employee Advances',
            help="Advances associated to the expense employee."),
        'payment_ids': fields.related(
            'account_move_id', 'line_id',
            type='one2many',
            relation='account.move.line',
            string=_('Expense Payments'),
            help=_('This table is a summary of the payments done to reconcile '
                   'the expense invoices, lines and advances. This is an only '
                   'read field that is set up once the expence reconciliation '
                   'is done (when user click the Reconcile button at the '
                   'Waiting Payment expense state.')),
        'skip': fields.boolean(
            string='This expense has not advances',
            help=_('Active this checkbox to allow leave the expense without '
                   'advances (This will create write off a journal entry when '
                   'reconciling). If this is not what you want please create '
                   'and advance for the expense employee and use the Refresh '
                   'button to associated to this expense')),
        'ait_ids': fields.related(
            #~ _get_ait_ids,
            'invoice_ids', 'tax_line',
            type="one2many",
            relation='account.invoice.tax',
            string=_('Deductible Tax Lines'),
            help=_('This are the account invoice taxes loaded into the '
                   'Expense invoices. The user can\'t change its content and '
                   'not have to worry about to fill the field. This taxes '
                   'will be auto update when the expense invoices change.\n\n'
                   'This invoices changes includes:\n - when a tax is added '
                   'or removed from an invoice line,\n - when an invoice line '
                   'is deleted from an invoice,\n - when the invoice is '
                   'unlinked to the expense.')),
        'state': fields.selection([
            ('draft', 'New'),
            ('cancelled', 'Refused'),
            ('confirm', 'Waiting Approval'),
            ('accepted', 'Approved'),
            ('done', 'Waiting Payment'),
            ('process', 'Processing Payment'),
            ('deduction', 'Processing Deduction'),
            ('paid', 'Paid')
            ],
            'Status', readonly=True, track_visibility='onchange',
            help=_('When the expense request is created the status is '
            '\'Draft\'.\n It is confirmed by the user and request is sent to '
            'admin, the status is \'Waiting Confirmation\'.\ \nIf the admin '
            'accepts it, the status is \'Accepted\'.\n If the accounting '
            'entries are made for the expense request, the status is '
            '\'Waiting Payment\'.')),
    }

    def onchange_no_danvace_option(self, cr, uid, ids, skip, context=None):
        """
        Clean up the expense advances when the No advances checkbox is set
        """
        context = context or {}
        res = {'value': {}}
        if skip:
            res['value'] = {'advance_ids': []}
        else:
            self.load_advances(cr, uid, ids, context=context)
            res['value'] = {'advance_ids':
               [advn.id
                for advn in self.browse(
                    cr, uid, ids[0], context=context).advance_ids]
            }
        return res

    def expense_confirm(self, cr, uid, ids, context=None):
        """ Overwrite the expense_confirm method to validate that the expense
        have expenses lines before sending to Manager."""
        context = context or {}
        for exp in self.browse(cr, uid, ids, context=context):
            if not exp.invoice_ids and not exp.line_ids:
                raise osv.except_osv(
                    _('Invalid Procedure'),
                    _('You have not Deductible or No Deductible lines loaded '
                      'into the expense'))
            super(hr_expense_expense, self).expense_confirm(
                cr, uid, ids, context=context)
        return True

    def action_receipt_create(self, cr, uid, ids, context=None):
        """ overwirte the method """
        context = context or {}
        am_obj = self.pool.get('account.move')
        self.check_expense_invoices(cr, uid, ids, context=context)
        super(hr_expense_expense, self).action_receipt_create(
            cr, uid, ids, context=context)
        return True

    def load_advances(self, cr, uid, ids, context=None):
        """ Load the expense advances table with the corresponding data. Adds
        account move lines that fulfill the following conditions:
            - Not reconciled.
            - Not partially reconciled.
            - Account associated of type payable.
            - That belongs to the expense employee or to the expense invoices
              partners.
        """
        context = context or {}
        aml_obj = self.pool.get('account.move.line')
        acc_payable_ids = self.pool.get('account.account').search(
            cr, uid, [('type', '=', 'payable')], context=context)
        for exp in self.browse(cr, uid, ids, context=context):
            partner_ids = [exp.employee_id.address_home_id.id]
            aml_ids = aml_obj.search(
                cr, uid,
                [('reconcile_id', '=', False),
                 ('reconcile_partial_id', '=', False),
                 ('account_id', 'in', acc_payable_ids),
                 ('partner_id', 'in', partner_ids),
                 ('debit', '>', 0.0),
                 ], context=context)
            vals = {}
            cr.execute(('SELECT aml_id FROM expense_advance_rel '
                        'WHERE expense_id != %s'), (exp.id,))
            already_use_aml = cr.fetchall()
            already_use_aml = map(lambda x: x[0], already_use_aml)
            aml_ids = list(set(aml_ids) - set(already_use_aml))
            vals['advance_ids'] = \
                [(6, 0, aml_ids)]
            self.write(cr, uid, exp.id, vals, context=context)
        return True

    def order_payments(self, cr, uid, ids, aml_ids, context=None):
        """ orders the payments lines by partner id. Recive only one id"""
        context = context or {}
        aml_obj = self.pool.get('account.move.line')
        exp = self.browse(cr, uid, ids, context=context)
        order_partner = list(set(
            [(payment.partner_id.name, payment.partner_id.id, payment.id)
             for payment in exp.advance_ids]))
        order_partner.sort()
        order_payments = [item[-1] for item in order_partner]
        return order_payments

    def group_aml_inv_ids_by_partner(self, cr, uid, aml_inv_ids,
                                     context=None):
        """
        Return a list o with sub lists of invoice ids grouped for partners.
        @param aml_inv_ids: list of invoices account move lines ids to order.
        """
        context = context or {}
        aml_obj = self.pool.get('account.move.line')
        inv_by = dict()
        for line in aml_obj.browse(cr, uid, aml_inv_ids, context=context):
            inv_by[line.partner_id.id] = \
                inv_by.get(line.partner_id.id, False) and \
                inv_by[line.partner_id.id] + [line.id] or \
                [line.id]
        return inv_by.values()

    def payment_reconcile(self, cr, uid, ids, context=None):
        """ It reconcile the expense advance and expense invoice account move
        lines.
        """
        context = context or {}
        aml_obj = self.pool.get('account.move.line')
        for exp in self.browse(cr, uid, ids, context=context):
            self.check_advance_no_empty_condition(cr, uid, exp.id,
                                                  context=context)
            #~ clear empty expense move.
            exp_credit = \
                [brw.id
                 for brw in exp.account_move_id.line_id
                 if brw.credit > 0.0]
            if not exp_credit:
                empty_aml_ids = [brw.id for brw in exp.account_move_id.line_id]
                aml_obj.unlink(cr, uid, empty_aml_ids, context=context)

            #~ manage the expense move lines
            exp_aml_brws = exp.account_move_id and \
                [aml_brw
                 for aml_brw in exp.account_move_id.line_id
                 if aml_brw.account_id.type == 'payable'] or []
            advance_aml_brws = [aml_brw
                                for aml_brw in exp.advance_ids
                                if aml_brw.account_id.type == 'payable']
            inv_aml_brws = [aml_brw
                            for inv in exp.invoice_ids
                            for aml_brw in inv.move_id.line_id
                            if aml_brw.account_id.type == 'payable']
            aml = {
                'exp':
                exp_aml_brws and [aml_brw.id for aml_brw in exp_aml_brws]
                or [],
                'advances': [aml_brw.id for aml_brw in advance_aml_brws],
                'invs': [aml_brw.id for aml_brw in inv_aml_brws],
                #~ self.group_aml_inv_ids_by_partner(
                #~ cr, uid, [aml_brw.id for aml_brw in inv_aml_brws],
                #~ context=context),
                'debit':
                sum([aml_brw.debit
                     for aml_brw in advance_aml_brws]),
                'credit':
                sum([aml_brw.credit
                     for aml_brw in exp_aml_brws + inv_aml_brws])
            }

            aml_amount = aml['debit'] - aml['credit']
            adjust_balance_to = aml_amount > 0.0 and 'debit' or \
            aml_amount < 0.0 and 'credit' or 'liquidate'

            #~ create and reconcile invoice move lines
            aml['invs'] and self.create_and_reconcile_invoice_lines(
                cr, uid, exp.id, aml['invs'],
                adjust_balance_to=adjust_balance_to, context=context)

            #~ reconcile partial with advance
            self.expense_reconcile_partial(cr, uid, exp.id, context=context)

            #~ change expense state
            if adjust_balance_to == 'debit':
                self.write(cr, uid, exp.id, {'state': 'deduction'},
                context=context)
            elif adjust_balance_to == 'credit':
                self.write(cr, uid, exp.id, {'state': 'process'},
                context=context)
            elif adjust_balance_to == 'liquidate':
                self.expense_reconcile(cr, uid, exp.id, context=context)
                raise osv.except_osv("ERROR",
                                     "This option is not completed implemented yet")
                self.write(cr, uid, exp.id, {'state': 'paid'}, context=context)
        return True

    def expense_reconcile_partial(self, cr, uid, ids, context=None):
        """
        make a partial reconciliation between invoices debit and advances
        credit.
        """
        context = context or {}
        aml_obj = self.pool.get('account.move.line')
        ids = isinstance(ids, (int,long)) and [ids] or ids
        for exp in self.browse(cr, uid, ids, context=context):
            exp_debit_lines = [aml.id for aml in exp.advance_ids]
            exp_credit_lines = [aml.id
                                for aml in exp.account_move_id
                                if aml.credit > 0.0]

            #~ print '\n'*3
            #~ print 'exp_debit_lines', exp_debit_lines
            #~ print 'exp_credit_lines', exp_credit_lines
            #~ for item in aml_obj.browse(cr, uid, exp_debit_lines + exp_credit_lines, context=context):
                #~ print (item.id, item.debit, item.credit, item.name)
            #~ print '\n'*3
            #~ raise osv.except_osv('testing', 'check console')

            aml_obj.reconcile_partial(cr, uid,
                exp_debit_lines + exp_credit_lines, 'manual',
                context=context)
        return True

    def expense_reconcile(self, cr, uid, ids, context=None):
        """
        When expense debit and credit are equal.
        """
        context = context or {}
        aml_obj = self.pool.get('account.move.line')
        ids = isinstance(ids, (int,long)) and [ids] or ids
        for exp in self.browse(cr, uid, ids, context=context):
            exp_debit_lines = [aml.id for aml in exp.advance_ids]
            exp_credit_lines = [aml.id
                                for aml in exp.account_move_id
                                if aml.credit > 0.0]
            aml_obj.reconcile(cr, uid, exp_debit_lines + exp_credit_lines,
                          'manual', context=context)
        return True

    def check_advance_no_empty_condition(self, cr, uid, ids, context=None):
        """
        Check if the Expense have not advances and force him to active the
        checkbox for allow leave the advances empty and leave the user now
        the repercussions of this configuration.
        """
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for exp in self.browse(cr, uid, ids, context=context):
            if exp.advance_ids and not exp.skip:
                pass
            elif exp.advance_ids and exp.skip:
                raise osv.except_osv(
                    _('Invalid Procedure!'),
                    _('Integrity Problem. You have advances for this expense '
                      'but in same time you active the No advances option. '
                      'Please uncheck the No advances option or clean the '
                      'advances table instead.'))
            elif not exp.advance_ids and not exp.skip:
                raise osv.except_osv(
                    _('Invalid Procedure!'),
                    _('You have leave the expense advances empty (Renconcile '
                      'the Expense will cause a Write Off journal entry). If '
                      'this is your purpose its required to check the This '
                      'expense has not advances checkbox into the expense '
                      'advances page. If not, please create some advances for '
                      'the employee and Refresh the expense advance lines '
                      'with the expense advance page refresh button.'))
            elif not exp.advance_ids and exp.skip:
                #~ reconciling the expense withhout advances
                pass
        return True

    def create_and_reconcile_invoice_lines(self, cr, uid, ids, inv_aml_ids,
                               adjust_balance_to, context=None):
        """
        Create the account move lines to balance the expense invoices and
        reconcile them with the original invoice move lines.
        @param inv_aml_ids: list of expense invoices move line ids.
        @param adjust_balance_to: indicates who is greater credit or debit.
        """
        context = context or {}
        aml_obj = self.pool.get('account.move.line')

        ids = isinstance(ids, (int, long)) and [ids] or ids
        for exp in self.browse(cr, uid, ids, context=context):
            #~ create invoice move lines.
            inv_match_pair = self.create_reconcile_move_lines(
                cr, uid, exp.id,
                am_id=exp.account_move_id.id,
                aml_ids=inv_aml_ids,
                line_type='invoice',
                adjust_balance_to=adjust_balance_to,
                context=context)
            # make reconcilation.
            for line_pair in inv_match_pair:
                aml_obj.reconcile(
                    cr, uid, list(line_pair), 'manual', context=context)
        return True

    def create_reconcile_move_lines(self, cr, uid, ids, am_id, aml_ids,
                                    advance_amount=False, line_type=None,
                                    adjust_balance_to=None, context=None):
        """
        Create new move lines to match to the expense. recieve only one id
        @param aml_ids: acc.move.line list of ids
        @param am_id: account move id
        """
        context = context or {}
        res = []
        aml_obj = self.pool.get('account.move.line')
        exp = self.browse(cr, uid, ids, context=context)
        vals = {}.fromkeys(['partner_id', 'debit', 'credit',
                           'name', 'move_id', 'account_id'])
        vals['move_id'] = am_id
        no_advance_account = \
            exp.employee_id.address_home_id.property_account_payable.id
        vals['journal_id'] = exp.journal_id
        vals['period_id'] = self.pool.get('account.period').find(
            cr, uid, context=context)[0]
        vals['date'] = time.strftime('%Y-%m-%d')

        advance_name = {
            'debit_line':
                adjust_balance_to == 'debit' and _('(Remaining Advance)')
                or _('(Reconciliation)'),
            'credit_line':
                adjust_balance_to == 'debit' and _('(Applyed Advance)')
                or _('(Debt to employee)'),
        }

        for aml_id in aml_ids:
            aml_brw = aml_id \
                and aml_obj.browse(cr, uid, aml_id, context=context) \
                or False
            #~ DEBIT LINE
            debit_vals = vals.copy()
            debit_vals.update({
                'partner_id': line_type == 'advance' and
                    exp.employee_id.address_home_id.id or
                    aml_brw.partner_id.id,
                'debit':
                    line_type == 'advance' and advance_amount or
                    aml_brw.credit,
                'credit': 0.0,
                'name':
                    line_type == 'invoice' and _('Payable to Partner')
                    or _('Payable to Employee') + (line_type == 'advance' and ' ' +
                    advance_name['debit_line'] or ''),
                'account_id':
                    aml_brw and aml_brw.account_id.id
                    or adjust_balance_to in ['no-advance']
                    and no_advance_account or False,
            })
            debit_id = aml_obj.create(cr, uid, debit_vals, context=context)
            #~ CREDIT LINE
            credit_vals = vals.copy()
            credit_vals.update({
                'partner_id': exp.employee_id.address_home_id.id,
                'debit': 0.0,
                'credit':
                    line_type == 'advance' and advance_amount
                    or aml_brw.credit,
                'name':
                    _('Payable to Employee') + (line_type == 'advance'
                        and ' ' + advance_name['credit_line'] or ''),
                'account_id':
                    aml_brw and aml_brw.account_id.id
                    or adjust_balance_to in ['no-advance']
                    and no_advance_account or False,
            })
            credit_id = aml_obj.create(cr, uid, credit_vals, context=context)

            if line_type in ['invoice']:
                res.append((aml_brw.id, debit_id))
            elif line_type in ['advance']:
                match_id = adjust_balance_to == 'debit' and credit_id \
                    or debit_id
                res.extend([aml_brw.id, match_id])
        return res

    def check_expense_invoices(self, cr, uid, ids, context=None):
        """ Overwrite the expense_accept method to add the validate
        invoice process """
        context = context or {}
        error_msj = str()
        for exp_brw in self.browse(cr, uid, ids, context=context):
            bad_invs = [inv_brw
                        for inv_brw in exp_brw.invoice_ids
                        if inv_brw.state not in ['open']]

            if bad_invs:
                for inv_brw in bad_invs:
                    error_msj = error_msj + \
                        '- ' + (inv_brw.number or inv_brw.partner_id.name) + \
                        ' Invoice total ' + str(inv_brw.amount_total) + ' (' \
                        + inv_brw.state.capitalize() + ')\n'

        if error_msj:
            raise osv.except_osv(
                _('Invalid Procedure'),
                _('The expense invoices need to be validated. After manually '
                  'check invoices you can validate all invoices in batch by '
                  'using the Validate Invoices button. \n Invoices to '
                  'Validate:\n')
                + error_msj)
        return True

    def validate_expense_invoices(self, cr, uid, ids, context=None):
        """ Validate Invoices asociated to the Expense. Put the invoices in
        Open State. """
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        wf_service = netsvc.LocalService("workflow")
        for exp_brw in self.browse(cr, uid, ids, context=context):
            validate_inv_ids = \
                [inv_brw.id
                 for inv_brw in exp_brw.invoice_ids
                 if inv_brw.state == 'draft']
            for inv_id in validate_inv_ids:
                wf_service.trg_validate(uid, 'account.invoice', inv_id,
                                        'invoice_open', cr)
        return True

    def generate_accounting_entries(self, cr, uid, ids, context=None):
        """ Active the workflow signals to change the expense to Done state
        and generate accounting entries for the expense by clicking the
        'Generate Accounting Entries' button. """
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        wf_service = netsvc.LocalService("workflow")
        for exp_brw in self.browse(cr, uid, ids, context=context):
            if exp_brw.state not in ['done']:
                wf_service.trg_validate(uid, 'hr.expense.expense', exp_brw.id,
                                        'confirm', cr)
                wf_service.trg_validate(uid, 'hr.expense.expense', exp_brw.id,
                                        'validate', cr)
                wf_service.trg_validate(uid, 'hr.expense.expense', exp_brw.id,
                                        'done', cr)
        return True

    def expense_pay(self, cr, uid, ids, context=None):
        """
        Expense credit is greater than the expense debit. That means that the
        expense have no advances or the total advances amount dont fullfill the
        payment. So now we create a account voucher to pay the employee the
        missing expense amount.
        """
        context = context or {}
        raise osv.except_osv ("Warning DUMMY method", "No yet implemented")

        #~ TODO: make the automatic the voucher linked to the no reconciled
        #~ expense move line

        #~ create account.voucher for employee (credits)
        #~ vals = {
            #~ 'move_line_id': av_aml,
        #~ }
        #~ voucher_line_id = self.pool.get('account.voucher.line').create(cr, uid, vals, context=context)
        #~ print 'i am about to create the voucher'

        #~ vals = {
            #~ 'partner_id': exp.account_move_id.partner_id.id,
            #~ 'amount': abs(aml['debit']-aml['credit']),
            #~ 'account_id': aml.account_id,
            #~ 'line_cr_ids': [voucher_line_id]
        #~ }
        #~ print 'i am about to create the voucher rigth now'
        #~ voucher_id = av_obj.create(cr, uid, vals, context=context)
        #~ print 'i create the voucher successfully'
        #~ print 'voucher_id', voucher_id

        return True

    def expense_deduction(self, cr, uid, ids, context=None):
        """
        Expense debit is greater than the expense credit. That means that the
        expense have advances and they fullfill the payment. So now is time
        to reconcile expense payable move lines with the expense advances.
        """
        context = context or {}
        aml_obj = self.pool.get('account.move.line')
        for exp in self.browse(cr, uid, ids, context=context):
            debit = sum([aml.debit for aml in exp.advance_ids])
            credit = sum([aml.credit
                          for aml in exp.account_move_id.line_id
                          if aml.credit > 0.0])
            credit_aml_ids = [aml.id
                              for aml in exp.account_move_id.line_id
                              if aml.credit > 0.0]
            debit_aml_ids = [aml.id for aml in exp.advance_ids]
            advance_match_pair = \
                self.create_reconcile_move_lines(
                    cr, uid, exp.id,
                    am_id=exp.account_move_id.id,
                    aml_ids=debit_aml_ids,
                    advance_amount=debit-credit,
                    line_type='advance',
                    adjust_balance_to='debit',
                    context=context)
            reconcile_list = advance_match_pair + credit_aml_ids

            #~ print '\n'*3
            #~ print 'reconcile_list', reconcile_list 
            #~ for item in aml_obj.browse(cr, uid, reconcile_list, context=context):
                #~ print (item.id, item.debit, item.credit, item.name)
            #~ print '\n'*3
            #~ raise osv.except_osv('testing', 'check console')

            aml_obj.reconcile(cr, uid, reconcile_list, 'manual',
                              context=context)
            self.write(cr, uid, exp.id, {'state': 'paid'}, context=context)
        return True

    def create_match_move(self, cr, uid, ids, context=None):
        """ Create new account move that containg the data of the expsense
        account move created and expense invoices moves. Receives only one
        id """
        context = context or {}
        am_obj = self.pool.get('account.move')
        exp_brw = self.browse(cr, uid, ids, context=context)
        vals = dict()
        vals['ref'] = 'Pago de Viaticos'
        vals['journal_id'] = self.get_purchase_journal_id(
            cr, uid, context=context)
        debit_lines = self.create_debit_lines_dict(
            cr, uid, exp_brw.id, context=context)

        print '\n'*5
        print 'exp_brw', exp_brw
        print 'exp_brw.account_move_id', exp_brw.account_move_id
        print 'exp.move.partner_id', exp_brw.account_move_id.partner_id
        credit_line = [
            (0, 0, {
             'name': 'Pago de Viaticos',
             'account_id': self.get_payable_account_id(
                 cr, uid, context=context),
             'partner_id': exp_brw.account_move_id.partner_id.id,
             'debit': 0.0,
             'credit': self.get_lines_credit_amount(
                 cr, uid, exp_brw.account_move_id.id, context=context)
             })
            #~ TODO: I think may to change this acocunt_id
        ]
        vals['line_id'] = debit_lines + credit_line
        return am_obj.create(cr, uid, vals, context=context)

    def create_debit_lines_dict(self, cr, uid, ids, context=None):
        """ Returns a list of dictionarys for create account move
        lines objects. Only recive one exp id """
        context = context or {}
        debit_lines = []
        am_obj = self.pool.get('account.move')
        exp_brw = self.browse(cr, uid, ids, context=context)
        move_ids = [inv_brw.move_id.id
                    for inv_brw in exp_brw.invoice_ids
                    if inv_brw.move_id]
        for inv_move_brw in am_obj.browse(cr, uid, move_ids, context=context):
            debit_lines.append(
                (0, 0, {
                 'name': 'Pago de Viaticos',
                 'account_id': self.get_payable_account_id(
                     cr, uid, context=context),
                 'partner_id': inv_move_brw.partner_id.id,
                 'invoice': inv_move_brw.line_id[0].invoice.id,
                 'debit':  self.get_lines_credit_amount(
                     cr, uid, inv_move_brw.id, context=context),
                 'credit': 0.0})
            )
            #~ TODO: invoice field is have not been set, check why
        return debit_lines

    def get_lines_credit_amount(self, cr, uid, move_id, context=None):
        """ Return the credit amount (float value) of the account move given.
        @param move_id: list of move id where the credit will be extract """
        context = context or {}
        am_obj = self.pool.get('account.move')
        move_brw = am_obj.browse(cr, uid, move_id, context=context)
        amount = [move_line.credit
                  for move_line in move_brw.line_id
                  if move_line.credit != 0.0]
        if not amount:
            raise osv.except_osv(
                'Invalid Procedure!',
                "There is a problem in your move definition " +
                move_brw.ref + ' ' + move_brw.name)
        return amount[0]

    def get_payable_account_id(self, cr, uid, context=None):
        """ Return the id of a payable account. """
        aa_obj = self.pool.get('account.account')
        return aa_obj.search(cr, uid, [('type', '=', 'payable')], limit=1,
                             context=context)[0]

    def get_purchase_journal_id(self, cr, uid, context=None):
        """ Return an journal id of type purchase. """
        context = context or {}
        aj_obj = self.pool.get('account.journal')
        return aj_obj.search(cr, uid, [('type', '=', 'purchase')], limit=1,
                             context=context)[0]
