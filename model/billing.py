from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, Warning

class BillingPeriode(models.Model):
    _name = 'billing.periode'
    _rec_name = 'billing_id'
    _description = 'New Description'

    @api.one
    def trans_generate(self):
        date = datetime.strptime(self.end_date, "%Y-%m-%d")
        d_month = date.month
        d_date = date.date

        date_now = datetime.now()
        d_year = date_now.year

        duration = timedelta(days=30)

        start_date = datetime.strptime(d_year + '-' + d_month + '-' + d_date, "%Y-%m-%d")

        self.line_ids.awal = start_date
        self.line_ids.akhir = start_date + duration

        # @api.one
        # def generate_billing_savings(self):
        #
        #     args = [('state', '=', 'active')]
        #     res = self.env['savings.account'].search(args)
        #
        #     for data_detail in res:
        #         # Generate Transaksi Simpanan Wajib
        #         savings_trans_obj = self.env['savings.trans']
        #
        #         mandatory_savings = self.env.user.company_id.mandatory_savings_trans_type_id
        #         if not mandatory_savings:
        #             raise ValidationError("Mandatory Savings not defined, please define on company information!")
        #
        #         vals = {}
        #         vals.update({'account_number_id': data_detail.savings_account.id})
        #         vals.update({'debit': self.env.user.company_id.mandatory_savings})
        #         vals.update({'saving_method': 'deposit'})
        #         vals.update({'credit': 0.0})
        #         vals.update({'trans_type_id': mandatory_savings.id})
        #         vals.update({'state': 'openbilling'})
        #         saving_trans = savings_trans_obj.create(vals)
        #
        #         if not saving_trans:
        #             raise ValidationError("Error Creating Simpanan Wajib")

    @api.one
    def trans_open(self):
        self.state = "generate"

    @api.model
    def create(self, vals):
        vals['billing_id'] = self.env['ir.sequence'].next_by_code('billing.periode')
        res = super(BillingPeriode, self).create(vals)
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
    billing_id = fields.Char(string="Billing ID", required=False, )
    awal = fields.Date(string="Start Date", required=False, )
    akhir = fields.Date(string="End Date", required=False, )
    jenis_langganan = fields.Char(string="Member Type", required=False, )

