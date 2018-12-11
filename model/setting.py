from odoo import api, fields, models
from datetime import datetime, timedelta
# from odoo.exceptions import ValidationError, Warning
import logging

_logger = logging.getLogger(__name__)


class Setting(models.Model):
    _inherit = 'res.company'

    langganan_baru_ids = fields.Integer('LANGGANAN BARU', )
    perpanjang_ids = fields.Integer('PERPANJANG', )
    beli_stiker_ids = fields.Integer('BELI STIKER', )
    ganti_nopol_ids = fields.Integer('GANTI NOPOL', )
    kartu_hilang_ids = fields.Integer('KARTU HILANG', )