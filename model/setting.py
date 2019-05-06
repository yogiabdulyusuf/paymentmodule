from odoo import api, fields, models
from datetime import datetime, timedelta
# from odoo.exceptions import ValidationError, Warning
import logging

_logger = logging.getLogger(__name__)


class Setting(models.Model):
    _inherit = 'res.company'

    jenis_member_st = fields.Integer(string="1st Membership", )
    jenis_member_nd = fields.Integer(string="2nd Membership", )
    jenis_member_rd = fields.Integer(string="3rd Membership", )
    jenis_member_th = fields.Integer(string="4th Membership", )
    perpanjang_ids = fields.Integer('PERPANJANG', )
    beli_stiker_ids = fields.Integer('Beli Stiker', )
    ganti_nopol_ids = fields.Integer('1st Membership', )
    ganti_nopol_dua_ids = fields.Integer('2nd Membership', )
    ganti_nopol_tiga_ids = fields.Integer('3rd Membership', )
    ganti_nopol_empat_ids = fields.Integer('4th Membership', )
    kartu_hilang_ids = fields.Integer('Kartu Hilang', )