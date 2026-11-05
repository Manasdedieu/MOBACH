# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Sociétés déjà équipées du plan SYSCOHADA (ou d'un plan pays qui en hérite, comme 'cm') :
    rechargement du plan pour créer les comptes du client et la TVA sur immobilisations.
    Les comptes existants ne sont pas recréés : Odoo les rattache par leur code."""
    ChartTemplate = env['account.chart.template']
    for company in env['res.company'].search([('chart_template', '!=', False)]):
        if 'syscohada' not in ChartTemplate._get_parent_template(company.chart_template):
            continue
        _logger.info("MOBACH : mise à jour du plan %s sur %s", company.chart_template, company.name)
        ChartTemplate.try_loading(company.chart_template, company)
