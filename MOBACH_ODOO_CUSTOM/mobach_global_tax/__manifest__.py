# -*- coding: utf-8 -*-
{
    'name': "mobach_global_tax",
    'summary': "Gestion des Taxes Globales sur les Documents Commerciaux (Ventes, Achats, Factures)",
    'description': """
        Ce module ajoute un champ 'Taxe Globale' dans l'en-tête des documents commerciaux :
        - Devis et Commandes de Ventes (sale.order)
        - Demandes de Prix et Commandes d'Achat (purchase.order)
        - Factures Clients et Fournisseurs (account.move)

        L'application d'une taxe globale en en-tête l'applique automatiquement sur toutes les lignes.
        Le retrait de la taxe globale en en-tête la retire de toutes les lignes.
        Le champ devient non éditable dès la confirmation de la pièce.
        La taxe globale d'un devis se propage automatiquement sur les factures générées.
    """,
    'author': "MOBACH",
    'website': "https://www.mobach.cm",
    'category': 'Accounting',
    'version': '19.0.2.0.0',
    'depends': [
        'sale',
        'purchase',
        'account'
    ],
    'data': [
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
