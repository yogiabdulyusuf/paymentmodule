from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, Warning
from dateutil.relativedelta import *


class StasiunKerja(models.Model):
    _name = 'stasiun.kerja'
    _rec_name = 'kode'
    _description = 'Stasiun Kerja'

    kode = fields.Char(string="Kode", required=False, )
    nama = fields.Char(string="Nama", required=False, )
    margin = fields.Integer(string="Margin", required=False, )
    spv = fields.Char(string="SPV", required=False, )
    target = fields.Integer(string="Target", required=False, )
    status = fields.Integer(string="Status", required=False, )
    trans_stiker_ids = fields.One2many(comodel_name="trans.stiker", inverse_name="stasiun_kerja_id",
                                       string="Trans Stiker #", required=False, )