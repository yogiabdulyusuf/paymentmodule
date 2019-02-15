from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, Warning
from dateutil.relativedelta import *

import logging

_logger = logging.getLogger(__name__)

class RequestTransStiker(models.Model):
    _name = 'request.transstiker'
    _inherit = ['mail.thread']
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



    @api.onchange('stiker_id', 'baru', 'jenis_transaksi', 'jenis_member')
    def _get_stiker(self):

        if self.ganti_nopol == True:
            ganti_nopol_id = self.env.user.company_id.ganti_nopol_ids

            if not ganti_nopol_id:
                raise ValidationError("Price Ganti Nopol not defined,  please define on company information!")

            if self.stiker_id:
                check_no_id = self.stiker_id.notrans[4]
            else:
                check_no_id = ''

            if check_no_id == "1":
                self.harga_ganti_nopol = 0
            else:
                self.harga_ganti_nopol = ganti_nopol_id



        if self.baru == True:
            if self.stiker_id:
                # Ambil data dari trans_id
                name = ''
                alamat = ''
                telphone = ''
                no_id = ''
                jenis_transaksi = ''
                awal = ''
                akhir = ''
                nopol = ''
                jenis_mobil = ''
                merk = ''
                tipe = ''
                tahun = ''
                color = ''

                # AMBIL DATA STIKER DARI TRANS STIKER
                for data_detail in self.stiker_id:
                    name = data_detail.name
                    alamat = data_detail.alamat
                    telphone = data_detail.telphone
                    no_id = data_detail.no_id
                    jenis_transaksi = data_detail.jenis_transaksi
                    awal = data_detail.awal
                    akhir = data_detail.akhir
                    nopol = data_detail.detail_ids.nopol
                    jenis_mobil = data_detail.detail_ids.jenis_mobil
                    merk = data_detail.detail_ids.merk
                    tipe = data_detail.detail_ids.tipe
                    tahun = data_detail.detail_ids.tahun
                    color = data_detail.detail_ids.warna
                self.name = name
                self.alamat = alamat
                self.telphone = telphone
                self.no_id = no_id
                if self.jenis_transaksi == "stop":
                    self.jenis_transaksi = "stop"
                elif self.jenis_transaksi == "perpanjang":
                    self.jenis_transaksi = "perpanjang"
                else:
                    self.jenis_transaksi = jenis_transaksi
                self.awal = awal
                if self.jenis_transaksi == "stop":
                    akhir = datetime.now() + relativedelta(months=1)
                    self.akhir = akhir
                    self.cara_bayar = "non_billing"
                else:
                    self.akhir = akhir
                self.nopol = nopol
                self.jenis_mobil = jenis_mobil
                self.merk = merk
                self.tipe = tipe
                self.tahun = tahun
                self.warna = color

                jenis_member_st_ids = self.env.user.company_id.jenis_member_st
                jenis_member_nd_ids = self.env.user.company_id.jenis_member_nd
                if not jenis_member_nd_ids:
                    raise ValidationError("Price 2nd Membership not defined,  please define on company information!")
                jenis_member_rd_ids = self.env.user.company_id.jenis_member_rd
                if not jenis_member_rd_ids:
                    raise ValidationError("Price 3rd Membership not defined,  please define on company information!")
                jenis_member_th_ids = self.env.user.company_id.jenis_member_th
                if not jenis_member_th_ids:
                    raise ValidationError("Price 4th Membership not defined,  please define on company information!")

                if self.no_id:
                    check_row = self.no_id[4]
                else:
                    check_row = ''

                if check_row == "1":
                    self.jenis_member = "1st"
                elif check_row == "2":

                    self.jenis_member = "2nd"
                elif check_row == "3":

                    self.jenis_member = "3rd"
                elif check_row == "4":
                    self.jenis_member = "4th"

                elif check_row == "":
                    self.val_harga = 0
                    self.jenis_member = ""


            else:
                # kosongkan data
                if self.jenis_transaksi == 'langganan_baru':
                    # check langganan baru mobil ke berapa
                    jenis_member_st_ids = self.env.user.company_id.jenis_member_st
                    jenis_member_nd_ids = self.env.user.company_id.jenis_member_nd
                    if not jenis_member_nd_ids:
                        raise ValidationError("Price 2nd Membership not defined,  please define on company information!")
                    jenis_member_rd_ids = self.env.user.company_id.jenis_member_rd
                    if not jenis_member_rd_ids:
                        raise ValidationError("Price 3rd Membership not defined,  please define on company information!")
                    jenis_member_th_ids = self.env.user.company_id.jenis_member_th
                    if not jenis_member_th_ids:
                        raise ValidationError("Price 4th Membership not defined,  please define on company information!")

                    check_row = self.jenis_member

                    if check_row == "1st":
                        self.val_harga = jenis_member_st_ids

                    elif check_row == "2nd":
                        self.val_harga = jenis_member_nd_ids

                    elif check_row == "3rd":
                        self.val_harga = jenis_member_rd_ids

                    elif check_row == "4th":
                        self.val_harga = jenis_member_th_ids

                    else:
                        self.val_harga = 0


                elif not self.jenis_transaksi:
                    # kosongkan
                    name = ''
                    alamat = ''
                    telphone = ''
                    no_id = ''
                    jenis_transaksi = ''
                    awal = ''
                    akhir = ''
                    cara_bayar = ''
                    nopol = ''
                    jenis_mobil = ''
                    merk = ''
                    tipe = ''
                    tahun = ''
                    color = ''

                    self.name = name
                    self.alamat = alamat
                    self.telphone = telphone
                    self.no_id = no_id
                    self.jenis_transaksi = jenis_transaksi
                    self.awal = awal
                    self.akhir = akhir
                    self.cara_bayar = cara_bayar
                    self.nopol = nopol
                    self.jenis_mobil = jenis_mobil
                    self.merk = merk
                    self.tipe = tipe
                    self.tahun = tahun
                    self.warna = color


        else:
            # kosongkan
            name = ''
            alamat = ''
            telphone = ''
            no_id = ''
            jenis_transaksi = ''
            awal = ''
            akhir = ''
            cara_bayar = ''
            nopol = ''
            jenis_mobil = ''
            merk = ''
            tipe = ''
            tahun = ''
            color = ''

            self.name = name
            self.alamat = alamat
            self.telphone = telphone
            self.no_id = no_id
            self.jenis_transaksi = jenis_transaksi
            self.awal = awal
            self.akhir = akhir
            self.cara_bayar = cara_bayar
            self.nopol = nopol
            self.jenis_mobil = jenis_mobil
            self.merk = merk
            self.tipe = tipe
            self.tahun = tahun
            self.warna = color


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

            if self.stiker_id:
                check_row = self.stiker_id.notrans[4]
            else:
                check_row = ''

            if check_row == "1":
                self.harga_ganti_nopol = 0
            elif check_row == "2":
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
        self.adm = self.create_uid


    # END DATE UPDATE
    @api.onchange('duration','cara_bayar')
    @api.depends('awal', 'duration')
    def _get_end_date(self):
        akhir = ''

        # AMBIL DATA STIKER DARI TRANS STIKER
        for data_detail in self.stiker_id:
            akhir = data_detail.akhir


        for r in self:
            # Pengecekan jika field duration & start_date tidak diisi, maka field end_date akan di update sama seperti field start_date
            if r.jenis_transaksi == 'langganan_baru':
                r.awal = datetime.now()
                r.akhir = datetime.now() + relativedelta(months=r.duration)

            else:
                if r.akhir:
                    start_date = fields.Datetime.from_string(akhir)

                    # Mengupdate field end_date dari perhitungan variabel start ditambah variabel duration
                    r.awal = start_date
                    r.akhir = start_date + relativedelta(months=r.duration)

        jenis_member_st_ids = self.env.user.company_id.jenis_member_st
        jenis_member_nd_ids = self.env.user.company_id.jenis_member_nd
        if not jenis_member_nd_ids:
            raise ValidationError("Price 2nd Membership not defined,  please define on company information!")
        jenis_member_rd_ids = self.env.user.company_id.jenis_member_rd
        if not jenis_member_rd_ids:
            raise ValidationError("Price 3rd Membership not defined,  please define on company information!")
        jenis_member_th_ids = self.env.user.company_id.jenis_member_th
        if not jenis_member_th_ids:
            raise ValidationError("Price 4th Membership not defined,  please define on company information!")

        if self.no_id:
            check_row = self.no_id[4]
        else:
            check_row = ''

        if check_row == "1":
            self.val_harga = jenis_member_st_ids

        elif check_row == "2":
            if self.jenis_transaksi == "stop":
                self.val_harga = 0
            else:
                if self.cara_bayar == "non_billing":
                    self.val_harga = int(jenis_member_nd_ids) * int(self.duration)
                else:
                    self.val_harga = int(jenis_member_nd_ids) * 2

        elif check_row == "3":
            if self.jenis_transaksi == "stop":
                self.val_harga = 0
            else:
                if self.cara_bayar == "non_billing":
                    self.val_harga = int(jenis_member_rd_ids) * int(self.duration)
                else:
                    self.val_harga = int(jenis_member_rd_ids) * 2

        elif check_row == "4":
            if self.jenis_transaksi == "stop":
                self.val_harga = 0
            else:
                if self.cara_bayar == "non_billing":
                    self.val_harga = int(jenis_member_th_ids) * int(self.duration)
                else:
                    self.val_harga = int(jenis_member_th_ids) * 2



    # BUTTON DONE PAYMENT
    @api.one
    def trans_done_payment(self):
        for v in self:
            if v.baru == True:

                if v.jenis_transaksi == "perpanjang":

                    # Process perpanjang to Server Database Parkir and update trans_id
                    base_external_dbsource_obj = self.env['base.external.dbsource']
                    postgresconn = base_external_dbsource_obj.browse(1)
                    postgresconn.connection_open()
                    _logger.info("Connection Open")
                    _logger.info("Sync Stasiun Kerja")

                    # Insert Data Trans Stiker with Odoo to Database Server Parkir
                    _logger.info('Update Data Trans Stiker')
                    strSQLUpdate_akhir = """UPDATE transaksi_stiker_tes """ \
                             """ SET akhir='{}'""" \
                             """ WHERE """ \
                             """notrans='{}'""".format(v.akhir, self.no_id)

                    postgresconn.execute_general(strSQLUpdate_akhir)

                    # UPDATE TO TRANS STIKER ODOO
                    args = [('id', '=', v.stiker_id.id)]
                    res = self.env['trans.stiker'].search(args).write({'akhir': v.akhir})

                    v.state = "done"

                if v.jenis_transaksi == "langganan_baru":

                    # Process create langganan_baru to Server Database Parkir and update trans_id
                    base_external_dbsource_obj = self.env['base.external.dbsource']
                    transaksi_stiker_obj = self.env['trans.stiker']
                    detail_stiker_obj = self.env['detail.transstiker']
                    postgresconn = base_external_dbsource_obj.browse(1)
                    postgresconn.connection_open()
                    _logger.info("Connection Open")
                    _logger.info("Sync Stasiun Kerja")

                    check = self.jenis_transaksi
                    if check == "langganan_baru":
                        jt = "0"
                    elif check == "perpanjang":
                        jt = "1"
                    elif check == "stop":
                        jt = "2"

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
                        cb = "0"
                    else:
                        cb = "1"

                    # Insert Data Trans Stiker with Odoo to Database Server Parkir
                    _logger.info('Insert Data Trans Stiker')
                    strSQL = """INSERT INTO transaksi_stiker_tes """ \
                             """(notrans, nama, alamat, telepon, jenis_transaksi, awal, harga, keterangan, tanggal, operator, akhir,""" \
                             """maks, no_id, unit_kerja, no_induk, jenis_stiker, hari_ke, jenis_langganan, exit_pass, no_kuitansi, tgl_edited,""" \
                             """tipe_exit_pass, seq_code, unitno, area, reserved, cara_bayar)""" \
                             """ VALUES """ \
                             """('{}', '{}', '{}', '{}', '{}', '{}', '0', '{}', '{}', '{}', '{}', '1',""" \
                             """'{}', '{}', NULL, '0', NULL, '{}', '0', '{}', '{}', '1', '0', NULL, NULL, '0', '{}')""".format(
                        self.no_id, self.name, self.alamat, self.telphone, jt, self.awal,self.keterangan, self.tanggal, self.adm.name,
                        self.akhir, self.no_id, self.unit_kerja.kode, j_member, self.no_id, DATE, cb)

                    postgresconn.execute_general(strSQL)

                    # Insert Detail Trans Stiker with Odoo to Database Server Parkir
                    _logger.info('Insert Detail Trans Stiker')
                    strSQL2 = """INSERT INTO detail_transaksi_stiker_tes """ \
                             """(notrans, nopol, jenis_mobil, adm, kategori, jenis_member, akses, akses_out, status, merk, tipe,""" \
                             """tahun, warna, keterangan)""" \
                             """ VALUES """ \
                             """('{}', '{}', '{}', '{}', '0', '{}', NULL, NULL, '1', '{}', '{}', '{}',""" \
                             """'{}', '{}')""".format(
                        self.no_id, self.nopol, self.jenis_mobil, self.adm.name, self.jenis_member, self.merk,
                        self.tipe, self.tahun, self.warna, self.keterangan)

                    # _logger.info()
                    postgresconn.execute_general(strSQL2)


                    # a = """Nama Saya {}""".format("Wahyu")


                    # UPDATE TRANS STIKER WITH DATABASE SERVER PARKIR
                    _logger.info('Sync Transaksi Stiker')
                    strSQL = """SELECT """ \
                             """'notrans','nama','alamat','telepon','jenis_transaksi',""" \
                             """'awal','harga','keterangan','tanggal','operator','akhir',""" \
                             """'maks','no_id','unit_kerja','no_induk','jenis_stiker','hari_ke',""" \
                             """'jenis_langganan','exit_pass','no_kuitansi','tgl_edited','tipe_exit_pass',""" \
                             """'seq_code','unitno','area','reserved','cara_bayar' """ \
                             """FROM transaksi_stiker_tes WHERE no_id='{}'""".format(self.no_id)

                    transaksistikers = postgresconn.execute(query=strSQL, metadata=False)
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
                            if int(transaksistiker[4]) == 0:
                                vals.update({'jenis_transaksi': 'langganan_baru'})
                            elif int(transaksistiker[4]) == 1:
                                vals.update({'jenis_transaksi': 'perpanjang'})
                            else:
                                vals.update({'jenis_transaksi': 'stop'})
                            vals.update({'awal': transaksistiker[5]})
                            vals.update({'harga': transaksistiker[6]})
                            vals.update({'keterangan': transaksistiker[7]})
                            vals.update({'tanggal': transaksistiker[8]})
                            vals.update({'operator': transaksistiker[9]})
                            vals.update({'akhir': transaksistiker[10]})
                            vals.update({'maks': transaksistiker[11]})
                            vals.update({'no_id': transaksistiker[12]})
                            vals.update({'unit_kerja': stasiunkerja.id})
                            vals.update({'no_induk': transaksistiker[14]})
                            vals.update({'jenis_stiker': str(transaksistiker[15])})
                            vals.update({'hari_ke': transaksistiker[16]})
                            vals.update({'jenis_langganan': transaksistiker[17]})
                            vals.update({'exit_pass': transaksistiker[18]})
                            vals.update({'no_kuitansi': transaksistiker[19]})
                            vals.update({'tgl_edited': transaksistiker[20]})
                            vals.update({'tipe_exit_pass': transaksistiker[21]})
                            vals.update({'seq_code': transaksistiker[22]})
                            vals.update({'unitno': transaksistiker[23]})
                            vals.update({'area': transaksistiker[24]})
                            vals.update({'reserved': transaksistiker[25]})
                            if int(transaksistiker[26]) == 0:
                                vals.update({'cara_bayar': 'non_billing'})
                            else:
                                vals.update({'cara_bayar': 'billing'})
                            current_record.write(vals)
                            _logger.info('Transaksi Stiker Updated')
                        else:
                            stasiunkerja = self.find_stasiun_kerja(transaksistiker[13])
                            vals = {}
                            vals.update({'stasiun_kerja_id': stasiunkerja.id})
                            vals.update({'notrans': transaksistiker[0]})
                            vals.update({'name': transaksistiker[1]})
                            vals.update({'alamat': transaksistiker[2]})
                            vals.update({'telphone': transaksistiker[3]})
                            if int(transaksistiker[4]) == 0:
                                vals.update({'jenis_transaksi': 'langganan_baru'})
                            elif int(transaksistiker[4]) == 1:
                                vals.update({'jenis_transaksi': 'perpanjang'})
                            else:
                                vals.update({'jenis_transaksi': 'stop'})
                            vals.update({'awal': transaksistiker[5]})
                            vals.update({'harga': transaksistiker[6]})
                            vals.update({'keterangan': transaksistiker[7]})
                            vals.update({'tanggal': transaksistiker[8]})
                            vals.update({'operator': transaksistiker[9]})
                            vals.update({'akhir': transaksistiker[10]})
                            vals.update({'maks': transaksistiker[11]})
                            vals.update({'no_id': transaksistiker[12]})
                            vals.update({'unit_kerja': transaksistiker[13]})
                            vals.update({'no_induk': transaksistiker[14]})
                            vals.update({'jenis_stiker': int(transaksistiker[15])})
                            vals.update({'hari_ke': transaksistiker[16]})
                            vals.update({'jenis_langganan': transaksistiker[17]})
                            vals.update({'exit_pass': transaksistiker[18]})
                            vals.update({'no_kuitansi': transaksistiker[19]})
                            vals.update({'tgl_edited': transaksistiker[20]})
                            vals.update({'tipe_exit_pass': transaksistiker[21]})
                            vals.update({'seq_code': transaksistiker[22]})
                            vals.update({'unitno': transaksistiker[23]})
                            vals.update({'area': transaksistiker[24]})
                            vals.update({'reserved': transaksistiker[25]})
                            if int(transaksistiker[26]) == 0:
                                vals.update({'cara_bayar': 'non_billing'})
                            else:
                                vals.update({'cara_bayar': 'billing'})
                            transaksi_stiker_obj.create(vals)
                            _logger.info('Transaksi Stiker Created')

                    _logger.info('Sync Detail Transaksi Stiker')
                    strSQL = """SELECT 'notrans','nopol','jenis_mobil','adm','kategori',""" \
                             """'jenis_member','akses','akses_out','status','merk','tipe',""" \
                             """'tahun','warna','keterangan' FROM detail_transaksi_stiker_tes WHERE notrans='{}'""".format(self.no_id)

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
                            current_record.write(vals)
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
                            detail_stiker_obj.create(vals)
                            _logger.info("Detail Created")

                    args = [('no_id', '=', self.no_id)]
                    res = self.env['trans.stiker'].search(args, limit=1)

                    self.stiker_id = res.id

                    v.state = "done"

                if v.jenis_transaksi == "stop":

                    # Process perpanjang to Server Database Parkir and update trans_id
                    base_external_dbsource_obj = self.env['base.external.dbsource']
                    postgresconn = base_external_dbsource_obj.browse(1)
                    postgresconn.connection_open()
                    _logger.info("Connection Open")
                    _logger.info("Sync Stasiun Kerja")

                    # Insert Data Trans Stiker with Odoo to Database Server Parkir
                    _logger.info('Update Data Trans Stiker')
                    strSQLUpdate_akhir = """UPDATE transaksi_stiker_tes """ \
                                         """ SET akhir='{}', cara_bayar='{}'""" \
                                         """ WHERE """ \
                                         """notrans='{}'""".format(v.akhir,v.cara_bayar, self.no_id)

                    postgresconn.execute_general(strSQLUpdate_akhir)

                    # UPDATE TO TRANS STIKER ODOO
                    args = [('id', '=', v.stiker_id.id)]
                    res = self.env['trans.stiker'].search(args).write({'akhir': v.akhir})

                    v.state = "done"

            if v.ganti_nopol == True:

                # Process perpanjang to Server Database Parkir and update trans_id
                base_external_dbsource_obj = self.env['base.external.dbsource']
                postgresconn = base_external_dbsource_obj.browse(1)
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
                         """notrans='{}'""".format(v.new_nopol, v.new_jenis_mobil, v.new_merk, v.new_tipe, v.new_tahun, v.new_warna, v.stiker_id.notrans)

                postgresconn.execute_general(strSQLUpdate_nopol)

                args = [('notrans', '=', v.stiker_id.notrans)]
                res = self.env['detail.transstiker'].search(args)
                vals = {}
                vals.update({'nopol': v.new_nopol})
                vals.update({'jenis_mobil': v.new_jenis_mobil})
                vals.update({'merk': v.new_merk})
                vals.update({'tipe': v.new_tipe})
                vals.update({'tahun': v.new_tahun})
                vals.update({'warna': v.new_warna})
                res.write(vals)

                v.state = "done"

            if v.beli_stiker == True:
                v.state = "done"
            if v.kartu_hilang == True:
                v.state = "done"

        self.message_post("Done Payment")

    @api.one
    def trans_payment(self):
        self.message_post("Save Request Transaction Stiker")
        self.state = "payment"

    # GENERATE TRANS ID WHERE langganan_baru
    @api.one
    def _generate_stiker_id(self):
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
            #_logger.info(unit)
            tex = unit[1:5]
            # self.stiker_id = tex + str(n)
            #_logger.info(tex)
            trans = tex + str(n)
            self.no_id = trans

            args = [('no_id', '=', trans)]
            res = self.env['trans.stiker'].search(args, limit=1)

            if res.no_id:
                raise ValidationError("this trans id : "+ trans +" already exists!")


    @api.model
    def create(self, vals):
        vals['notrans'] = self.env['ir.sequence'].next_by_code('request.transstiker')
        res = super(RequestTransStiker, self).create(vals)
        res._get_stiker()
        res._change_harga_beli_stiker()
        res.calculate_rts()
        res._get_end_date()
        res.trans_payment()
        res._generate_stiker_id()
        return res


    notrans = fields.Char(string="ID #", readonly=True)  #
    unit_kerja = fields.Many2one('stasiun.kerja', 'UNIT #', required=True, readonly=False)  #
    stiker_id = fields.Many2one('trans.stiker', 'STIKER #', required=True, readonly=True)
    name = fields.Char(string="Nama", required=False, readonly=False)
    alamat = fields.Char(string="Alamat", required=False, readonly=False)
    telphone = fields.Char(string="No Telphone", required=False, readonly=False)
    no_id = fields.Char(string="No ID", readonly=True, )  #
    duration = fields.Integer('Duration', default=1, required=False, readonly=False)
    awal = fields.Datetime(string="Start Date", required=False, readonly=True, )  #
    akhir = fields.Datetime(string="End Date", required=False, readonly=True, )  #
    val_harga = fields.Integer(string="Harga", required=False, readonly=True)  #
    tanggal = fields.Datetime(string="Date", required=False, default=fields.Datetime().now(), readonly=True, )  #
    adm = fields.Many2one(comodel_name="res.users", string="Created By", required=False,
                          default=lambda self: self.env.user and self.env.user.id or False, readonly=True)  #
    no_kartu = fields.Char(string="No Card", required=False, )
    jenis_member = fields.Selection(string="Mobil",
                                    selection=[('1st', '1st'), ('2nd', '2nd'), ('3rd', '3rd'), ('4th', '4th'), ],
                                    required=False, readonly=False)
    jenis_transaksi = fields.Selection(string="Jenis Transaksi",
                                       selection=[('langganan_baru', 'LANGGANAN BARU'), ('perpanjang', 'PERPANJANG'),
                                                  ('stop', 'STOP'), ],
                                       required=False, readonly=False)
    keterangan = fields.Text(string="Keterangan", required=False, readonly=False)
    cara_bayar = fields.Selection(string="Cara Pembayaran",
                                  selection=[('billing', 'Billing'), ('non_billing', 'Non Billing'), ],
                                  required=False, readonly=True)
    nopol = fields.Char(string="No Polisi", required=False, readonly=False)
    jenis_mobil = fields.Char(string="Jenis Mobil", required=False, readonly=False)
    merk = fields.Char(string="Merk Mobil", required=False, readonly=False)
    tipe = fields.Char(string="Tipe Mobil", required=False, readonly=False)
    tahun = fields.Char(string="Tahun", required=False, readonly=False)
    warna = fields.Char(string="Warna", required=False, readonly=False)
    amount = fields.Integer(string="Total Amount", required=False, readonly=True)  #
    baru = fields.Boolean(string="KONTRIBUSI", readonly=False)
    perpanjang = fields.Boolean(string="PERPANJANG", default=False, readonly=False)
    beli_stiker = fields.Boolean(string="STIKER", default=False, readonly=False)
    ganti_nopol = fields.Boolean(string="GANTI NOPOL", default=False, readonly=False)
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
    harga_beli_stiker = fields.Integer(string="Beli Stiker", required=False, readonly=True)
    harga_kartu_hilang = fields.Integer(string="Kartu Hilang", required=False, readonly=True)
    harga_ganti_nopol = fields.Integer(string="Ganti Nomor Polisi", required=False, readonly=True)
    new_nopol = fields.Char(string="No Polisi", required=False, readonly=False)
    new_jenis_mobil = fields.Char(string="Jenis Mobil", required=False, readonly=False)
    new_merk = fields.Char(string="Merk Mobil", required=False, readonly=False)
    new_tipe = fields.Char(string="Tipe Mobil", required=False, readonly=False)
    new_tahun = fields.Char(string="Tahun", required=False, readonly=False)
    new_warna = fields.Char(string="Warna", required=False, readonly=False)
    state = fields.Selection(string="State",
                         selection=[('open', 'Open'), ('payment', 'Waiting Payment'), ('done', 'Done'), ],
                         required=False, default="open", )

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