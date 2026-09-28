# -*- coding: utf-8 -*-
from odoo import fields, models

ACCOUNTING_NATURE_SELECTION = [
    ('charge', 'Charge'),
    ('immobilisation', 'Immobilisation'),
]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Indicatif uniquement : aucun impact sur les prix ni sur les comptes pour le moment.
    accounting_nature = fields.Selection(
        selection=ACCOUNTING_NATURE_SELECTION,
        string="Nature comptable",
        help="Charge : consommé dans l'exercice (classe 6).\n"
             "Immobilisation : bien durable amorti sur plusieurs exercices (classe 2).\n"
             "Affiché en surbrillance sur les lignes de devis et de facture.",
    )

    def action_clear_accounting_nature(self):
        self.accounting_nature = False
