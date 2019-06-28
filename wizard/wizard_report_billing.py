from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class WizardReportMonthlyBilling(models.TransientModel):
    _name = 'wizard.report.billing'
    _description = 'Monthly Report Billing'

    billing_periode_ids = fields.Many2one(comodel_name="billing.periode", string="Billing Periode", required=True,)


    @api.multi
    def generate_report(self):
        data = {
            'billing_periode_ids': self.billing_periode_ids.id,
        }

        # _logger.info('monthly report billing id : ',billing_periode_id)
        return self.env['report'].get_action([], 'paymentmodule.report_monthly_billing_template', data=data)
