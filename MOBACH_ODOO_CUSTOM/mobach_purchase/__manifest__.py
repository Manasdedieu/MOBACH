# -*- coding: utf-8 -*-
{
    'name': "mobach_purchase",
    'summary': "Conversion automatique des prix lors du changement de devise (Achats)",
    'description': """
        Ce module permet de convertir automatiquement les prix unitaires des lignes
        lorsqu'un utilisateur modifie la devise d'un bon de commande.
    """,
    'author': "ATTALA",
    'website': "https://www.mobach.com",
    'category': 'Purchases',
    'version': '1.0',
    'depends': [
        'purchase'
    ],
    'data': [
        'views/currency_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
