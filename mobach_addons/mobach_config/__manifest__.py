# -*- coding: utf-8 -*-
{
    'name': 'MOBACH - Configuration Multi-Sociétés',
    'version': '19.0.2.0.0',
    'summary': 'Configuration initiale des 4 sociétés MOBACH, NAS ET FILS, MOHAMADOU BACHIROU et AFRIDRIVE',
    'description': """
        Module de configuration initiale pour le groupe MOBACH.
        - Création des 4 sociétés avec logos (multi-sociétés activé)
        - Champ NUI sur res.company
        - En-têtes et pieds de page OHADA sur chaque société (mentions légales)
        - Journaux comptables SYSCOHADA/OHADA (JV, JA, BQ, CAI, OD, AN, NDF, FR...)
        - Plan comptable SYSCOHADA appliqué automatiquement sur chaque société
        - Entrepôt configuré par société (flux réception/livraison adaptés)
        - Localisation SYSCOHADA (XAF)
        - Couleurs primaires et secondaires par société
    """,
    'author': 'MOBACH',
    'category': 'Configuration',
    'depends': [
        'base',
        'account',
        'sale_management',
        'purchase',
        'hr',
        'stock',
        'project',
        'sale_project',
        'l10n_syscohada',
        'muk_web_theme',
        'om_account_accountant',
    ],
    'data': [
        'views/res_company_views.xml',
        'data/companies_data.xml',
        'views/account_menu.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
