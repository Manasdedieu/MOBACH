# -*- coding: utf-8 -*-
from odoo import fields, models

IMMOBILISATION_ACCOUNT_DOMAIN = [('account_type', 'in', ('asset_fixed', 'asset_non_current'))]


class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_account_immobilisation_categ_id = fields.Many2one(
        'account.account',
        company_dependent=True,
        string="Compte d'immobilisation",
        domain=IMMOBILISATION_ACCOUNT_DOMAIN,
        help="Compte de classe 2 utilisé sur les factures fournisseur des produits "
             "de nature « Immobilisation » de cette catégorie.",
    )


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_account_immobilisation_id = fields.Many2one(
        'account.account',
        company_dependent=True,
        string="Compte d'immobilisation",
        domain=IMMOBILISATION_ACCOUNT_DOMAIN,
        help="Compte de classe 2 utilisé sur les factures fournisseur quand la nature comptable "
             "est « Immobilisation ». À défaut, celui de la catégorie de produit.",
    )

    def _get_immobilisation_account(self):
        self.ensure_one()
        if self.accounting_nature != 'immobilisation':
            return self.env['account.account']
        return (
            self.property_account_immobilisation_id
            or self._get_category_account('property_account_immobilisation_categ_id')
        )
