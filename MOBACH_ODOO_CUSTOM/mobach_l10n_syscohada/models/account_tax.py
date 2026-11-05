# -*- coding: utf-8 -*-
from odoo import models

# TVA déductible sur achats (4452) -> TVA déductible sur immobilisations (4451), templates l10n_cm.
IMMOBILISATION_TAX_MAP = {
    'tva_purchase_good_19_25': 'tva_purchase_immo_19_25',
    'tva_purchase_services_19_25': 'tva_purchase_immo_19_25',
}


class AccountTax(models.Model):
    _inherit = 'account.tax'

    def _mobach_immobilisation_taxes(self, company):
        ChartTemplate = self.env['account.chart.template'].with_company(company)
        mapping = {}
        for source, target in IMMOBILISATION_TAX_MAP.items():
            source_tax = ChartTemplate.ref(source, raise_if_not_found=False)
            target_tax = ChartTemplate.ref(target, raise_if_not_found=False)
            if source_tax and target_tax:
                mapping[source_tax.id] = target_tax.id
        # _origin : dans un formulaire en cours de saisie, les taxes de la ligne sont des NewId.
        return self.browse([mapping.get(tax._origin.id, tax._origin.id) for tax in self])
