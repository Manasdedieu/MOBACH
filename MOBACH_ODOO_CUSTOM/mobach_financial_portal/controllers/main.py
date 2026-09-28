# -*- coding: utf-8 -*-
import logging

from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class FinancialPortalController(http.Controller):

    def _check_access(self):
        """Réserve le portail financier aux profils comptables."""
        if not request.env.user.has_group('account.group_account_invoice') \
                and not request.env.user.has_group('account.group_account_readonly'):
            raise AccessError(_("Vous n'avez pas les droits d'accès aux données financières."))

    def _resolve_companies(self, company_id=None):
        """Sociétés à afficher.

        On part de `user.company_ids` (les sociétés RATTACHÉES à l'utilisateur) et
        non de `env.companies` (celles COCHÉES dans le sélecteur en haut de page).
        Les agrégations sont ensuite faites en sudo() dans `get_financial_kpis` :
        sans cela, la règle multi-société native sur account.move filtrerait sur
        `env.companies` et les sociétés décochées afficheraient zéro sans le moindre
        message d'erreur.
        """
        user_companies = request.env.user.company_ids
        if not company_id:
            return user_companies
        try:
            cid = int(company_id)
        except (TypeError, ValueError):
            return user_companies
        return user_companies.filtered(lambda c: c.id == cid)

    def _collect_kpis(self, period, company_id=None):
        Dashboard = request.env['mobach.financial.performance']
        date_from, date_to = Dashboard._get_period_bounds(period)

        company_kpis = []
        for company in self._resolve_companies(company_id):
            company_kpis.append(company.sudo().get_financial_kpis(
                date_from=date_from,
                date_to=date_to,
            ))
        return company_kpis

    @http.route('/financial_performance', type='http', auth='user', website=True)
    def financial_performance_portal(self, period='all', company_id=None, **kw):
        """Page portail de performance financière par société MOBACH."""
        self._check_access()

        if period not in ('all', 'month', 'quarter', 'year'):
            period = 'all'

        company_kpis = self._collect_kpis(period, company_id)

        # Les totaux de groupe n'ont de sens qu'entre sociétés de même devise :
        # additionner des XAF et des EUR produirait un nombre sans signification.
        currency_ids = {kpi['currency_id'] for kpi in company_kpis}
        totals_comparable = len(currency_ids) <= 1

        total_ca = sum(k['ca_realise'] for k in company_kpis) if totals_comparable else 0.0
        total_depenses = sum(k['depenses_totales'] for k in company_kpis) if totals_comparable else 0.0
        total_cash_in = sum(k['ca_encaisse_cash'] for k in company_kpis) if totals_comparable else 0.0
        total_cash_out = sum(k['depenses_cash'] for k in company_kpis) if totals_comparable else 0.0
        total_marge = total_ca - total_depenses

        if total_ca > 0:
            total_taux_marge = total_marge / total_ca * 100.0
        elif total_marge < 0:
            total_taux_marge = -100.0
        else:
            total_taux_marge = 0.0

        total_currency = request.env['res.currency'].browse(
            currency_ids.pop() if (totals_comparable and currency_ids) else request.env.company.currency_id.id
        )

        values = {
            'company_kpis': company_kpis,
            'totals_comparable': totals_comparable,
            'total_currency': total_currency,
            'total_ca': total_ca,
            'total_depenses': total_depenses,
            'total_cash_in': total_cash_in,
            'total_cash_out': total_cash_out,
            'total_marge': total_marge,
            'total_marge_cash': total_cash_in - total_cash_out,
            'total_taux_marge': round(total_taux_marge, 2),
            'period': period,
            'selected_company_id': company_kpis[0]['company_id'] if (company_id and company_kpis) else False,
            'companies': request.env.user.company_ids,
            'current_year': request.env['mobach.financial.performance']._get_period_bounds('year')[1].year,
        }

        return request.render('mobach_financial_portal.portal_financial_performance_template', values)

    @http.route('/api/financial_kpis', type='jsonrpc', auth='user')
    def get_financial_kpis_api(self, period='all', company_id=None):
        """API JSONRPC pour rafraîchissement dynamique des KPI par société."""
        try:
            self._check_access()
        except AccessError:
            return {'status': 'error', 'message': _("Accès refusé : droits comptables requis.")}

        if period not in ('all', 'month', 'quarter', 'year'):
            period = 'all'

        try:
            return {'status': 'success', 'data': self._collect_kpis(period, company_id)}
        except Exception:
            # Le détail technique part dans les logs serveur, pas chez le client.
            _logger.exception("Echec du calcul des KPI financiers (periode=%s, societe=%s)",
                              period, company_id)
            return {'status': 'error', 'message': _("Impossible de calculer les indicateurs financiers.")}
