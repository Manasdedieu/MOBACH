# -*- coding: utf-8 -*-
{
    'name': 'Groupe Mobach - Portail Multi-Sociétés',
    'version': '19.0.2',
    'summary': 'Portail de sélection multi-société avec logos et descriptions configurables.',
    'description': """
Ce module remplace la page d\'accueil par défaut d\'Odoo par un portail d\'accueil multi-société élégant.
- Point d\'entrée direct à la racine (http://localhost:8069/) sur le portail de sélection.
- Résout dynamiquement les sociétés créées par le module 'mobach_config' via request.env.ref.
- Calcule dynamiquement le nombre de collaborateurs (utilisateurs Odoo) ayant accès à chaque société.
- Surcharge de l\'action de déconnexion pour rediriger l\'utilisateur vers le portail d\'accueil.
- Outrepasse la société par défaut configurée sur la fiche utilisateur pour forcer la société sélectionnée lors du login.
    """,
    'author': 'ATTALA',
    'category': 'Website',
    'depends': ['web', 'portal', 'mobach_config'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/portal_templates.xml',
        'data/company_portal_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
