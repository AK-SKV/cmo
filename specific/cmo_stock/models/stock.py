# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.tools.translate import _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    partner_id = fields.Many2one(
        'res.partner',
        default=lambda self: self._get_partner_id(),
    )
    default_operating_unit_id = fields.Many2one(
        'operating.unit',
        string='Default Operating Unit',
        compute='_compute_default_operating_unit_id',
    )

    @api.model
    def _get_partner_id(self):
        user = self.env['res.users'].browse(self._uid)
        return user.partner_id and user.partner_id.id or False

    @api.multi
    @api.depends('partner_id')
    def _compute_default_operating_unit_id(self):
        for picking in self:
            User = picking.env['res.users']
            picking.default_operating_unit_id = False
            if picking.partner_id:
                user = User.search([('partner_id', '=',
                                     picking.partner_id.id)])
                if user:
                    picking.default_operating_unit_id = \
                        user[0].default_operating_unit_id.id

    @api.multi
    def action_open_stock(self):
        # Get product_id in each line
        product_ids = []
        for picking in self:
            product_ids += picking.move_lines.mapped('product_id.id')
        return {
            'name': _('Cuurent Inventory Valuation'),
            'res_model': 'stock.history',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,graph',
            'domain': "[('product_id','in', \
                [" + ','.join(map(str, product_ids)) + "])]",
            'context': "{'search_default_group_by_location': True, \
                         'search_default_group_by_product': True}"
        }


class StockMove(models.Model):
    _inherit = 'stock.move'

    project_id = fields.Many2one(
        'project.project',
        string='Project name',
        domain=lambda self: self._get_domain(),
    )
    location_dest_id = fields.Many2one(
        'stock.location',
        default=lambda self: self._get_location_dest_id(),
    )

    @api.model
    def _get_domain(self):
        user = self.env['res.users'].browse(self._uid)
        operating_unit_ids = []
        for operating_unit in user.operating_unit_ids:
            operating_unit_ids.append(operating_unit.id)
        return [('operating_unit_id', 'in', operating_unit_ids)]

    @api.model
    def _get_location_dest_id(self):
        Location = self.env['stock.location']
        user = self.env['res.users'].browse(self._uid)
        ou_id = user.default_operating_unit_id and \
            user.default_operating_unit_id.id or False
        if ou_id:
            location = Location.search([('operating_unit_id', '=', ou_id)])
        return location and location[0].id or False

    # @api.multi
    # @api.onchange('product_id', 'location_id', 'location_dest_id',
    #               'picking_id.partner_id')
    # def onchange_product_id(self):
    #     for move in self:
    #         res = super(StockMove, move).onchange_product_id(
    #             move.product_id.id, move.location_id.id,
    #             move.location_dest_id.id, move.picking_id.partner_id.id
    #         )
    #         if res:
    #             res = res['value']
    #             move.name = res.get('name', False)
    #             move.product_uom = res.get('product_uom', False)
    #             move.product_uos = res.get('product_uos', False)
    #             move.product_uom_qty = res.get('product_uom_qty', False)
    #             move.product_uos_qty = res.get('product_uos_qty', False)
    #             move.location_id = res.get('location_id', False)
    #             move.location_dest_id = res.get('location_dest_id', False)


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    @api.multi
    def action_picking_type_form(self):
        user = self.env['res.users'].browse(self._uid)
        domain = [(1, '=', 1)]
        if user.has_group('stock.group_stock_manager'):
            domain = ['|', ('code', '=', 'incoming'),
                      '|', ('code', '=', 'outgoing'),
                           ('code', '=', 'internal')]
        elif user.has_group('cmo_stock.group_stock_wh_user'):
            domain = ['|', ('code', '=', 'incoming'),
                           ('code', '=', 'outgoing')]
        elif user.has_group('stock.group_stock_user'):
            domain = [('code', '=', 'outgoing')]
        elif user.has_group('cmo_stock.group_stock_readonly'):
            domain = [('code', '=', 'outgoing')]
        return {
            'name': _('All Operations'),
            'res_model': 'stock.picking.type',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'kanban,form',
            'domain': domain
        }
