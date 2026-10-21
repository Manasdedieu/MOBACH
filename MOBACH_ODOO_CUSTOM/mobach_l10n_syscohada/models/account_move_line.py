# -*- coding: utf-8 -*-
from odoo import models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _compute_account_id(self):
        # Achat d'une immobilisation : classe 2 au lieu de la charge (classe 6).
        # Les ventes ne sont pas concernées : vendre un bien reste un produit (classe 7).
        super()._compute_account_id()
        for line in self._mobach_immobilisation_lines():
            account = line.with_company(line.company_id).product_id.product_tmpl_id._get_immobilisation_account()
            if account:
                line.account_id = line.move_id.fiscal_position_id.map_account(account)

    def _get_computed_taxes(self):
        # TVA récupérable sur immobilisations (4451) au lieu de la TVA sur achats (4452).
        # (Pas de filtre sur display_type : il n'est pas encore calculé à la création de la ligne.)
        taxes = super()._get_computed_taxes()
        if (
            self.product_id.accounting_nature == 'immobilisation'
            and self.move_id.is_purchase_document(include_receipts=True)
        ):
            taxes = taxes._mobach_immobilisation_taxes(self.move_id.company_id)
        return taxes

    def _mobach_immobilisation_lines(self):
        return self.filtered(
            lambda line: line.display_type == 'product'
            and line.product_id.accounting_nature == 'immobilisation'
            and line.move_id.is_purchase_document(include_receipts=True)
        )
