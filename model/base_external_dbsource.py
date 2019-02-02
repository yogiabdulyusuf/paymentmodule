from odoo import api, fields, models

class BaseExternalDbsource(models.Model):
    _inherit = 'base.external.dbsource'

    def execute_general(self, query, params=False):
        with self.connection_open() as connection:
            cur = connection.cursor()
            cur.execute(query, params)
            connection.commit()
            connection.close()