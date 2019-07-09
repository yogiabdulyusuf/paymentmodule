import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError


class ReportSaleDetails(models.AbstractModel):
    _name = 'report.paymentmodule.report_requestdetails'


    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, transaction=False, billing=False):
        """ Serialise the orders of the day information
        params: date_start, date_stop string representing the datetime of order
        """

        if billing == 'billing_non_billing':
            billing_status = ''
            operator = '!='
        else:
            billing_status = billing
            operator = '='

        transstikers = self.env['request.transstiker'].search([
            ('tanggal', '>=', date_start),
            ('tanggal', '<=', date_stop), ('state', '=', transaction), ('cara_bayar', operator, billing_status)])

        transstiker_datas = []

        for stiker in transstikers:
            vals = {}
            vals.update({'notrans' : stiker.notrans})
            vals.update({'unit_kerja' : stiker.unit_kerja.kode})
            vals.update({'name' : stiker.name})
            vals.update({'tanggal' : stiker.tanggal})
            vals.update({'cara_bayar' : stiker.cara_bayar})
            if stiker.baru:
                vals.update({'start_date' : stiker.awal})
                vals.update({'end_date' : stiker.akhir})
                vals.update({'duration' : stiker.duration})
                vals.update({'nopol' : stiker.nopol})
            else:
                vals.update({'start_date': ''})
                vals.update({'end_date': ''})
                vals.update({'duration':''})
                vals.update({'nopol': ''})

            vals.update({'state': stiker.state})
            vals.update({'val_harga' : stiker.val_harga})
            vals.update({'harga_beli_stiker' : stiker.harga_beli_stiker})
            vals.update({'harga_kartu_hilang' : stiker.harga_kartu_hilang})
            vals.update({'harga_ganti_nopol' : stiker.harga_ganti_nopol})
            vals.update({'amount' : stiker.amount})

            transstiker_datas.append(vals)


        return {
            "transstikers" : transstiker_datas
        }

    @api.multi
    def render_html(self, docids, data=None):
        data = dict(data or {})
        data.update(self.get_sale_details(data['date_start'], data['date_stop'],data['transaction'],data['billing']))
        return self.env['report'].render('paymentmodule.report_requestdetails', data)



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