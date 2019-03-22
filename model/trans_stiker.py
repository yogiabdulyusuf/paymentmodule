from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, Warning
from dateutil.relativedelta import *



# TRANSACTION PAYMENT
class TransStiker(models.Model):
    _name = 'trans.stiker'
    _rec_name = 'notrans'
    _description = 'Transaction Payment Module'

    stasiun_kerja_id = fields.Many2one(comodel_name="stasiun.kerja", string="Stasiun Kerja", required=False, )
    notrans = fields.Char(string="No Transaksi", required=False, )
    name = fields.Char(string="Nama", required=False, )
    alamat = fields.Char(string="Alamat", required=False, )
    telphone = fields.Char(string="No Telphone", required=False, )
    jenis_transaksi = fields.Selection(string="Jenis Transaksi",
                                       selection=[('langganan_baru', 'Langganan Baru'), ('perpanjang', 'Perpanjang'),
                                                  ('stop', 'Stop Langganan'), ], required=False, )
    awal = fields.Date(string="Start Date", required=False, )
    harga = fields.Integer(string="Harga", required=False, )
    keterangan = fields.Text(string="Keterangan", required=False, )
    tanggal = fields.Date(string="Date", required=False, default=datetime.now())
    operator = fields.Char(string="Operator", required=False, )
    akhir = fields.Date(string="End Date", required=True, )
    maks = fields.Char(string="Maks", required=False, )
    no_id = fields.Char(string="No ID", required=False, )
    unit_kerja = fields.Char(string="Unit Kerja", required=False, )
    no_induk = fields.Char(string="No Induk", required=False, )
    jenis_stiker = fields.Char(string="Jenis Stiker", required=False, )
    hari_ke = fields.Char(string="Hari ke", required=False, )
    jenis_langganan = fields.Char(string="Jenis Langganan", required=False, )
    exit_pass = fields.Char(string="Exit Pass", required=False, )
    no_kuitansi = fields.Char(string="No Kuitansi", required=False, )
    tgl_edited = fields.Date(string="Tanggal Edit", required=False, )
    tipe_exit_pass = fields.Char(string="Tipe Exit Pass", required=False, )
    seq_code = fields.Char(string="Seq Code", required=False, )
    unitno = fields.Char(string="Unit No", required=False, )
    area = fields.Char(string="Area", required=False, )
    reserved = fields.Char(string="Reserved", required=False, )
    cara_bayar = fields.Selection(string="Cara Pembayaran",
                                  selection=[('billing', 'Billing'), ('non_billing', 'Non Billing'), ],
                                  required=False, )
    detail_ids = fields.One2many('detail.transstiker', 'trans_stiker_id', 'Details')