from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, Warning
import logging

_logger = logging.getLogger(__name__)


class WizardReportMonthlyBilling(models.TransientModel):
    _name = 'wizard.check.kartu'
    _description = 'Check Kartu Parkir'


    @api.one
    def proses_check_kartu_parkir(self):

        base_external_dbsource_obj = self.env['base.external.dbsource']
        postgresconn = base_external_dbsource_obj.sudo().browse(1)
        postgresconn.connection_open()
        _logger.info("Connection Open")

        _logger.info('Get Card Member')
        strSQL = """SELECT """ \
                 """notrans,no_urut,no_card """ \
                 """FROM card_member WHERE no_card='{}' OR no_urut='{}'""".format(self.no_card,self.no_urut)

        select_card_member = postgresconn.execute(query=strSQL, metadata=False)
        _logger.info(select_card_member)

        if select_card_member:
            for row in select_card_member:
                raise ValidationError("Kartu anda sudah terdaftar di Stiker# "+ row[0] +", dengan No Urut : "+ row[1] +", No Card / Barcode : "+ row[2] +"")
        else:
            raise ValidationError("Kartu anda belum terdaftar !!")



    no_urut = fields.Char(string="No Urut", required=False, )
    no_card = fields.Char(string="No Card / Barcode", required=False, )

