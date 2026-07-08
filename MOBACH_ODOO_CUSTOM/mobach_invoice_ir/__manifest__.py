# -*- coding: utf-8 -*-
{
    'name': 'MOBACH - IR sur Factures (SYSCOHADA)',
    'version': '19.0.2.0.0',
    'category': 'Accounting/Localizations',
    'summary': "Retenue IR (2,2% / 5,5%) sur factures - SYSCOHADA Cameroun",
    'author': 'MOBACH',
    'website': 'https://www.mobach.cm',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_tax_group_data.xml',
        'data/account_tax_data.xml',
        'views/account_tax_views.xml',
        'views/account_move_views.xml',
        'report/report_invoice_ir.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mobach_invoice_ir/static/src/components/tax_totals_ir/tax_totals_ir.xml',
            'mobach_invoice_ir/static/src/components/tax_totals_ir/tax_totals_ir.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
