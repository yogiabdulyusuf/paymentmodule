from odoo import api, fields, models


class ReportSaleDetails(models.AbstractModel):

    _name = 'report.point_of_sale.report_saledetails'


    @api.model
    def get_sale_details(self, date_start=False, date_stop=False):
        """ Serialise the orders of the day information
        params: date_start, date_stop string representing the datetime of order
        """


        date_start = fields.Datetime.to_string(date_start)
        date_stop = fields.Datetime.to_string(date_stop)

        transstikers = self.env['request.transstiker'].search([
            ('tanggal', '>=', date_start),
            ('tanggal', '<=', date_stop),])

        transstiker_datas = []

        for stiker in transstikers:
            vals = {}
            vals.update({'notrans' : stiker.notrans})
            vals.update({'unit_kerja' : stiker.unit_kerja})
            vals.update({'no_id' : stiker.no_id})
            vals.update({'name' : stiker.name})
            vals.update({'tanggal' : stiker.tanggal})
            vals.update({'amount' : stiker.amount})

            transstiker_datas.append(vals)


        return {
            "transstikers" : transstiker_datas
        }

    @api.multi
    def render_html(self, docids, data=None):
        data = dict(data or {})
        data.update(self.get_sale_details(data['date_start'], data['date_stop'],))
        return self.env['report'].render('paymentmodule.report_requestdetails', data)