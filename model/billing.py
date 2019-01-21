from odoo import api, fields, models
from datetime import datetime, timedelta, time
from odoo.exceptions import ValidationError, Warning
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class BillingPeriode(models.Model):
    _name = 'billing.periode'
    _rec_name = 'billing_id'

    @api.one
    def trans_generate_line(self):
        args = [('jenis_transaksi','!=','stop')]
        res = self.env['trans.stiker'].search(args)
        date_akhir = datetime.strptime(str(self.billing_year) + '-' + str(self.billing_month).zfill(2) + '-' + '01', "%Y-%m-%d")
        akhir = date_akhir + relativedelta(months=+2)

        for row in res:
            #_logger.info(row.no_id)

            arg = [('no_id', '=', row.no_id), ('jenis_member', '!=', '1st'), ('approvedstatus', '=', '1'), ('status', '=', '1'), ]

            list = self.env['request.transstiker'].search(arg, order='akhir desc')
            #_logger.info(line_check.no_id)

            for line in list:
                if line.jenis_transaksi == 'stop' or line.cara_bayar == 'non_billing':
                    break
                if line.akhir <= str(akhir):
                    continue
                if line.akhir >= str(akhir):

                    jenis_member_st_ids = self.env.user.company_id.jenis_member_st
                    jenis_member_nd_ids = self.env.user.company_id.jenis_member_nd
                    if not jenis_member_nd_ids:
                        raise ValidationError("Price 2nd Membership not defined,  please define on company information!")
                    jenis_member_rd_ids = self.env.user.company_id.jenis_member_rd
                    if not jenis_member_rd_ids:
                        raise ValidationError("Price 3rd Membership not defined,  please define on company information!")
                    jenis_member_th_ids = self.env.user.company_id.jenis_member_th
                    if not jenis_member_th_ids:
                        raise ValidationError("Price 4th Membership not defined,  please define on company information!")

                    if line.jenis_member == "1st":
                        val_harga = jenis_member_st_ids
                    elif line.jenis_member == "2nd":
                        val_harga = jenis_member_nd_ids
                    elif line.jenis_member == "3rd":
                        val_harga = jenis_member_rd_ids
                    elif line.jenis_member == "4th":
                        val_harga = jenis_member_th_ids
                    else:
                        val_harga = jenis_member_st_ids

                    #_logger.info(line.no_id)
                    tgl = fields.Datetime.from_string(line.akhir)
                    str_start_date = str(self.billing_year) + "-" + str(self.billing_month).zfill(2) + "-" + str(tgl.day).zfill(2)
                    start_date = datetime.strptime(str_start_date,"%Y-%m-%d") + relativedelta(months=+1)
                    #d_date = tgl.day
                    #date_now = datetime.now()
                    #duration = timedelta(days=30)
                    #date_delta = date_now + duration
                    #d_year = date_delta.year
                    #d_month = date_delta.month

                    duration = relativedelta(months=+1)
                    #start_date = datetime.strptime(str(d_year) + '-' + str(d_month) + '-' + str(d_date) + ' 00:00:00' , "%Y-%m-%d %H:%M:%S")
                    str_start_date = start_date.strftime('%d/%m/%Y')
                    end_date = start_date + duration
                    str_end_date = end_date.strftime('%d/%m/%Y')

                    billing_line_obj = self.env['billingperiode.line']
                    vals = {}
                    vals.update({'billing_periode': self.id})
                    vals.update({'unitno': line.unit_kerja.kode})
                    vals.update({'date_trans': datetime.now()})
                    vals.update(
                        {'description': 'Contribution A ( ' + line.jenis_member + ' ) periode ' + str_start_date + ' - ' + str_end_date})
                    vals.update({'amount': val_harga})
                    vals.update({'awal': start_date})
                    vals.update({'akhir': end_date})
                    vals.update({'jenis_langganan': line.jenis_member})
                    billing_line_save = billing_line_obj.create(vals)

                    if not billing_line_save:
                        raise ValidationError("Error Creating Billing Periode Line")

                    break

        self.state = "transfer"

    @api.one
    def trans_generate(self):
        self.trans_generate_line()

    @api.one
    def trans_open(self):
        self.state = "generate"

    @api.model
    def create(self, vals):
        vals['billing_id'] = self.env['ir.sequence'].next_by_code('billing.periode')
        res = super(BillingPeriode, self).create(vals) # PERINTAH SUPER INI DI GUNAKAN KETIKA
        res.trans_open()
        return res

    billing_id = fields.Char(string="Billing ID", readonly=True)
    billing_year = fields.Integer(string="Billing Year", required=False, )
    billing_month = fields.Integer(string="Billing Month", required=False, )
    line_ids = fields.One2many('billingperiode.line', 'billing_periode', 'Details', readonly=True)
    state = fields.Selection(string="", selection=[('open', 'Open'), ('generate', 'Waiting Generate'), ('transfer', 'Waiting Transfer'), ('close', 'Close'), ], required=False, default="open" )

class BillingPeriodeLine(models.Model):
    _name = 'billingperiode.line'

    billing_periode = fields.Many2one(comodel_name="billing.periode", string="Billing Periode #", required=False, readonly=True)
    unitno = fields.Char(string="Unit No", required=False, )
    date_trans = fields.Date(string="Date", required=False, )
    description = fields.Text(string="Description", required=False, )
    amount = fields.Integer(string="Amount", required=False, )
    awal = fields.Date(string="Start Date", required=False, )
    akhir = fields.Date(string="End Date", required=False, )
    jenis_langganan = fields.Char(string="Member Type", required=False, )

