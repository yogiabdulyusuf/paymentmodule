from odoo import api, fields, models, _
from odoo.exceptions import UserError
import xlwt
from xlwt import easyxf
import logging

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.debug('Cannot `import xlwt`.')

try:
    from cStringIO import StringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')

try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')

_logger = logging.getLogger(__name__)


class WizardReportMonthlyBilling(models.TransientModel):
    _name = 'wizard.report.billing'
    _description = 'Monthly Report Billing'


    @api.model
    def get_billing_details(self):
        """ Serialise the orders of the day information
        params: date_start, date_stop string representing the datetime of order
        """

        monthlybilling = self.env['billing.periode'].search([
            ('id', '=', self.billing_periode_ids.id), ])

        _logger.info(monthlybilling)

        monthlybilling_datas = []

        for billing in monthlybilling:

            for line in billing.line_ids:
                vals = {}
                vals.update({'unitno': line.unitno})
                vals.update({'date_trans': line.date_trans})
                vals.update({'description': line.description})
                vals.update({'amount': line.amount})

                monthlybilling_datas.append(vals)

        return {
            "monthlybilling": monthlybilling_datas
        }


    billing_periode_ids = fields.Many2one(comodel_name="billing.periode", string="Billing Periode", required=True,)
    report_filename = fields.Char('Filename', size=100, readonly=True, default='BillingReport.xlsx')
    report_file = fields.Binary('File', readonly=True)
    report_printed = fields.Boolean('Report Printed', default=False, readonly=True)

    @api.multi
    def generate_report_excel(self):
        for wizard in self:

            fp = StringIO()
            workbook = xlsxwriter.Workbook(fp)
            column_heading_style = easyxf('font:height 200;font:bold True;')

            request_details = self.get_billing_details()
            worksheet = workbook.add_worksheet('Billing Report')
            worksheet.write(0, 0, _('UNIT #'))
            worksheet.write(0, 1, _('DATE'))
            worksheet.write(0, 2, _('DESCRIPTION'))
            worksheet.write(0, 3, _('AMOUNT'))
            row = 1
            for order in request_details['monthlybilling']:
                worksheet.write(row, 0, order['unitno'])
                worksheet.write(row, 1, order['date_trans'])
                worksheet.write(row, 2, order['description'])
                worksheet.write(row, 3, order['amount'])
                row += 1

            workbook.close()
            excel_file = base64.encodestring(fp.getvalue())
            wizard.report_file = excel_file
            wizard.report_printed = True
            fp.close()

            return {
                'view_mode': 'form',
                'res_id': wizard.id,
                'res_model': 'wizard.report.billing',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'target': 'new',
            }


    @api.multi
    def generate_report(self):
        data = {
            'billing_periode_ids': self.billing_periode_ids.id,
        }

        # _logger.info('monthly report billing id : ',billing_periode_id)
        return self.env['report'].get_action([], 'paymentmodule.report_monthly_billing_template', data=data)
