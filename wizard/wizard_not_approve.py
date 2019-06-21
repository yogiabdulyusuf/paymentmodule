# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class WizardNotApprove(models.TransientModel):
    _name = 'wizard.not.approve'
    _description = 'Not Approve'

    # GET ID RTS
    def _get_default_rts(self):
        return self.env['request.transstiker'].browse(self.env.context.get('active_id'))

    rts_ids = fields.Many2one(comodel_name="request.transstiker", string="RTS ID", required=False, readonly=True, default=_get_default_rts)
    note = fields.Text(string="Message", required=False, )

    @api.multi
    def not_approve_message(self):
        for record in self:
            if record.rts_ids:
                for row in record.rts_ids:
                    row.message_post(self.note)
                    row.state = 'done'
                    # row.message_post(self.note)