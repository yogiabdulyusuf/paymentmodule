from odoo import api, fields, models
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, Warning
from dateutil.relativedelta import *
import json
import logging

_logger = logging.getLogger(__name__)

class RequestTransStiker(models.Model):
    _name = 'request.transstiker'
    _inherit = ['mail.thread']
    _rec_name = 'notrans'
    _description = 'Request Transaction Stiker'
    _order = 'notrans desc'

    def find_stasiun_kerja(self, kode):
        stasiunkerja_obj = self.env['stasiun.kerja']
        args = [('kode', '=', str(kode))]
        stasiunkerja = stasiunkerja_obj.search(args, limit=1)
        return stasiunkerja

    def find_transaksi_stiker(self, notrans):
        transaksistiker_obj = self.env['trans.stiker']
        args = [('notrans', '=', str(notrans))]
        transaksistiker = transaksistiker_obj.search(args, limit=1)
        return transaksistiker

    def find_detail_stiker(self, notrans):
        detailstiker_obj = self.env['detail.transstiker']
        args = [('notrans', '=', str(notrans))]
        detailstiker = detailstiker_obj.search(args, limit=1)
        return detailstiker



    @api.onchange('unit_kerja')
    def _change_trans_stiker(self):
        res = {}
        res['domain'] = {'stiker_id':[('stasiun_kerja_id', '=', self.unit_kerja.id)]}
        return res

    @api.onchange('jenis_transaksi','kartu_hilang','stiker_id') #
    def _change_kartu_hilang(self):
        if self.kartu_hilang == True:
            base_external_dbsource_obj = self.env['base.external.dbsource']
            postgresconn = base_external_dbsource_obj.sudo().browse(1)
            postgresconn.connection_open()
            _logger.info("Connection Open")

            _logger.info('Get Card Member')
            strSQL = """SELECT """ \
                     """no_card, no_urut """ \
                     """FROM card_member WHERE notrans='{}'""".format(self.stiker_id.notrans)

            select_card_member = postgresconn.execute(query=strSQL, metadata=False)
            _logger.info(select_card_member)
            no_kartu_old = ""
            no_urut_old = ""

            for row in select_card_member:
                no_kartu_old = row[0]
                no_urut_old = row[1]

            self.old_no_kartu = no_kartu_old
            self.old_no_urut = no_urut_old

        if self.kartu_hilang == False:
            self.old_no_kartu = ""
            self.old_no_urut = ""
            self.no_kartu = ""
            self.no_urut = ""

        if self.jenis_transaksi == 'langganan_baru':
            self.old_no_kartu = ""
            self.old_no_urut = ""

    @api.onchange('new_nopol')
    def validation_ganti_nopol(self):
        if self.new_nopol:
            base_external_dbsource_obj = self.env['base.external.dbsource']
            postgresconn = base_external_dbsource_obj.sudo().browse(1)
            postgresconn.connection_open()
            _logger.info("Connection Open")
            # Kondisi pengecekan stiker
            strSQL = """SELECT notrans FROM detail_transaksi_stiker WHERE nopol='{}'""".format(
                self.new_nopol)
            detail_trans_stiker = postgresconn.execute(query=strSQL, metadata=False)
            _logger.info(detail_trans_stiker)

            if detail_trans_stiker:
                for row in detail_trans_stiker:
                    no_trans = row[0]
                    raise ValidationError(
                        "Nopol anda sudah terdaftar di Stiker# : " + no_trans + ", Jika transaksi di lanjutkan maka mobil akan di pindahkan ke Stiker#: " + self.stiker_id.notrans + " dan data lama mobil yang ada di Stiker#: " + self.stiker_id.notrans + " akan di hapus")


    @api.onchange('stiker_id', 'ganti_nopol')
    def calculate_harga_ganti_nopol(self):
        if self.ganti_nopol == True:

            if self.new_nopol:

                base_external_dbsource_obj = self.env['base.external.dbsource']
                postgresconn = base_external_dbsource_obj.sudo().browse(1)
                postgresconn.connection_open()
                _logger.info("Connection Open")
                # Kondisi pengecekan stiker
                strSQL = """SELECT notrans FROM detail_transaksi_stiker WHERE nopol='{}'""".format(
                    self.new_nopol)
                detail_trans_stiker = postgresconn.execute(query=strSQL, metadata=False)
                _logger.info(detail_trans_stiker)

                if detail_trans_stiker:
                    for row in detail_trans_stiker:
                        no_trans = row[0]
                        # Kondisi pengecekan stiker
                        strSQL = """SELECT no_card FROM card_member WHERE notrans='{}'""".format(no_trans)
                        cardmember = postgresconn.execute(query=strSQL, metadata=False)
                        _logger.info(cardmember)

                        for record in cardmember:
                            no_card = record[0]
                            # Kondisi pengecekan stiker
                            strSQL = """SELECT no_pol FROM transaksi_parkir WHERE no_pol='{}'""".format(no_card)
                            trans_parkir = postgresconn.execute(query=strSQL, metadata=False)
                            _logger.info(trans_parkir)

                            if trans_parkir:
                                for row in trans_parkir:
                                    raise ValidationError(
                                        "Mobil anda masih di dalam dengan NOPOL : " + self.new_nopol + ", Stiker : " + no_trans + ", No Card : " +
                                        row[
                                            0] + " , Silahkan mobil anda di keluarkan terlebih dahulu !!")

            ganti_nopol_id = self.env.user.company_id.ganti_nopol_ids
            ganti_nopol_dua_id = self.env.user.company_id.ganti_nopol_dua_ids
            ganti_nopol_tiga_id = self.env.user.company_id.ganti_nopol_tiga_ids
            ganti_nopol_empat_id = self.env.user.company_id.ganti_nopol_empat_ids

            if not ganti_nopol_dua_id:
                raise ValidationError("Price Ganti Nopol 2nd not defined,  please define on company information!")
            if not ganti_nopol_tiga_id:
                raise ValidationError("Price Ganti Nopol 3rd not defined,  please define on company information!")
            if not ganti_nopol_empat_id:
                raise ValidationError("Price Ganti Nopol 4th not defined,  please define on company information!")

            if self.stiker_id:
                check_no_id = self.stiker_id.notrans[4]
            else:
                check_no_id = ''

            if check_no_id == "1":
                self.harga_ganti_nopol = ganti_nopol_id
                self.new_jenis_member = "1st"
            elif check_no_id == "2":
                self.harga_ganti_nopol = ganti_nopol_dua_id
                self.new_jenis_member = "2nd"
            elif check_no_id == "3":
                self.harga_ganti_nopol = ganti_nopol_tiga_id
                self.new_jenis_member = "3rd"
            elif check_no_id == "4":
                self.harga_ganti_nopol = ganti_nopol_empat_id
                self.new_jenis_member = "4th"

            # AMBIL DATA STIKER DARI TRANS STIKER
            for data_detail in self.stiker_id:
                self.nopol = data_detail.detail_ids.nopol
                self.merk = data_detail.detail_ids.merk
                self.tipe = data_detail.detail_ids.tipe
                self.tahun = data_detail.detail_ids.tahun
                self.warna = data_detail.detail_ids.warna

        else:
            self.harga_ganti_nopol = 0

    @api.onchange('baru','jenis_transaksi','stiker_id')
    def _get_stiker(self):
        # check langganan baru mobil ke berapa
        jenis_member_st_ids = self.env.user.company_id.jenis_member_st
        jenis_member_nd_ids = self.env.user.company_id.jenis_member_nd
        jenis_member_rd_ids = self.env.user.company_id.jenis_member_rd
        jenis_member_th_ids = self.env.user.company_id.jenis_member_th
        if not jenis_member_nd_ids:
            raise ValidationError("Price 2nd Membership not defined,  please define on company information!")
        if not jenis_member_rd_ids:
            raise ValidationError("Price 3rd Membership not defined,  please define on company information!")
        if not jenis_member_th_ids:
            raise ValidationError("Price 4th Membership not defined,  please define on company information!")

            # ======================================================================================

        if self.baru == True:

            if self.jenis_transaksi == 'perpanjang_baru':

                if self.stiker_id:

                    # Process perpanjang to Server Database Parkir and update trans_id
                    base_external_dbsource_obj = self.env['base.external.dbsource']
                    postgresconn = base_external_dbsource_obj.sudo().browse(1)
                    postgresconn.connection_open()
                    _logger.info("Connection Open")
                    _logger.info("Check mobil di dalam")

                    # Kondisi pengecekan stiker
                    strSQL = """SELECT no_card FROM card_member WHERE notrans='{}'""".format(self.stiker_id.notrans)
                    cardmember = postgresconn.execute(query=strSQL, metadata=False)
                    _logger.info(cardmember)

                    stikers = self.stiker_id.notrans

                    for record in cardmember:
                        # Kondisi pengecekan stiker
                        strSQL = """SELECT no_pol FROM transaksi_parkir WHERE no_pol='{}'""".format(record[0])
                        trans_parkir = postgresconn.execute(query=strSQL, metadata=False)
                        _logger.info(trans_parkir)

                        for row in trans_parkir:
                            if row[0]:
                                raise ValidationError(
                                    "Mobil anda masih di dalam, Stiker : " + stikers + ", Nopol : " + row[0] + "")

                    if self.new_nopol_pb:

                        strSQL = """SELECT notrans FROM detail_transaksi_stiker WHERE nopol='{}'""".format(
                            self.new_nopol_pb)
                        detail_trans_stiker = postgresconn.execute(query=strSQL, metadata=False)
                        _logger.info(detail_trans_stiker)

                        if detail_trans_stiker:
                            for row in detail_trans_stiker:
                                no_trans = row[0]
                                raise ValidationError(
                                    "Mobil dengan NOPOL " + self.new_nopol_pb + " ini sudah terdaftar di Stiker# : " + no_trans + "")

                    # AMBIL DATA STIKER DARI TRANS STIKER
                    for data_detail in self.stiker_id:
                        self.name = data_detail.name
                        self.alamat = data_detail.alamat
                        self.telphone = data_detail.telphone
                        self.no_id = data_detail.no_id
                        self.awal_old = data_detail.awal
                        self.akhir_old = data_detail.akhir
                        self.nopol = data_detail.detail_ids.nopol
                        self.merk = data_detail.detail_ids.merk
                        self.tipe = data_detail.detail_ids.tipe
                        self.tahun = data_detail.detail_ids.tahun
                        self.warna = data_detail.detail_ids.warna

                    if self.stiker_id.notrans:
                        check_row = self.stiker_id.notrans[4]
                    else:
                        check_row = ''

                    # if self.stiker_id.notrans:
                    #     check_motor = self.stiker_id.notrans[0]
                    # else:
                    #     check_motor = ''
                    #
                    # if check_motor == "K" or check_motor == "k":
                    #     self.jenis_member = "1st"
                    # else:
                    if check_row == "1":
                        self.jenis_member = "1st"
                    elif check_row == "2":
                        self.jenis_member = "2nd"
                    elif check_row == "3":
                        self.jenis_member = "3rd"
                    elif check_row == "4":
                        self.jenis_member = "4th"
                    elif check_row == "":
                        self.jenis_member = ""

                else:
                    raise ValidationError("Stiker not defined,  please define Stiker!")

            elif self.jenis_transaksi == 'perpanjang':

                if self.stiker_id:

                    # AMBIL DATA STIKER DARI TRANS STIKER
                    for data_detail in self.stiker_id:
                        self.name = data_detail.name
                        self.alamat = data_detail.alamat
                        self.telphone = data_detail.telphone
                        self.no_id = data_detail.no_id
                        self.awal_old = data_detail.awal

                        # checktglakhir = datetime.strptime(data_detail.akhir, "%H:%M:%S")
                        #
                        # if str(checktglakhir) == "00:00:00":
                        #     tglakhir = datetime.strptime(data_detail.akhir, "%Y-%m-%d %H:%M:%S")
                        #     tglakhir = datetime(tglakhir.year, tglakhir.month, tglakhir.day, 23, 59, 59) + relativedelta(hours=17)
                        # else:
                        #     tglakhir = data_detail.akhir
                        # tglakhir = datetime.strptime(data_detail.akhir, "%Y-%m-%d %H:%M:%S")
                        # tglakhir = '-'.join(str(x) for x in (tglakhir.year, tglakhir.month, tglakhir.day))
                        # _logger.info(tglakhir)
                        tglakhir = datetime.strptime(data_detail.akhir, "%Y-%m-%d %H:%M:%S")
                        _logger.info(tglakhir)
                        if not (tglakhir.hour == 16 and tglakhir.minute == 59):
                            tglakhir = datetime(tglakhir.year, tglakhir.month, tglakhir.day, 23, 59, 59) - relativedelta(hours=7) + relativedelta(days=1)

                        _logger.info(tglakhir)
                        self.akhir_old = tglakhir
                        self.nopol = data_detail.detail_ids.nopol
                        self.merk = data_detail.detail_ids.merk
                        self.tipe = data_detail.detail_ids.tipe
                        self.tahun = data_detail.detail_ids.tahun
                        self.warna = data_detail.detail_ids.warna


                    if self.stiker_id.notrans:
                        check_row = self.stiker_id.notrans[4]
                    else:
                        check_row = ''

                    # if self.stiker_id.notrans:
                    #     check_motor = self.stiker_id.notrans[0]
                    # else:
                    #     check_motor = ''
                    #
                    # if check_motor == "K" or check_motor == "k":
                    #     self.jenis_member = "1st"
                    # else:
                    if check_row == "1":
                        self.jenis_member = "1st"
                    elif check_row == "2":
                        self.jenis_member = "2nd"
                    elif check_row == "3":
                        self.jenis_member = "3rd"
                    elif check_row == "4":
                        self.jenis_member = "4th"
                    elif check_row == "":
                        self.jenis_member = ""

                    # dt1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                    # start_dt = date(dt1.year, dt1.month, dt1.day)
                    # dt2 = datetime.now()
                    # end_dt = date(dt2.year, dt2.month, dt2.day)
                    #
                    #
                    # if self.cara_bayar == "billing":
                    #     jml = 0
                    #     month = ""
                    #     for dt in self.daterange(start_dt, end_dt):
                    #         if dt.strftime("%m") == month:
                    #             continue
                    #         else:
                    #             month = dt.strftime("%m")
                    #             jml = jml + 1
                    #
                    #     self.duration = jml

                else:
                    raise ValidationError("Stiker not defined,  please define Stiker!")

            elif self.jenis_transaksi == 'stop':

                if self.stiker_id:

                    # AMBIL DATA STIKER DARI TRANS STIKER
                    for data_detail in self.stiker_id:
                        self.name = data_detail.name
                        self.alamat = data_detail.alamat
                        self.telphone = data_detail.telphone
                        self.no_id = data_detail.no_id
                        self.awal_old = data_detail.awal
                        self.akhir_old = data_detail.akhir
                        self.nopol = data_detail.detail_ids.nopol
                        self.jenis_mobil = data_detail.detail_ids.jenis_mobil
                        self.merk = data_detail.detail_ids.merk
                        self.tipe = data_detail.detail_ids.tipe
                        self.tahun = data_detail.detail_ids.tahun
                        self.warna = data_detail.detail_ids.warna

                    # akhir = datetime.now()
                    # if self.jenis_transaksi == "stop":
                    #     self.akhir = akhir
                    #     self.cara_bayar = "non_billing"

                    self.duration = 2

                    if self.stiker_id.notrans:
                        check_row = self.stiker_id.notrans[4]
                    else:
                        check_row = ''

                    # if self.stiker_id.notrans:
                    #     check_motor = self.stiker_id.notrans[0]
                    # else:
                    #     check_motor = ''
                    #
                    # if check_motor == "K" or check_motor == "k":
                    #     self.jenis_member = "1st"
                    # else:
                    if check_row == "1":
                        self.jenis_member = "1st"
                    elif check_row == "2":
                        self.jenis_member = "2nd"
                    elif check_row == "3":
                        self.jenis_member = "3rd"
                    elif check_row == "4":
                        self.jenis_member = "4th"
                    elif check_row == "":
                        self.jenis_member = ""

                else:
                    raise ValidationError("Stiker not defined,  please define Stiker!")

        else:
            self.jenis_transaksi = ""
            self.duration = 0
            self.awal_old = ""
            self.akhir_old = ""
            self.awal = ""
            self.akhir = ""
            self.cara_bayar = ""
            self.keterangan = ""
            self.nopol = ""
            self.jenis_mobil = ""
            self.jenis_member = ""
            self.merk = ""
            self.tipe = ""
            self.tahun = ""
            self.warna = ""



    # END DATE UPDATe
    @api.onchange('duration','jenis_transaksi','stiker_id','jenis_mobil','def_akhir')
    @api.depends('stiker_id','name','duration','jenis_mobil','def_akhir')
    def calculate_start_end_date(self):

        # Pengecekan jika field duration & start_date tidak diisi, maka field end_date akan di update sama seperti field start_date
        if not self.jenis_transaksi:
            self.awal = ""
            self.akhir = ""
        elif self.jenis_transaksi == 'langganan_baru':
            tglawal = datetime.now()
            str_start_date = str(tglawal.year) + "-" + str(tglawal.month).zfill(2) + "-" + str(tglawal.day).zfill(2) + " 00:00:00"
            tglawal = datetime.strptime(str_start_date, "%Y-%m-%d %H:%M:%S")
            cal_tglawal = tglawal - relativedelta(hours=7)
            self.awal = cal_tglawal

            if self.def_akhir:
                if self.cara_bayar == 'billing':
                    self.duration = 300
                else:
                    raise ValidationError("Cara Pembayaran Harus Billing")

            tglakhir = tglawal + relativedelta(months=self.duration)

            str_end_date = str(tglakhir.year) + "-" + str(tglakhir.month).zfill(2) + "-" + str(tglakhir.day).zfill(2) + " 23:59:59"
            self.akhir = datetime.strptime(str_end_date, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)

        elif self.jenis_transaksi == 'perpanjang_baru':
            tglawal = datetime.now()
            str_start_date = str(tglawal.year) + "-" + str(tglawal.month).zfill(2) + "-" + str(tglawal.day).zfill(
                2) + " 00:00:00"
            tglawal = datetime.strptime(str_start_date, "%Y-%m-%d %H:%M:%S")
            cal_tglawal = tglawal - relativedelta(hours=7)
            self.awal = cal_tglawal

            if self.def_akhir:
                if self.cara_bayar == 'billing':
                    self.duration = 300
                else:
                    raise ValidationError("Cara Pembayaran Harus Billing")

            tglakhir = tglawal + relativedelta(months=self.duration)

            str_end_date = str(tglakhir.year) + "-" + str(tglakhir.month).zfill(2) + "-" + str(tglakhir.day).zfill(
                2) + " 23:59:59"
            self.akhir = datetime.strptime(str_end_date, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)

        elif self.jenis_transaksi == 'perpanjang':

            tglawal = fields.Datetime.from_string(self.akhir_old)
            str_start_date = str(tglawal.year) + "-" + str(tglawal.month).zfill(2) + "-" + str(tglawal.day).zfill(
                2) + " 00:00:00"
            tglawal = datetime.strptime(str_start_date, "%Y-%m-%d %H:%M:%S")
            cal_tglawal = tglawal - relativedelta(hours=7)
            self.awal = cal_tglawal

            if self.def_akhir:
                if self.cara_bayar == 'billing':
                    self.duration = 300
                else:
                    raise ValidationError("Cara Pembayaran Harus Billing")

            tglakhir = tglawal + relativedelta(months=self.duration)

            str_end_date = str(tglakhir.year) + "-" + str(tglakhir.month).zfill(2) + "-" + str(tglakhir.day).zfill(
                2) + " 23:59:59"
            self.akhir = datetime.strptime(str_end_date, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)

        elif self.jenis_transaksi == 'stop':
            date_now = datetime.now()
            tglawal = fields.Datetime.from_string(self.akhir_old) + relativedelta(hours=7)
            deposit_date = tglawal - relativedelta(months=2)

            if date_now < tglawal:
                if date_now < tglawal and date_now > deposit_date:
                    raise ValidationError("Can't stop billing because customer has a deposit")
                else:

                    tglawal = datetime(date_now.year, date_now.month, tglawal.day)
                    str_start_date = str(tglawal.year) + "-" + str(tglawal.month).zfill(2) + "-" + str(
                        tglawal.day).zfill(
                        2) + " 00:00:00"
                    tglawal = datetime.strptime(str_start_date, "%Y-%m-%d %H:%M:%S")

                    self.awal = tglawal - relativedelta(hours=7)
                    tglakhir = tglawal + relativedelta(months=self.duration)
                    str_end_date = str(tglakhir.year) + "-" + str(tglakhir.month).zfill(2) + "-" + str(
                        tglakhir.day).zfill(
                        2) + " 23:59:59"
                    self.akhir = datetime.strptime(str_end_date, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)

            else:
                raise ValidationError("Can't stop billing because billing expired")


    @api.onchange('beli_stiker')
    def calculate_harga_beli_stiker(self):

        # PILIH STIKER
        if self.beli_stiker == True:
            beli_stiker_id = self.env.user.company_id.beli_stiker_ids
            if not beli_stiker_id:
                raise ValidationError("Price Beli Stiker not defined,  please define on company information!")

            self.harga_beli_stiker = beli_stiker_id
        else:
            self.harga_beli_stiker = 0


    @api.onchange('kartu_hilang')
    def calculate_harga_kartu_hilang(self):
        if self.kartu_hilang == True:
            kartu_hilang_id = self.env.user.company_id.kartu_hilang_ids
            if not kartu_hilang_id:
                raise ValidationError("Price Kartu Parkir not defined,  please define on company information!")

            self.harga_kartu_hilang = kartu_hilang_id
        else:
            self.harga_kartu_hilang = 0


    # Calculate date range perpanjang
    def daterange(self, date1, date2):
        for n in range(int((date2 - date1).days) + 1):
            yield date1 + timedelta(n)


    @api.onchange('baru','cara_bayar','jenis_transaksi','stiker_id','duration','jenis_mobil','jenis_member')
    def calculate_harga_kontribusi(self):
        self.calculate_start_end_date()
        if self.baru == True:

            jenis_member_st_ids = self.env.user.company_id.jenis_member_st
            jenis_member_nd_ids = self.env.user.company_id.jenis_member_nd
            jenis_member_rd_ids = self.env.user.company_id.jenis_member_rd
            jenis_member_th_ids = self.env.user.company_id.jenis_member_th
            tagihan_motor_ids = self.env.user.company_id.tagihan_motor_ids

            if not jenis_member_nd_ids:
                raise ValidationError("Price 2nd Membership not defined,  please define on company information!")
            if not jenis_member_rd_ids:
                raise ValidationError("Price 3rd Membership not defined,  please define on company information!")
            if not jenis_member_th_ids:
                raise ValidationError("Price 4th Membership not defined,  please define on company information!")


            if self.jenis_transaksi == "perpanjang": # ,'perpanjang_baru'
                if self.jenis_member == "1st":
                    # 'S' - Jenis kendaraan Motor
                    if self.jenis_mobil == "S":
                        self.val_harga = int(tagihan_motor_ids) * int(self.duration)
                    else:
                        self.val_harga = int(jenis_member_st_ids)

                elif self.jenis_member == "2nd":
                    if self.cara_bayar == "non_billing":
                        # 'S' - Jenis kendaraan Motor
                        if self.jenis_mobil == "S":
                            self.val_harga = int(tagihan_motor_ids) * int(self.duration)
                        else:
                            self.val_harga = int(jenis_member_nd_ids) * int(self.duration)

                    elif self.cara_bayar == "billing":

                        tgl = fields.Datetime.from_string(self.akhir_old) # tgl akhir
                        DATE = datetime.now()   # tgl saat ini
                        _logger.info('check tgl old : '+ str(tgl))
                        _logger.info('check tgl sekarang : ' + str(DATE))

                        if tgl < DATE:
                            # ambil tanggal akhir expired
                            dt1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                            start_dt = date(dt1.year, dt1.month, dt1.day)

                            # ambil tanggal today
                            dt2 = datetime.now()
                            end_dt = date(dt2.year, dt2.month, dt2.day)

                            jml = 0
                            for dt in self.daterange(start_dt, end_dt):
                                # menentukan pertanggal 1 berdasarkan narik billing
                                if dt.day == 1:
                                    jml = jml + 1

                            hasil = int(jenis_member_nd_ids) * jml
                            jml_dp = int(jenis_member_nd_ids) * 2
                            self.val_harga = hasil + jml_dp

                        elif tgl > DATE:

                            date1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                            date2 = datetime.now()
                            _logger.info('check tgl date1 : ' + str(date1))
                            _logger.info('check tgl date2 : ' + str(date2))
                            r = relativedelta(date1, date2)
                            _logger.info('check tgl date2 : ' + str(r))

                            # Check year+1
                            if r.years == 0:
                                sum_month = r.months
                            else:
                                sum_month = r.years*12+r.months

                            _logger.info('check month : ' + str(sum_month))
                            if sum_month == 0:
                                self.val_harga = int(jenis_member_nd_ids) * 2
                            elif sum_month == 1:
                                self.val_harga = int(jenis_member_nd_ids)
                            else:
                                self.val_harga = 0

                elif self.jenis_member == "3rd":
                    if self.cara_bayar == "non_billing":
                        # 'S' - Jenis kendaraan Motor
                        if self.jenis_mobil == "S":
                            self.val_harga = int(tagihan_motor_ids) * int(self.duration)
                        else:
                            self.val_harga = int(jenis_member_rd_ids) * int(self.duration)

                    elif self.cara_bayar == "billing":

                        tgl = fields.Datetime.from_string(self.akhir_old)  # tgl akhir
                        DATE = datetime.now()  # tgl saat ini

                        if tgl < DATE:
                            # ambil tanggal akhir expired
                            dt1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                            start_dt = date(dt1.year, dt1.month, dt1.day)

                            # ambil tanggal today
                            dt2 = datetime.now()
                            end_dt = date(dt2.year, dt2.month, dt2.day)

                            jml = 0
                            for dt in self.daterange(start_dt, end_dt):
                                if dt.day == 1:
                                    jml = jml + 1

                            hasil = int(jenis_member_rd_ids) * jml
                            jml_dp = int(jenis_member_rd_ids) * 2
                            self.val_harga = hasil + jml_dp

                        elif tgl > DATE:
                            date1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                            date2 = datetime.now()
                            r = relativedelta(date1, date2)

                            # Check year+1
                            if r.years == 0:
                                sum_month = r.months
                            else:
                                sum_month = r.years * 12 + r.months

                            if sum_month == 0:
                                self.val_harga = int(jenis_member_rd_ids) * 2
                            elif sum_month == 1:
                                self.val_harga = int(jenis_member_rd_ids)
                            else:
                                self.val_harga = 0

                elif self.jenis_member == "4th":
                    if self.cara_bayar == "non_billing":
                        # 'S' - Jenis kendaraan Motor
                        if self.jenis_mobil == "S":
                            self.val_harga = int(tagihan_motor_ids) * int(self.duration)
                        else:
                            self.val_harga = int(jenis_member_th_ids) * int(self.duration)

                    elif self.cara_bayar == "billing":
                        tgl = fields.Datetime.from_string(self.akhir_old)  # tgl akhir
                        DATE = datetime.now()  # tgl saat ini

                        if tgl < DATE:
                            # ambil tanggal akhir expired
                            dt1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                            start_dt = date(dt1.year, dt1.month, dt1.day)

                            # ambil tanggal today
                            dt2 = datetime.now()
                            end_dt = date(dt2.year, dt2.month, dt2.day)

                            jml = 0
                            for dt in self.daterange(start_dt, end_dt):
                                if dt.day == 1:
                                    jml = jml + 1

                            hasil = int(jenis_member_th_ids) * jml
                            jml_dp = int(jenis_member_th_ids) * 2
                            self.val_harga = hasil + jml_dp

                        elif tgl > DATE:
                            date1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                            date2 = datetime.now()
                            r = relativedelta(date1, date2)

                            # Check year+1
                            if r.years == 0:
                                sum_month = r.months
                            else:
                                sum_month = r.years * 12 + r.months

                            if sum_month == 0:
                                self.val_harga = int(jenis_member_th_ids) * 2
                            elif sum_month == 1:
                                self.val_harga = int(jenis_member_th_ids)
                            else:
                                self.val_harga = 0


            elif self.jenis_transaksi in ["langganan_baru","perpanjang_baru"]:

                if self.jenis_member == "1st":
                    # 'S' - Jenis kendaraan Motor
                    if self.jenis_mobil == "S":
                        self.val_harga = int(tagihan_motor_ids) * int(self.duration)
                    else:
                        self.val_harga = int(jenis_member_st_ids)

                elif self.jenis_member == "2nd":
                    if self.cara_bayar == "non_billing":
                        # 'S' - Jenis kendaraan Motor
                        if self.jenis_mobil == "S":
                            self.val_harga = int(tagihan_motor_ids) * int(self.duration)
                        else:
                            self.val_harga = int(jenis_member_nd_ids) * int(self.duration)

                    elif self.cara_bayar == "billing":
                        self.val_harga = int(jenis_member_nd_ids) * 2
                    # else:
                    #     raise ValidationError("Please define on Mobil!")

                elif self.jenis_member == "3rd":
                    if self.cara_bayar == "non_billing":
                        # 'S' - Jenis kendaraan Motor
                        if self.jenis_mobil == "S":
                            self.val_harga = int(tagihan_motor_ids) * int(self.duration)
                        else:
                            self.val_harga = int(jenis_member_rd_ids) * int(self.duration)

                    elif self.cara_bayar == "billing":
                        self.val_harga = int(jenis_member_rd_ids) * 2
                    # else:
                    #     raise ValidationError("Please define on Mobil!")

                elif self.jenis_member == "4th":
                    if self.cara_bayar == "non_billing":
                        # 'S' - Jenis kendaraan Motor
                        if self.jenis_mobil == "S":
                            self.val_harga = int(tagihan_motor_ids) * int(self.duration)
                        else:
                            self.val_harga = int(jenis_member_th_ids) * int(self.duration)

                    elif self.cara_bayar == "billing":
                        self.val_harga = int(jenis_member_th_ids) * 2
                    # else:
                    #     raise ValidationError("Please define on Mobil!")

            elif self.jenis_transaksi == "stop":
                self.val_harga = jenis_member_st_ids
        else:
            self.val_harga = 0


    @api.onchange('val_harga', 'harga_beli_stiker', 'harga_ganti_nopol', 'harga_kartu_hilang')
    def calculate_total_harga(self):
        total = self.val_harga + self.harga_beli_stiker + self.harga_ganti_nopol + self.harga_kartu_hilang
        self.amount = total
        self.adm = self.create_uid


    # GENERATE TRANS ID WHERE langganan_baru
    @api.onchange('jenis_member')
    def generate_stiker_id(self):
        unit = self.unit_kerja.kode
        check = self.jenis_member

        if check == "1st":
            n = "1"
        elif check == "2nd":
            n = "2"
        elif check == "3rd":
            n = "3"
        elif check == "4th":
            n = "4"

        if self.jenis_transaksi == "langganan_baru":

            # _logger.info(unit)
            tex = unit[1:5]
            # self.stiker_id = tex + str(n)
            # _logger.info(tex)
            trans = tex + str(n)

            if not self.stiker_id:
                args = [('no_id', '=', trans)]
                res = self.env['trans.stiker'].search(args, limit=1)

                if res.no_id:
                    raise ValidationError("this trans id : " + trans + " already exists!")

                self.no_id = trans


    @api.onchange('edit_info_mobil')
    def change_info_mobil(self):
        self.merk = ""
        self.jenis_mobil = ""
        self.nopol = ""
        self.tipe = ""
        self.tahun = ""
        self.warna = ""

    @api.one
    def proses_check_ganti_nopol(self):
        base_external_dbsource_obj = self.env['base.external.dbsource']
        postgresconn = base_external_dbsource_obj.sudo().browse(1)
        postgresconn.connection_open()
        _logger.info("Connection Open")

        for trans in self:
            no_trans = trans.stiker_id.notrans
            # Kondisi pengecekan stiker
            strSQL = """SELECT no_card FROM card_member WHERE notrans='{}'""".format(no_trans)
            cardmember = postgresconn.execute(query=strSQL, metadata=False)
            _logger.info(cardmember)

            for record in cardmember:
                no_card = record[0]
                # Kondisi pengecekan stiker
                strSQL = """SELECT no_pol FROM transaksi_parkir WHERE no_pol='{}'""".format(no_card)
                trans_parkir = postgresconn.execute(query=strSQL, metadata=False)
                _logger.info(trans_parkir)

                if trans_parkir:
                    for row in trans_parkir:
                        raise ValidationError(
                            "Mobil anda masih di dalam dengan NOPOL : " + trans.stiker_id.detail_ids.nopol + ", Stiker : " + no_trans + ", No Card : " +
                            row[
                                0] + ". Silahkan mobil anda di keluarkan terlebih dahulu !!")

        # CHECK NOPOL DI STIKER LAMA
        strSQL = """SELECT nopol,notrans FROM detail_transaksi_stiker WHERE nopol='{}'""".format(
            trans.new_nopol)
        nopolcheck = postgresconn.execute(query=strSQL, metadata=False)
        _logger.info(nopolcheck)

        # KONDISI DIMANA NOPOL SUDAH ADA INGIN PINDAH STIKER ATAU UNIT
        if nopolcheck:
            for ids in nopolcheck:
                nopol = ids[0]
                no_trans = ids[1]
                # Kondisi pengecekan stiker
                strSQL = """SELECT no_card FROM card_member WHERE notrans='{}'""".format(no_trans)
                cardmember = postgresconn.execute(query=strSQL, metadata=False)
                _logger.info(cardmember)

                for record in cardmember:
                    no_card = record[0]
                    # Kondisi pengecekan stiker
                    strSQL = """SELECT no_pol FROM transaksi_parkir WHERE no_pol='{}'""".format(no_card)
                    trans_parkir = postgresconn.execute(query=strSQL, metadata=False)
                    _logger.info(trans_parkir)

                    if trans_parkir:
                        for row in trans_parkir:
                            raise ValidationError(
                                "Mobil yang ada di Stiker# : " + no_trans + ", ini masih di dalam dengan NOPOL : " + nopol + ", No Card : " +
                                row[0] + ". Silahkan mobil anda di keluarkan terlebih dahulu !!")

    @api.one
    def proses_ganti_nopol(self):

        base_external_dbsource_obj = self.env['base.external.dbsource']
        postgresconn = base_external_dbsource_obj.sudo().browse(1)
        postgresconn.connection_open()
        _logger.info("Connection Open")

        for trans in self:

            # CHECK NOPOL DI STIKER LAMA
            strSQL = """SELECT nopol,notrans FROM detail_transaksi_stiker WHERE nopol='{}'""".format(trans.new_nopol)
            nopolcheck = postgresconn.execute(query=strSQL, metadata=False)
            _logger.info(nopolcheck)

            # KONDISI DIMANA NOPOL SUDAH ADA INGIN PINDAH STIKER ATAU UNIT
            if nopolcheck:
                # 72B2
                for transstiker_ids in self.stiker_id:
                    trans_stiker_id_s = transstiker_ids.detail_ids.trans_stiker_id.id
                    nopol_s = transstiker_ids.detail_ids.nopol
                    jenis_mobil_s = transstiker_ids.detail_ids.jenis_mobil
                    jenis_member_s = transstiker_ids.detail_ids.jenis_member
                    merk_s = transstiker_ids.detail_ids.merk
                    tipe_s = transstiker_ids.detail_ids.tipe
                    tahun_s = transstiker_ids.detail_ids.tahun
                    warna_s = transstiker_ids.detail_ids.warna
                    notrans_s = transstiker_ids.detail_ids.notrans
                    kategori_s = transstiker_ids.detail_ids.kategori
                    akses_s = transstiker_ids.detail_ids.akses
                    akses_out_s = transstiker_ids.detail_ids.akses_out
                    status_s = transstiker_ids.detail_ids.status
                    keterangan_s = transstiker_ids.detail_ids.keterangan

                args = [('nopol', '=', self.new_nopol)]
                res = self.env['detail.transstiker'].sudo().search(args)

                for list in res:
                    # trans_stiker_id_l = list.trans_stiker_id.id
                    nopol_l = list.nopol
                    jenis_mobil_l = list.jenis_mobil
                    jenis_member_l = list.jenis_member
                    merk_l = list.merk
                    tipe_l = list.tipe
                    tahun_l = list.tahun
                    warna_l = list.warna
                    notrans_l = list.notrans
                    kategori_l = list.kategori
                    akses_l = list.akses
                    akses_out_l = list.akses_out
                    status_l = list.status
                    keterangan_l = list.keterangan

                # SIMPAN DATA NOPOL LAMA
                valus = {}
                valus.update({'trans_stiker_id_s': trans_stiker_id_s})
                valus.update({'nopol_s': nopol_s})  # Data Nopol pada Stiker# yang saat ini di pilih
                valus.update({'jenis_mobil_s': jenis_mobil_s})
                valus.update({'jenis_member_s': jenis_member_s})
                valus.update({'merk_s': merk_s})
                valus.update({'tipe_s': tipe_s})
                valus.update({'tahun_s': tahun_s})
                valus.update({'warna_s': warna_s})
                valus.update({'notrans_s': notrans_s})
                valus.update({'kategori_s': kategori_s})
                valus.update({'akses_s': akses_s})
                valus.update({'status_s': status_s})
                valus.update({'akses_out_s': akses_out_s})
                valus.update({'keterangan_s': keterangan_s})
                # valus.update({'trans_stiker_id_l': trans_stiker_id_l})
                # valus.update({'nopol_l': nopol_l})  # Data Nopol pada Stiker# lama yanng ingin di hapus
                # valus.update({'jenis_mobil_l': jenis_mobil_l})
                # valus.update({'jenis_member_l': jenis_member_l})
                # valus.update({'merk_l': merk_l})
                # valus.update({'tipe_l': tipe_l})
                # valus.update({'tahun_l': tahun_l})
                # valus.update({'warna_l': warna_l})
                # valus.update({'notrans_l': notrans_l})
                # valus.update({'kategori_l': kategori_l})
                # valus.update({'akses_l': akses_l})
                # valus.update({'status_l': status_l})
                # valus.update({'akses_out_l': akses_out_l})
                # valus.update({'keterangan_l': keterangan_l})

                # Convert datas to json
                str_bck_nopol = json.dumps(valus)
                datas = {}
                datas.update({'nopol_lama': str(str_bck_nopol)})
                super(RequestTransStiker, self).write(datas)

                for record in nopolcheck:
                    nopol = record[0]
                    # DELETE NOPOL PADA STIKER LAMA
                    strSQL = """DELETE FROM detail_transaksi_stiker WHERE nopol='{}'""".format(nopol)
                    delete_nopol = postgresconn.execute_general(strSQL)
                    _logger.info(delete_nopol)
                # delete nopol pada odoo
                args = [('nopol', '=', nopol)]
                self.env['detail.transstiker'].sudo().search(args).unlink()

                # CHECK NOPOL DI STIKER YANG DI PILIH SAAT INI
                strSQL = """SELECT nopol FROM detail_transaksi_stiker WHERE notrans='{}'""".format(
                    trans.stiker_id.notrans)
                nopolcheck_utama = postgresconn.execute(query=strSQL, metadata=False)
                _logger.info(nopolcheck_utama)

                if nopolcheck_utama:
                    for record in nopolcheck_utama:
                        nopol = record[0]
                        # DELETE NOPOL DI STIKER YANG DI PILIH SAAT INI
                        strSQL = """DELETE FROM detail_transaksi_stiker WHERE nopol='{}'""".format(nopol)
                        delete_nopol = postgresconn.execute_general(strSQL)
                        _logger.info(delete_nopol)

                    _logger.info('Insert Detail Trans Stiker')
                    strSQL = """INSERT INTO detail_transaksi_stiker """ \
                             """(notrans, nopol, jenis_mobil, kategori, jenis_member, akses, akses_out, status, merk, tipe,""" \
                             """tahun, warna, keterangan)""" \
                             """ VALUES """ \
                             """('{}', '{}', '{}', 0, '{}', NULL, NULL, 1, '{}', '{}', '{}',""" \
                             """'{}', '{}')""".format(
                        trans.stiker_id.notrans, trans.new_nopol, trans.new_jenis_mobil, trans.new_jenis_member,
                        trans.new_merk,
                        trans.new_tipe, trans.new_tahun, trans.new_warna, trans.ket_nopol)

                    insert_nopol = postgresconn.execute_general(strSQL)
                    _logger.info(insert_nopol)

                    args = [('notrans', '=', trans.stiker_id.notrans)]
                    res = self.env['detail.transstiker'].sudo().search(args)
                    vals = {}
                    vals.update({'nopol': trans.new_nopol})
                    vals.update({'jenis_mobil': trans.new_jenis_mobil})
                    vals.update({'merk': trans.new_merk})
                    vals.update({'tipe': trans.new_tipe})
                    vals.update({'tahun': trans.new_tahun})
                    vals.update({'warna': trans.new_warna})
                    res.write(vals)

                else:

                    _logger.info('Insert Detail Trans Stiker')
                    strSQL = """INSERT INTO detail_transaksi_stiker """ \
                             """(notrans, nopol, jenis_mobil, kategori, jenis_member, akses, akses_out, status, merk, tipe,""" \
                             """tahun, warna, keterangan)""" \
                             """ VALUES """ \
                             """('{}', '{}', '{}', 0, '{}', NULL, NULL, 1, '{}', '{}', '{}',""" \
                             """'{}', '{}')""".format(
                        trans.stiker_id.notrans, trans.new_nopol, trans.new_jenis_mobil, trans.new_jenis_member,
                        trans.new_merk,
                        trans.new_tipe, trans.new_tahun, trans.new_warna, trans.ket_nopol)

                    insert_nopol = postgresconn.execute_general(strSQL)
                    _logger.info(insert_nopol)

                    res = self.env['detail.transstiker']
                    args = [('notrans', '=', trans.stiker_id.notrans)]
                    str_id = self.env['trans.stiker'].sudo().search(args)

                    vals = {}
                    vals.update({'trans_stiker_id': str_id.id})
                    vals.update({'notrans': trans.stiker_id.notrans})
                    vals.update({'nopol': trans.new_nopol})
                    vals.update({'jenis_mobil': trans.new_jenis_mobil})
                    vals.update({'jenis_member': trans.new_jenis_member})
                    vals.update({'merk': trans.new_merk})
                    vals.update({'tipe': trans.new_tipe})
                    vals.update({'tahun': trans.new_tahun})
                    vals.update({'warna': trans.new_warna})
                    res.sudo().create(vals)


            else:

                for transstiker_ids in self.stiker_id:
                    trans_stiker_id_s = transstiker_ids.detail_ids.trans_stiker_id.id
                    nopol_s = transstiker_ids.detail_ids.nopol
                    jenis_mobil_s = transstiker_ids.detail_ids.jenis_mobil
                    jenis_member_s = transstiker_ids.detail_ids.jenis_member
                    merk_s = transstiker_ids.detail_ids.merk
                    tipe_s = transstiker_ids.detail_ids.tipe
                    tahun_s = transstiker_ids.detail_ids.tahun
                    warna_s = transstiker_ids.detail_ids.warna
                    notrans_s = transstiker_ids.detail_ids.notrans
                    kategori_s = transstiker_ids.detail_ids.kategori
                    akses_s = transstiker_ids.detail_ids.akses
                    akses_out_s = transstiker_ids.detail_ids.akses_out
                    status_s = transstiker_ids.detail_ids.status
                    keterangan_s = transstiker_ids.detail_ids.keterangan

                # SIMPAN DATA NOPOL LAMA
                valus = {}
                valus.update({'trans_stiker_id_s': trans_stiker_id_s})
                valus.update({'nopol_s': nopol_s})  # Data Nopol pada Stiker# yang saat ini di pilih
                valus.update({'jenis_mobil_s': jenis_mobil_s})
                valus.update({'jenis_member_s': jenis_member_s})
                valus.update({'merk_s': merk_s})
                valus.update({'tipe_s': tipe_s})
                valus.update({'tahun_s': tahun_s})
                valus.update({'warna_s': warna_s})
                valus.update({'notrans_s': notrans_s})
                valus.update({'kategori_s': kategori_s})
                valus.update({'akses_s': akses_s})
                valus.update({'status_s': status_s})
                valus.update({'akses_out_s': akses_out_s})
                valus.update({'keterangan_s': keterangan_s})

                args = [('nopol', '=', trans.new_nopol)]
                detail_trans_ids = self.env['detail.transstiker'].sudo().search(args)

                if detail_trans_ids:
                    for list in detail_trans_ids:
                        trans_stiker_id_l = list.trans_stiker_id.id
                        nopol_l = list.nopol
                        jenis_mobil_l = list.jenis_mobil
                        jenis_member_l = list.jenis_member
                        merk_l = list.merk
                        tipe_l = list.tipe
                        tahun_l = list.tahun
                        warna_l = list.warna
                        notrans_l = list.notrans
                        kategori_l = list.kategori
                        akses_l = list.akses
                        akses_out_l = list.akses_out
                        status_l = list.status
                        keterangan_l = list.keterangan

                    valus.update({'trans_stiker_id_l': trans_stiker_id_l})
                    valus.update({'nopol_l': nopol_l})  # Data Nopol pada Stiker# lama yanng ingin di hapus
                    valus.update({'jenis_mobil_l': jenis_mobil_l})
                    valus.update({'jenis_member_l': jenis_member_l})
                    valus.update({'merk_l': merk_l})
                    valus.update({'tipe_l': tipe_l})
                    valus.update({'tahun_l': tahun_l})
                    valus.update({'warna_l': warna_l})
                    valus.update({'notrans_l': notrans_l})
                    valus.update({'kategori_l': kategori_l})
                    valus.update({'akses_l': akses_l})
                    valus.update({'status_l': status_l})
                    valus.update({'akses_out_l': akses_out_l})
                    valus.update({'keterangan_l': keterangan_l})
                else:
                    valus.update({'trans_stiker_id_l': False})
                    valus.update({'nopol_l': False})  # Data Nopol pada Stiker# lama yanng ingin di hapus
                    valus.update({'jenis_mobil_l': False})
                    valus.update({'jenis_member_l': False})
                    valus.update({'merk_l': False})
                    valus.update({'tipe_l': False})
                    valus.update({'tahun_l': False})
                    valus.update({'warna_l': False})
                    valus.update({'notrans_l': False})
                    valus.update({'kategori_l': False})
                    valus.update({'akses_l': False})
                    valus.update({'status_l': False})
                    valus.update({'akses_out_l': False})
                    valus.update({'keterangan_l': False})

                # Convert datas to json
                str_bck_nopol = json.dumps(valus)
                datas = {}
                datas.update({'nopol_lama': str(str_bck_nopol)})
                super(RequestTransStiker, self).write(datas)


                # CHECK NOPOL DI STIKER YANG DI PILIH SAAT INI
                strSQL = """SELECT nopol,notrans FROM detail_transaksi_stiker WHERE notrans='{}'""".format(
                    trans.stiker_id.notrans)
                nopolcheck_utama = postgresconn.execute(query=strSQL, metadata=False)
                _logger.info(nopolcheck_utama)

                if nopolcheck_utama:
                    for record in nopolcheck_utama:
                        nopol = record[0]

                        # Insert Data Trans Stiker with Odoo to Database Server Parkir
                        _logger.info('Update NOPOL')
                        strSQLUpdate_nopol = """UPDATE detail_transaksi_stiker """ \
                                             """ SET """ \
                                             """nopol='{}', jenis_mobil='{}', merk='{}', tipe='{}',""" \
                                             """tahun='{}', warna='{}'""" \
                                             """ WHERE """ \
                                             """nopol='{}'""".format(trans.new_nopol, trans.new_jenis_mobil,
                                                                     trans.new_merk,
                                                                     trans.new_tipe, trans.new_tahun, trans.new_warna,
                                                                     nopol)
                        postgresconn.execute_general(strSQLUpdate_nopol)

                    args = [('notrans', '=', trans.stiker_id.notrans)]
                    res = self.env['detail.transstiker'].sudo().search(args)
                    vals = {}
                    vals.update({'nopol': trans.new_nopol})
                    vals.update({'jenis_mobil': trans.new_jenis_mobil})
                    vals.update({'merk': trans.new_merk})
                    vals.update({'tipe': trans.new_tipe})
                    vals.update({'tahun': trans.new_tahun})
                    vals.update({'warna': trans.new_warna})
                    vals.update({'keterangan': trans.ket_nopol})
                    res.write(vals)

                else:
                    _logger.info('Insert Detail Trans Stiker')
                    strSQL = """INSERT INTO detail_transaksi_stiker """ \
                             """(notrans, nopol, jenis_mobil, kategori, jenis_member, akses, akses_out, status, merk, tipe,""" \
                             """tahun, warna, keterangan)""" \
                             """ VALUES """ \
                             """('{}', '{}', '{}', 0, '{}', NULL, NULL, 1, '{}', '{}', '{}',""" \
                             """'{}', '{}')""".format(
                        trans.stiker_id.notrans, trans.new_nopol, trans.new_jenis_mobil, trans.new_jenis_member,
                        trans.new_merk,
                        trans.new_tipe, trans.new_tahun, trans.new_warna, trans.ket_nopol)

                    insert_nopol = postgresconn.execute_general(strSQL)
                    _logger.info(insert_nopol)

                    res = self.env['detail.transstiker']
                    args = [('notrans', '=', trans.stiker_id.notrans)]
                    str_id = self.env['trans.stiker'].sudo().search(args)

                    vals = {}
                    vals.update({'trans_stiker_id': str_id.id})
                    vals.update({'notrans': trans.stiker_id.notrans})
                    vals.update({'nopol': trans.new_nopol})
                    vals.update({'jenis_mobil': trans.new_jenis_mobil})
                    vals.update({'jenis_member': trans.new_jenis_member})
                    vals.update({'merk': trans.new_merk})
                    vals.update({'tipe': trans.new_tipe})
                    vals.update({'tahun': trans.new_tahun})
                    vals.update({'warna': trans.new_warna})
                    vals.update({'keterangan': trans.ket_nopol})
                    res.sudo().create(vals)

    # BUTTON DONE PAYMENT
    @api.one
    def trans_done_payment(self):

        for v in self:
            if v.baru == True:
                if v.jenis_transaksi == "perpanjang":

                    # Process perpanjang to Server Database Parkir and update trans_id
                    base_external_dbsource_obj = self.env['base.external.dbsource']
                    postgresconn = base_external_dbsource_obj.sudo().browse(1)
                    postgresconn.connection_open()
                    _logger.info("Connection Open")
                    _logger.info("Sync Stasiun Kerja")

                    tglakhir = datetime.strptime(v.akhir, "%Y-%m-%d %H:%M:%S") + relativedelta(hours=7)

                    # Insert Data Trans Stiker with Odoo to Database Server Parkir
                    _logger.info('Update Data Trans Stiker')
                    strSQLUpdate_akhir = """UPDATE transaksi_stiker """ \
                             """ SET akhir='{}'""" \
                             """ WHERE """ \
                             """notrans='{}'""".format(tglakhir, self.stiker_id.notrans)

                    postgresconn.execute_general(strSQLUpdate_akhir)

                    # UPDATE TO TRANS STIKER ODOO
                    args = [('id', '=', v.stiker_id.id)]
                    self.env['trans.stiker'].search(args).sudo().write({'akhir': v.akhir})

                if v.jenis_transaksi == "perpanjang_baru":
                    base_external_dbsource_obj = self.env['base.external.dbsource']
                    postgresconn = base_external_dbsource_obj.sudo().browse(1)
                    postgresconn.connection_open()
                    _logger.info('Connection Open')

                    if self.ganti_nopol_pb:

                        # CHECK NOPOL DI STIKER YANG DI PILIH SAAT INI
                        strSQL = """SELECT nopol FROM detail_transaksi_stiker WHERE notrans='{}'""".format(
                            self.stiker_id.notrans)
                        nopolcheck_utama = postgresconn.execute(query=strSQL, metadata=False)
                        _logger.info(nopolcheck_utama)

                        if nopolcheck_utama:

                            for record in nopolcheck_utama:
                                nopol = record[0]

                                _logger.info('Update NOPOL')
                                strSQLUpdate_nopol = """UPDATE detail_transaksi_stiker """ \
                                                     """ SET """ \
                                                     """nopol='{}', jenis_mobil='{}', merk='{}', tipe='{}',""" \
                                                     """tahun='{}', warna='{}'""" \
                                                     """ WHERE """ \
                                                     """nopol='{}'""".format(v.new_nopol_pb, v.new_jenis_mobil_pb,
                                                                             v.new_merk_pb,
                                                                             v.new_tipe_pb, v.new_tahun_pb, v.new_warna_pb,
                                                                             nopol)
                                update_nopol = postgresconn.execute_general(strSQLUpdate_nopol)
                                _logger.info(update_nopol)

                                args = [('notrans', '=', v.stiker_id.notrans)]
                                res = self.env['detail.transstiker'].sudo().search(args)
                                vals = {}
                                vals.update({'nopol': v.new_nopol_pb})
                                vals.update({'jenis_mobil': v.new_jenis_mobil_pb})
                                vals.update({'merk': v.new_merk_pb})
                                vals.update({'tipe': v.new_tipe_pb})
                                vals.update({'tahun': v.new_tahun_pb})
                                vals.update({'warna': v.new_warna_pb})
                                res.write(vals)
                        else:

                            _logger.info('Insert Detail Trans Stiker')
                            strSQL = """INSERT INTO detail_transaksi_stiker """ \
                                     """(notrans, nopol, jenis_mobil, kategori, jenis_member, akses, akses_out, status, merk, tipe,""" \
                                     """tahun, warna)""" \
                                     """ VALUES """ \
                                     """('{}', '{}', '{}', 0, '{}', NULL, NULL, 1, '{}', '{}', '{}',""" \
                                     """'{}')""".format(
                                v.stiker_id.notrans, v.new_nopol_pb, v.new_jenis_mobil_pb, v.jenis_member,
                                v.new_merk_pb, v.new_tipe_pb, v.new_tahun_pb, v.new_warna_pb)

                            insert_nopol = postgresconn.execute_general(strSQL)
                            _logger.info(insert_nopol)

                            res = self.env['detail.transstiker']
                            args = [('notrans', '=', v.stiker_id.notrans)]
                            str_id = self.env['trans.stiker'].sudo().search(args)

                            vals = {}
                            vals.update({'trans_stiker_id': str_id.id})
                            vals.update({'notrans': v.stiker_id.notrans})
                            vals.update({'nopol': v.new_nopol_pb})
                            vals.update({'jenis_mobil': v.new_jenis_mobil_pb})
                            vals.update({'jenis_member': v.jenis_member})
                            vals.update({'merk': v.new_merk_pb})
                            vals.update({'tipe': v.new_tipe_pb})
                            vals.update({'tahun': v.new_tahun_pb})
                            vals.update({'warna': v.new_warna_pb})
                            res.sudo().create(vals)

                    tglakhir = datetime.strptime(v.akhir, "%Y-%m-%d %H:%M:%S") + relativedelta(hours=7)

                    # Insert Data Trans Stiker with Odoo to Database Server Parkir
                    _logger.info('Update Data Trans Stiker')
                    strSQLUpdate_akhir = """UPDATE transaksi_stiker """ \
                                         """ SET akhir='{}'""" \
                                         """ WHERE """ \
                                         """notrans='{}'""".format(tglakhir, v.no_id)

                    postgresconn.execute_general(strSQLUpdate_akhir)

                    # UPDATE TO TRANS STIKER ODOO
                    args = [('id', '=', v.stiker_id.id)]
                    self.env['trans.stiker'].search(args).sudo().write({'akhir': v.akhir})


                if v.jenis_transaksi == "langganan_baru":

                    # Process create langganan_baru to Server Database Parkir and update trans_id
                    base_external_dbsource_obj = self.env['base.external.dbsource']
                    transaksi_stiker_obj = self.env['trans.stiker']
                    detail_stiker_obj = self.env['detail.transstiker']
                    postgresconn = base_external_dbsource_obj.sudo().browse(1)
                    postgresconn.connection_open()
                    _logger.info("Connection Open")
                    _logger.info("Sync Stasiun Kerja")

                    check = self.jenis_transaksi
                    if check == "langganan_baru":
                        jt = 0
                    elif check == "perpanjang":
                        jt = 1
                    elif check == "stop":
                        jt = 2

                    check_row = self.jenis_member
                    if check_row == "1st":
                        j_member = 'C'
                    elif check_row == "2nd":
                        j_member = 'C2'
                    elif check_row == "3rd":
                        j_member = 'C3'
                    elif check_row == "4th":
                        j_member = 'C4'

                    DATE = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    if self.cara_bayar == "non_billing":
                        cb = 0
                    else:
                        cb = 1


                # ================================  CHECK & CREATE DATA KE SERVER PARKIR  ==================================

                    # Kondisi pengecekan stiker
                    # strSQL = """SELECT notrans FROM transaksi_stiker WHERE notrans='{}'""".format(self.no_id)
                    # stikercheck = postgresconn.execute(query=strSQL, metadata=False)
                    # _logger.info(stikercheck)
                    #
                    # for record in stikercheck:
                    #     record_one = self.find_detail_stiker(record[0])
                    #     # Kondisi ketika stiker tidak ada maka di jalankan
                    #     if not record_one:
                    #         # Insert Data Trans Stiker with Odoo to Database Server Parkir

                    tglawal = datetime.strptime(self.awal, "%Y-%m-%d %H:%M:%S") + relativedelta(hours=7)
                    tglakhir = datetime.strptime(self.akhir, "%Y-%m-%d %H:%M:%S") + relativedelta(hours=7)
                    tlp = "Tidak Bayar"
                    _logger.info('Insert Data Trans Stiker')
                    strSQL = """INSERT INTO transaksi_stiker """ \
                             """(notrans, nama, alamat, telepon, jenis_transaksi, awal, harga, keterangan, tanggal, operator, akhir,""" \
                             """maks, no_id, unit_kerja, no_induk, jenis_stiker, hari_ke, jenis_langganan, exit_pass, no_kuitansi, tgl_edited,""" \
                             """tipe_exit_pass, seq_code, unitno, area, reserved, cara_bayar)""" \
                             """ VALUES """ \
                             """('{}', '{}', '{}', '{}', '{}', '{}', 0, '{}', '{}', '{}', '{}', 1,""" \
                             """'{}', '{}', NULL, 0, NULL, '{}', 0, '{}', '{}', 1, 0, NULL, NULL, 0, '{}')""".format(
                        self.no_id, self.name, self.alamat, tlp, jt, tglawal, self.keterangan, self.tanggal,
                        self.adm.name,
                        tglakhir, self.no_id, self.unit_kerja.kode, j_member, self.no_id, DATE, cb)

                    ts1 = postgresconn.execute_general(strSQL)

                    _logger.info(ts1)

                    # Kondisi pengecekan stiker
                    # strSQL = """SELECT notrans FROM detail_transaksi_stiker WHERE notrans='{}'""".format(self.no_id)
                    # detailstikercheck = postgresconn.execute(query=strSQL, metadata=False)
                    # _logger.info(detailstikercheck)
                    #
                    # for detailrecord in detailstikercheck:
                    #     record_two = self.find_detail_stiker(detailrecord[0])
                    #     # Kondisi ketika stiker tidak ada maka di jalankan
                    #     if not record_two:
                    # Insert Detail Trans Stiker with Odoo to Database Server Parkir
                    _logger.info('Insert Detail Trans Stiker')
                    strSQL2 = """INSERT INTO detail_transaksi_stiker """ \
                                """(notrans, nopol, jenis_mobil, adm, kategori, jenis_member, akses, akses_out, status, merk, tipe,""" \
                                """tahun, warna, keterangan)""" \
                                """ VALUES """ \
                                """('{}', '{}', '{}', '{}', 0, '{}', NULL, NULL, 1, '{}', '{}', '{}',""" \
                                """'{}', '{}')""".format(
                        self.no_id, self.nopol, self.jenis_mobil, self.adm.name, self.jenis_member, self.merk,
                        self.tipe, self.tahun, self.warna, self.keterangan)

                    # _logger.info()
                    ts2 = postgresconn.execute_general(strSQL2)
                    _logger.info(ts2)

                # ============================================   END   =========================================================


                # ==============================  SELECT DATA KE SERVER PARKIR & CREATE KE ODOO  ===============================

                    _logger.info('Sync Transaksi Stiker')
                    strSQL = """SELECT """ \
                             """notrans,nama,alamat,telepon,jenis_transaksi,""" \
                             """awal,harga,keterangan,tanggal,operator,akhir,""" \
                             """maks,no_id,unit_kerja,no_induk,jenis_stiker,hari_ke,""" \
                             """jenis_langganan,exit_pass,no_kuitansi,tgl_edited,tipe_exit_pass,""" \
                             """seq_code,unitno,area,reserved,cara_bayar """ \
                             """FROM transaksi_stiker WHERE no_id='{}'""".format(self.no_id)
                    transaksistikers = postgresconn.execute(query=strSQL, metadata=False)
                    _logger.info(transaksistikers)
                    for transaksistiker in transaksistikers:
                        current_record = self.find_transaksi_stiker(transaksistiker[0])
                        if current_record:
                            stasiunkerja = self.find_stasiun_kerja(transaksistiker[13])
                            vals = {}
                            vals.update({'stasiun_kerja_id': stasiunkerja.id})
                            vals.update({'notrans': transaksistiker[0]})
                            vals.update({'name': transaksistiker[1]})
                            vals.update({'alamat': transaksistiker[2]})
                            vals.update({'telphone': transaksistiker[3]})
                            jt = transaksistiker[4]
                            if jt == 0:
                                vals.update({'jenis_transaksi': 'langganan_baru'})
                            elif jt == 1:
                                vals.update({'jenis_transaksi': 'perpanjang'})
                            else:
                                vals.update({'jenis_transaksi': 'stop'})
                            tglawal = fields.Datetime.from_string(transaksistiker[5]) - relativedelta(hours=7)
                            vals.update({'awal': tglawal})
                            vals.update({'harga': transaksistiker[6]})
                            vals.update({'keterangan': transaksistiker[7]})
                            tgl = fields.Datetime.from_string(transaksistiker[8]) - relativedelta(hours=7)
                            vals.update({'tanggal': tgl})
                            vals.update({'operator': transaksistiker[9]})
                            tglakhir = fields.Datetime.from_string(transaksistiker[10]) - relativedelta(hours=7)
                            vals.update({'akhir': tglakhir})
                            vals.update({'maks': transaksistiker[11]})
                            vals.update({'no_id': transaksistiker[12]})
                            vals.update({'unit_kerja': stasiunkerja.id})
                            vals.update({'no_induk': transaksistiker[14]})
                            vals.update({'jenis_stiker': transaksistiker[15]})
                            vals.update({'hari_ke': transaksistiker[16]})
                            vals.update({'jenis_langganan': transaksistiker[17]})
                            vals.update({'exit_pass': transaksistiker[18]})
                            vals.update({'no_kuitansi': transaksistiker[19]})
                            tgledit = fields.Datetime.from_string(transaksistiker[20]) - relativedelta(hours=7)
                            vals.update({'tgl_edited': tgledit})
                            vals.update({'tipe_exit_pass': transaksistiker[21]})
                            vals.update({'seq_code': transaksistiker[22]})
                            vals.update({'unitno': transaksistiker[23]})
                            vals.update({'area': transaksistiker[24]})
                            vals.update({'reserved': transaksistiker[25]})
                            if transaksistiker[26] == 0:
                                vals.update({'cara_bayar': 'non_billing'})
                            else:
                                vals.update({'cara_bayar': 'billing'})
                            current_record.sudo().write(vals)
                            _logger.info('Transaksi Stiker Updated')
                        else:
                            stasiunkerja = self.find_stasiun_kerja(transaksistiker[13])
                            vals = {}
                            vals.update({'stasiun_kerja_id': stasiunkerja.id})
                            vals.update({'notrans': transaksistiker[0]})
                            vals.update({'name': transaksistiker[1]})
                            vals.update({'alamat': transaksistiker[2]})
                            _logger.info(transaksistiker[3])
                            vals.update({'telphone': transaksistiker[3]})
                            jt = transaksistiker[4]
                            if jt == 0:
                                vals.update({'jenis_transaksi': 'langganan_baru'})
                            elif jt == 1:
                                vals.update({'jenis_transaksi': 'perpanjang'})
                            else:
                                vals.update({'jenis_transaksi': 'stop'})
                            tglawal = fields.Datetime.from_string(transaksistiker[5]) - relativedelta(hours=7)
                            vals.update({'awal': tglawal})
                            vals.update({'harga': transaksistiker[6]})
                            vals.update({'keterangan': transaksistiker[7]})
                            tgl = fields.Datetime.from_string(transaksistiker[8]) - relativedelta(hours=7)
                            vals.update({'tanggal': tgl})
                            vals.update({'operator': transaksistiker[9]})
                            tglakhir = fields.Datetime.from_string(transaksistiker[10]) - relativedelta(hours=7)
                            vals.update({'akhir': tglakhir})
                            vals.update({'maks': transaksistiker[11]})
                            vals.update({'no_id': transaksistiker[12]})
                            vals.update({'unit_kerja': transaksistiker[13]})
                            vals.update({'no_induk': transaksistiker[14]})
                            vals.update({'jenis_stiker': transaksistiker[15]})
                            vals.update({'hari_ke': transaksistiker[16]})
                            vals.update({'jenis_langganan': transaksistiker[17]})
                            vals.update({'exit_pass': transaksistiker[18]})
                            vals.update({'no_kuitansi': transaksistiker[19]})
                            tgledit = fields.Datetime.from_string(transaksistiker[20]) - relativedelta(hours=7)
                            vals.update({'tgl_edited': tgledit})
                            vals.update({'tipe_exit_pass': transaksistiker[21]})
                            vals.update({'seq_code': transaksistiker[22]})
                            vals.update({'unitno': transaksistiker[23]})
                            vals.update({'area': transaksistiker[24]})
                            vals.update({'reserved': transaksistiker[25]})
                            if transaksistiker[26] == 0:
                                vals.update({'cara_bayar': 'non_billing'})
                            else:
                                vals.update({'cara_bayar': 'billing'})
                            transaksi_stiker_obj.sudo().create(vals)
                            _logger.info('Transaksi Stiker Created')

                    _logger.info('Sync Detail Transaksi Stiker')
                    strSQL = """SELECT notrans,nopol,jenis_mobil,adm,kategori,""" \
                             """jenis_member,akses,akses_out,status,merk,tipe,""" \
                             """tahun,warna,keterangan FROM detail_transaksi_stiker WHERE notrans='{}'""".format(self.no_id)

                    detailstikers = postgresconn.execute(query=strSQL, metadata=False)
                    for detailstiker in detailstikers:
                        current_record = self.find_detail_stiker(detailstiker[0])
                        if current_record:
                            transaksistiker = self.find_transaksi_stiker(detailstiker[0])
                            vals = {}
                            vals.update({'trans_stiker_id': transaksistiker.id})
                            vals.update({'notrans': detailstiker[0]})
                            vals.update({'nopol': detailstiker[1]})
                            vals.update({'jenis_mobil': detailstiker[2]})
                            vals.update({'adm': detailstiker[3]})
                            vals.update({'kategori': detailstiker[4]})
                            vals.update({'jenis_member': detailstiker[5]})
                            vals.update({'akses': detailstiker[6]})
                            vals.update({'akses_out': detailstiker[7]})
                            vals.update({'status': detailstiker[8]})
                            vals.update({'merk': detailstiker[9]})
                            vals.update({'tipe': detailstiker[10]})
                            vals.update({'tahun': detailstiker[11]})
                            vals.update({'warna': detailstiker[12]})
                            vals.update({'keterangan': detailstiker[13]})
                            current_record.sudo().write(vals)
                            _logger.info("Detail Updated")
                        else:
                            transaksistiker = self.find_transaksi_stiker(detailstiker[0])
                            vals = {}
                            vals.update({'trans_stiker_id': transaksistiker.id})
                            vals.update({'notrans': detailstiker[0]})
                            vals.update({'nopol': detailstiker[1]})
                            vals.update({'jenis_mobil': detailstiker[2]})
                            vals.update({'adm': detailstiker[3]})
                            vals.update({'kategori': detailstiker[4]})
                            vals.update({'jenis_member': detailstiker[5]})
                            vals.update({'akses': detailstiker[6]})
                            vals.update({'akses_out': detailstiker[7]})
                            vals.update({'status': detailstiker[8]})
                            vals.update({'merk': detailstiker[9]})
                            vals.update({'tipe': detailstiker[10]})
                            vals.update({'tahun': detailstiker[11]})
                            vals.update({'warna': detailstiker[12]})
                            vals.update({'keterangan': detailstiker[13]})
                            detail_stiker_obj.sudo().create(vals)
                            _logger.info("Detail Created")

                    args = [('no_id', '=', self.no_id)]
                    res = self.env['trans.stiker'].search(args, limit=1)
                    datas = {}
                    datas.update({'stiker_id': res.id})
                    super(RequestTransStiker, self).write(datas)

                # =============================================   END   =======================================================

                if v.jenis_transaksi == "stop":

                    # Process perpanjang to Server Database Parkir and update trans_id
                    base_external_dbsource_obj = self.env['base.external.dbsource']
                    postgresconn = base_external_dbsource_obj.sudo().browse(1)
                    postgresconn.connection_open()
                    _logger.info("Connection Open")
                    _logger.info("Sync Stasiun Kerja")

                    tglakhir = datetime.strptime(v.akhir, "%Y-%m-%d %H:%M:%S") + relativedelta(hours=7)

                    # Insert Data Trans Stiker with Odoo to Database Server Parkir
                    _logger.info('Update Data Trans Stiker')
                    strSQLUpdate_akhir = """UPDATE transaksi_stiker """ \
                                         """ SET akhir='{}', cara_bayar='{}'""" \
                                         """ WHERE """ \
                                         """notrans='{}'""".format(tglakhir,0, self.stiker_id.notrans)

                    postgresconn.execute_general(strSQLUpdate_akhir)

                    # UPDATE TO TRANS STIKER ODOO
                    args = [('id', '=', v.stiker_id.id)]
                    res = self.env['trans.stiker'].search(args).sudo().write({'akhir': v.akhir})

            if v.ganti_nopol == True:
                # Proses Ganti Nopol
                self.proses_ganti_nopol()

            if v.kartu_hilang == True:
                # Process perpanjang to Server Database Parkir and update trans_id
                base_external_dbsource_obj = self.env['base.external.dbsource']
                postgresconn = base_external_dbsource_obj.sudo().browse(1)
                postgresconn.connection_open()
                _logger.info("Connection Open")

                tglakhir_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                tglakhir = datetime.strptime(tglakhir_str, "%Y-%m-%d %H:%M:%S")
                DATE = tglakhir + relativedelta(hours=7)

                RTS_adm = v.adm.name

                _logger.info('Get Card Member')
                strSQL = """DELETE FROM card_member WHERE notrans='{}'""".format(v.stiker_id.notrans)

                postgresconn.execute_general(strSQL)
                # postgresconn.execute(query=strSQL, metadata=False)

                # if select_card_member:
                #     for datas in select_card_member:
                #         # Insert Data Trans Stiker with Odoo to Database Server Parkir
                #         _logger.info('Update NOPOL')
                #         strSQL_cardmember = """UPDATE card_member """ \
                #                             """SET """ \
                #                             """no_card='{}', no_urut='{}', tanggal='{}', adm='{}'""" \
                #                             """ WHERE """ \
                #                             """notrans='{}'""".format(v.no_kartu, v.no_urut, DATE, RTS_adm,
                #                                                       datas[0])
                #
                # else:

                # Insert Data Trans Stiker with Odoo to Database Server Parkir
                _logger.info('INSERT CARD MEMBER')
                strSQL_cardmember = """INSERT INTO card_member """ \
                                    """(notrans,no_card,no_urut,tanggal,adm)""" \
                                    """ VALUES """ \
                                    """('{}','{}','{}','{}','{}')""".format(v.stiker_id.notrans, v.no_kartu,
                                                                            v.no_urut,
                                                                            DATE,
                                                                            RTS_adm)

                postgresconn.execute_general(strSQL_cardmember)


        datas = {}
        datas.update({'state': 'done'})
        super(RequestTransStiker, self).write(datas)

        # =================

        desired_group_name = self.env['res.groups'].sudo().search([('name', '=', 'Duty Manager')])
        is_desired_group = self.env.user.id in desired_group_name.users.ids

        if is_desired_group:
            args = [('name', '=', 'Done Payment')]
            template_ids = self.env['mail.template'].search(args)  # search tamplate dengan nama : Request for Cancel
            template_ids[0].sudo().send_mail(self.id, force_send=True)

            self.message_post("Send Email notification done payment from Duty Manager")
        self.message_post("Done Payment")

    @api.one
    def trans_approve(self):
        state = "request_cancel"
        if self.baru == True:

            if self.jenis_transaksi == "perpanjang":
                # Process perpanjang to Server Database Parkir and update trans_id
                base_external_dbsource_obj = self.env['base.external.dbsource']
                postgresconn = base_external_dbsource_obj.sudo().browse(1)
                postgresconn.connection_open()
                _logger.info("Connection Open")
                _logger.info("Sync Stasiun Kerja")

                # Insert Data Trans Stiker with Odoo to Database Server Parkir
                _logger.info('Update Data Trans Stiker')
                strSQLUpdate_akhir = """UPDATE transaksi_stiker """ \
                                     """ SET akhir='{}'""" \
                                     """ WHERE """ \
                                     """notrans='{}'""".format(self.akhir_old, self.stiker_id.notrans)

                postgresconn.execute_general(strSQLUpdate_akhir)

                # UPDATE TO TRANS STIKER ODOO
                args = [('id', '=', self.stiker_id.id)]
                self.env['trans.stiker'].search(args).sudo().write({'awal':self.awal_old, 'akhir': self.akhir_old})

                state = "cancel"

            if self.jenis_transaksi == "perpanjang_baru":
                # Process perpanjang to Server Database Parkir and update trans_id
                base_external_dbsource_obj = self.env['base.external.dbsource']
                postgresconn = base_external_dbsource_obj.sudo().browse(1)
                postgresconn.connection_open()
                _logger.info("Connection Open")
                _logger.info("Sync Stasiun Kerja")

                # Insert Data Trans Stiker with Odoo to Database Server Parkir
                _logger.info('Update Data Trans Stiker')
                strSQLUpdate_akhir = """UPDATE transaksi_stiker """ \
                                     """ SET akhir='{}'""" \
                                     """ WHERE """ \
                                     """notrans='{}'""".format(self.akhir_old, self.stiker_id.notrans)

                postgresconn.execute_general(strSQLUpdate_akhir)

                if self.ganti_nopol_pb == True:
                    # Insert Data Trans Stiker with Odoo to Database Server Parkir
                    _logger.info('Update NOPOL')
                    strSQLUpdate_nopol = """UPDATE detail_transaksi_stiker """ \
                                         """ SET """ \
                                         """nopol='{}', jenis_mobil='{}', merk='{}', tipe='{}',""" \
                                         """tahun='{}', warna='{}'""" \
                                         """ WHERE """ \
                                         """notrans='{}'""".format(self.nopol, self.jenis_mobil, self.merk, self.tipe,
                                                                   self.tahun, self.warna, self.stiker_id.notrans)

                    postgresconn.execute_general(strSQLUpdate_nopol)

                    args = [('notrans', '=', self.stiker_id.notrans)]
                    res = self.env['detail.transstiker'].search(args)
                    vals = {}
                    vals.update({'nopol': self.nopol})
                    vals.update({'jenis_mobil': self.jenis_mobil})
                    vals.update({'merk': self.merk})
                    vals.update({'tipe': self.tipe})
                    vals.update({'tahun': self.tahun})
                    vals.update({'warna': self.warna})
                    res.sudo().write(vals)

                # UPDATE TO TRANS STIKER ODOO
                args = [('id', '=', self.stiker_id.id)]
                self.env['trans.stiker'].search(args).sudo().write({'awal':self.awal_old, 'akhir': self.akhir_old})

                state = "cancel"

            if self.jenis_transaksi == "langganan_baru":

                # Process create langganan_baru to Server Database Parkir and update trans_id
                base_external_dbsource_obj = self.env['base.external.dbsource']
                transaksi_stiker_obj = self.env['trans.stiker']
                detail_stiker_obj = self.env['detail.transstiker']
                postgresconn = base_external_dbsource_obj.sudo().browse(1)
                postgresconn.connection_open()
                _logger.info("Connection Open")
                _logger.info("Sync Stasiun Kerja")


                # DELETE Data Trans Stiker
                _logger.info('DELETE Data Trans Stiker')
                strSQL = """DELETE FROM transaksi_stiker WHERE notrans='{}'""".format(self.stiker_id.notrans)

                postgresconn.execute_general(strSQL)

                # DELETE Data Detail Trans Stiker
                _logger.info('DELETE Data Detail Trans Stiker')
                strSQL2 = """DELETE FROM detail_transaksi_stiker WHERE notrans='{}'""".format(self.stiker_id.notrans)

                # _logger.info()
                postgresconn.execute_general(strSQL2)

                # DELETE Data Card Member
                _logger.info('DELETE Data Card Member')
                strSQL3 = """DELETE FROM card_member WHERE notrans='{}'""".format(self.stiker_id.notrans)

                postgresconn.execute_general(strSQL3)

                # delete cancel
                args1 = [('notrans', '=', self.stiker_id.notrans)]
                self.env['detail.transstiker'].search(args1).sudo().unlink()

                # delete cancel
                args2 = [('id', '=', self.stiker_id.id)]
                self.env['trans.stiker'].search(args2).sudo().unlink()

                state = "cancel"

            if self.jenis_transaksi == "stop":
                # Process perpanjang to Server Database Parkir and update trans_id
                base_external_dbsource_obj = self.env['base.external.dbsource']
                postgresconn = base_external_dbsource_obj.sudo().browse(1)
                postgresconn.connection_open()
                _logger.info("Connection Open")
                _logger.info("Sync Stasiun Kerja")

                if self.cara_bayar == 'non_billing':
                    cara_b = 0
                else:
                    cara_b = 1

                # Insert Data Trans Stiker with Odoo to Database Server Parkir
                _logger.info('Update Data Trans Stiker')
                strSQLUpdate_akhir = """UPDATE transaksi_stiker """ \
                                     """ SET akhir='{}', cara_bayar='{}'""" \
                                     """ WHERE """ \
                                     """notrans='{}'""".format(self.akhir_old, cara_b, self.stiker_id.notrans)

                postgresconn.execute_general(strSQLUpdate_akhir)

                # UPDATE TO TRANS STIKER ODOO
                args = [('id', '=', self.stiker_id.id)]
                self.env['trans.stiker'].search(args).sudo().write({'akhir': self.akhir_old})

                state = "cancel"

        if self.ganti_nopol == True:
            # Process perpanjang to Server Database Parkir and update trans_id
            base_external_dbsource_obj = self.env['base.external.dbsource']
            postgresconn = base_external_dbsource_obj.sudo().browse(1)
            postgresconn.connection_open()
            _logger.info("Connection Open")

            # Ambil data json backup nopol
            datas = json.loads(self.nopol_lama)

            if datas["nopol_l"] != False:
                _logger.info('Insert Detail Trans Stiker')
                strSQL = """INSERT INTO detail_transaksi_stiker """ \
                         """(notrans, nopol, jenis_mobil, kategori, jenis_member, akses, akses_out, status, merk, tipe,""" \
                         """tahun, warna, keterangan)""" \
                         """ VALUES """ \
                         """('{}', '{}', '{}', 0, '{}', NULL, NULL, 1, '{}', '{}', '{}',""" \
                         """'{}', '{}')""".format(
                    datas["notrans_l"], datas["nopol_l"], datas["jenis_mobil_l"], datas["jenis_member_l"],
                    datas["merk_l"],
                    datas["tipe_l"], datas["tahun_l"], datas["warna_l"], datas["keterangan_l"])

                postgresconn.execute_general(strSQL)

                res = self.env['detail.transstiker']
                vals = {}
                vals.update({'trans_stiker_id': datas["trans_stiker_id_l"]})
                vals.update({'notrans': datas["notrans_l"]})
                vals.update({'nopol': datas["nopol_l"]})
                vals.update({'jenis_mobil': datas["jenis_mobil_l"]})
                vals.update({'adm': self.adm.name})
                vals.update({'kategori': datas["kategori_l"]})
                vals.update({'jenis_member': datas["jenis_member_l"]})
                vals.update({'akses': datas["akses_l"]})
                vals.update({'akses_out': datas["akses_out_l"]})
                vals.update({'status': datas["status_l"]})
                vals.update({'merk': datas["merk_l"]})
                vals.update({'tipe': datas["tipe_l"]})
                vals.update({'tahun': datas["tahun_l"]})
                vals.update({'warna': datas["warna_l"]})
                vals.update({'keterangan': datas["keterangan_l"]})
                res.sudo().create(vals)
                _logger.info("Detail Create Backup Nopol Lama")

            if datas["nopol_s"]:
                # Insert Data Trans Stiker with Odoo to Database Server Parkir
                _logger.info('Update NOPOL')
                strSQLUpdate_nopol = """UPDATE detail_transaksi_stiker """ \
                                     """ SET """ \
                                     """nopol='{}', jenis_mobil='{}', jenis_member='{}', merk='{}', tipe='{}',""" \
                                     """tahun='{}', warna='{}'""" \
                                     """ WHERE """ \
                                     """notrans='{}'""".format(datas["nopol_s"], datas["jenis_mobil_s"],
                                                               datas["jenis_member_s"], datas["merk_s"],
                                                               datas["tipe_s"],
                                                               datas["tahun_s"], datas["warna_s"],
                                                               self.stiker_id.notrans)

                postgresconn.execute_general(strSQLUpdate_nopol)

                args = [('trans_stiker_id', '=', datas["trans_stiker_id_s"])]
                res = self.env['detail.transstiker'].search(args)
                vals = {}
                vals.update({'notrans': datas["notrans_s"]})
                vals.update({'nopol': datas["nopol_s"]})
                vals.update({'jenis_mobil': datas["jenis_mobil_s"]})
                vals.update({'adm': self.adm.name})
                vals.update({'kategori': datas["kategori_s"]})
                vals.update({'jenis_member': datas["jenis_member_s"]})
                vals.update({'akses': datas["akses_s"]})
                vals.update({'akses_out': datas["akses_out_s"]})
                vals.update({'status': datas["status_s"]})
                vals.update({'merk': datas["merk_s"]})
                vals.update({'tipe': datas["tipe_s"]})
                vals.update({'tahun': datas["tahun_s"]})
                vals.update({'warna': datas["warna_s"]})
                vals.update({'keterangan': datas["keterangan_s"]})
                res.sudo().write(vals)
                _logger.info("Detail Create Backup Nopol Saat ini")

            state = "cancel"

        if self.kartu_hilang == True:
            # Process perpanjang to Server Database Parkir and update trans_id
            base_external_dbsource_obj = self.env['base.external.dbsource']
            postgresconn = base_external_dbsource_obj.sudo().browse(1)
            postgresconn.connection_open()
            _logger.info("Connection Open")

            DATE = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Insert Data Trans Stiker with Odoo to Database Server Parkir
            _logger.info('Update NOPOL')
            strSQLUpdate_cardmember = """UPDATE card_member """ \
                                      """ SET """ \
                                      """no_card='{}', no_urut='{}', tanggal='{}'""" \
                                      """ WHERE """ \
                                      """notrans='{}'""".format(self.old_no_kartu, self.old_no_urut, DATE, self.stiker_id.notrans)

            postgresconn.execute_general(strSQLUpdate_cardmember)

            state = "cancel"

        datas = {}
        datas.update({'state': state})
        super(RequestTransStiker, self).write(datas)

        self.message_post("Request for Cancel - Approve")

    # Buttom Payment
    @api.one
    def trans_payment(self):
        self.message_post("Save Request Transaction Stiker")
        self.state = "confirm"

    # Buttom Confirm
    @api.one
    def trans_confirm(self):
        self.message_post("Confirm Request Transaction Stiker")
        for trans in self:

            state = "payment"
            if trans.baru == True and trans.amount == 0:
                self.trans_done_payment()
                state = "done"

            if trans.ganti_nopol == True and trans.amount == 0:

                check_row = self.stiker_id.notrans[4]

                if check_row == "1":
                    # Call proses ganti nopol
                    self.proses_ganti_nopol()

                    state = "done"

            if trans.jenis_transaksi == 'stop' and trans.amount == 0:
                # Process perpanjang to Server Database Parkir and update trans_id
                base_external_dbsource_obj = self.env['base.external.dbsource']
                postgresconn = base_external_dbsource_obj.sudo().browse(1)
                postgresconn.connection_open()
                _logger.info("Connection Open")

                tglakhir = datetime.strptime(trans.akhir, "%Y-%m-%d %H:%M:%S") + relativedelta(hours=7)

                # Insert Data Trans Stiker with Odoo to Database Server Parkir
                _logger.info('Update Data Trans Stiker')
                strSQLUpdate_akhir = """UPDATE transaksi_stiker """ \
                                     """ SET akhir='{}', cara_bayar='{}'""" \
                                     """ WHERE """ \
                                     """notrans='{}'""".format(tglakhir, 0, trans.stiker_id.notrans)

                postgresconn.execute_general(strSQLUpdate_akhir)

                # UPDATE TO TRANS STIKER ODOO
                args = [('id', '=', trans.stiker_id.id)]
                self.env['trans.stiker'].search(args).sudo().write({'akhir': trans.akhir})

                state = "done"

            datas = {}
            datas.update({'state': state})
            super(RequestTransStiker, self).write(datas)

    # Buttom request for cancel
    @api.one
    def request_cancel_send_mail(self):
        args = [('name', '=', 'Request for Cancel')]
        template_ids = self.env['mail.template'].search(args)  # search tamplate dengan nama : Request for Cancel
        template_ids[0].sudo().send_mail(self.id, force_send=True)

        self.message_post("Send Email notification for cancel transaction to Manager")

        datas = {}
        datas.update({'state': 'request_cancel'})
        super(RequestTransStiker, self).write(datas)


    @api.multi
    def trans_reject(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Not Approve Message',
            'res_model': 'wizard.not.approve',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('view_wizard_not_approve', False),
            'target': 'new',
        }

    @api.multi
    def wizard_add_card_member(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'ADD CARD MEMBER',
            'res_model': 'wizard.add.card.member',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('view_wizard_add_card_member', False),
            'target': 'new',
        }


    notrans = fields.Char(string="ID #", readonly=True)
    unit_kerja = fields.Many2one('stasiun.kerja', 'UNIT #', required=True, readonly=False)
    stiker_id = fields.Many2one('trans.stiker', 'STIKER #', required=False, readonly=False)
    name = fields.Char(string="Nama", required=False, readonly=False)
    alamat = fields.Char(string="Alamat", required=False, readonly=False)
    telphone = fields.Char(string="No Telphone", required=False, readonly=False)
    no_id = fields.Char(string="No ID", readonly=True, )
    duration = fields.Integer('Duration', required=False, readonly=False,)
    awal = fields.Datetime(string="New Start Date", required=False, readonly=True,)
    akhir = fields.Datetime(string="New End Date", required=False, readonly=True,)
    awal_old = fields.Datetime(string="Start Date", required=False, readonly=True,)
    akhir_old = fields.Datetime(string="End Date", required=False, readonly=True, )
    val_harga = fields.Integer(string="Kontribusi", required=False, readonly=True,)
    tanggal = fields.Datetime(string="Date", required=False, default=lambda self: fields.datetime.now(), readonly=True, )
    adm = fields.Many2one(comodel_name="res.users", string="Created By", required=False,
                          default=lambda self: self.env.user and self.env.user.id or False, readonly=True)
    no_kartu = fields.Char(string="No Card / Barcode", required=False, )
    no_urut = fields.Char(string="No Urut", required=False, )
    old_no_kartu = fields.Char(string="No Card / Barcode", required=False, readonly=True)
    old_no_urut = fields.Char(string="No Urut", required=False, readonly=True)
    jenis_member = fields.Selection(string="Mobil",
                                    selection=[('1st', '1st'), ('2nd', '2nd'), ('3rd', '3rd'), ('4th', '4th'), ],
                                    required=False, readonly=False)
    jenis_transaksi = fields.Selection(string="Jenis Transaksi",
                                       selection=[('langganan_baru', 'LANGGANAN BARU'), ('perpanjang_baru', 'PERPANJANG BARU'), ('perpanjang', 'PERPANJANG'),
                                                  ('stop', 'STOP BILLING'), ],
                                       required=False, readonly=False)
    def_akhir = fields.Boolean(string="Duration Billing", default=False)
    keterangan = fields.Text(string="Keterangan", required=False, readonly=False)
    cara_bayar = fields.Selection(string="Cara Pembayaran",
                                  selection=[('billing', 'Billing'), ('non_billing', 'Non Billing'), ],
                                  required=False, readonly=False)
    nopol = fields.Char(string="No Polisi", required=False, readonly=False)
    # jenis_mobil = fields.Char(string="Jenis Kendaraan", required=False, readonly=False)
    jenis_mobil = fields.Selection(string="Jenis Kendaraan",
                                    selection=[('M', 'MOBIL (M)'), ('S', 'MOTOR (S)'), ],
                                    required=False, readonly=False)
    merk = fields.Char(string="Merk Mobil", required=False, readonly=False)
    tipe = fields.Char(string="Tipe Mobil", required=False, readonly=False)
    tahun = fields.Char(string="Tahun", required=False, readonly=False)
    warna = fields.Char(string="Warna", required=False, readonly=False)
    amount = fields.Integer(string="Total Amount", required=False, readonly=True,)  #
    edit_info_mobil = fields.Boolean(string="Edit Info Mobil", readonly=False)
    baru = fields.Boolean(string="KONTRIBUSI", readonly=False)
    perpanjang = fields.Boolean(string="PERPANJANG", default=False, readonly=False)
    beli_stiker = fields.Boolean(string="STIKER", default=False, readonly=False)
    ganti_nopol = fields.Boolean(string="GANTI NOPOL", default=False, readonly=False)
    ganti_nopol_pb = fields.Boolean(string="NOPOL BARU", default=False, readonly=False)
    kartu_hilang = fields.Boolean(string="KARTU PARKIR", default=False, readonly=False)
    tipe_trans = fields.Selection(string="Tipe Transaksi",
                                  selection=[('ganti_nopol', 'GANTI NOPOL'), ('kartu_hilang', 'KARTU HILANG'), ],
                                  required=False, readonly=False)
    tgl_approved = fields.Datetime(string="Tanggal Approve", required=False, readonly=False)
    adm_approved = fields.Char(string="Admin Approve", required=False, readonly=False)
    flag = fields.Char(string="Flag", required=False, readonly=False)
    remark = fields.Char(string="Remark", required=False, readonly=False)
    start_date_status = new_field = fields.Char(string="Start Date Status", required=False, readonly=False)
    approvedstatus = fields.Char(string="Approve Status", required=False, readonly=False)
    status = fields.Char(string="Status", required=False, readonly=False)
    harga_beli_stiker = fields.Integer(string="Stiker", required=False, readonly=True)
    harga_kartu_hilang = fields.Integer(string="Kartu Parkir", required=False, readonly=True)
    harga_ganti_nopol = fields.Integer(string="Ganti Nopol", required=False, readonly=True)
    new_nopol = fields.Char(string="No Polisi", required=False, readonly=False)
    new_jenis_mobil = fields.Selection(string="Jenis Kendaraan",
                                    selection=[('M', 'MOBIL (M)'), ('S', 'MOTOR (S)'), ],
                                    required=False, readonly=False)
    new_jenis_member = fields.Selection(string="Mobil ke",
                                        selection=[('1st', '1st'), ('2nd', '2nd'), ('3rd', '3rd'), ('4th', '4th'), ],
                                        required=False, readonly=False)
    new_merk = fields.Char(string="Merk Mobil", required=False, readonly=False)
    new_tipe = fields.Char(string="Tipe Mobil", required=False, readonly=False)
    new_tahun = fields.Char(string="Tahun", required=False, readonly=False)
    new_warna = fields.Char(string="Warna", required=False, readonly=False)
    new_nopol_pb = fields.Char(string="No Polisi", required=False, readonly=False)
    new_jenis_mobil_pb = fields.Selection(string="Jenis Kendaraan",
                                    selection=[('M', 'MOBIL (M)'), ('S', 'MOTOR (S)'), ],
                                    required=False, readonly=False)
    new_merk_pb = fields.Char(string="Merk Mobil", required=False, readonly=False)
    new_tipe_pb = fields.Char(string="Tipe Mobil", required=False, readonly=False)
    new_tahun_pb = fields.Char(string="Tahun", required=False, readonly=False)
    new_warna_pb = fields.Char(string="Warna", required=False, readonly=False)
    ket_nopol = fields.Text(string="Keterangan", required=False, readonly=False)
    nopol_lama = fields.Text(string="Data lama NOPOL", required=False, readonly=True)
    state = fields.Selection(string="State",
                             selection=[('open', 'Open'), ('confirm', 'Confirm'),('payment', 'Waiting for Payment'),
                                        ('request_cancel', 'Request for Cancel'), ('cancel', 'Cancel'), ('delete', 'Delete'),
                                        ('done', 'Done')],
                             required=False, default='open')

    @api.model
    def create(self, vals):
        vals['notrans'] = self.env['ir.sequence'].next_by_code('request.transstiker')

        if vals.get('ganti_nopol') == True:
            if 'new_nopol' in vals.keys():
                string_new_nopol = vals.get('new_nopol')
                vals['new_nopol'] = string_new_nopol.strip()

        if vals.get('ganti_nopol_pb') == True:
            if 'new_nopol_pb' in vals.keys():
                string_new_nopol_pb = vals.get('new_nopol_pb')
                vals['new_nopol_pb'] = string_new_nopol_pb.strip()

        if vals.get('kartu_hilang') == True:
            if 'no_urut' in vals.keys():
                string_no_urut = vals.get('no_urut')
                vals['no_urut'] = string_no_urut.strip()

            if 'no_kartu' in vals.keys():
                string_no_kartu = vals.get('no_kartu')
                vals['no_kartu'] = string_no_kartu.strip()

        if 'duration' not in vals.keys():
            raise ValidationError("Duration empty")
        if vals.get('duration') <= 0 and vals.get('jenis_transaksi') in ('langganan_baru', 'perpanjang_baru', 'perpanjang'):
            raise ValidationError("Duration harus lebih besar dari 0")

        res = super(RequestTransStiker, self).create(vals)
        _logger.info(res.stiker_id)
        res._get_stiker()
        res._change_kartu_hilang()
        res.generate_stiker_id()
        res.calculate_harga_beli_stiker()
        res.calculate_harga_ganti_nopol()
        res.calculate_harga_kartu_hilang()
        res.calculate_start_end_date()
        res.calculate_harga_kontribusi()
        res.calculate_total_harga()
        res.trans_payment()
        return res

    @api.multi
    def unlink(self):
        for status in self:
           if status.state in ('done', 'cancel', 'request_cancel'):
               raise ValidationError("Can't delete record")

        vals = {}
        vals.update({'state': 'delete'})
        _logger.info("Delete Transaction Stiker : " + str(self.stiker_id.notrans) + ", ID# : " + str(
            self.notrans) + ", Date delete : " + str(datetime.now()))
        self.message_post("Delete transaction")
        return super(RequestTransStiker, self).write(vals)

    @api.multi
    def write(self, vals):
        """Override default Odoo write function and extend."""
        # Do your custom logic here

        if vals.get('ganti_nopol') == True:
            if 'new_nopol' in vals.keys():
                string_new_nopol = vals.get('new_nopol')
                vals['new_nopol'] = string_new_nopol.strip()

        if vals.get('ganti_nopol_pb') == True:
            if 'new_nopol_pb' in vals.keys():
                string_new_nopol_pb = vals.get('new_nopol_pb')
                vals['new_nopol_pb'] = string_new_nopol_pb.strip()

        if vals.get('kartu_hilang') == True:
            if 'no_urut' in vals.keys():
                string_no_urut = vals.get('no_urut')
                vals['no_urut'] = string_no_urut.strip()

            if 'no_kartu' in vals.keys():
                string_no_kartu = vals.get('no_kartu')
                vals['no_kartu'] = string_no_kartu.strip()

        #FO Access
        for trans in self:
            if trans.state in ('request_cancel', 'cancel', 'done') :
                raise ValidationError("Can't edit record")


        # if "state" in vals.keys():
        #     state = vals.get('state')
        #     # Request Change Password
        #     if state == "payment":
        #         raise ValidationError("Can't edit record")
        #     if state == "request_cancel":
        #         raise ValidationError("Can't edit record")
        #     if state == "cancel":
        #         raise ValidationError("Can't edit record")
        #     if state == "done":
        #         raise ValidationError("Can't edit record")


        return super(RequestTransStiker, self).write(vals)