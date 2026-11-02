# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    ui_last_currency_id = fields.Many2one('res.currency', string="Last UI Currency", copy=False)

    has_linked_order = fields.Boolean(
        string="Est liée à une commande",
        compute="_compute_has_linked_order"
    )

    @api.depends('invoice_line_ids')
    def _compute_has_linked_order(self):
        for move in self:
            has_order = False
            # Check for sale module integration
            if 'sale_line_ids' in self.env['account.move.line']._fields:
                if any(line.sale_line_ids for line in move.invoice_line_ids):
                    has_order = True
            move.has_linked_order = has_order

    @api.onchange('currency_id')
    def _onchange_currency_id_convert_prices(self):
        # L'ancienne devise est accessible via self._origin ou le dernier track UI
        old_currency = self.ui_last_currency_id or self._origin.currency_id
        new_currency = self.currency_id
        
        # S'il y a bien un changement de devise (et qu'on a une ancienne devise)
        if old_currency and new_currency and old_currency != new_currency:
            date = self.invoice_date or self.date or fields.Date.context_today(self)
            
            # Parcourir les lignes de la facture (lignes de produits uniquement)
            for line in self.invoice_line_ids.filtered(lambda l: l.display_type in ('product', False, '')):
                if line.price_unit:
                    # _convert gère la conversion mathématique en fonction des taux de change
                    new_price = old_currency._convert(
                        line.price_unit, 
                        new_currency, 
                        self.company_id, 
                        date
                    )
                    line.price_unit = new_price
            
            self.ui_last_currency_id = new_currency

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
        'invoice_line_ids.price_unit',
        'invoice_line_ids.quantity',
        'invoice_line_ids.discount',
        'invoice_line_ids.price_subtotal',
        'invoice_line_ids.product_id',
        'invoice_line_ids.display_type',
        'invoice_line_ids.is_global_discount_line',
        'amount_untaxed',
        'currency_id',
    )
    def _compute_global_discount_totals(self):
        for move in self:
            currency = move.currency_id or move.company_currency_id
            product_lines = move.invoice_line_ids.filtered(lambda l: l.display_type in ('product', False, ''))
            normal_lines = product_lines.filtered(lambda l: not l._is_global_discount_line())
            gross_ht = 0.0
            for line in normal_lines:
                if line.discount:
                    line_gross = line.price_unit * line.quantity
                    gross_ht += currency.round(line_gross) if currency else line_gross
                else:
                    gross_ht += line.price_subtotal
            gross_ht = currency.round(gross_ht) if currency else gross_ht
            net_ht = move.amount_untaxed
            discount_amt = max(0.0, (currency.round(gross_ht - net_ht) if currency else (gross_ht - net_ht)))
            move.gross_untaxed_amount = gross_ht
            move.global_discount_amount = discount_amt
            move.net_untaxed_amount = net_ht

    def _get_move_lines_to_report(self):
        lines = super()._get_move_lines_to_report()
        return lines.filtered(lambda l: not l._is_global_discount_line())

    @api.depends(
        'gross_untaxed_amount',
        'global_discount_amount',
        'net_untaxed_amount',
        'invoice_line_ids.is_global_discount_line',
        'invoice_line_ids.discount',
    )
    def _compute_tax_totals(self):
        super()._compute_tax_totals()
        for move in self:
            if not move.is_invoice(include_receipts=True) or not move.tax_totals or not isinstance(move.tax_totals, dict):
                continue
            currency = move.currency_id or move.company_currency_id
            has_discount = bool(
                currency.compare_amounts(move.global_discount_amount, 0.0) > 0
                if currency else move.global_discount_amount > 0
            )
            move.tax_totals['has_global_discount'] = has_discount
            move.tax_totals['gross_untaxed_amount'] = move.gross_untaxed_amount
            move.tax_totals['global_discount_amount'] = move.global_discount_amount
            move.tax_totals['net_untaxed_amount'] = move.net_untaxed_amount

    def action_open_discount_wizard(self):
        self.ensure_one()
        return {
            'name': _("Remise"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.discount',
            'view_mode': 'form',
            'target': 'new',
        }


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

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
                    line.display_type in ('product', False, '')
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
                self.display_type in ('product', False, '')
                and discount_product
                and self.product_id == discount_product
                and self.price_unit < 0
            )
        )
