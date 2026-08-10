# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    is_retenue = fields.Boolean(
        string="Génère une retenue sur solde",
        default=False,
        help="Cochez cette case si cette condition de paiement doit déclencher l'affichage et le blocage d'une retenue sur solde sur les factures et commandes de vente."
    )
