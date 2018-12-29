from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, Warning

class BillingPeriode(models.Model):
    _name = 'billing.periode'
    _rec_name = 'billing_id'

    @api.one
    def trans_generate_line(self):
        args = [('val_cara_bayar', '=', 'billing'), ('state', '=', 'done'), ('baru', '=', True)]
        res = self.env['request.transstiker'].search(args)
        for row in res:
            arg = [('nopol', '=', row.nopol)]
            list = res.search(arg, limit=1, order='create_date desc',)
            date = fields.Datetime.from_string(list.end_date)
            d_date = date.day
            date_now = datetime.now()
            duration = timedelta(days=30)
            date_delta = date_now + duration
            d_year = date_delta.year
            d_month = date_delta.month

            duration = timedelta(days=30)
            start_date = datetime.strptime(str(d_year) + '-' + str(d_month) + '-' + str(d_date) + " 00:00:00" , "%Y-%m-%d %H:%M:%S")
            str_start_date = str(start_date)
            end_date = start_date + duration
            str_end_date = str(end_date)

            billing_line_obj = self.env['billingperiode.line']
            vals = {}
            vals.update({'billing_periode': self.id})
            vals.update({'unitno': row.unit_kerja.kode})
            vals.update({'date_trans': datetime.now()})
            vals.update(
                {'description': 'Contribution A ( ' + row.jenis_member + ' ) periode ' + str_start_date + ' - ' + str_end_date})
            vals.update({'amount': row.val_harga})
            vals.update({'awal': start_date})
            vals.update({'akhir': end_date})
            vals.update({'jenis_langganan': row.jenis_member})
            billing_line_save = billing_line_obj.create(vals)

            if not billing_line_save:
                raise ValidationError("Error Creating Billing Periode Line")

        self.state = "confirm"

    @api.one
    def trans_generate(self):
        self.trans_generate_line()

    @api.one
    def back_trans_generate(self):
        self.state = "generate"

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
    state = fields.Selection(string="", selection=[('open', 'Open'), ('generate', 'Waiting Generate'), ('confirm', 'Waiting Confirm'), ('transfer', 'Waiting Transfer'), ('close', 'Close'), ], required=False, default="open" )

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

