# -*- coding: utf-8 -*-
{
    'name': 'MOBACH - VENTE',
    'version': '19.0.2.0.0',
    'category': 'Sale',
    'summary': "Modification module vente",
    'author': 'MOBACH',
    'website': 'https://www.mobach.cm',
    'depends': ['mobach_config'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/account_move.xml',
        'report/report_invoice_.xml',
        'report/sale_report_templates.xml',
    ],
    'assets': {},
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
