# -*- coding: utf-8 -*-
from odoo import _, api, models, Command
from odoo.exceptions import ValidationError
from odoo.tools import float_repr


class SaleOrderDiscount(models.TransientModel):
    _inherit = 'sale.order.discount'

    @api.constrains('discount_type', 'discount_percentage', 'discount_amount')
    def _check_discount_amount(self):
        super()._check_discount_amount()
        for wizard in self:
            if wizard.discount_type in ('sol_discount', 'so_discount') and wizard.discount_percentage < 0.0:
                raise ValidationError(_("La remise ne peut pas être négative."))
            if wizard.discount_type == 'amount' and wizard.discount_amount < 0.0:
                raise ValidationError(_("La remise ne peut pas être négative."))

    def _clear_previous_discounts(self):
        """Supprime toute ancienne remise (sur les lignes ou ligne de remise globale/fixe)."""
        self.ensure_one()
        order = self.sale_order_id
        discount_lines = order.order_line.filtered(lambda l: l._is_global_discount_line())
        if discount_lines:
            discount_lines.unlink()
        other_discounted_lines = order.order_line.filtered(lambda l: l.discount != 0.0)
        if other_discounted_lines:
            other_discounted_lines.write({'discount': 0.0})

    def _create_discount_lines(self):
        self.ensure_one()
        self = self.with_context(lang=self.sale_order_id._get_lang())
        discount_product = self._get_discount_product()
        order = self.sale_order_id
        currency = order.currency_id or order.company_id.currency_id
        order_lines = order.order_line.filtered(
            lambda x: not x.display_type and not x.is_downpayment and not x._is_global_discount_line()
        )
        if not order_lines:
            return

        discount_dp = self.env['decimal.precision'].precision_get('Discount')
        if self.discount_type == 'so_discount':
            gross_ht = sum(order_lines.mapped('price_subtotal'))
            amount = currency.round(gross_ht * self.discount_percentage) if currency else (gross_ht * self.discount_percentage)
            so_line_description = _("Remise %(percent)s%%") % {
                'percent': float_repr(self.discount_percentage * 100.0, discount_dp),
            }
        else:
            amount = currency.round(self.discount_amount) if currency else self.discount_amount
            so_line_description = _("Remise")

        if not amount:
            return

        taxes = self.env['account.tax']
        if getattr(order, 'global_tax_id', False):
            taxes |= order.global_tax_id
        if order_lines:
            lines_with_taxes = order_lines.filtered(lambda l: l.tax_ids)
            if lines_with_taxes:
                common_taxes = lines_with_taxes[0].tax_ids
                for line in lines_with_taxes[1:]:
                    common_taxes &= line.tax_ids
                taxes |= common_taxes

        values = {
            'name': so_line_description,
            'product_id': discount_product.id,
            'price_unit': -amount,
            'technical_price_unit': -amount,
            'product_uom_qty': 1.0,
            'tax_ids': [Command.set(taxes.ids)] if taxes else [Command.clear()],
            'sequence': 999,
            'is_global_discount_line': True,
        }
        order.order_line = [Command.create(values)]

    def action_apply_discount(self):
        self.ensure_one()
        self = self.with_company(self.company_id)
        # Écraser toute ancienne remise avant d'appliquer la nouvelle
        self._clear_previous_discounts()

        if self.discount_type == 'sol_discount':
            product_lines = self.sale_order_id.order_line.filtered(
                lambda l: not l.display_type and not l._is_global_discount_line()
            )
            if product_lines:
                product_lines.write({'discount': self.discount_percentage * 100.0})
        else:
            self._create_discount_lines()
