# -*- coding: utf-8 -*-
{
    'name': 'MOBACH - Fond de page pleine page des rapports',
    'version': '19.0.1.0.0',
    'summary': "Image de fond couvrant toute la page PDF (en-tête, corps et pied de page) pour tous les external_layout",
    'description': """
        Ajoute l'option « Pleine page » au champ Fond (layout_background) de la
        mise en page des documents.

        Avec wkhtmltopdf, l'en-tête, le corps (div.article) et le pied de page sont
        rendus dans trois zones séparées : un background CSS posé sur l'article ne
        peut donc jamais couvrir l'en-tête ni le pied de page.

        Ce module applique l'image après la génération du PDF, sous le contenu de
        chaque page, sur toute la surface de la feuille. Fonctionne avec tous les
        external_layout (standard, boxed, bold, striped, folder, wave, bubble...).
    """,
    'author': 'MOBACH',
    'category': 'Technical',
    'depends': ['web'],
    'data': [
        'data/report_paperformat_data.xml',
        'views/base_document_layout_views.xml',
    ],
    'assets': {
        'web.report_assets_pdf': [
            'mobach_report_background/static/src/scss/report_full_background.scss',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
