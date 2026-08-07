# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Ce champ caché permet de mémoriser la dernière devise affichée à l'écran par l'utilisateur.
    # Ceci corrige un problème d'Odoo natif où le changement de devise multiple sans sauvegarder 
    # ne permettait pas de revenir au taux initial correctement.
    ui_last_currency_id = fields.Many2one('res.currency', string="Last UI Currency", copy=False)

    @api.onchange('currency_id')
    def _onchange_currency_id_convert_prices(self):
        # On utilise le champ mémoire de l'UI en priorité. Sinon on prend la devise enregistrée en BD.
        old_currency = self.ui_last_currency_id or self._origin.currency_id
        new_currency = self.currency_id
        
        # Si la devise a changé, on applique la conversion sur les prix unitaires.
        if old_currency and new_currency and old_currency != new_currency:
            date = self.date_order or fields.Date.context_today(self)
            
            for line in self.order_line.filtered(lambda l: l.display_type in ('product', False, '')):
                if line.price_unit:
                    new_price = old_currency._convert(
                        line.price_unit, 
                        new_currency, 
                        self.company_id, 
                        date
                    )
                    line.price_unit = new_price
            
            # On met à jour la mémoire de l'UI pour un éventuel changement consécutif sans sauvegarde.
            self.ui_last_currency_id = new_currency

    def _prepare_invoice(self):
        """
        Surcharge de la création de facture pour forcer la propagation de la devise 
        de la commande d'achat vers la facture fournisseur.
        """
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        # On force la devise de la facture à être celle de la commande
        invoice_vals['currency_id'] = self.currency_id.id
        return invoice_vals

