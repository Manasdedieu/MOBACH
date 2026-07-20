# -*- coding: utf-8 -*-
from odoo import api, models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    object = fields.Text(string="Objet")

    ir_tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='Taxe IR',
        domain=[('is_withholding_ir', '=', True), ('active', '=', True)],
        ondelete='restrict',
        help="Taxe IR applicable sur le montant HT de ce devis.\n"
             "Ex : IR 2,2% ou IR 5,5%",
    )

    ir_amount = fields.Monetary(
        string='Montant IR',
        currency_field='currency_id',
        compute='_compute_ir_amounts',
        store=True,
    )

    amount_net_mandate = fields.Monetary(
        string='Net à Mandater',
        currency_field='currency_id',
        compute='_compute_ir_amounts',
        store=True,
        help="Net à Mandater = Total HT − IR",
    )

    @api.depends('amount_untaxed', 'ir_tax_id', 'ir_tax_id.amount')
    def _compute_ir_amounts(self):
        for order in self:
            if order.ir_tax_id and order.ir_tax_id.amount_type == 'percent':
                ir_amt = order.amount_untaxed * order.ir_tax_id.amount / 100.0
            else:
                ir_amt = 0.0
            order.ir_amount = ir_amt
            order.amount_net_mandate = order.amount_untaxed - ir_amt

    def _prepare_invoice(self):
        result = super()._prepare_invoice()
        if self.object:
            result.update({'object': self.object})
        if self.ir_tax_id:
            result.update({'ir_tax_id': self.ir_tax_id.id})
        return result

    @api.depends('ir_tax_id', 'ir_amount', 'amount_net_mandate')
    def _compute_tax_totals(self):
        super()._compute_tax_totals()
        for order in self:
            if order.tax_totals is None:
                continue
            order.tax_totals['ir_tax_name'] = (
                order.ir_tax_id.name if order.ir_tax_id else False
            )
            order.tax_totals['ir_amount'] = order.ir_amount
            order.tax_totals['amount_net_mandate'] = order.amount_net_mandate
            order.tax_totals['has_ir'] = bool(order.ir_tax_id)

