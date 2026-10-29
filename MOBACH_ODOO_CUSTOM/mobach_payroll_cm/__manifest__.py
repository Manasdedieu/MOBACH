# -*- coding: utf-8 -*-
{
    'name': 'MOBACH - Paie & Fiscalité Cameroun (SYSCOHADA)',
    'version': '19.0.1.0.1',
    'category': 'Human Resources/Payroll',
    'summary': 'Moteur de paie conforme à la législation du Cameroun (CGI & CNPS) : IRPP, CAC, CFC, RAV, TDC, FNE, ancienneté et bulletin officiel MOBACH',
    'description': """
MOBACH - Paie & Fiscalité Cameroun (SYSCOHADA / CGI Cameroun)
==============================================================

Ce module implémente le moteur de calcul salarial et la fiscalité sociale en vigueur en République du Cameroun, conformément au Code du Travail, au Code Général des Impôts (CGI) et au régime de la Caisse Nationale de Prévoyance Sociale (CNPS).

Fonctionnalités et caractéristiques principales :
-------------------------------------------------
1. Rémunération Brute & Indemnités :
   - Salaire de base contractuel (`contract.wage`)
   - Calcul automatique de la Prime d'ancienneté légale (4% dès 2 ans + 1% par an supplémentaire)
   - Primes et indemnités préconfigurées de la matrice MOBACH : accueil/entretien, responsabilité, heures supplémentaires (20%), heures d'absence, représentation, transport, logement, eau, électricité, salissure, panier, lait.

2. Assiettes & Bases de Calcul Intermédiaires :
   - Salaire Brut Global (`GROSS`)
   - Salaire Brut Taxable (`GROSS_TAX`) avec exclusion des frais professionnels réels (représentation)
   - Salaire Cotisable CNPS (`GROSS_COTIS`) avec exclusion du transport et représentation, plafonné légalement à 750 000 FCFA/mois
   - Base Nette Imposable IRPP (`BASE_IRPP`) calculée après déduction de la CNPS salariale, abattement forfaitaire pour frais professionnels (30%) et abattement légal (500 000 FCFA/an soit 41 667 FCFA/mois) pour les salaires > 62 000 FCFA.

3. Retenues Salariales (Cotisations & Fiscalité) :
   - CNPS Pension Vieillesse (PVI) Salariale : 4,2% (plafonnée à 31 500 FCFA)
   - Crédit Foncier du Cameroun (CFC) Salarial : 1% du brut taxable
   - Redevance Audio-Visuelle (RAV / CRTV) : Barème officiel par tranches de 0 à 13 000 FCFA/mois
   - Taxe de Développement Local / Communale (TDC) : Barème par tranches de 0 à 3 000 FCFA/mois
   - Impôt sur le Revenu des Personnes Physiques (IRPP) : Barème progressif mensuel par tranches (10%, 15%, 25%, 35%)
   - Centimes Additionnels Communaux (CAC) : 10% de l'IRPP
   - Retenues diverses : Avances sur salaires (`AVANCE`) et remboursement de prêts (`PRET`).

4. Charges Patronales (Coût Employeur) :
   - CNPS Prestations Familiales (PF) : 7% sur le salaire cotisable plafonné (750 000 FCFA)
   - CNPS Pension Vieillesse (PVI) Patronale : 4,2% sur le salaire cotisable plafonné
   - CNPS Accidents du Travail (AT) : 2,5% (taux entreprise / groupe de risque)
   - Crédit Foncier du Cameroun (CFC) Patronal : 1,5% sur le brut total
   - Fonds National de l'Emploi (FNE) : 1% sur le brut total
   - Cumul automatique du total des charges patronales (`TOTAL_PAT`).

5. Structure et Rendu :
   - Structure salariale standard : `CM_STD`
   - Registres d'organismes collecteurs : CNPS, DGI, CTD/Communes, CFC, FNE, Salariés
   - Modèle de bulletin de paie officiel MOBACH au format QWeb PDF
   - Jeux de données de démonstration avec employés et contrats types pour tests immédiats.
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
        'views/report_payslip_cm.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
