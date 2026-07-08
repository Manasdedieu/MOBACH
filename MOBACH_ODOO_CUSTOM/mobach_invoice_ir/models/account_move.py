# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    """
    Extension d'account.move pour la gestion de l'IR (Impôt sur le Revenu).

    Approche retenue :
      On surcharge _compute_tax_totals() pour injecter directement dans le
      dictionnaire tax_totals les clés custom :
        - 'ir_amount'          : montant de la retenue IR
        - 'ir_tax_name'        : libellé de la taxe IR (ex: "IR 2,2%")
        - 'amount_net_mandate' : HT - IR

      Ces clés sont ensuite lues par le patch JS du widget TaxTotalsField.

    Calcul métier :
      IR            = Total HT × taux IR
      Net à Mandater = Total HT − IR
      Total TTC      = Total HT + TVA  (inchangé)
    """
    _inherit = 'account.move'

    # ------------------------------------------------------------------
    # Champs IR
    # ------------------------------------------------------------------

    ir_tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='Taxe IR',
        domain=[('is_withholding_ir', '=', True)],
        ondelete='restrict',
        tracking=True,
        help="Taxe IR applicable globalement sur le montant HT de cette facture.\n"
             "Ex : IR 2,2% ou IR 5,5%",
    )

    ir_amount = fields.Monetary(
        string='Montant IR',
        currency_field='currency_id',
        compute='_compute_ir_amounts',
        store=True,
    )

    amount_net_mandate = fields.Monetary(
        string='Net à Mandater',
        currency_field='currency_id',
        compute='_compute_ir_amounts',
        store=True,
        help="Net à Mandater = Total HT − IR",
    )

    # ------------------------------------------------------------------
    # Calcul IR / Net à Mandater
    # ------------------------------------------------------------------

    @api.depends('amount_untaxed', 'ir_tax_id', 'ir_tax_id.amount')
    def _compute_ir_amounts(self):
        for move in self:
            if move.ir_tax_id and move.ir_tax_id.amount_type == 'percent':
                ir_amt = move.amount_untaxed * move.ir_tax_id.amount / 100.0
            else:
                ir_amt = 0.0
            move.ir_amount = ir_amt
            move.amount_net_mandate = move.amount_untaxed - ir_amt

    # ------------------------------------------------------------------
    # Injection dans tax_totals pour le widget JS
    # ------------------------------------------------------------------

    @api.depends('ir_tax_id', 'ir_amount', 'amount_net_mandate')
    def _compute_tax_totals(self):
        """
        On appelle le super() pour obtenir le dict tax_totals natif,
        puis on y injecte nos clés IR pour que le widget JS puisse
        les lire directement sans avoir à accéder au record.
        """
        super()._compute_tax_totals()
        for move in self:
            if move.tax_totals is None:
                continue
            # Injection des données IR dans le dict tax_totals
            move.tax_totals['ir_tax_name'] = (
                move.ir_tax_id.name if move.ir_tax_id else False
            )
            move.tax_totals['ir_amount'] = move.ir_amount
            move.tax_totals['amount_net_mandate'] = move.amount_net_mandate
            move.tax_totals['has_ir'] = bool(move.ir_tax_id)
