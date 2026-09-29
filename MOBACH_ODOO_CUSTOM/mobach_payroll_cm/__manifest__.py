# -*- coding: utf-8 -*-
{
    'name': 'MOBACH - Paie & Fiscalité Cameroun (SYSCOHADA)',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Barèmes sociaux et fiscaux du Cameroun : CNPS, IRPP, CAC, CFC, RAV, TDC, FNE',
    'description': """
Module de Paie et Fiscalité pour le Cameroun (SYSCOHADA / CGI Cameroun) :
==========================================================================
- Catégories de règles salariales (Base, Primes, Brut, Retenues Sociales, Retenues Fiscales, Net, Patronal)
- Organismes / Registres de contributions (CNPS, DGI, Communes, CFC, FNE)
- Retenues salariales :
  * CNPS PVI Salariale (4,2% plafonné à 750 000 FCFA)
  * Crédit Foncier du Cameroun Salarial (CFC 1%)
  * Redevance Audio-Visuelle (RAV / CRTV barème officiel)
  * Taxe de Développement Communal (TDC barème officiel)
  * IRPP (barème progressif avec abattement CNPS, 30% frais pro et 41 667 FCFA/mois)
  * Centimes Additionnels Communaux (CAC 10% de l'IRPP)
- Charges patronales :
  * CNPS PVI Patronale (4,2% plafonné à 750 000 FCFA)
  * CNPS Prestations Familiales (7% plafonné à 750 000 FCFA)
  * CNPS Accidents du Travail (2,5% risque moyen)
  * CFC Patronal (1,5% non plafonné)
  * FNE Patronal (1% non plafonné)
- Structure salariale Standard Cameroun
- Employés et contrats de démonstration pour tests immédiats
    """,
    'author': 'MOBACH',
    'depends': [
        'payroll',
        'hr',
    ],
    'data': [
        'data/hr_contribution_register_data.xml',
        'data/hr_salary_rule_category_data.xml',
        'data/hr_salary_rule_data.xml',
        'data/hr_rule_input_data.xml',
        'data/hr_payroll_structure_data.xml',
        'data/hr_demo_cm_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
