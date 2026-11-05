# -*- coding: utf-8 -*-
{
    'name': 'MOBACH - Plan comptable SYSCOHADA',
    'version': '19.0.1.0.0',
    'summary': "Plan comptable SYSCOHADA du client et imputation automatique des immobilisations",
    'description': """
        Complète le plan SYSCOHADA d'Odoo (l10n_syscohada, utilisé par l10n_cm) avec le plan
        comptable fourni par le client :
        - comptes manquants créés, comptes existants non recréés (libellés français corrigés) ;
        - codes à 4 chiffres ;
        - TVA 19,25 % récupérable sur immobilisations (4451).

        Factures fournisseur : les lignes de produits de nature « Immobilisation »
        (mobach_sale) sont imputées sur le compte de classe 2 du produit ou de sa catégorie,
        avec la TVA sur immobilisations.
    """,
    'author': 'MOBACH',
    'category': 'Accounting/Localizations/Account Charts',
    'depends': ['l10n_cm', 'purchase', 'mobach_sale'],
    'data': [
        'views/product_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
