# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, Command
from odoo.exceptions import ValidationError
from odoo.tools import float_repr
import logging

_logger = logging.getLogger(__name__)

class AccountMoveDiscount(models.TransientModel):
    _name = 'account.move.discount'
    _description = "Assistant de remise sur facture"

    move_id = fields.Many2one(
        'account.move', default=lambda self: self.env.context.get('active_id'), required=True)
    company_id = fields.Many2one(related='move_id.company_id')
    currency_id = fields.Many2one(related='move_id.currency_id')
    discount_amount = fields.Monetary(string="Montant")
    discount_percentage = fields.Float(string="Pourcentage")
    discount_type = fields.Selection(
        selection=[
            ('line_discount', "Sur toutes les lignes"),
            ('global_discount', "Remise globale"),
            ('amount', "Montant fixe"),
        ],
        default='line_discount',
        string="Type de remise"
    )

    @api.constrains('discount_type', 'discount_percentage', 'discount_amount')
    def _check_discount_amount(self):
        for wizard in self:
            if wizard.discount_type in ('line_discount', 'global_discount') and wizard.discount_percentage > 1.0:
                raise ValidationError(_("La remise ne peut pas dépasser 100%."))
            if wizard.discount_type in ('line_discount', 'global_discount') and wizard.discount_percentage < 0.0:
                raise ValidationError(_("La remise ne peut pas être négative."))
            if wizard.discount_type == 'amount' and wizard.discount_amount < 0.0:
                raise ValidationError(_("La remise ne peut pas être négative."))

    def _prepare_discount_product_values(self):
        self.ensure_one()
        values = {
            'name': _('Remise'),
            'type': 'service',
            'invoice_policy': 'order',
            'list_price': 0.0,
            'company_id': self.company_id.id,
            'taxes_id': False,
            'supplier_taxes_id': False,
        }
        services_category = self.env.ref('product.product_category_services', raise_if_not_found=False)
        if services_category:
            values['categ_id'] = services_category.id
        return values

    def _get_discount_product(self):
        """Return product.product used for discount line"""
        self.ensure_one()
        company = self.company_id
        discount_product = company.sale_discount_product_id
        if not discount_product:
            if self.env['product.product'].has_access('create') and company.has_access('write'):
                company.sale_discount_product_id = self.env['product.product'].create(
                    self._prepare_discount_product_values()
                )
            else:
                raise ValidationError(_(
                    "Aucun article de remise n'est configuré pour cette société. "
                    "Veuillez demander à un administrateur d'en configurer un."
                ))
            discount_product = company.sale_discount_product_id
        return discount_product

    def _prepare_global_discount_move_lines(self, base_lines):
        self.ensure_one()
        AccountTax = self.env['account.tax']
        discount_dp = self.env['decimal.precision'].precision_get('Discount')
        has_multiple_tax_combinations = len(set(base_line['tax_ids'] for base_line in base_lines if base_line['tax_ids'])) > 1
        
        move_line_values_list = []
        for base_line in base_lines:
            # The name of the invoice line
            if has_multiple_tax_combinations:
                if self.discount_type in ('global_discount', 'line_discount'):
                    line_description = _("Remise %(percent)s%%\n- Sur les articles avec les taxes suivantes : %(taxes)s") % {
                        'percent': float_repr(self.discount_percentage * 100.0, discount_dp),
                        'taxes': ", ".join(base_line['tax_ids'].mapped('name')),
                    }
                else:
                    line_description = _("Remise\n- Sur les articles avec les taxes suivantes : %(taxes)s") % {
                        'taxes': ", ".join(base_line['tax_ids'].mapped('name')),
                    }
            else:
                if self.discount_type in ('global_discount', 'line_discount'):
                    line_description = _("Remise %(percent)s%%") % {
                        'percent': float_repr(self.discount_percentage * 100.0, discount_dp),
                    }
                else:
                    line_description = _("Remise")

            move_line_values_list.append({
                'name': line_description,
                'product_id': base_line['product_id'].id,
                'price_unit': base_line['price_unit'],
                'quantity': base_line['quantity'],
                'tax_ids': [Command.set(base_line['tax_ids'].ids)],
                'extra_tax_data': AccountTax._export_base_line_extra_tax_data(base_line),
                'sequence': 999,
                'is_global_discount_line': True,
            })

        return move_line_values_list

    def _clear_previous_discounts(self):
        """Supprime toute ancienne remise (sur les lignes ou ligne de remise globale/fixe)."""
        self.ensure_one()
        move = self.move_id
        discount_lines = move.invoice_line_ids.filtered(lambda l: l._is_global_discount_line())
        other_discounted_lines = (move.invoice_line_ids - discount_lines).filtered(lambda l: l.discount != 0.0)
        commands = [Command.unlink(line.id) for line in discount_lines] + [
            Command.update(line.id, {'discount': 0.0}) for line in other_discounted_lines
        ]
        if commands:
            move.with_context(check_move_validity=False).write({'invoice_line_ids': commands})

    def _create_discount_lines(self):
        self.ensure_one()
        discount_product = self._get_discount_product()
        move = self.move_id
        currency = move.currency_id or move.company_currency_id
        move_lines = move.invoice_line_ids.filtered(
            lambda x: x.display_type == 'product' and not x._is_global_discount_line()
        )
        if not move_lines:
            return

        discount_dp = self.env['decimal.precision'].precision_get('Discount')
        if self.discount_type in ('global_discount', 'line_discount'):
            gross_ht = sum(move_lines.mapped('price_subtotal'))
            amount = currency.round(gross_ht * self.discount_percentage) if currency else (gross_ht * self.discount_percentage)
            line_description = _("Remise %(percent)s%%") % {
                'percent': float_repr(self.discount_percentage * 100.0, discount_dp),
            }
        else:
            amount = currency.round(self.discount_amount) if currency else self.discount_amount
            line_description = _("Remise")

        if not amount:
            return

        taxes = self.env['account.tax']
        if getattr(move, 'global_tax_id', False):
            taxes |= move.global_tax_id
        if move_lines:
            lines_with_taxes = move_lines.filtered(lambda l: l.tax_ids)
            if lines_with_taxes:
                common_taxes = lines_with_taxes[0].tax_ids
                for line in lines_with_taxes[1:]:
                    common_taxes &= line.tax_ids
                taxes |= common_taxes

        values = {
            'name': line_description,
            'product_id': discount_product.id,
            'price_unit': -amount,
            'quantity': 1.0,
            'tax_ids': [Command.set(taxes.ids)] if taxes else [Command.clear()],
            'sequence': 999,
            'is_global_discount_line': True,
        }
        move.with_context(check_move_validity=False).write({
            'invoice_line_ids': [Command.create(values)],
        })

    def action_apply_discount(self):
        self.ensure_one()
        if self.move_id.state != 'draft':
            raise ValidationError(_("Vous ne pouvez appliquer une remise que sur une facture à l'état brouillon."))
        
        # Écraser toute ancienne remise avant d'appliquer la nouvelle
        self._clear_previous_discounts()

        if self.discount_type == 'line_discount':
            product_lines = self.move_id.invoice_line_ids.filtered(
                lambda l: l.display_type == 'product' and not l._is_global_discount_line()
            )
            if product_lines:
                self.move_id.with_context(check_move_validity=False).write({
                    'invoice_line_ids': [
                        Command.update(line.id, {'discount': self.discount_percentage * 100.0})
                        for line in product_lines
                    ]
                })
        else:
            self._create_discount_lines()
