# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    gross_untaxed_amount = fields.Monetary(
        string="Montant HT Brut",
        currency_field='currency_id',
        compute='_compute_global_discount_totals',
    )
    global_discount_amount = fields.Monetary(
        string="Remise",
        currency_field='currency_id',
        compute='_compute_global_discount_totals',
    )
    net_untaxed_amount = fields.Monetary(
        string="Nouveau HT",
        currency_field='currency_id',
        compute='_compute_global_discount_totals',
    )

    @api.depends(
        'order_line.price_unit',
        'order_line.product_uom_qty',
        'order_line.discount',
        'order_line.price_subtotal',
        'order_line.product_id',
        'order_line.display_type',
        'order_line.is_global_discount_line',
        'amount_untaxed',
        'currency_id',
    )
    def _compute_global_discount_totals(self):
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            product_lines = order.order_line.filtered(lambda l: not l.display_type and not l.is_downpayment)
            normal_lines = product_lines.filtered(lambda l: not l._is_global_discount_line())
            gross_ht = 0.0
            for line in normal_lines:
                if line.discount:
                    line_gross = line.price_unit * line.product_uom_qty
                    gross_ht += currency.round(line_gross) if currency else line_gross
                else:
                    gross_ht += line.price_subtotal
            gross_ht = currency.round(gross_ht) if currency else gross_ht
            net_ht = order.amount_untaxed
            discount_amt = max(0.0, (currency.round(gross_ht - net_ht) if currency else (gross_ht - net_ht)))
            order.gross_untaxed_amount = gross_ht
            order.global_discount_amount = discount_amt
            order.net_untaxed_amount = net_ht

    def _get_order_lines_to_report(self):
        lines = super()._get_order_lines_to_report()
        return lines.filtered(lambda l: not l._is_global_discount_line())

    @api.depends(
        'gross_untaxed_amount',
        'global_discount_amount',
        'net_untaxed_amount',
        'order_line.is_global_discount_line',
        'order_line.discount',
    )
    def _compute_tax_totals(self):
        super()._compute_tax_totals()
        for order in self:
            if not order.tax_totals or not isinstance(order.tax_totals, dict):
                continue
            currency = order.currency_id or order.company_id.currency_id
            has_discount = bool(
                currency.compare_amounts(order.global_discount_amount, 0.0) > 0
                if currency else order.global_discount_amount > 0
            )
            order.tax_totals['has_global_discount'] = has_discount
            order.tax_totals['gross_untaxed_amount'] = order.gross_untaxed_amount
            order.tax_totals['global_discount_amount'] = order.global_discount_amount
            order.tax_totals['net_untaxed_amount'] = order.net_untaxed_amount


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_global_discount_line = fields.Boolean(
        string="Est une ligne de remise globale",
        compute="_compute_is_global_discount_line",
        store=True,
        readonly=False,
        copy=True,
    )

    @api.depends('product_id', 'price_unit', 'display_type', 'company_id.sale_discount_product_id')
    def _compute_is_global_discount_line(self):
        for line in self:
            if not line.is_global_discount_line:
                discount_product = line.company_id.sale_discount_product_id
                line.is_global_discount_line = bool(
                    not line.display_type
                    and discount_product
                    and line.product_id == discount_product
                    and line.price_unit < 0
                )

    def _is_global_discount_line(self):
        self.ensure_one()
        discount_product = self.company_id.sale_discount_product_id
        return bool(
            self.is_global_discount_line
            or (
                not self.display_type
                and discount_product
                and self.product_id == discount_product
                and self.price_unit < 0
            )
        )

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        if self._is_global_discount_line():
            res['is_global_discount_line'] = True
        return res

    def _get_section_lines(self):
        return super()._get_section_lines().filtered(lambda l: not l._is_global_discount_line())
