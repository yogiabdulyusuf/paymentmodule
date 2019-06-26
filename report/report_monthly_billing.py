import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ReportMonthlyBilling(models.AbstractModel):
    _name = 'report.paymentmodule.report_monthly_billing_template'


    @api.model
    def get_sale_details(self, billing_periode_ids=False,):
        """ Serialise the orders of the day information
        params: date_start, date_stop string representing the datetime of order
        """

        monthlybilling = self.env['billing.periode'].search([
            ('id', '=', billing_periode_ids),])

        _logger.info(monthlybilling)

        monthlybilling_datas = []

        for billing in monthlybilling:

            for line in billing.line_ids:
                vals = {}
                vals.update({'unitno' : line.unitno})
                vals.update({'date_trans' : line.date_trans})
                vals.update({'description' : line.description})
                vals.update({'amount' : line.amount})

                monthlybilling_datas.append(vals)


        return {
            "monthlybilling" : monthlybilling_datas
        }

    @api.multi
    def render_html(self, docids, data=None):
        data = dict(data or {})
        data.update(self.get_sale_details(data['billing_periode_ids'],))
        return self.env['report'].render('paymentmodule.report_monthly_billing_template', data)



    # @api.model
    # def render_html(self, docids, data=None):
    #     self.model = self.env.context.get('active_model')
    #     docs = self.env[self.model].browse(self.env.context.get('active_id'))
    #     sales_records = []
    #     orders = self.env['sale.order'].search([('user_id', '=', docs.salesperson_id.id)])
    #     if docs.date_from and docs.date_to:
    #         for order in orders:
    #             if parse(docs.date_from) <= parse(order.date_order) and parse(docs.date_to) >= parse(order.date_order):
    #                 sales_records.append(order);
    #     else:
    #         raise UserError("Please enter duration")
    #
    #     docargs = {
    #         'doc_ids': self.ids,
    #         'doc_model': self.model,
    #         'docs': docs,
    #         'time': time,
    #         'orders': sales_records
    #     }
    #     return self.env['report'].render('sales_report.report_salesperson', docargs)