# -*- coding: utf-8 -*-
from odoo import models
from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    # Les fonctions d'un même template sont appliquées par ordre alphabétique de nom :
    # le suffixe « _mobach » les fait passer après celles de l10n_syscohada.

    @template('syscohada')
    def _get_syscohada_template_data_mobach(self):
        return {'code_digits': self._mobach_code_digits()}

    @template('syscohada', 'account.account')
    def _get_syscohada_account_account_mobach(self):
        # Plan du client : comptes manquants + libellés français corrigés des comptes existants.
        return self._parse_csv('syscohada', 'account.account', module='mobach_l10n_syscohada')

    @template('syscohada', 'account.journal')
    def _get_syscohada_account_journal_mobach(self):
        # Sinon Odoo crée un compte « Bank » au prochain code libre (5212).
        return {'bank': {'default_account_id': 'pcg_5211'}}

    @template('cm', 'account.tax')
    def _get_cm_account_tax_mobach(self):
        tax_data = self._parse_csv('cm', 'account.tax', module='mobach_l10n_syscohada')
        self._deref_account_tags('cm', tax_data)
        return tax_data

    def _post_load_data(self, template_code, company, template_data):
        super()._post_load_data(template_code, company, template_data)
        if 'syscohada' in self._get_parent_template(template_code):
            self._mobach_unlink_unused_bank_accounts(company)

    def _mobach_unlink_unused_bank_accounts(self, company):
        """Le journal Banque est créé avec son propre compte « Bank » (521001) avant de
        recevoir 5211 : ce compte n'est plus utilisé, on le supprime."""
        xmlids = self.env['ir.model.data'].search([
            ('model', '=', 'account.account'),
            ('module', '=', 'account'),
            ('name', '=like', f'{company.id}_bank_journal_default_account_%'),
        ])
        accounts = self.env['account.account'].browse(xmlids.mapped('res_id')).exists()
        used = self.env['account.journal'].search([('default_account_id', 'in', accounts.ids)]).default_account_id
        used |= self.env['account.move.line'].search([('account_id', 'in', accounts.ids)]).account_id
        (accounts - used).unlink()

    def _mobach_code_digits(self):
        """Codes à 4 chiffres comme le plan du client (4111, 6011…).
        Sur une société déjà équipée d'un plan, on garde sa longueur de code pour ne pas
        mélanger les numérotations."""
        account = self.env['account.account'].search([
            *self.env['account.account']._check_company_domain(self.env.company),
            ('account_type', '=', 'asset_receivable'),
        ], limit=1)
        return str(len(account.code)) if account.code else '4'
