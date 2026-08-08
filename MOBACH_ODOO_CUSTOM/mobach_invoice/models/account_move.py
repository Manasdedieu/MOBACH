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

    def action_open_discount_wizard(self):
        self.ensure_one()
        return {
            'name': _("Remise"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.discount',
            'view_mode': 'form',
            'target': 'new',
        }
