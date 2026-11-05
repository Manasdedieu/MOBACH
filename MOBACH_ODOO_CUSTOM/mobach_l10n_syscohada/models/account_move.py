# -*- coding: utf-8 -*-
from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        lines = self.invoice_line_ids._mobach_immobilisation_lines().filtered(
            lambda line: not line.account_id.code.startswith('2')
        )
        if lines:
            raise UserError(_(
                "Ces lignes portent sur des immobilisations mais ne sont pas imputées "
                "sur un compte de classe 2 :\n%(lines)s\n\n"
                "Renseignez le compte d'immobilisation sur le produit ou sa catégorie "
                "(onglet Comptabilité), ou choisissez un compte de classe 2 sur la ligne.",
                lines="\n".join(f"- {line.move_id.name or ''} : {line.product_id.display_name} ({line.account_id.code})"
                                for line in lines),
            ))
        return super()._post(soft)
