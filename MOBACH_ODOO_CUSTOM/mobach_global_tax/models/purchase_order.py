# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    global_tax_id = fields.Many2one(
        'account.tax',
        string="Taxe Globale",
        domain="[('type_tax_use', '=', 'purchase'), ('company_id', 'in', (company_id, False))]",
        check_company=True,
        tracking=True,
        copy=True,
        help="Taxe appliquée globalement sur toutes les lignes de la commande d'achat.",
    )
    applied_global_tax_id = fields.Many2one(
        'account.tax',
        string="Dernière Taxe Globale Appliquée",
        copy=False,
    )

    @api.onchange('global_tax_id')
    def _onchange_global_tax_id(self):
        old_tax = self.applied_global_tax_id
        new_tax = self.global_tax_id
        if old_tax == new_tax:
            return
        for line in self.order_line.filtered(lambda l: l.display_type in (False, '', 'product')):
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
            for order in self:
                if order.state in ('purchase', 'done', 'cancel'):
                    raise UserError(_("Vous ne pouvez pas modifier la taxe globale sur une commande d'achat confirmée ou annulée."))
                old_tax = order.applied_global_tax_id
                if old_tax != new_tax:
                    for line in order.order_line.filtered(lambda l: l.display_type in (False, '', 'product')):
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
        orders = super().create(vals_list)
        for order in orders:
            if order.global_tax_id:
                for line in order.order_line.filtered(lambda l: l.display_type in (False, '', 'product')):
                    if order.global_tax_id not in line.tax_ids:
                        line.tax_ids |= order.global_tax_id
        return orders

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.global_tax_id:
            invoice_vals['global_tax_id'] = self.global_tax_id.id
            invoice_vals['applied_global_tax_id'] = self.global_tax_id.id
        return invoice_vals


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _compute_tax_id(self):
        super()._compute_tax_id()
        for line in self:
            if line.order_id.global_tax_id and line.display_type in (False, '', 'product'):
                if line.order_id.global_tax_id not in line.tax_ids:
                    line.tax_ids |= line.order_id.global_tax_id
