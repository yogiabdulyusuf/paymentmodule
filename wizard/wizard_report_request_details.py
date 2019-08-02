from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import *
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


class WizardReportRequestDetails(models.TransientModel):
    _name = 'wizard.report.request.details'
    _description = 'Open Sale Details Report'

    @api.model
    def get_request_details(self):
        """ Serialise the orders of the day information
        params: date_start, date_stop string representing the datetime of order
        """
        args = []
        args.append((('tanggal', '>=', self.start_date)))
        args.append((('tanggal', '<=', self.end_date)))

        if self.billing_status == 'billing':
            args.append((('cara_bayar', '=', self.billing_status)))
        elif self.billing_status == 'non_billing':
            args.append((('cara_bayar', '=', self.billing_status)))

        if self.transaction_status == 'done':
            args.append((('state', '=', self.transaction_status)))
        elif self.transaction_status == 'payment':
            args.append((('state', '=', self.transaction_status)))
        elif self.transaction_status == 'cancel':
            args.append((('state', '=', self.transaction_status)))

        if self.jenis_member == '1st':
            args.append((('jenis_member', '=', self.jenis_member)))
        elif self.jenis_member == '2nd':
            args.append((('jenis_member', '!=', '1st')))



        #args = [('tanggal', '>=', self.start_date),('tanggal', '<=', self.end_date), ('state', '=', self.transaction_status), ('cara_bayar', operator, billing_status)]

        transstikers = self.env['request.transstiker'].sudo().search(args)

        # _logger.info(transstikers)

        transstiker_datas = []

        for stiker in transstikers:
            vals = {}
            vals.update({'notrans': stiker.notrans})
            vals.update({'unit_kerja': stiker.unit_kerja.kode})
            vals.update({'name': stiker.name})
            vals.update({'tanggal': stiker.tanggal})
            vals.update({'cara_bayar': stiker.cara_bayar})
            if stiker.jenis_transaksi == 'stop':
                vals.update({'jenis_transaksi': 'stop_billing'})
            else:
                vals.update({'jenis_transaksi': stiker.jenis_transaksi})
            if stiker.baru:
                if stiker.awal:
                    awal = datetime.strptime(stiker.awal, "%Y-%m-%d %H:%M:%S") + relativedelta(hours=7)
                    vals.update({'start_date': awal.strftime("%Y-%m-%d %H:%M:%S")})
                else:
                    vals.update({'start_date': False})

                if stiker.akhir:
                    akhir = datetime.strptime(stiker.akhir, "%Y-%m-%d %H:%M:%S") + relativedelta(hours=7)
                    vals.update({'end_date': akhir.strftime("%Y-%m-%d %H:%M:%S")})
                else:
                    vals.update({'end_date': False})
                vals.update({'duration': stiker.duration})
                vals.update({'nopol': stiker.nopol})
            else:
                vals.update({'start_date': ''})
                vals.update({'end_date': ''})
                vals.update({'duration': ''})
                vals.update({'nopol': ''})

            vals.update({'state': stiker.state})
            vals.update({'val_harga': stiker.val_harga})
            vals.update({'harga_beli_stiker': stiker.harga_beli_stiker})
            vals.update({'harga_kartu_hilang': stiker.harga_kartu_hilang})
            vals.update({'harga_ganti_nopol': stiker.harga_ganti_nopol})
            vals.update({'amount': stiker.amount})

            transstiker_datas.append(vals)

        return {
            "transstikers": transstiker_datas
        }

    start_date = fields.Date(required=True, )
    end_date = fields.Date(required=True, )
    billing_status = fields.Selection(string="Billing Status", selection=[('billing', 'Billing'), ('non_billing', 'Non Billing'), ('billing_non_billing', 'Billing & Non Billing'), ], required=False, default='billing')
    transaction_status = fields.Selection(string="Transaction Status", selection=[('done', 'Done'),('payment', 'Waiting for Payment'),('cancel', 'Cancel')], required=False, default='done')
    jenis_member = fields.Selection(string="Mobil ke", selection=[('1st', '1st'), ('2nd', '>= 2nd') ], required=False, readonly=False)
    report_filename = fields.Char('Filename', size=100, readonly=True, default='ReportTransaction.xlsx')
    report_file = fields.Binary('File', readonly=True)
    report_printed = fields.Boolean('Report Printed', default=False, readonly=True)

    @api.multi
    def generate_report_excel(self):
        for wizard in self:

            fp = StringIO()
            workbook = xlsxwriter.Workbook(fp)
            column_heading_style = easyxf('font:height 200;font:bold True;')

            request_details = self.get_request_details()
            worksheet = workbook.add_worksheet('Request Details')
            worksheet.write(0, 0, _('ID #'))
            worksheet.write(0, 1, _('UNIT'))
            worksheet.write(0, 2, _('NAMA'))
            worksheet.write(0, 3, _('TANGGAL'))
            worksheet.write(0, 4, _('BILLING STATUS'))
            worksheet.write(0, 5, _('JENIS TRANSAKSI'))
            worksheet.write(0, 6, _('START DATE'))
            worksheet.write(0, 7, _('END DATE'))
            worksheet.write(0, 8, _('DURASI'))
            worksheet.write(0, 9, _('NOPOL'))
            worksheet.write(0, 10, _('STATUS'))
            worksheet.write(0, 11, _('HARGA KONTRIBUSI'))
            worksheet.write(0, 12, _('HARGA STIKER'))
            worksheet.write(0, 13, _('HARGA KARTU PARKIR'))
            worksheet.write(0, 14, _('HARGA GANTI NOPOL'))
            worksheet.write(0, 15, _('TOTAL'))
            row = 1
            for order in request_details['transstikers']:
                worksheet.write(row, 0, order['notrans'])
                worksheet.write(row, 1, order['unit_kerja'])
                worksheet.write(row, 2, order['name'])
                worksheet.write(row, 3, order['tanggal'])
                worksheet.write(row, 4, order['cara_bayar'])
                worksheet.write(row, 5, order['jenis_transaksi'])
                if order['start_date']:
                    startdate = order['start_date']
                else:
                    startdate = ''
                worksheet.write(row, 6, startdate)
                if order['end_date']:
                    enddate = order['end_date']
                else:
                    enddate = ''
                worksheet.write(row, 7, enddate)
                worksheet.write(row, 8, order['duration'])
                worksheet.write(row, 9, order['nopol'])
                worksheet.write(row, 10, order['state'])
                worksheet.write(row, 11, order['val_harga'])
                worksheet.write(row, 12, order['harga_beli_stiker'])
                worksheet.write(row, 13, order['harga_kartu_hilang'])
                worksheet.write(row, 14, order['harga_ganti_nopol'])
                worksheet.write(row, 15, order['amount'])
                row += 1

            workbook.close()
            excel_file = base64.encodestring(fp.getvalue())
            wizard.report_file = excel_file
            wizard.report_printed = True
            fp.close()

            return {
                'view_mode': 'form',
                'res_id': wizard.id,
                'res_model': 'wizard.report.request.details',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'target': 'new',
            }

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
