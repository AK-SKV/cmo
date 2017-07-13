# -*- coding: utf-8 -*-
from openerp import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_id = fields.Many2one(
        'project.project',
        string='Project Name',
        ondelete='restrict',
    )
    order_ref = fields.Many2one(
        'sale.order',
        string='Quotation Number',
        ondelete='restrict',
    )
    event_date_description = fields.Char(
        string='Event Date',
        size=250,
    )
    venue_description = fields.Char(
        string='Venue',
        size=250,
    )
    po_type_id = fields.Many2one(
        'purchase.order.type.config',
        string='PO Type',
        required=True,
    )
    po_type_related = fields.Char(
        string='PO Type Related',
        related='po_type_id.name',
    )
    approve_ids = fields.Many2one(
        'hr.employee',
        string='PO Approve',
        required=True,
    )
    operating_unit_id = fields.Many2one(
        change_default=True,
    )

    @api.onchange('po_type_id')
    def _onchange_po_type_id(self):
        self.project_id = False
        self.order_ref = False
        self.event_date_description = False
        self.venue_description = False
        self.order_line = False

    @api.onchange('project_id')
    def _onchange_project_id(self):
        self.order_ref = False
        self.event_date_description = False
        self.venue_description = False
        for line in self.order_line:
            line.product_ref = False

    @api.onchange('order_ref')
    def _onchange_order_id(self):
        self.event_date_description = self.order_ref.event_date_description
        self.venue_description = self.order_ref.venue_description
        for line in self.order_line:
            line.product_ref = False

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            ctx = self._context.copy()
            fiscalyear_id = self.env['account.fiscalyear'].find()
            ctx["fiscalyear_id"] = fiscalyear_id
            vals['name'] = self.env['ir.sequence'].\
                with_context(ctx).get('cmo.purchase')
        return super(PurchaseOrder, self).create(vals)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_ref = fields.Many2one(
        'product.product',
        string='Product Ref',
    )
    date_planned = fields.Date(
        required=False,
    )


class PurchaseOrderTypeConfig(models.Model):
    _name = "purchase.order.type.config"

    name = fields.Char(
        string='PO Type',
    )
    category_id = fields.Many2one(
        'product.category',
        string='Internal Category',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
