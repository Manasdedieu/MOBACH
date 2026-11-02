# -*- coding: utf-8 -*-
from odoo import api, fields, models

# Champ MOBACH -> champ natif recopié (et inversement).
SYNCED_FIELDS = {
    'nui': 'vat',
    'rccm': 'company_registry',
}


class ResPartner(models.Model):
    _inherit = 'res.partner'

    nui = fields.Char(
        string="NUI",
        help="Numéro Unique d'Identification fiscale. Recopié dans le N° TVA (et inversement).",
    )
    rccm = fields.Char(
        string="RCCM",
        help="Registre du Commerce et du Crédit Mobilier. Recopié dans le Company ID (et inversement).",
    )

    @api.model
    def _synced_commercial_fields(self):
        return super()._synced_commercial_fields() + ['nui']

    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + ['rccm']

    @api.model
    def _mobach_sync_identifiers(self, vals):
        vals = dict(vals)
        for field, native in SYNCED_FIELDS.items():
            if field in vals and native not in vals:
                vals[native] = vals[field]
            elif native in vals and field not in vals:
                vals[field] = vals[native]
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._mobach_sync_identifiers(vals) for vals in vals_list])

    def write(self, vals):
        return super().write(self._mobach_sync_identifiers(vals))

    @api.onchange('nui')
    def _onchange_nui(self):
        self.vat = self.nui

    @api.onchange('vat')
    def _onchange_vat_mobach(self):
        self.nui = self.vat

    @api.onchange('rccm')
    def _onchange_rccm(self):
        self.company_registry = self.rccm

    @api.onchange('company_registry')
    def _onchange_company_registry_mobach(self):
        self.rccm = self.company_registry
