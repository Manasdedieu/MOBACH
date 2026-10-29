# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError


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

    currency_id = fields.Many2one(
        'res.currency',
        readonly=False,
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

    retenue_amount = fields.Monetary(
        string='Retenue de Solde',
        currency_field='currency_id',
        compute='_compute_retenue_amount',
        store=True,
    )

    # Ce champ caché permet de mémoriser la dernière devise affichée à l'écran par l'utilisateur.
    ui_last_currency_id = fields.Many2one('res.currency', string="Last UI Currency", copy=False)

    @api.onchange('currency_id')
    def _onchange_currency_id_convert_prices(self):
        # On utilise le champ mémoire de l'UI en priorité. Sinon on prend la devise enregistrée en BD.
        old_currency = self.ui_last_currency_id or self._origin.currency_id
        new_currency = self.currency_id
        
        # Si la devise a changé, on applique la conversion sur les prix unitaires.
        if old_currency and new_currency and old_currency != new_currency:
            date = self.date_order or fields.Date.context_today(self)
            
            for line in self.order_line.filtered(lambda l: l.display_type in ('product', False, '')):
                if line.price_unit:
                    new_price = old_currency._convert(
                        line.price_unit, 
                        new_currency, 
                        self.company_id, 
                        date
                    )
                    line.price_unit = new_price
            
            # On met à jour la mémoire de l'UI pour un éventuel changement consécutif sans sauvegarde.
            self.ui_last_currency_id = new_currency

    @api.depends('amount_untaxed', 'ir_tax_id', 'ir_tax_id.amount')
    def _compute_ir_amounts(self):
        for order in self:
            if order.ir_tax_id and order.ir_tax_id.amount_type == 'percent':
                ir_amt = order.amount_untaxed * order.ir_tax_id.amount / 100.0
            else:
                ir_amt = 0.0
            order.ir_amount = ir_amt
            order.amount_net_mandate = order.amount_untaxed - ir_amt

    @api.depends('payment_term_id', 'payment_term_id.is_retenue', 'amount_total', 'amount_untaxed', 'amount_tax', 'date_order')
    def _compute_retenue_amount(self):
        for order in self:
            if order.payment_term_id and order.payment_term_id.is_retenue and order.amount_total:
                ref_date = (order.date_order and order.date_order.date()) or fields.Date.context_today(order)
                currency = order.currency_id or order.company_id.currency_id
                company = order.company_id or self.env.company
                try:
                    terms = order.payment_term_id._compute_terms(
                        date_ref=ref_date,
                        currency=currency,
                        company=company,
                        tax_amount=order.amount_tax,
                        tax_amount_currency=order.amount_tax,
                        untaxed_amount=order.amount_untaxed,
                        untaxed_amount_currency=order.amount_untaxed,
                        sign=1,
                    )
                    delayed_amount = sum(
                        term['foreign_amount']
                        for term in terms.get('line_ids', [])
                        if term.get('date') and fields.Date.to_date(term.get('date')) > ref_date
                    )
                    order.retenue_amount = abs(delayed_amount)
                except Exception:
                    order.retenue_amount = 0.0
            else:
                order.retenue_amount = 0.0

    def write(self, vals):
        if 'ir_tax_id' in vals:
            for order in self:
                if order.state in ('sale', 'cancel'):
                    raise UserError(_("Vous ne pouvez pas modifier la taxe IR sur une commande confirmée ou annulée."))
        return super().write(vals)

    def _prepare_invoice(self):
        result = super()._prepare_invoice()
        if self.object:
            result.update({'object': self.object})
        if self.ir_tax_id:
            result.update({'ir_tax_id': self.ir_tax_id.id})
        return result

    @api.depends('ir_tax_id', 'ir_amount', 'amount_net_mandate', 'retenue_amount')
    def _compute_tax_totals(self):
        super()._compute_tax_totals()
        for order in self:
            if not order.tax_totals or not isinstance(order.tax_totals, dict):
                continue
            order.tax_totals['ir_tax_name'] = (
                order.ir_tax_id.name if order.ir_tax_id else False
            )
            order.tax_totals['ir_amount'] = order.ir_amount
            order.tax_totals['amount_net_mandate'] = order.amount_net_mandate
            order.tax_totals['retenue_amount'] = order.retenue_amount
            order.tax_totals['has_ir'] = bool(order.ir_tax_id)
