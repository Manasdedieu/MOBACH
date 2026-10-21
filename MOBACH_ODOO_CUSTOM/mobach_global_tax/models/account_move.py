# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    tax_type_use = fields.Selection(
        selection=[('sale', 'Vente'), ('purchase', 'Achat')],
        compute='_compute_tax_type_use',
        string="Type de taxe applicable",
    )

    global_tax_id = fields.Many2one(
        'account.tax',
        string="Taxe Globale",
        domain="[('type_tax_use', '=', tax_type_use), ('company_id', 'in', (company_id, False))]",
        check_company=True,
        tracking=True,
        copy=True,
        help="Taxe appliquée globalement sur toutes les lignes de la facture.",
    )
    applied_global_tax_id = fields.Many2one(
        'account.tax',
        string="Dernière Taxe Globale Appliquée",
        copy=False,
    )

    @api.depends('move_type')
    def _compute_tax_type_use(self):
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund', 'out_receipt'):
                move.tax_type_use = 'sale'
            else:
                move.tax_type_use = 'purchase'

    @api.onchange('global_tax_id')
    def _onchange_global_tax_id(self):
        old_tax = self.applied_global_tax_id
        new_tax = self.global_tax_id
        if old_tax == new_tax:
            return
        for line in self.invoice_line_ids.filtered(lambda l: l.display_type in (False, '', 'product')):
            taxes = line.tax_ids
            if old_tax and old_tax in taxes:
                taxes -= old_tax
            if new_tax and new_tax not in taxes:
                taxes |= new_tax
            line.tax_ids = taxes
        self.applied_global_tax_id = new_tax

    def write(self, vals):
        if 'global_tax_id' in vals:
            new_tax_id = vals.get('global_tax_id')
            new_tax = self.env['account.tax'].browse(new_tax_id) if new_tax_id else False
            for move in self:
                if move.state != 'draft':
                    raise UserError(_("Vous ne pouvez pas modifier la taxe globale sur une facture validée ou annulée."))
                old_tax = move.applied_global_tax_id
                if old_tax != new_tax:
                    for line in move.invoice_line_ids.filtered(lambda l: l.display_type in (False, '', 'product')):
                        taxes = line.tax_ids
                        if old_tax and old_tax in taxes:
                            taxes -= old_tax
                        if new_tax and new_tax not in taxes:
                            taxes |= new_tax
                        line.tax_ids = taxes
            vals['applied_global_tax_id'] = new_tax_id
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('global_tax_id') and not vals.get('applied_global_tax_id'):
                vals['applied_global_tax_id'] = vals.get('global_tax_id')
        moves = super().create(vals_list)
        for move in moves:
            if move.global_tax_id:
                for line in move.invoice_line_ids.filtered(lambda l: l.display_type in (False, '', 'product')):
                    if move.global_tax_id not in line.tax_ids:
                        line.tax_ids |= move.global_tax_id
        return moves


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _compute_tax_ids(self):
        super()._compute_tax_ids()
        for line in self:
            if line.move_id.global_tax_id and line.display_type in (False, '', 'product'):
                if line.move_id.global_tax_id not in line.tax_ids:
                    line.tax_ids |= line.move_id.global_tax_id
