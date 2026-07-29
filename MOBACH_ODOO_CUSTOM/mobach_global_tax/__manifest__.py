# -*- coding: utf-8 -*-
{
    'name': "mobach_global_tax",
    'summary': "Gestion des Taxes Globales sur les Documents Commerciaux",
    'description': """
        Ce module ajoute un assistant (Wizard) permettant d'affecter, remplacer ou supprimer 
        des taxes sur toutes les lignes d'un document en une seule action.
        
        S'applique aux modèles :
        - Devis et Commandes de Ventes (sale.order)
        - Demandes de Prix et Commandes d'Achat (purchase.order)
        - Factures Clients et Fournisseurs (account.move)
    """,
    'author': "MOBACH",
    'website': "https://www.mobach.com",
    'category': 'Accounting',
    'version': '1.0',
    'depends': [
        'sale',
        'purchase',
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/global_tax_wizard_view.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
