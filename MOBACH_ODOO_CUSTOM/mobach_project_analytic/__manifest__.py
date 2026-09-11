# -*- coding: utf-8 -*-
{
    'name': 'MOBACH - Comptabilité Analytique par Projet',
    'version': '19.0.1.4.0',
    'category': 'Accounting/Accounting',
    'summary': "Affecter un projet aux lignes de commande, de facture et d'écriture, "
               "et suivre le chiffre d'affaires et les dépenses par projet",
    'description': """
Comptabilite analytique par projet pour le groupe MOBACH (Odoo 19).

Odoo pilote l'analytique par un champ ``analytic_distribution`` : un
dictionnaire JSON compte -> pourcentage, saisi dans un widget dedie. C'est
puissant, mais personne sur le terrain ne saisit une repartition a la main sur
chaque ligne.

Ce module pose un champ "Projet analytique" -- un simple Many2one vers
project.project -- sur les lignes de commande client, de bon de commande
fournisseur, de facture et d'ecriture comptable. Le module traduit ce choix en
distribution analytique standard : tous les etats analytiques natifs d'Odoo
continuent donc de fonctionner.

Fonctionnalites :

- Creation d'un projet -> creation automatique de son compte analytique.
- Projet affectable ligne par ligne (Odoo standard ne l'offre qu'en en-tete).
- Propagation commande -> facture : la ligne facturee herite du projet de la
  ligne de commande, a la livraison comme a la facturation manuelle.
- Propagation bon de commande fournisseur -> facture fournisseur.
- Saisie manuelle : le projet est disponible sur les lignes de facture et sur
  les lignes d'ecriture des operations diverses.
- Suivi par projet : chiffre d'affaires realise, depenses engagees, marge.
- Tableau croise dynamique de la rentabilite par projet, croisable par mois,
  compte, client ou fournisseur.
- L'application Projet est reduite a deux entrees : « Projet » (la liste, pour
  creer et tenir les chantiers) et « Rentabilite » (le tableau croise). Les
  menus natifs (Taches, Analyse, Configuration) sont masques, les projets
  restant des centres de couts alimentes par les commandes et les factures.
    """,
    'author': 'ATTALA / MOBACH SARL',
    'website': 'https://www.mobach.cm',
    'depends': [
        'account',
        'analytic',
        'project',
        'sale_management',
        'sale_project',
        'purchase',
        'project_purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/mobach_project_margin_report_security.xml',
        'data/project_data.xml',
        'views/project_views.xml',
        'views/project_menus.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'report/mobach_project_margin_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mobach_project_analytic/static/src/scss/project_kanban.scss',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
