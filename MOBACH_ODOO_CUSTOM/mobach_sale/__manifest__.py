# -*- coding: utf-8 -*-
{
    'name': 'MOBACH - VENTE',
    'version': '19.0.2.1.0',
    'category': 'Sale',
    'summary': "Modification module vente",
    'author': 'ATTALA',
    'website': 'https://www.mobach.cm',
    'depends': ['mobach_invoice_ir', 'sale_management', 'mobach_invoice'],
    'data': [
        'security/ir.model.access.csv',
        'data/res_currency_data.xml',
        'views/sale_order.xml',
        'views/account_move.xml',
        'views/hr_employee.xml',
        'views/product_template.xml',
        'views/res_partner.xml',
        'report/report_invoice_.xml',
        'report/sale_report_templates.xml',
    ],
    'assets': {
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
