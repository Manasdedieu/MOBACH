# -*- coding: utf-8 -*-
{
    'name': 'MOBACH - Configuration Multi-Sociétés',
    'version': '19.0.2.1.0',
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
        # Plan du client (codes à 4 chiffres) : doit être installé avant l'application du plan par le hook.
        'mobach_l10n_syscohada',
        'muk_web_theme',
        'om_account_accountant',
        'mobach_sale',
        'mobach_purchase',
        'mobach_invoice',
        'mobach_invoice_ir',
        'mobach_global_tax',
    ],
    'data': [
        'views/res_company_views.xml',
        'data/companies_data.xml',
        # Taxes des autres sociétés : elles référencent les sociétés créées juste au-dessus.
        # Identifiants mobach_invoice_ir.* conservés (fichiers venus de ce module) : pas de doublon sur les bases existantes.
        'data/account_tax_group_other_companies_data.xml',
        'data/account_tax_other_companies_data.xml',
        'views/account_menu.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
