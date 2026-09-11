# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.tools import SQL

from ..models.project_project import REVENUE_ACCOUNT_TYPES, EXPENSE_ACCOUNT_TYPES


class MobachProjectMarginReport(models.Model):
    """Rentabilité par projet, en lecture seule, pour le tableau croisé dynamique.

    Calcule les indicateurs au niveau ligne de pièce comptable avec répartition cascade :
    - CA Facturé (TTC) : Montant total TTC facturé
    - CA Encaissé (TTC) : Montant TTC effectivement perçu (reconnaissance au paiement)
    - Encours Client : Montant TTC en attente de paiement (reste à percevoir)
    - Dépenses Facturées (TTC) : Montant total TTC facturé par les fournisseurs
    - Dépenses Décaissées (TTC) : Règlements fournisseurs effectués
    - Encours Fournisseur : Montant TTC en attente de paiement (reste à payer)
    - Marge Réalisée (Trésorerie) : CA Encaissé TTC - Dépenses Décaissées TTC (0 pour Générique)
    """
    _name = 'mobach.project.margin.report'
    _description = 'Rentabilité par projet'
    _auto = False
    _order = 'date desc, project_id'
    _rec_name = 'project_id'

    # ------------------------------------------------------------------
    # AXES D'ANALYSE
    # ------------------------------------------------------------------
    date = fields.Date(string='Date', readonly=True)
    project_id = fields.Many2one('project.project', string='Projet', readonly=True)
    project_partner_id = fields.Many2one('res.partner', string='Client du Projet', readonly=True)
    project_user_id = fields.Many2one('res.users', string='Chef de Projet', readonly=True)
    stage_id = fields.Many2one(
        'project.project.stage', string='Étape du Projet', readonly=True,
        groups='project.group_project_stages',
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Compte Analytique', readonly=True,
    )
    general_account_id = fields.Many2one(
        'account.account', string='Compte Général', readonly=True,
    )
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partenaire', readonly=True)
    product_id = fields.Many2one('product.product', string='Article', readonly=True)
    move_line_id = fields.Many2one('account.move.line', string='Écriture', readonly=True)
    move_id = fields.Many2one('account.move', string='Pièce Comptable', readonly=True)
    nature = fields.Selection(
        [('revenue', "Chiffre d'affaires"), ('expense', 'Dépense'), ('other', 'Hors exploitation')],
        string='Nature', readonly=True,
    )
    company_id = fields.Many2one('res.company', string='Société', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Devise', readonly=True)

    # ------------------------------------------------------------------
    # MESURES
    # ------------------------------------------------------------------
    invoiced_revenue = fields.Monetary(
        string='CA Facturé (TTC)', currency_field='currency_id', readonly=True,
    )
    revenue = fields.Monetary(
        string="CA Encaissé (TTC)", currency_field='currency_id', readonly=True,
    )
    customer_encours = fields.Monetary(
        string='Encours Client', currency_field='currency_id', readonly=True,
    )
    invoiced_expense = fields.Monetary(
        string='Dépenses Facturées (TTC)', currency_field='currency_id', readonly=True,
    )
    expense = fields.Monetary(
        string='Dépenses Décaissées', currency_field='currency_id', readonly=True,
    )
    vendor_encours = fields.Monetary(
        string='Encours Fournisseur', currency_field='currency_id', readonly=True,
    )
    margin = fields.Monetary(
        string='Marge Réalisée', currency_field='currency_id', readonly=True,
    )
    unit_amount = fields.Float(string='Quantité', readonly=True)

    # ------------------------------------------------------------------
    # VUE SQL
    # ------------------------------------------------------------------
    @property
    def _table_query(self):
        generic_project = self.env['project.project']._mobach_get_generic_project()
        generic_id = generic_project.id if generic_project else 0

        return SQL(
            """
            WITH ranked_lines AS (
                SELECT
                    aml.id                          AS id,
                    aml.move_id                     AS move_id,
                    am.date                         AS date,
                    am.move_type                    AS move_type,
                    am.state                        AS state,
                    am.partner_id                   AS partner_id,
                    am.journal_id                   AS journal_id,
                    am.company_id                   AS company_id,
                    am.currency_id                  AS currency_id,
                    aml.account_id                  AS general_account_id,
                    aml.product_id                  AS product_id,
                    aml.quantity                    AS unit_amount,
                    aml.price_total                 AS price_total,
                    aml.balance                     AS balance,
                    COALESCE(aml.analytic_project_id, %(generic_id)s) AS project_id,
                    am.amount_total                 AS amount_total,
                    GREATEST(0.0, LEAST(am.amount_total, am.amount_total - am.amount_residual)) AS paid_total,
                    COALESCE(SUM(aml.price_total) OVER (
                        PARTITION BY aml.move_id
                        ORDER BY (CASE WHEN aml.analytic_project_id IS NULL OR aml.analytic_project_id = %(generic_id)s THEN 1 ELSE 0 END), aml.sequence, aml.id
                        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                    ), 0.0)                         AS prev_cumul
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                WHERE am.state = 'posted'
                  AND (
                      (am.move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')
                       AND aml.display_type = 'product')
                      OR
                      (am.move_type = 'entry'
                       AND aml.analytic_project_id IS NOT NULL
                       AND (aml.display_type = 'product' OR aml.display_type IS NULL))
                  )
            )
            SELECT
                rl.id                           AS id,
                rl.date                         AS date,
                rl.project_id                   AS project_id,
                pp.partner_id                   AS project_partner_id,
                pp.user_id                      AS project_user_id,
                pp.stage_id                     AS stage_id,
                pp.account_id                   AS analytic_account_id,
                rl.general_account_id           AS general_account_id,
                rl.journal_id                   AS journal_id,
                rl.partner_id                   AS partner_id,
                rl.product_id                   AS product_id,
                rl.id                           AS move_line_id,
                rl.move_id                      AS move_id,
                rl.company_id                   AS company_id,
                rl.currency_id                  AS currency_id,
                rl.unit_amount                  AS unit_amount,
                CASE
                    WHEN rl.move_type IN ('out_invoice', 'out_refund') THEN 'revenue'
                    WHEN rl.move_type IN ('in_invoice', 'in_refund') THEN 'expense'
                    WHEN aa.account_type IN %(revenue_types)s THEN 'revenue'
                    WHEN aa.account_type IN %(expense_types)s THEN 'expense'
                    ELSE 'other'
                END                             AS nature,
                -- CA Facturé (TTC)
                CASE
                    WHEN rl.move_type IN ('out_invoice', 'out_refund') THEN
                        (CASE WHEN rl.move_type = 'out_refund' THEN -1.0 ELSE 1.0 END) * rl.price_total
                    WHEN rl.move_type = 'entry' AND aa.account_type IN %(revenue_types)s THEN
                        -rl.balance
                    ELSE 0.0
                END                             AS invoiced_revenue,
                -- CA Encaissé (TTC)
                CASE
                    WHEN rl.move_type IN ('out_invoice', 'out_refund') THEN
                        (CASE WHEN rl.move_type = 'out_refund' THEN -1.0 ELSE 1.0 END) * LEAST(rl.price_total, GREATEST(0.0, rl.paid_total - rl.prev_cumul))
                    WHEN rl.move_type = 'entry' AND aa.account_type IN %(revenue_types)s THEN
                        -rl.balance
                    ELSE 0.0
                END                             AS revenue,
                -- Encours Client (Reste à percevoir)
                CASE
                    WHEN rl.move_type IN ('out_invoice', 'out_refund') THEN
                        (CASE WHEN rl.move_type = 'out_refund' THEN -1.0 ELSE 1.0 END) * (rl.price_total - LEAST(rl.price_total, GREATEST(0.0, rl.paid_total - rl.prev_cumul)))
                    ELSE 0.0
                END                             AS customer_encours,
                -- Dépenses Facturées (TTC)
                CASE
                    WHEN rl.move_type IN ('in_invoice', 'in_refund') THEN
                        (CASE WHEN rl.move_type = 'in_refund' THEN -1.0 ELSE 1.0 END) * rl.price_total
                    WHEN rl.move_type = 'entry' AND aa.account_type IN %(expense_types)s THEN
                        rl.balance
                    ELSE 0.0
                END                             AS invoiced_expense,
                -- Dépenses Décaissées (TTC)
                CASE
                    WHEN rl.move_type IN ('in_invoice', 'in_refund') THEN
                        (CASE WHEN rl.move_type = 'in_refund' THEN -1.0 ELSE 1.0 END) * LEAST(rl.price_total, GREATEST(0.0, rl.paid_total - rl.prev_cumul))
                    WHEN rl.move_type = 'entry' AND aa.account_type IN %(expense_types)s THEN
                        rl.balance
                    ELSE 0.0
                END                             AS expense,
                -- Encours Fournisseur (Reste à payer)
                CASE
                    WHEN rl.move_type IN ('in_invoice', 'in_refund') THEN
                        (CASE WHEN rl.move_type = 'in_refund' THEN -1.0 ELSE 1.0 END) * (rl.price_total - LEAST(rl.price_total, GREATEST(0.0, rl.paid_total - rl.prev_cumul)))
                    ELSE 0.0
                END                             AS vendor_encours,
                -- Marge (0 pour le projet Générique)
                CASE
                    WHEN rl.project_id = %(generic_id)s THEN 0.0
                    ELSE (
                        (CASE
                            WHEN rl.move_type IN ('out_invoice', 'out_refund') THEN
                                (CASE WHEN rl.move_type = 'out_refund' THEN -1.0 ELSE 1.0 END) * LEAST(rl.price_total, GREATEST(0.0, rl.paid_total - rl.prev_cumul))
                            WHEN rl.move_type = 'entry' AND aa.account_type IN %(revenue_types)s THEN
                                -rl.balance
                            ELSE 0.0
                        END)
                        -
                        (CASE
                            WHEN rl.move_type IN ('in_invoice', 'in_refund') THEN
                                (CASE WHEN rl.move_type = 'in_refund' THEN -1.0 ELSE 1.0 END) * LEAST(rl.price_total, GREATEST(0.0, rl.paid_total - rl.prev_cumul))
                            WHEN rl.move_type = 'entry' AND aa.account_type IN %(expense_types)s THEN
                                rl.balance
                            ELSE 0.0
                        END)
                    )
                END                             AS margin
            FROM ranked_lines rl
            JOIN project_project pp ON pp.id = rl.project_id
            LEFT JOIN account_account aa ON aa.id = rl.general_account_id
            """,
            generic_id=generic_id,
            revenue_types=tuple(REVENUE_ACCOUNT_TYPES),
            expense_types=tuple(EXPENSE_ACCOUNT_TYPES),
        )
