from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, Warning


class DetailTransStiker(models.Model):
    _name = 'detail.transstiker'
    _rec_name = 'nopol'
    _description = 'Transaction Stiker'

    trans_stiker_id = fields.Many2one('trans.stiker', 'Stiker #')
    notrans = fields.Char(string="No Transaksi", required=False, )
    nopol = fields.Char(string="No Polisi", required=False, )
    jenis_mobil = fields.Char(string="Jenis Mobil", required=False, )
    adm = fields.Char(string="Admin", required=False, )
    kategori = fields.Integer(string="Kategori", required=False, )
    jenis_member = fields.Char(string="Jenis Member", required=False, )
    akses = fields.Char(string="Akses", required=False, )
    akses_out = fields.Char(string="Akses Out", required=False, )
    status = fields.Integer(string="Status", required=False, )
    merk = fields.Char(string="Merk Mobil", required=False, )
    tipe = fields.Char(string="Tipe Mobil", required=False, )
    tahun = fields.Char(string="Tahun", required=False, )
    warna = fields.Char(string="Warna", required=False, )
    keterangan = fields.Text(string="Keterangan", required=False, )