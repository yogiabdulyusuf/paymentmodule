# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class WizardAddCardMember(models.TransientModel):
    _name = 'wizard.add.card.member'
    _description = 'Add Card Member'

    @api.multi
    def add_card_member(self):

        base_external_dbsource_obj = self.env['base.external.dbsource']
        postgresconn = base_external_dbsource_obj.sudo().browse(1)
        postgresconn.connection_open()
        _logger.info("Connection Open")

        DATE = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # AMBIL ACTIVE ID YANG ADA DI FORM
        active_id = self.env['request.transstiker'].browse(self.env.context.get('active_id'))
        # rts = self.env['request.transstiker'].browse(active_id)
        # _logger.info(rts)
        # _logger.info(rts.no_id)
        # _logger.info(rts.adm.name)
        # _logger.info(self.card_member)
        # _logger.info(self.no_urut)


        RTS_stiker_id = active_id.no_id
        RTS_adm = active_id.adm.name

        # Insert Data Trans Stiker with Odoo to Database Server Parkir
        _logger.info('INSERT CARD MEMBER')
        strSQLCreate = """INSERT INTO card_member """ \
                       """(notrans,no_card,no_urut,tanggal,adm)""" \
                       """ VALUES """ \
                       """('{}','{}','{}','{}','{}')""".format(RTS_stiker_id, self.card_member, self.no_urut, DATE,
                                                               RTS_adm)

        postgresconn.execute_general(strSQLCreate)

        active_id.state = 'payment'

    no_urut = fields.Char(string="No Urut", required=True, )
    card_member = fields.Char(string="No Card", required=True, )







