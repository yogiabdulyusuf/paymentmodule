from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, Warning


class RequestTransStiker(models.Model):
    _name = 'request.transstiker'
    _description = 'Request Transaction Stiker'

    @api.onchange('unit_kerja')
    def _change_trans_stiker(self):
        res = {}
        res['domain'] = {'sticker_id':[('unit_kerja', '=', self.unit_kerja.id)]}
        return res

    @api.onchange('sticker_id')
    def _get_stiker(self):
        name = ''
        no_id = ''
        jenis_transaksi = ''
        awal = ''
        akhir = ''
        cara_bayar = ''
        nopol = ''
        jenis_mobil = ''
        jenis_member = ''
        merk = ''
        tipe = ''
        tahun = ''
        color = ''

        for data_detail in self.sticker_id:
            name = data_detail.name
            no_id = data_detail.no_id
            jenis_transaksi = data_detail.jenis_transaksi
            awal = data_detail.awal
            akhir = data_detail.akhir
            cara_bayar = data_detail.cara_bayar
            nopol = data_detail.detail_ids.nopol
            jenis_mobil = data_detail.detail_ids.jenis_mobil
            jenis_member = data_detail.detail_ids.jenis_member
            merk = data_detail.detail_ids.merk
            tipe = data_detail.detail_ids.tipe
            tahun = data_detail.detail_ids.tahun
            color = data_detail.detail_ids.warna
        self.name = name
        self.no_id = no_id
        if jenis_transaksi == "langganan_baru":
            jenis_transaksi = "perpanjang"
        self.jenis_transaksi = jenis_transaksi
        self.val_awal = awal
        self.val_akhir = akhir
        self.val_cara_bayar = cara_bayar
        self.nopol = nopol
        self.jenis_mobil = jenis_mobil
        self.jenis_member = jenis_member
        self.merk_kendaraan = merk
        self.val_tipe = tipe
        self.val_tahun = tahun
        self.val_color = color

    @api.onchange('baru', 'jenis_transaksi')
    def _change_harga_langganan(self):
        if self.baru == True:
            if self.jenis_transaksi == "langganan_baru":
                langganan_baru_id = self.env.user.company_id.langganan_baru_ids
                if not langganan_baru_id:
                    raise ValidationError("Price Langganan Baru not defined,  please define on company information!")

                self.val_harga = langganan_baru_id

            else:

                perpanjang_id = self.env.user.company_id.perpanjang_ids
                if not perpanjang_id:
                    raise ValidationError("Price Perpanjang not defined,  please define on company information!")

                self.val_harga = perpanjang_id
        else:
            self.val_harga = 0


    @api.onchange('beli_stiker','ganti_nopol','kartu_hilang')
    def _change_harga_beli_stiker(self):
        if self.beli_stiker == True:
            beli_stiker_id = self.env.user.company_id.beli_stiker_ids
            if not beli_stiker_id:
                raise ValidationError("Price Beli Stiker not defined,  please define on company information!")

            self.harga_beli_stiker = beli_stiker_id
        else:
            self.harga_beli_stiker = 0

        if self.ganti_nopol == True:
            ganti_nopol_id = self.env.user.company_id.ganti_nopol_ids
            if not ganti_nopol_id:
                raise ValidationError("Price Ganti Nopol not defined,  please define on company information!")

            self.harga_ganti_nopol = ganti_nopol_id
        else:
            self.harga_ganti_nopol = 0

        if self.kartu_hilang == True:
            kartu_hilang_id = self.env.user.company_id.kartu_hilang_ids
            if not kartu_hilang_id:
                raise ValidationError("Price Kartu Hilang not defined,  please define on company information!")

            self.harga_kartu_hilang = kartu_hilang_id
        else:
            self.harga_kartu_hilang = 0

    @api.onchange('val_harga','harga_beli_stiker','harga_ganti_nopol','harga_kartu_hilang')
    def calculate_rts(self):
        total = self.val_harga + self.harga_beli_stiker + self.harga_ganti_nopol + self.harga_kartu_hilang
        self.amount = total


    @api.onchange('duration')
    @api.depends('val_awal', 'duration')
    def _get_end_date(self):
        for r in self:
            # Pengecekan jika field duration & start_date tidak diisi, maka field end_date akan di update sama seperti field start_date
            if not (r.val_awal and r.duration):
                r.val_akhir = r.val_awal
                continue

            # Membuat variable start yang isinya tanggal dari field start_date
            start_date = fields.Datetime.from_string(r.val_akhir)

            # Membuat variable duration yang isinya durasi hari dari field duration
            # Durasi hari dikurangi 1 detik agar start_date masuk kedalam durasi hari , seconds=-1
            val_day = 30 * r.duration
            duration = timedelta(days=val_day)

            # Mengupdate field end_date dari perhitungan variabel start ditambah variabel duration
            r.start_date = start_date
            r.end_date = start_date + duration


    @api.one
    def update_startdate_enddate(self):
        for v in self:
            if v.baru == True:
                if v.jenis_transaksi == "perpanjang":
                    args = [('id', '=', v.sticker_id.id)]
                    res = self.env['trans.stiker'].search(args).write({'awal': v.start_date, 'akhir': v.end_date})
                    v.state = "done"

    @api.one
    def trans_payment(self):
        self.state = "payment"

    @api.model
    def create(self, vals):
        vals['trans_stiker_id'] = self.env['ir.sequence'].next_by_code('request.transstiker')
        res = super(RequestTransStiker, self).create(vals)
        res._get_stiker()
        res._change_harga_beli_stiker()
        res._change_harga_langganan()
        res.calculate_rts()
        res._get_end_date()
        res.trans_payment()
        return res

    trans_stiker_id = fields.Char(string="Transaksi ID", readonly=True)
    unit_kerja = fields.Many2one('stasiun.kerja','Unit Kerja #', required=True)
    sticker_id = fields.Many2one('trans.stiker','Stiker #', required=True, )
    name = fields.Char(string="Nama", )
    no_id = fields.Char(string="No ID", )
    duration = fields.Integer('Duration', default=1, required=False)
    val_awal = fields.Date(string="Start Date", required=False, )
    val_akhir = fields.Date(string="End Date", required=False, )
    start_date = fields.Date(string="New Start Date", required=False, readonly=True,)
    end_date = fields.Date(string="New End Date", required=False, readonly=True,)
    val_harga = fields.Integer(string="Harga Perpanjang/Baru", required=False, readonly=True, )
    tanggal = fields.Date(string="Date", required=False, readonly=True, default=datetime.now())
    adm = fields.Char(string="Adm", required=False, readonly=True, )
    jenis_transaksi = fields.Selection(string="Jenis Transaksi",
                                       selection=[('langganan_baru', 'LANGGANAN BARU'), ('perpanjang', 'PERPANJANG'), ],
                                       required=True, readonly=False, default="langganan_baru")
    val_cara_bayar = fields.Selection(string="Cara Pembayaran",
                                  selection=[('billing', 'Billing'), ('non_billing', 'Non Billing'), ], required=False, )
    nopol = fields.Char(string="No Polisi", required=False, )
    jenis_mobil = fields.Char(string="Jenis Mobil", required=False, )
    jenis_member = fields.Char(string="Jenis Member", required=False, )
    merk_kendaraan = fields.Char(string="Merk Mobil", required=False, )
    val_tipe = fields.Char(string="Tipe Mobil", required=False, )
    val_tahun = fields.Char(string="Tahun", required=False, )
    val_color = fields.Char(string="Warna", required=False, )
    amount = fields.Integer(string="Amount", required=False, readonly=True )
    baru = fields.Boolean(string="LANGGANAN",  )
    perpanjang = fields.Boolean(string="PERPANJANG",  default=False,)
    beli_stiker = fields.Boolean(string="BELI STIKER",  default=False,)
    ganti_nopol = fields.Boolean(string="GANTI NOPOL",  default=False,)
    kartu_hilang = fields.Boolean(string="KARTU HILANG",  default=False, )
    tipe_trans = fields.Selection(string="Tipe Transaksi",
                                  selection=[('ganti_nopol', 'GANTI NOPOL'), ('kartu_hilang', 'KARTU HILANG'), ],
                                  required=False, )
    harga_beli_stiker = fields.Integer(string="Harga Beli Stiker", required=False, readonly=True)
    harga_kartu_hilang = fields.Integer(string="Harga Kartu Hilang", required=False, readonly=True)
    harga_ganti_nopol = fields.Integer(string="Harga Ganti NOPOL", required=False, readonly=True)
    new_val_cara_bayar = fields.Selection(string="Cara Pembayaran",
                                  selection=[('billing', 'Billing'), ('non_billing', 'Non Billing'), ], required=False, )
    new_nopol = fields.Char(string="No Polisi", required=False, )
    new_jenis_mobil = fields.Char(string="Jenis Mobil", required=False, )
    new_jenis_member = fields.Char(string="Jenis Member", required=False, )
    new_merk_kendaraan = fields.Char(string="Merk Mobil", required=False, )
    new_val_tipe = fields.Char(string="Tipe Mobil", required=False, )
    new_val_tahun = fields.Char(string="Tahun", required=False, )
    new_val_color = fields.Char(string="Warna", required=False, )
    state = fields.Selection(string="state", selection=[('open', 'Open'),('payment','Waiting Payment'), ('done', 'Done'), ], required=False, default="open",)

class StasiunKerja(models.Model):
    _name = 'stasiun.kerja'
    _rec_name = 'nama'
    _description = 'Stasiun Kerja'

    kode = fields.Char(string="Kode", required=False, )
    nama = fields.Char(string="Nama", required=False, )
    margin = fields.Integer(string="Margin", required=False, )
    spv = fields.Char(string="SPV", required=False, )
    target = fields.Integer(string="Target", required=False, )
    status = fields.Integer(string="Status", required=False, )
    trans_stiker_ids = fields.One2many(comodel_name="trans.stiker", inverse_name="stasiun_kerja_id", string="Trans Stiker #", required=False, )

# TRANSACTION PAYMENT
class TransStiker(models.Model):
    _name = 'trans.stiker'
    _rec_name = 'notrans'
    _description = 'Transaction Payment Module'

    stasiun_kerja_id = fields.Many2one(comodel_name="stasiun.kerja", string="Stasiun Kerja", required=False, )
    notrans = fields.Char(string="No Transaksi", required=False, )
    name = fields.Char(string="Nama", required=False,  )
    alamat = fields.Char(string="Alamat", required=False, )
    telphone = fields.Char(string="No Telphone", required=False, )
    jenis_transaksi = fields.Selection(string="Jenis Transaksi", selection=[('langganan_baru', 'Langganan Baru'), ('perpanjang', 'Perpanjang'), ('stop', 'Stop Langganan'), ], required=False, )
    awal = fields.Date(string="Start Date", required=False, )
    harga = fields.Integer(string="Harga", required=False, )
    keterangan = fields.Text(string="Keterangan", required=False, )
    tanggal = fields.Date(string="Date", required=False, default=datetime.now())
    operator = fields.Char(string="Operator", required=False, )
    akhir = fields.Date(string="End Date", required=True, )
    maks = fields.Integer(string="Maks", required=False, )
    no_id = fields.Char(string="No ID", required=False,  )
    unit_kerja = fields.Char(string="Unit Kerja", required=False, )
    no_induk = fields.Char(string="No Induk", required=False, )
    jenis_stiker = fields.Integer(string="Jenis Stiker", required=False, )
    hari_ke = fields.Char(string="Hari ke", required=False, )
    jenis_langganan = fields.Char(string="Jenis Langganan", required=False, )
    exit_pass = fields.Integer(string="Exit Pass", required=False, )
    no_kuitansi = fields.Char(string="No Kuitansi", required=False, )
    tgl_edited = fields.Date(string="Tanggal Edit", required=False, )
    tipe_exit_pass = fields.Integer(string="Tipe Exit Pass", required=False, )
    seq_code = fields.Char(string="Seq Code", required=False, )
    unitno = fields.Char(string="Unit No", required=False, )
    area = fields.Char(string="Area", required=False, )
    reserved = fields.Integer(string="Reserved", required=False, )
    cara_bayar = fields.Selection(string="Cara Pembayaran", selection=[('billing', 'Billing'), ('non_billing', 'Non Billing'), ], required=False, )
    detail_ids = fields.One2many('detail.transstiker','trans_stiker_id','Details')


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