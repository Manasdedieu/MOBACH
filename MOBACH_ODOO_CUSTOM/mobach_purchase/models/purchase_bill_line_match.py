# -*- coding: utf-8 -*-
from odoo import api, models

class PurchaseBillLineMatch(models.Model):
    _inherit = 'purchase.bill.line.match'

    @api.model
    def _action_create_bill_from_po_lines(self, partner, po_lines):
        """ Surcharge pour propager la devise de la commande d'achat à la facture. """
        create_vals = {
            'move_type': 'in_invoice',
            'partner_id': partner.id,
        }
        currency_id = po_lines.mapped('order_id.currency_id')[:1]
        if currency_id:
            create_vals['currency_id'] = currency_id.id
            
        bill = self.env['account.move'].create(create_vals)
        bill._add_purchase_order_lines(po_lines)
        return bill._get_records_action()
