# -*- coding: utf-8 -*-
# © 2016 Eficent Business and IT Consulting Services S.L.
# - Jordi Ballester Alomar
# © 2016 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class AccountInvoiceReport(models.Model):

    _inherit = "account.invoice.report"

    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit')

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """
            ,sub.operating_unit_id
        """
        return select_str

    def _sub_select(self):
        select_str = super(AccountInvoiceReport, self)._sub_select()
        select_str += """
            ,ai.operating_unit_id
        """
        return select_str

    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += """
            ,ai.operating_unit_id
        """
        return group_by_str
