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

    @api.constrains('discount_type', 'discount_percentage')
    def _check_discount_amount(self):
        for wizard in self:
            if wizard.discount_type in ('line_discount', 'global_discount') and wizard.discount_percentage > 1.0:
                raise ValidationError(_("La remise ne peut pas dépasser 100%."))
            if wizard.discount_type in ('line_discount', 'global_discount') and wizard.discount_percentage < 0.0:
                raise ValidationError(_("La remise ne peut pas être négative."))

    def _prepare_discount_product_values(self):
        self.ensure_one()
        values = {
            'name': _('Remise'),
            'type': 'service',
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
                'sequence': 999,
            })

        return move_line_values_list

    def _create_discount_lines(self):
        self.ensure_one()
        discount_product = self._get_discount_product()

        if self.discount_type in ('global_discount', 'line_discount'):
            amount_type = 'percent'
            amount = self.discount_percentage * 100.0
        else:
            amount_type = 'fixed'
            amount = self.discount_amount

        move = self.move_id
        AccountTax = self.env['account.tax']
        move_lines = move.invoice_line_ids.filtered(lambda x: x.display_type == 'product')
        
        # We need to compute the base lines for tax calculations similar to sale order
        base_lines = [move._prepare_product_base_line_for_taxes_computation(line) for line in move_lines]
        AccountTax._add_tax_details_in_base_lines(base_lines, move.company_id)
        AccountTax._round_base_lines_tax_details(base_lines, move.company_id)

        def grouping_function(base_line):
            return {'product_id': discount_product}

        global_discount_base_lines = AccountTax._prepare_global_discount_lines(
            base_lines=base_lines,
            company=self.company_id,
            amount_type=amount_type,
            amount=amount,
            computation_key=f'global_discount,{self.id}',
            grouping_function=grouping_function,
        )
        _logger.info(f"\n\n\n\n\n\n\n\n\n\n\n\n\n  global_discount_base_lines ===> {global_discount_base_lines}\n\n\n\n\n\n\n\n\n\n\n\n")

        commands = [
            Command.create(values)
            for values in self._prepare_global_discount_move_lines(global_discount_base_lines)
        ]
        _logger.info(f"\n\n\n\n\n\n\n\n\n\n\n\n\n  commande ===> {self._prepare_global_discount_move_lines(global_discount_base_lines)}\n\n\n\n\n\n\n\n\n\n\n\n")
        _logger.info(f"\n\n\n\n\n\n\n\n\n\n\n\n\n  global_discount_base_lines ===> {global_discount_base_lines}\n\n\n\n\n\n\n\n\n\n\n\n")
        if commands:
            move.with_context(check_move_validity=False).write({'invoice_line_ids': commands})

    def action_apply_discount(self):
        self.ensure_one()
        if self.move_id.state != 'draft':
            raise ValidationError(_("Vous ne pouvez appliquer une remise que sur une facture à l'état brouillon."))
        
        if self.discount_type == 'line_discount':
            # On applique le pourcentage dans la colonne '% Remise' de chaque ligne
            _logger.info("\n\n\n\n\nteste\n\n\n\n")
            self.move_id.invoice_line_ids.write({'discount': self.discount_percentage * 100.0})
        else:
            self._create_discount_lines()
