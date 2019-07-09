from odoo import api, fields, models
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, Warning
from dateutil.relativedelta import *

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

    @api.onchange('jenis_transaksi','kartu_hilang','stiker_id')
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


    @api.onchange('stiker_id','ganti_nopol','new_nopol')
    def calculate_harga_ganti_nopol(self):
        if self.ganti_nopol == True:

            if self.new_nopol:
                # Process perpanjang to Server Database Parkir and update trans_id
                base_external_dbsource_obj = self.env['base.external.dbsource']
                postgresconn = base_external_dbsource_obj.sudo().browse(1)
                postgresconn.connection_open()
                _logger.info("Connection Open")

                # Kondisi pengecekan NOPOL
                strSQL = """SELECT notrans FROM detail_transaksi_stiker WHERE nopol='{}'""".format(self.new_nopol)
                nopolcheck = postgresconn.execute(query=strSQL, metadata=False)
                _logger.info(nopolcheck)

                if nopolcheck:
                    for record in nopolcheck:
                        raise ValidationError("Nopol ini sudah ada dengan Stiker# : " + record[0] + " , Jika nopol ini ingin rubah ke UNIT# lain atau STIKER# lain silahkan menggunakan system lama. Terima kasih..")

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
            elif check_no_id == "2":
                self.harga_ganti_nopol = ganti_nopol_dua_id
            elif check_no_id == "3":
                self.harga_ganti_nopol = ganti_nopol_tiga_id
            elif check_no_id == "4":
                self.harga_ganti_nopol = ganti_nopol_empat_id

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
                                    "Mobil anda masih di dalam, Stiker : " + stikers + ", No Card : " + row[0] + "")

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

                    if self.stiker_id.notrans:
                        check_motor = self.stiker_id.notrans[0]
                    else:
                        check_motor = ''

                    if check_motor == "K" or check_motor == "k":
                        self.jenis_member = "1st"
                    else:
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

                    if self.stiker_id.notrans:
                        check_motor = self.stiker_id.notrans[0]
                    else:
                        check_motor = ''

                    if check_motor == "K" or check_motor == "k":
                        self.jenis_member = "1st"
                    else:
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

                    dt1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                    start_dt = date(dt1.year, dt1.month, dt1.day)
                    dt2 = datetime.now()
                    end_dt = date(dt2.year, dt2.month, dt2.day)


                    if self.cara_bayar == "billing":
                        jml = 0
                        month = ""
                        for dt in self.daterange(start_dt, end_dt):
                            if dt.strftime("%m") == month:
                                continue
                            else:
                                month = dt.strftime("%m")
                                jml = jml + 1

                        self.duration = jml

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

                    akhir = datetime.now()
                    if self.jenis_transaksi == "stop":
                        self.akhir = akhir
                        self.cara_bayar = "non_billing"

                    self.duration = 0

                    if self.stiker_id.notrans:
                        check_row = self.stiker_id.notrans[4]
                    else:
                        check_row = ''

                    if self.stiker_id.notrans:
                        check_motor = self.stiker_id.notrans[0]
                    else:
                        check_motor = ''

                    if check_motor == "K" or check_motor == "k":
                        self.jenis_member = "1st"
                    else:
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
    @api.onchange('duration','jenis_transaksi','stiker_id','jenis_mobil')
    @api.depends('stiker_id','name','duration','jenis_mobil')
    def calculate_start_end_date(self):

        # Pengecekan jika field duration & start_date tidak diisi, maka field end_date akan di update sama seperti field start_date
        if not self.jenis_transaksi:
            self.awal = ""
            self.akhir = ""
        elif self.jenis_transaksi == 'langganan_baru':
            tglawal = datetime.now()
            str_start_date = str(tglawal.year) + "-" + str(tglawal.month).zfill(2) + "-" + str(tglawal.day).zfill(2) + " 00:00:00"
            tglawal = datetime.strptime(str_start_date, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)
            self.awal = tglawal

            tglakhir = tglawal + relativedelta(months=self.duration, days=1)
            str_end_date = str(tglakhir.year) + "-" + str(tglakhir.month).zfill(2) + "-" + str(tglakhir.day).zfill(2) + " 23:59:59"
            self.akhir = datetime.strptime(str_end_date, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)

        elif self.jenis_transaksi == 'perpanjang_baru':
            tglawal = datetime.now()
            str_start_date = str(tglawal.year) + "-" + str(tglawal.month).zfill(2) + "-" + str(tglawal.day).zfill(
                2) + " 00:00:00"
            tglawal = datetime.strptime(str_start_date, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)
            self.awal = tglawal

            tglakhir = tglawal + relativedelta(months=self.duration, days=1)
            str_end_date = str(tglakhir.year) + "-" + str(tglakhir.month).zfill(2) + "-" + str(tglakhir.day).zfill(
                2) + " 23:59:59"
            self.akhir = datetime.strptime(str_end_date, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)

        elif self.jenis_transaksi == 'perpanjang':

            tglawal = fields.Datetime.from_string(self.akhir_old)
            str_start_date = str(tglawal.year) + "-" + str(tglawal.month).zfill(2) + "-" + str(tglawal.day).zfill(
                2) + " 00:00:00"
            tglawal = datetime.strptime(str_start_date, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)
            self.awal = tglawal + relativedelta(days=1)

            tglakhir = tglawal + relativedelta(months=self.duration, days=2)
            str_end_date = str(tglakhir.year) + "-" + str(tglakhir.month).zfill(2) + "-" + str(tglakhir.day).zfill(
                2) + " 23:59:59"
            self.akhir = datetime.strptime(str_end_date, "%Y-%m-%d %H:%M:%S") - relativedelta(hours=7)

            # start_date = fields.Datetime.from_string(self.akhir_old)
            # # Mengupdate field end_date dari perhitungan variabel start ditambah variabel duration
            # if start_date:
            #     self.awal = start_date
            #     self.akhir = start_date + relativedelta(months=self.duration)


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

                        if tgl < DATE:

                            dt1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                            start_dt = date(dt1.year, dt1.month, dt1.day)
                            dt2 = datetime.now()
                            end_dt = date(dt2.year, dt2.month, dt2.day)
                            jml = 0
                            month = ""
                            for dt in self.env['request.transstiker'].daterange(start_dt, end_dt):
                                if dt.strftime("%m") == month:
                                    continue
                                else:
                                    month = dt.strftime("%m")
                                    jml = jml + 1

                            hasil = int(jenis_member_nd_ids) * jml
                            jml_dp = int(jenis_member_nd_ids) * 2
                            self.val_harga = hasil + jml_dp

                        elif tgl > DATE:

                            date1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                            date2 = datetime.now()
                            r = relativedelta(date1, date2)
                            sum_month = r.months
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

                            dt1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                            start_dt = date(dt1.year, dt1.month, dt1.day)
                            dt2 = datetime.now()
                            end_dt = date(dt2.year, dt2.month, dt2.day)
                            jml = 0
                            month = ""
                            for dt in self.env['request.transstiker'].daterange(start_dt, end_dt):
                                if dt.strftime("%m") == month:
                                    continue
                                else:
                                    month = dt.strftime("%m")
                                    jml = jml + 1

                            hasil = int(jenis_member_rd_ids) * jml
                            jml_dp = int(jenis_member_rd_ids) * 2
                            self.val_harga = hasil + jml_dp

                        elif tgl > DATE:
                            date1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                            date2 = datetime.now()
                            r = relativedelta(date1, date2)
                            sum_month = r.months
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

                            dt1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                            start_dt = date(dt1.year, dt1.month, dt1.day)
                            dt2 = datetime.now()
                            end_dt = date(dt2.year, dt2.month, dt2.day)
                            jml = 0
                            month = ""
                            for dt in self.env['request.transstiker'].daterange(start_dt, end_dt):
                                if dt.strftime("%m") == month:
                                    continue
                                else:
                                    month = dt.strftime("%m")
                                    jml = jml + 1

                            hasil = int(jenis_member_th_ids) * jml
                            jml_dp = int(jenis_member_th_ids) * 2
                            self.val_harga = hasil + jml_dp

                        elif tgl > DATE:
                            date1 = datetime.strptime(str(self.akhir_old), '%Y-%m-%d %H:%M:%S')
                            date2 = datetime.now()
                            r = relativedelta(date1, date2)
                            sum_month = r.months
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
                    res = self.env['trans.stiker'].search(args).sudo().write({'akhir': v.akhir})

                if v.jenis_transaksi == "perpanjang_baru":

                    if self.ganti_nopol_pb == True:
                        base_external_dbsource_obj = self.env['base.external.dbsource']
                        postgresconn = base_external_dbsource_obj.sudo().browse(1)
                        postgresconn.connection_open()
                        _logger.info('Update NOPOL')
                        strSQLUpdate_nopol = """UPDATE detail_transaksi_stiker """ \
                                             """ SET """ \
                                             """nopol='{}', jenis_mobil='{}', merk='{}', tipe='{}',""" \
                                             """tahun='{}', warna='{}'""" \
                                             """ WHERE """ \
                                             """notrans='{}'""".format(self.new_nopol_pb, self.new_jenis_mobil_pb, self.new_merk_pb,
                                                                       self.new_tipe_pb, self.new_tahun_pb, self.new_warna_pb,
                                                                       self.stiker_id.notrans)
                        postgresconn.execute_general(strSQLUpdate_nopol)

                        # UPDATE TO TRANS STIKER ODOO
                        args = [('trans_stiker_id', '=', v.stiker_id.id)]
                        self.env['detail.transstiker'].search(args).write({
                            'nopol': self.new_nopol_pb,
                            'jenis_mobil': self.new_jenis_mobil_pb,
                            'merk': self.new_merk_pb,
                            'tipe': self.new_tipe_pb,
                            'tahun': self.new_tahun_pb,
                            'warna': self.new_warna_pb,
                        })

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

                    _logger.info('Insert Data Trans Stiker')
                    strSQL = """INSERT INTO transaksi_stiker """ \
                                """(notrans, nama, alamat, telepon, jenis_transaksi, awal, harga, keterangan, tanggal, operator, akhir,""" \
                                """maks, no_id, unit_kerja, no_induk, jenis_stiker, hari_ke, jenis_langganan, exit_pass, no_kuitansi, tgl_edited,""" \
                                """tipe_exit_pass, seq_code, unitno, area, reserved, cara_bayar)""" \
                                """ VALUES """ \
                                """('{}', '{}', '{}', '{}', '{}', '{}', 0, '{}', '{}', '{}', '{}', 1,""" \
                                """'{}', '{}', NULL, 0, NULL, '{}', 0, '{}', '{}', 1, 0, NULL, NULL, 0, '{}')""".format(
                        self.no_id, self.name, self.alamat, self.telphone, jt, tglawal,self.keterangan, self.tanggal, self.adm.name,
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

                # Process perpanjang to Server Database Parkir and update trans_id
                base_external_dbsource_obj = self.env['base.external.dbsource']
                postgresconn = base_external_dbsource_obj.sudo().browse(1)
                postgresconn.connection_open()
                _logger.info("Connection Open")
                _logger.info("Sync Stasiun Kerja")

                # Insert Data Trans Stiker with Odoo to Database Server Parkir
                _logger.info('Update NOPOL')
                strSQLUpdate_nopol = """UPDATE detail_transaksi_stiker """ \
                                     """ SET """ \
                                     """nopol='{}', jenis_mobil='{}', merk='{}', tipe='{}',""" \
                                     """tahun='{}', warna='{}'""" \
                                     """ WHERE """ \
                                     """notrans='{}'""".format(v.new_nopol, v.new_jenis_mobil, v.new_merk,
                                                               v.new_tipe, v.new_tahun, v.new_warna,
                                                               v.stiker_id.notrans)
                postgresconn.execute_general(strSQLUpdate_nopol)

                args = [('notrans', '=', self.stiker_id.notrans)]
                res = self.env['detail.transstiker'].search(args)
                vals = {}
                vals.update({'nopol': v.new_nopol})
                vals.update({'jenis_mobil': v.new_jenis_mobil})
                vals.update({'merk': v.new_merk})
                vals.update({'tipe': v.new_tipe})
                vals.update({'tahun': v.new_tahun})
                vals.update({'warna': v.new_warna})
                res.write(vals)

            if v.kartu_hilang == True:
                # Process perpanjang to Server Database Parkir and update trans_id
                base_external_dbsource_obj = self.env['base.external.dbsource']
                postgresconn = base_external_dbsource_obj.sudo().browse(1)
                postgresconn.connection_open()
                _logger.info("Connection Open")

                tglakhir_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                tglakhir = datetime.strptime(tglakhir_str, "%Y-%m-%d %H:%M:%S")
                DATE = tglakhir + relativedelta(hours=7)

                RTS_stiker_id = self.no_id
                RTS_adm = self.adm.name

                if v.jenis_transaksi == "langganan_baru":
                    # Insert Data Trans Stiker with Odoo to Database Server Parkir
                    _logger.info('INSERT CARD MEMBER')
                    strSQL_cardmember = """INSERT INTO card_member """ \
                                        """(notrans,no_card,no_urut,tanggal,adm)""" \
                                        """ VALUES """ \
                                        """('{}','{}','{}','{}','{}')""".format(RTS_stiker_id, self.no_kartu,
                                                                                self.no_urut,
                                                                                DATE,
                                                                                RTS_adm)
                else:
                    # Insert Data Trans Stiker with Odoo to Database Server Parkir
                    _logger.info('Update NOPOL')
                    strSQL_cardmember = """UPDATE card_member """ \
                                        """ SET """ \
                                        """no_card='{}', no_urut='{}', tanggal='{}', adm='{}'""" \
                                        """ WHERE """ \
                                        """notrans='{}'""".format(v.no_kartu, v.no_urut, DATE, RTS_adm,
                                                                  self.stiker_id.notrans)

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
                res = self.env['trans.stiker'].search(args).write({'awal':self.awal_old, 'akhir': self.akhir_old})

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
                    res.write(vals)

                # UPDATE TO TRANS STIKER ODOO
                args = [('id', '=', self.stiker_id.id)]
                self.env['trans.stiker'].search(args).write({'awal':self.awal_old, 'akhir': self.akhir_old})

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
                self.env['trans.stiker'].search(args).write({'akhir': self.akhir_old})

                state = "cancel"

        if self.ganti_nopol == True:
            nopol = self.nopol
            jenis_mobil = self.jenis_mobil
            merk = self.merk
            tipe = self.tipe
            tahun = self.tahun
            warna = self.warna
            stiker = self.stiker_id.notrans

            # Process perpanjang to Server Database Parkir and update trans_id
            base_external_dbsource_obj = self.env['base.external.dbsource']
            postgresconn = base_external_dbsource_obj.sudo().browse(1)
            postgresconn.connection_open()
            _logger.info("Connection Open")
            _logger.info("Sync Stasiun Kerja")

            # Insert Data Trans Stiker with Odoo to Database Server Parkir
            _logger.info('Update NOPOL')
            strSQLUpdate_nopol = """UPDATE detail_transaksi_stiker """ \
                                 """ SET """ \
                                 """nopol='{}', jenis_mobil='{}', merk='{}', tipe='{}',""" \
                                 """tahun='{}', warna='{}'""" \
                                 """ WHERE """ \
                                 """notrans='{}'""".format(nopol, jenis_mobil, merk, tipe,
                                                           tahun, warna, stiker)

            postgresconn.execute_general(strSQLUpdate_nopol)

            args = [('notrans', '=', stiker)]
            res = self.env['detail.transstiker'].search(args)
            vals = {}
            vals.update({'nopol': self.nopol})
            vals.update({'jenis_mobil': self.jenis_mobil})
            vals.update({'merk': self.merk})
            vals.update({'tipe': self.tipe})
            vals.update({'tahun': self.tahun})
            vals.update({'warna': self.warna})
            res.write(vals)

            datas = {}
            datas.update({'state = "cancel'})
            super(RequestTransStiker, self).write(datas)

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

            datas = {}
            datas.update({'state': 'cancel'})
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
                state = "done"

            if trans.ganti_nopol == True and trans.amount == 0:

                check_row = self.stiker_id.notrans[4]

                if check_row == "1":
                    base_external_dbsource_obj = self.env['base.external.dbsource']
                    postgresconn = base_external_dbsource_obj.sudo().browse(1)
                    postgresconn.connection_open()
                    _logger.info("Connection Open")
                    _logger.info("Sync Stasiun Kerja")

                    # Insert Data Trans Stiker with Odoo to Database Server Parkir
                    _logger.info('Update NOPOL')
                    strSQLUpdate_nopol = """UPDATE detail_transaksi_stiker_tes """ \
                                         """ SET """ \
                                         """nopol='{}', jenis_mobil='{}', merk='{}', tipe='{}',""" \
                                         """tahun='{}', warna='{}'""" \
                                         """ WHERE """ \
                                         """notrans='{}'""".format(trans.new_nopol, trans.new_jenis_mobil,
                                                                   trans.new_merk,
                                                                   trans.new_tipe, trans.new_tahun, trans.new_warna,
                                                                   trans.stiker_id.notrans)
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
                    res.write(vals)

                    # AMBIL DATA STIKER DARI TRANS STIKER
                    for data_detail in self.stiker_id:
                        self.nopol = data_detail.detail_ids.nopol
                        self.jenis_mobil = data_detail.detail_ids.jenis_mobil
                        self.merk = data_detail.detail_ids.merk
                        self.tipe = data_detail.detail_ids.tipe
                        self.tahun = data_detail.detail_ids.tahun
                        self.warna = data_detail.detail_ids.warna

                    state = "done"

            if trans.jenis_transaksi == 'stop':
                # Process perpanjang to Server Database Parkir and update trans_id
                base_external_dbsource_obj = self.env['base.external.dbsource']
                postgresconn = base_external_dbsource_obj.sudo().browse(1)
                postgresconn.connection_open()
                _logger.info("Connection Open")
                _logger.info("Sync Stasiun Kerja")

                tglakhir = datetime.strptime(trans.akhir, "%Y-%m-%d %H:%M:%S") + relativedelta(hours=7)

                # Insert Data Trans Stiker with Odoo to Database Server Parkir
                _logger.info('Update Data Trans Stiker')
                strSQLUpdate_akhir = """UPDATE transaksi_stiker_tes """ \
                                     """ SET akhir='{}', cara_bayar='{}'""" \
                                     """ WHERE """ \
                                     """notrans='{}'""".format(tglakhir, 0, trans.stiker_id.notrans)

                postgresconn.execute_general(strSQLUpdate_akhir)

                # UPDATE TO TRANS STIKER ODOO
                args = [('id', '=', trans.stiker_id.id)]
                res = self.env['trans.stiker'].search(args).sudo().write({'akhir': trans.akhir})

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
    state = fields.Selection(string="State",
                             selection=[('open', 'Open'), ('confirm', 'Confirm'),('payment', 'Waiting for Payment'),
                                        ('request_cancel', 'Request for Cancel'), ('cancel', 'Cancel'),
                                        ('done', 'Done')],
                             required=False, default='open')

    @api.model
    def create(self, vals):
        vals['notrans'] = self.env['ir.sequence'].next_by_code('request.transstiker')

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

        return super(RequestTransStiker, self).unlink()

    @api.multi
    def write(self, vals):
        """Override default Odoo write function and extend."""
        # Do your custom logic here

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