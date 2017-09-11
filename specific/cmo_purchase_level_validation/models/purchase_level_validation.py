# -*- coding: utf-8 -*-

from openerp import fields, models, api, _
from openerp.exceptions import ValidationError


class PurchaseLevelValidataion(models.Model):
    _name = 'purchase.level.validation'

    level = fields.Integer(
        string='Level',
        required=True,
    )
    limit_amount = fields.Float(
        string='Limit Amount',
        required=True,
    )
    operating_unit_id = fields.Many2one(
        'operating.unit',
        string='Operating Unit',
    )
    user_ids = fields.Many2many(
        'res.users',
        'res_user_purchase_level_validation_rel', 'validation_id', 'user_id',
        string='Users',
    )


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    level_id = fields.Many2one(
        'purchase.level.validation',
        string='Validation Level',
        track_visibility='onchange',
        copy=False,
    )
    approver_ids = fields.Many2many(
        'res.users',
        'purchase_approver_rel', 'purchase_id', 'user_id',
        string='Approval',
        track_visibility='onchange',
        copy=False,
    )
    approve_level = fields.Integer(
        related='level_id.level',
        string='Validation Level',
        store=False,
        readonly=True,
    )

    @api.multi
    def action_check_approval(self):
        self.ensure_one
        amount_untaxed = self.amount_untaxed
        target_levels = self.env['purchase.level.validation'].search([
            ('operating_unit_id', 'in',
                self.env.user.operating_unit_ids.ids),
            ('limit_amount', '<=', amount_untaxed),
        ]).sorted(key=lambda r: r.level)
        if self.approver_ids and self.env.user not in self.approver_ids:
            raise ValidationError(_("Your user is not allow to "
                                    "approve this document."))
        if target_levels:
            if self.level_id:
                min_level = min(filter(
                        lambda r: r >= self.level_id.level,
                        target_levels.mapped('level')))
                target_level = target_levels.filtered(
                    lambda r: r.level == min_level + 1
                )
                if target_level:
                    self.write({
                        'level_id': target_level.id,
                        'approver_ids': [
                            (6, 0, target_level.user_ids.ids)
                        ],
                    })
                else:
                    self.write({
                        'level_id': False,
                        'approver_ids': False,
                    })
            else:
                if not self.level_id and not self.approver_ids:
                    target_level = target_levels.filtered(
                        lambda r: r.level == min(target_levels.mapped('level'))
                    )
                    self.write({
                        'level_id': target_level.id,
                        'approver_ids': [
                            (6, 0, target_level.user_ids.ids)
                        ],
                    })
        return True
