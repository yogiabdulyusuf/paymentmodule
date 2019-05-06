# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class WizardAddCardMember(models.TransientModel):
    _name = 'wizard.add.card.member'
    _description = 'Add Card Member'

    card_member = fields.Char(string="Card Member", required=False, )
    # note = fields.Text(string="note", required=False, )

    @api.multi
    def add_card_member(self):
        for record in self:

            base_external_dbsource_obj = self.env['base.external.dbsource']
            postgresconn = base_external_dbsource_obj.sudo().browse(1)
            postgresconn.connection_open()
            _logger.info("Connection Open")

            DATE = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # AMBIL ACTIVE ID YANG ADA DI FORM
            active_id = self.env['request.transstiker'].browse(self.env.context.get('active_id'))
            rts = self.env['request.transstiker'].browse(active_id)

            RTS_stiker_id = rts.stiker_id.notrans
            RTS_adm = rts.adm.name

            # Insert Data Trans Stiker with Odoo to Database Server Parkir
            _logger.info('INSERT CARD MEMBER')
            strSQLCreate = """INSERT INTO card_member """ \
                                 """(notrans,no_card,no_urut,tanggal,adm)""" \
                                 """ VALUES """ \
                                 """('{}','{}','','{}','{}')""".format(RTS_stiker_id, self.card_member, DATE, RTS_adm)

            postgresconn.execute_general(strSQLCreate)

            for row in record.rts_ids:
                row.state = 'done'
                # row.message_post(self.note)




