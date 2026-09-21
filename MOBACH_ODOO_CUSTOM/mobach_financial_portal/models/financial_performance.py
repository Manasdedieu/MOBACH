# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from .res_company import KPI_FIELD_NAMES


class MobachFinancialPerformance(models.Model):
    """Tableau de bord de performance financière par société MOBACH (SYSCOHADA).

    Les KPI ne sont volontairement PAS stockés. Ils dérivent de account.move,
    account.move.line et account.partial.reconcile, avec lesquels ce modèle n'a
    aucun lien relationnel : aucun `@api.depends` ne peut les atteindre. Les
    stocker imposait un cron de rafraîchissement, donc des chiffres faux entre
    deux passages — inacceptable pour un tableau de bord de direction. Non
    stockés, ils sont recalculés à chaque affichage et toujours exacts.
    """
    _name = 'mobach.financial.performance'
    _description = 'Performance Financière par Société MOBACH'
    _order = 'company_id, period'

    _unique_company_period = models.Constraint(
        'UNIQUE(company_id, period)',
        "Un seul tableau de bord par couple société / période d'analyse.",
    )

    name = fields.Char(
        string='Société / Intitulé',
        compute='_compute_name',
        store=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Société MOBACH',
        required=True,
        ondelete='cascade',
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Devise'
    )
    portal_description = fields.Char(
        related='company_id.portal_description',
        string='Secteur d\'Activité'
    )
    company_logo = fields.Binary(
        related='company_id.logo_web',
        string='Logo Société'
    )
    company_phone = fields.Char(
        related='company_id.phone',
        string='Téléphone'
    )
    company_email = fields.Char(
        related='company_id.email',
        string='Email'
    )
    company_city = fields.Char(
        related='company_id.city',
        string='Ville'
    )
    period = fields.Selection([
        ('all', 'Historique Global'),
        ('month', 'Mois en Cours'),
        ('quarter', 'Trimestre en Cours'),
        ('year', 'Année en Cours'),
    ], string='Période d\'Analyse', default='all', required=True)

    # ------------------------------------------------------------------
    # FLUX DE LA PÉRIODE
    # ------------------------------------------------------------------
    ca_realise = fields.Monetary(
        string="Chiffre d'Affaires Encaissé",
        currency_field='currency_id', compute='_compute_kpi_metrics')
    ca_encaisse_cash = fields.Monetary(
        string="dont Encaissements Réels",
        currency_field='currency_id', compute='_compute_kpi_metrics')
    ca_compense_avoir = fields.Monetary(
        string="dont Compensé par Avoir (ventes)",
        currency_field='currency_id', compute='_compute_kpi_metrics')
    ca_annule_perte = fields.Monetary(
        string="CA Annulé / Passé en Perte",
        currency_field='currency_id', compute='_compute_kpi_metrics')

    depenses_totales = fields.Monetary(
        string="Dépenses Réglées",
        currency_field='currency_id', compute='_compute_kpi_metrics')
    depenses_cash = fields.Monetary(
        string="dont Décaissements Réels",
        currency_field='currency_id', compute='_compute_kpi_metrics')
    depenses_compense_avoir = fields.Monetary(
        string="dont Compensé par Avoir (achats)",
        currency_field='currency_id', compute='_compute_kpi_metrics')
    depenses_annulees = fields.Monetary(
        string="Dépenses Annulées / Abandonnées",
        currency_field='currency_id', compute='_compute_kpi_metrics')

    marge_nette = fields.Monetary(
        string="Marge Nette",
        currency_field='currency_id', compute='_compute_kpi_metrics')
    marge_cash = fields.Monetary(
        string="Marge de Trésorerie",
        currency_field='currency_id', compute='_compute_kpi_metrics')
    marge_taux = fields.Float(
        string="Taux de Marge (%)",
        digits=(16, 2), compute='_compute_kpi_metrics')
    marge_status = fields.Selection([
        ('positive', 'Bénéficiaire'),
        ('negative', 'Déficitaire'),
        ('neutral', 'Neutre'),
    ], string='Statut Marge', compute='_compute_kpi_metrics')

    # ------------------------------------------------------------------
    # ENCOURS (photo à la date du jour, hors période)
    # ------------------------------------------------------------------
    creances_brutes = fields.Monetary(
        string="Factures Clients Impayées",
        currency_field='currency_id', compute='_compute_kpi_metrics')
    avoirs_clients_a_imputer = fields.Monetary(
        string="Avoirs Clients à Imputer",
        currency_field='currency_id', compute='_compute_kpi_metrics')
    creances_en_cours = fields.Monetary(
        string="Créances Clients Nettes",
        currency_field='currency_id', compute='_compute_kpi_metrics')

    dettes_brutes = fields.Monetary(
        string="Factures Fournisseurs Impayées",
        currency_field='currency_id', compute='_compute_kpi_metrics')
    avoirs_fournisseurs_a_imputer = fields.Monetary(
        string="Avoirs Fournisseurs à Imputer",
        currency_field='currency_id', compute='_compute_kpi_metrics')
    dettes_en_cours = fields.Monetary(
        string="Dettes Fournisseurs Nettes",
        currency_field='currency_id', compute='_compute_kpi_metrics')

    last_update = fields.Datetime(
        string='Données Calculées Le',
        compute='_compute_kpi_metrics',
    )

    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.company_id.name} — Performance Financière" if rec.company_id else "Performance Financière"

    @api.model
    def _get_period_bounds(self, period, today=None):
        """Bornes de la période analysée.

        La borne haute est plafonnée à aujourd'hui : un tableau de bord de
        performance montre ce qui est RÉALISÉ, jamais des flux postdatés.
        """
        today = today or fields.Date.context_today(self)
        if period == 'month':
            date_from = today.replace(day=1)
        elif period == 'quarter':
            quarter_month = 3 * ((today.month - 1) // 3) + 1
            date_from = today.replace(month=quarter_month, day=1)
        elif period == 'year':
            date_from = today.replace(month=1, day=1)
        else:
            return None, None
        return date_from, today

    @api.depends('company_id', 'period')
    def _compute_kpi_metrics(self):
        now = fields.Datetime.now()
        for rec in self:
            if not rec.company_id:
                # Enregistrement en cours de saisie : rien à agréger.
                for fname in KPI_FIELD_NAMES:
                    rec[fname] = 0.0
                rec.marge_status = 'neutral'
                rec.last_update = now
                continue

            date_from, date_to = rec._get_period_bounds(rec.period)
            kpis = rec.company_id.get_financial_kpis(date_from=date_from, date_to=date_to)

            for fname in KPI_FIELD_NAMES:
                rec[fname] = kpis[fname]

            if kpis['marge_nette'] > 0:
                rec.marge_status = 'positive'
            elif kpis['marge_nette'] < 0:
                rec.marge_status = 'negative'
            else:
                rec.marge_status = 'neutral'

            rec.last_update = now

    def action_refresh_kpis(self):
        """Force le recalcul des indicateurs.

        Les KPI n'étant plus stockés, il suffit d'invalider le cache : le prochain
        rendu de la vue les recalculera à partir des écritures comptables.
        """
        self.invalidate_recordset()
        return True

    def action_view_invoices(self):
        """Redirige vers les factures et avoirs de la société."""
        self.ensure_one()
        return {
            'name': _('Factures — %s', self.company_id.name),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('company_id', '=', self.company_id.id),
                ('move_type', 'in', ['out_invoice', 'out_refund', 'out_receipt',
                                     'in_invoice', 'in_refund', 'in_receipt']),
            ],
            'context': {'default_company_id': self.company_id.id},
        }

    def action_view_payments(self):
        """Redirige vers les paiements enregistrés de la société."""
        self.ensure_one()
        return {
            'name': _('Paiements — %s', self.company_id.name),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('company_id', '=', self.company_id.id)],
            'context': {'default_company_id': self.company_id.id},
        }
