# -*- coding: utf-8 -*-
{
    'name': 'MOBACH - Portail de Performance Financière',
    'version': '19.0.1.1.0',
    'category': 'Accounting/Localizations',
    'summary': 'Tableau de bord et portail de performance financière par société et domaine d\'activité (SYSCOHADA)',
    'description': """
Portail et Tableau de bord de Performance Financière par Société pour le Groupe MOBACH (Odoo 19).

Les flux sont reconstitués à partir des LETTRAGES comptables, et non du résiduel
des factures : pour chaque rapprochement le module regarde la nature de la
contrepartie (règlement, avoir, écriture diverse). Une créance passée en perte
n'est donc jamais comptée comme du chiffre d'affaires encaissé, et le chiffre
d'une période close ne bouge plus rétroactivement.

Fonctionnalités principales :
- Chiffre d'Affaires Encaissé, ventilé entre encaissements réels et compensations par avoir client.
- Dépenses Réglées, ventilées de la même façon côté fournisseurs.
- Isolation du CA annulé ou passé en perte (créance irrécouvrable, escompte, écart de règlement).
- Marge Nette, Taux de Marge et Marge de Trésorerie (cash net généré par l'exploitation).
- Créances et Dettes nettes, avec le détail des avoirs restant à imputer.
- Périodes calées sur la date de règlement, plafonnées à la date du jour.
- Accessible via le tableau de bord backend Odoo et via le portail Web multi-sociétés MOBACH.
    """,
    'author': 'ATTALA / MOBACH SARL',
    'website': 'https://www.mobach.cm',
    'depends': ['account', 'analytic', 'portal', 'groupe_mobach_portal', 'mobach_config'],
    'data': [
        'security/financial_portal_security.xml',
        'security/ir.model.access.csv',
        'data/financial_performance_data.xml',
        'data/ir_cron_data.xml',
        'views/financial_dashboard_views.xml',
        'views/res_company_views.xml',
        'views/financial_portal_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mobach_financial_portal/static/src/scss/financial_kanban.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
