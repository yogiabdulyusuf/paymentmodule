from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning


class WizardLoanBillingProcess(models.TransientModel):
    _name = 'wizard.loan.billing.process'

    billing_periode_id = fields.Many2one('billing.periode', 'Periode', required=True)
    billing_periode_line_id = fields.Many2one('billing.periode.line', 'Line', required=True)

    @api.one
    def process(self):
        loan_trans_line_obj = self.env['loan.trans.line']
        args = [('due_date','>=', self.billing_periode_line_id.start_date),('due_date','<=', self.billing_periode_line_id.end_date)]
        loan_trans_line_ids = loan_trans_line_obj.search(args)
        for loan_trans_line_id in loan_trans_line_ids:
            print "Create Invoice"
            print "Update Invoice line_trans_line_id"