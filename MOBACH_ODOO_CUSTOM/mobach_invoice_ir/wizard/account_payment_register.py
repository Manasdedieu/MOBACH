# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    is_retenue_early_payment = fields.Boolean(
        compute='_compute_is_retenue_early_payment',
        string="Paiement anticipé de retenue"
    )
    
    is_account_manager = fields.Boolean(
        compute='_compute_is_account_manager'
    )

    @api.depends('amount', 'line_ids')
    def _compute_is_retenue_early_payment(self):
        today = fields.Date.context_today(self)
        for wizard in self:
            delayed_lines = wizard.line_ids.filtered(
                lambda l: l.display_type == 'payment_term' 
                and l.date_maturity 
                and l.date_maturity > today 
                and l.move_id.invoice_payment_term_id.is_retenue
            )
            if not delayed_lines:
                wizard.is_retenue_early_payment = False
                continue

            immediate_lines = wizard.line_ids.filtered(
                lambda l: l.display_type == 'payment_term' and (not l.date_maturity or l.date_maturity <= today)
            )
            immediate_amount = abs(sum(immediate_lines.mapped('amount_residual_currency')))

            if wizard.amount > immediate_amount + 0.01: # Tolerance
                wizard.is_retenue_early_payment = True
            else:
                wizard.is_retenue_early_payment = False

    @api.depends_context('uid')
    def _compute_is_account_manager(self):
        for wizard in self:
            wizard.is_account_manager = self.env.user.has_group('account.group_account_manager')

    def action_create_payments(self):
        self.ensure_one()
        if self.is_retenue_early_payment and not self.is_account_manager:
            today = fields.Date.context_today(self)
            delayed_lines = self.line_ids.filtered(
                lambda l: l.display_type == 'payment_term' 
                and l.date_maturity 
                and l.date_maturity > today
                and l.move_id.invoice_payment_term_id.is_retenue
            )
            immediate_lines = self.line_ids.filtered(
                lambda l: l.display_type == 'payment_term' and (not l.date_maturity or l.date_maturity <= today)
            )
            immediate_amount = abs(sum(immediate_lines.mapped('amount_residual_currency')))
            delayed_amount = abs(sum(delayed_lines.mapped('amount_residual_currency')))
            earliest_date = min(delayed_lines.mapped('date_maturity')) if delayed_lines else today
            formatted_amount = self.currency_id.format(immediate_amount) if self.currency_id else str(immediate_amount)
            formatted_delayed_amount = self.currency_id.format(delayed_amount) if self.currency_id else str(delayed_amount)
            
            raise UserError(_(
                "Paiement bloqué : Vous tentez de payer un montant incluant la retenue de garantie.\n\n"
                "Règle de l'entreprise : Le paiement total n'est autorisé qu'après la date limite.\n"
                "Le reste (retenue de garantie de %(retenue_amount)s) est bloqué jusqu'au %(date)s.\n\n"
                "Seul un administrateur comptabilité peut forcer ce paiement.",
                amount=formatted_amount,
                retenue_amount=formatted_delayed_amount,
                date=earliest_date.strftime('%d/%m/%Y')
            ))
        return super().action_create_payments()
