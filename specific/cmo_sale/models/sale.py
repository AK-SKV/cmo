# -*- coding: utf-8 -*-

from openerp import fields, models, api


class sale_order(models.Model):
    _inherit = 'sale.order'

    project_number = fields.Char(
        string='Project Code',
        readonly=True,
        copy=False,
    )
    project_related_id = fields.Many2one(
        'project.project',
        string='Project',
        inverse='_compute_project_related_id',
        states={'done': [('readonly', True)]},
    )
    event_date_description = fields.Char(
        string='Event Date',
        size=250,
        states={'done': [('readonly', True)]},
    )
    venue_description = fields.Char(
        string='Venue',
        size=250,
        states={'done': [('readonly', True)]},
    )
    amount_before_management_fee = fields.Float(
        string="Before Management Fee",
        compute='_compute_before_management_fee',
    )
    payment_term_description = fields.Text(
        string='Payment Term',
        states={'done': [('readonly', True)]},
    )
    convenant_description = fields.Text(
        string='Convenant',
        states={'done': [('readonly', True)]},
    )
    discount_type = fields.Selection(
        [('percent', 'Percentage'),
         ('amount', 'Amount')],
         inverse='_compute_discount_rate',
         string='Discount Type',
         states={'done': [('readonly', True)]},
    )
    discount_rate = fields.Float(
        string='Discount Rate',
        inverse='_compute_discount_rate',
        store=True,
        states={'done': [('readonly', True)]},
    )
    amount_discount = fields.Float(
        string="Discount",
        compute='_compute_amount_discount',
        readonly=True,
    )

    @api.depends('amount_untaxed')
    def _compute_amount_discount(self):
        for line in self:
            total = sum(line.order_line.mapped('price_unit'))
            line.amount_discount = total - line.amount_untaxed

    @api.multi
    @api.depends('amount_before_management_fee')
    def _compute_before_management_fee(self):
        total = sum(self.order_line.filtered(\
            lambda r : r.order_lines_group == 'before'
            ).mapped('price_unit'))
        self.amount_before_management_fee = total

    @api.depends('discount_type', 'discount_rate', 'order_line')
    def _compute_discount_rate(self):
        lines = self.order_line
        if not self.discount_type:
            return
        percent = 0
        if self.discount_type == 'percent':
            percent = self.discount_rate
        elif self.discount_type == 'amount':
            total = sum(self.order_line.mapped('price_unit'))
            percent = (self.discount_rate * 100.0) / total
        for line in lines: # TODO: refactor iterator
            line.discount = percent

    @api.onchange('project_related_id')
    def _onchange_project_number(self):
        project = self.env['project.project']\
            .browse(self.project_related_id.id)
        self.project_id = project.analytic_account_id.id
        self.project_number = project.project_number

    @api.multi
    def _compute_project_related_id(self):
        for quote in self:
            parent_project = self.env['project.project']\
                .browse(quote.project_related_id.id)
            quote.project_id = parent_project.analytic_account_id.id
            quote.project_number = parent_project.project_number


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    order_lines_group = fields.Selection(
        [('before','Before Management Fee'),
         ('manage_fee','Management and Operation Fee'),
        ],
        string='Group',
        default='before',
    )

    sale_layout_custom_group_id = fields.Many2one(
        'sale_layout.custom_group',
        string='Custom Group',
    )

    sale_order_line_margin = fields.Float(
        string='Margin',
        compute='_get_sale_order_line_margin',
        readonly=True,
    )

    section_code = fields.Selection(
        [('A', 'A'),
         ('B', 'B'),
         ('C', 'C'),
         ('D', 'D'),
         ('E', 'E'),
         ('F', 'F'),
        ],
        string='Section Code',
    )

    @api.multi
    def cal_management_fee(self):
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.cal.manage.fee',
            'src_model': 'sale.order',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {'order_line_id': self.id, 'view_id': 'view_sale_management_fee',}
        }

    @api.onchange('price_unit', 'purchase_price')
    def _get_sale_order_line_margin(self):
        margin = self.price_unit - self.purchase_price
        self.sale_order_line_margin = margin

class SaleLayoutCustomGroup(models.Model):
    _name = 'sale_layout.custom_group'

    name = fields.Char(
        string='Name',
        required=True,
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Name must be unique!'),
    ]
