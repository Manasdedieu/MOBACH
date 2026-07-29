# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MobachGlobalTaxWizard(models.TransientModel):
    _name = 'mobach.global.tax.wizard'
    _description = 'Assistant de Gestion des Taxes Globales'

    action_type = fields.Selection([
        ('add', 'Ajouter les taxes'),
        ('remove', 'Supprimer les taxes'),
        ('replace', 'Remplacer toutes les taxes')
    ], string='Action', required=True, default='add')

    tax_ids = fields.Many2many(
        'account.tax', 
        string='Taxes à appliquer / supprimer', 
        required=True
    )
    
    document_type = fields.Selection([
        ('sale', 'Vente'),
        ('purchase', 'Achat')
    ], string='Type de document', compute='_compute_document_type')
    
    @api.model
    def default_get(self, fields_list):
        res = super(MobachGlobalTaxWizard, self).default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        
        if active_model == 'sale.order' and active_id:
            order = self.env['sale.order'].browse(active_id)
            if any(inv.state == 'posted' for inv in order.invoice_ids):
                raise UserError(_("Cette commande possède déjà une facture validée. Vous ne pouvez plus modifier ses taxes globales. (Veuillez annuler la facture au besoin)."))
                
        elif active_model == 'purchase.order' and active_id:
            order = self.env['purchase.order'].browse(active_id)
            if any(inv.state == 'posted' for inv in order.invoice_ids):
                raise UserError(_("Cette commande possède déjà une facture validée. Vous ne pouvez plus modifier ses taxes globales. (Veuillez annuler la facture au besoin)."))
                
        return res

    @api.depends()
    def _compute_document_type(self):
        for wizard in self:
            active_model = self.env.context.get('active_model')
            active_id = self.env.context.get('active_id')
            
            if active_model == 'sale.order':
                wizard.document_type = 'sale'
            elif active_model == 'purchase.order':
                wizard.document_type = 'purchase'
            elif active_model == 'account.move':
                move = self.env['account.move'].browse(active_id)
                if move.move_type in ['out_invoice', 'out_refund', 'out_receipt']:
                    wizard.document_type = 'sale'
                else:
                    wizard.document_type = 'purchase'
            else:
                wizard.document_type = 'sale'

    @api.onchange('document_type')
    def _onchange_document_type(self):
        domain = [('type_tax_use', '=', self.document_type)]
        return {'domain': {'tax_ids': domain}}

    def action_apply_taxes(self):
        self.ensure_one()
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if not active_model or not active_id:
            raise UserError(_("Contexte manquant pour appliquer les taxes."))

        if active_model == 'sale.order':
            lines = self.env['sale.order'].browse(active_id).order_line.filtered(lambda l: l.display_type in (False, '', 'product'))
            tax_field = 'tax_ids'
        elif active_model == 'purchase.order':
            lines = self.env['purchase.order'].browse(active_id).order_line.filtered(lambda l: l.display_type in (False, '', 'product'))
            tax_field = 'tax_ids'
            
        elif active_model == 'account.move':
            move = self.env['account.move'].browse(active_id)
            if move.state != 'draft':
                raise UserError(_("Vous ne pouvez modifier les taxes que sur une facture à l'état brouillon."))
            lines = move.invoice_line_ids.filtered(lambda l: l.display_type in (False, '', 'product'))
            tax_field = 'tax_ids'
        else:
            raise UserError(_("Modèle non supporté."))

        records_to_process = [(lines, tax_field)]

        if active_model == 'sale.order':
            order = self.env['sale.order'].browse(active_id)
            draft_invoices = order.invoice_ids.filtered(lambda i: i.state == 'draft')
            if draft_invoices:
                inv_lines = draft_invoices.mapped('invoice_line_ids').filtered(lambda l: l.display_type in (False, '', 'product') and l.sale_line_ids)
                if inv_lines:
                    records_to_process.append((inv_lines, 'tax_ids'))
        
        elif active_model == 'purchase.order':
            order = self.env['purchase.order'].browse(active_id)
            draft_invoices = order.invoice_ids.filtered(lambda i: i.state == 'draft')
            if draft_invoices:
                inv_lines = draft_invoices.mapped('invoice_line_ids').filtered(lambda l: l.display_type in (False, '', 'product') and l.purchase_line_id)
                if inv_lines:
                    records_to_process.append((inv_lines, 'tax_ids'))

        for record_lines, field_name in records_to_process:
            for line in record_lines:
                if self.action_type == 'add':
                    current_taxes = getattr(line, field_name)
                    new_taxes = current_taxes | self.tax_ids
                    line.write({field_name: [(6, 0, new_taxes.ids)]})
                
                elif self.action_type == 'remove':
                    current_taxes = getattr(line, field_name)
                    new_taxes = current_taxes - self.tax_ids
                    line.write({field_name: [(6, 0, new_taxes.ids)]})
                
                elif self.action_type == 'replace':
                    line.write({field_name: [(6, 0, self.tax_ids.ids)]})
                
        return {'type': 'ir.actions.act_window_close'}
