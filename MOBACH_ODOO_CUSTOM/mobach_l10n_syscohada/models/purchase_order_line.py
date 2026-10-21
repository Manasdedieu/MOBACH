# -*- coding: utf-8 -*-
from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _compute_tax_id(self):
        # Même TVA sur immobilisations que sur la facture : les taxes de la commande y sont recopiées.
        super()._compute_tax_id()
        for line in self.filtered(lambda l: l.product_id.accounting_nature == 'immobilisation'):
            line.tax_ids = line.tax_ids._mobach_immobilisation_taxes(line.company_id)
