# -*- coding: utf-8 -*-
{
    'name': "mobach_invoice",
    'summary': "Gestion centrale de la facturation MOBACH",
    'description': """
        Ce module centralise la logique de facturation de MOBACH (ex: conversion automatique 
        des prix lors du changement de devise sur les factures).
    """,
    'author': "ATTALA",
    'website': "https://www.mobach.com",
    'category': 'Accounting',
    'version': '19.0.1.0',
    'depends': [
        'account',
        'sale'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_move_discount_views.xml',
        'views/account_move_views.xml',
        'views/sale_order_views.xml',
        'report/report_discount_totals.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mobach_invoice/static/src/components/discount_totals/discount_totals.xml',
            'mobach_invoice/static/src/components/discount_totals/discount_totals.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
