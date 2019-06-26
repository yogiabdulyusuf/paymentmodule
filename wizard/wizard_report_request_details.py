# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class WizardReportRequestDetails(models.TransientModel):
    _name = 'wizard.report.request.details'
    _description = 'Open Sale Details Report'


    start_date = fields.Date(required=True, )
    end_date = fields.Date(required=True, )
    billing_status = fields.Selection(string="Billing Status", selection=[('billing', 'Billing'), ('non_billing', 'Non Billing'), ], required=False, default='billing')
    transaction_status = fields.Selection(string="Transaction Status", selection=[('done', 'Done'),('cancel', 'Cancel')], required=False, default='done')

    # @api.onchange('start_date')
    # def _onchange_start_date(self):
    #     if self.start_date and self.end_date and self.end_date < self.start_date:
    #         self.end_date = self.start_date
    #
    # @api.onchange('end_date')
    # def _onchange_end_date(self):
    #     if self.end_date and self.end_date < self.start_date:
    #         self.start_date = self.end_date

    @api.multi
    def generate_report(self):
        data = {
            'date_start': self.start_date,
            'date_stop': self.end_date,
            'billing': self.billing_status,
            'transaction': self.transaction_status,
        }
        return self.env['report'].get_action([], 'paymentmodule.report_requestdetails', data=data)
