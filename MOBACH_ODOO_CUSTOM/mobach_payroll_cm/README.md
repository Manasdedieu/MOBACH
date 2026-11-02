# Documentation Officielle - Module MOBACH Paie & Fiscalité Cameroun (`mobach_payroll_cm`)

Ce module assure la gestion intégrale de la paie et des obligations socio-fiscales en République du Cameroun, conformément au **Code du Travail**, au **Code Général des Impôts (CGI)**, à la réglementation de la **CNPS** (Caisse Nationale de Prévoyance Sociale) et au système comptable **SYSCOHADA**.

---

## Sommaire
1. [Vue d'Ensemble & Architecture](#1-vue-densemble--architecture)
2. [Catégories de Règles Salariales](#2-catégories-de-règles-salariales)
3. [Organismes & Registres de Contributions](#3-organismes--registres-de-contributions)
4. [Matrice Complète des Règles Salariales](#4-matrice-complète-des-règles-salariales)
5. [Détail et Formules de Calcul des Règles](#5-détail-et-formules-de-calcul-des-règles)
   - [A. Gains et Indemnités (Éléments Bruts)](#a-gains-et-indemnités-éléments-bruts)
   - [B. Assiettes et Totaux Intermédiaires](#b-assiettes-et-totaux-intermédiaires)
   - [C. Retenues Salariales (Sociales, Fiscales et Diverses)](#c-retenues-salariales-sociales-fiscales-et-diverses)
   - [D. Charges Patronales (Coût Employeur)](#d-charges-patronales-coût-employeur)
   - [E. Totaux Finaux (Net à Payer)](#e-totaux-finaux-net-à-payer)
6. [Barèmes Officiels en Vigueur (CGI & Réglementations)](#6-barèmes-officiels-en-vigueur-cgi--réglementations)
   - [Barème de la Redevance Audio-Visuelle (RAV / CRTV)](#barème-de-la-redevance-audio-visuelle-rav--crtv)
   - [Barème de la Taxe de Développement Communal (TDC)](#barème-de-la-taxe-de-développement-communal-tdc)
   - [Barème Progressif Mensuel de l'IRPP](#barème-progressif-mensuel-de-lirpp)
7. [Guide Opérationnel du Gestionnaire de Paie](#7-guide-opérationnel-du-gestionnaire-de-paie)
8. [Cas Pratiques & Jeux de Données de Démonstration](#8-cas-pratiques--jeux-de-données-de-démonstration)

---

## 1. Vue d'Ensemble & Architecture

Le module `mobach_payroll_cm` s'appuie sur le framework de paie standard Odoo (`payroll`) et fournit :
* Une **structure salariale standard** pour le Cameroun (`CM_STD` : *Structure Salariale Standard - Cameroun (SYSCOHADA)*).
* La configuration des **organismes tiers / registres de contributions** pour le suivi des règlements (CNPS, DGI, Communes, CFC, FNE).
* Le paramétrage de l'ensemble des **types d'entrées variables** (`hr.rule.input`) pour les primes et indemnités spécifiques.
* Un **modèle de rapport d'impression QWeb PDF** fidèle au bulletin officiel de MOBACH.
* Deux fiches d'employés et contrats types pour la validation immédiate des calculs.

---

## 2. Catégories de Règles Salariales

Les règles salariales sont regroupées selon les catégories suivantes (`hr.salary.rule.category`) :

| Code Catégorie | Nom | Rôle et Description |
| :--- | :--- | :--- |
| `BASIC` | **Salaire de Base** | Salaire contractuel de base (`contract.wage`). |
| `ALW` | **Primes et Indemnités Imposables** | Gains accessoires, sursalaires, primes soumises aux cotisations et taxes. |
| `NON_IMP` | **Indemnités Non Imposables** | Indemnités de remboursement de frais professionnels exonérées dans la limite légale. |
| `GROSS` | **Salaire Brut Imposable** | Cumul des rémunérations brutes (`BASIC + ALW`). |
| `INFO` | **Informations & Bases de Calcul** | Variables intermédiaires nécessaires au calcul (assiettes cotisables et imposables). |
| `DED` | **Retenues Salariales** | Ensemble des cotisations sociales et retenues fiscales supportées par le salarié, ainsi que les avances/prêts. |
| `COMP` | **Charges Patronales** | Cotisations de sécurité sociale et taxes parafiscales supportées exclusivement par l'employeur. |
| `NET` | **Salaire Net à Payer** | Salaire net viré au collaborateur (`GROSS + NON_IMP - DED`). |

---

## 3. Organismes & Registres de Contributions

Pour chaque retenue salariale ou cotisation patronale, un registre d'organisme (`hr.contribution.register`) est associé :

* **CNPS** (*Caisse Nationale de Prévoyance Sociale*) : Régime de pension vieillesse, invalidité et décès (PVI), prestations familiales (PF) et accidents du travail (AT).
* **DGI** (*Direction Générale des Impôts*) : Impôt sur le Revenu des Personnes Physiques (IRPP) et Redevance Audio-Visuelle (RAV/CRTV).
* **Communes / CTD** (*Collectivités Territoriales Décentralisées*) : Centimes Additionnels Communaux (CAC 10% de l'IRPP) et Taxe de Développement Local/Communal (TDC).
* **CFC** (*Crédit Foncier du Cameroun*) : Contribution salariale (1%) et patronale (1,5%) pour le logement social.
* **FNE** (*Fonds National de l'Emploi*) : Contribution employeur (1%) pour la promotion de l'emploi et la formation professionnelle.
* **Salariés** : Règlement des salaires nets bancaires.

---

## 4. Matrice Complète des Règles Salariales

| Séquence | Code Règle | Nom de la Règle | Catégorie | Type / Origine | Assiette / Référence | Taux ou Formule | Organisme |
| :---: | :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| **1** | `BASIC` | Salaire de base | `BASIC` | Contrat | `contract.wage` | Montant fixe contrat | Salarié |
| **2** | `PRIME_ACC_ENT` | Prime d'accueil et d'entretien | `ALW` | Saisie mensuelle | `inputs.PRIME_ACC_ENT` | Montant saisi | - |
| **3** | `ANC` | Prime d'ancienneté | `ALW` | Automatique | `contract.wage` & date début | 4% dès 2 ans + 1%/an | - |
| **4** | `IND_CONGE` | Indemnité de congé | `ALW` | Saisie mensuelle | `inputs.IND_CONGE` | Montant saisi | - |
| **5** | `PRIME_RESP` | Prime de responsabilité | `ALW` | Saisie mensuelle | `inputs.PRIME_RESP` | Montant saisi | - |
| **6** | `HS_20` | Heures supplémentaires 20% | `ALW` | Saisie mensuelle | `inputs.HS_20` | Montant saisi | - |
| **7** | `H_ABS` | Heures d'absence | `ALW` | Saisie mensuelle | `inputs.H_ABS` | Déduction négative | - |
| **8** | `IND_REP` | Indemnité de représentation | `ALW` | Saisie mensuelle | `inputs.IND_REP` | Montant saisi | - |
| **9** | `IND_TRANS` | Indemnité de transport | `ALW` | Saisie mensuelle | `inputs.IND_TRANS` | Montant saisi | - |
| **10** | `IND_LOG` | Indemnité de logement | `ALW` | Saisie mensuelle | `inputs.IND_LOG` | Montant saisi | - |
| **11** | `IND_EAU` | Indemnité d'eau | `ALW` | Saisie mensuelle | `inputs.IND_EAU` | Montant saisi | - |
| **12** | `IND_ELEC` | Indemnité d'électricité | `ALW` | Saisie mensuelle | `inputs.IND_ELEC` | Montant saisi | - |
| **13** | `IND_SALIS` | Indemnité de salissure | `ALW` | Saisie mensuelle | `inputs.IND_SALIS` | Montant saisi | - |
| **14** | `IND_PANIER` | Indemnité de panier | `ALW` | Saisie mensuelle | `inputs.IND_PANIER` | Montant saisi | - |
| **15** | `IND_LAIT` | Indemnité de lait | `ALW` | Saisie mensuelle | `inputs.IND_LAIT` | Montant saisi | - |
| **50** | `GROSS` | **SALAIRE BRUT** | `GROSS` | Calculé | `categories.BASIC + categories.ALW` | Somme brute totale | - |
| **51** | `GROSS_TAX` | SALAIRE BRUT TAXABLE | `INFO` | Calculé | `GROSS - IND_REP` | Brut hors frais réels | - |
| **52** | `GROSS_COTIS` | SALAIRE COTISABLE CNPS | `INFO` | Calculé | `GROSS - IND_REP - IND_TRANS` | Plafonné à 750 000 FCFA | - |
| **70** | `CNPS_PF_PAT` | ALLOC FAM (Prestations familiales) | `COMP` | Calculé | `GROSS_COTIS` | 7,0 % | CNPS |
| **71** | `CNPS_PVI_PAT` | PENS VIEIL (Patronale) | `COMP` | Calculé | `GROSS_COTIS` | 4,2 % | CNPS |
| **72** | `CNPS_AT_PAT` | ACC TRAV (Accidents du travail) | `COMP` | Calculé | `GROSS_COTIS` | 2,5 % (taux moyen) | CNPS |
| **73** | `CFC_PAT` | CREDIT FONC (Patronal) | `COMP` | Calculé | `GROSS` | 1,5 % | CFC |
| **74** | `FNE_PAT` | F.N.E (Patronal) | `COMP` | Calculé | `GROSS` | 1,0 % | FNE |
| **79** | `TOTAL_PAT` | **TOTAL CHARGES PATRONALES** | `COMP` | Calculé | Somme des charges employeur | Somme séq. 70 à 74 | - |
| **90** | `BASE_IRPP` | Base Nette Imposable IRPP | `INFO` | Calculé | `(GROSS_TAX - CNPS) * 70% - 41 667` | Règle intermédiaire | - |
| **100** | `IRPP` | Impôt sur le Revenu (IRPP) | `DED` | Calculé | `BASE_IRPP` | Barème progressif mensuel | DGI |
| **105** | `CAC` | Centimes additionnels communaux | `DED` | Calculé | `abs(IRPP)` | 10 % de l'IRPP | Communes |
| **110** | `TDC` | Taxe de développement local | `DED` | Calculé | `contract.wage` | Barème officiel par tranche | Communes |
| **120** | `CNPS_PVI_SAL` | Pension vieillesse salariale | `DED` | Calculé | `GROSS_COTIS` | 4,2 % (max 31 500 FCFA) | CNPS |
| **130** | `CFC_SAL` | Crédit foncier salarial | `DED` | Calculé | `GROSS_TAX` | 1,0 % | CFC |
| **140** | `RAV` | Redevance audio-visuelle (CRTV) | `DED` | Calculé | `GROSS` | Barème officiel par tranche | DGI |
| **150** | `AVANCE` | Avances sur salaires | `DED` | Saisie mensuelle | `inputs.AVANCE` | Déduction négative | Salarié |
| **160** | `PRET` | Remboursement prêts - retenues | `DED` | Saisie mensuelle | `inputs.PRET` | Déduction négative | Entreprise |
| **190** | `TOTAL_DED` | **TOTAL DES RETENUES** | `INFO` | Calculé | `abs(categories.DED)` | Cumul absolu déductions | - |
| **200** | `NET` | **SALAIRE NET A PAYER** | `NET` | Calculé | `categories.BASIC + ALW + DED` | Net à virer | Salarié |

---

## 5. Détail et Formules de Calcul des Règles

### A. Gains et Indemnités (Éléments Bruts)

#### 1. Salaire de base (`BASIC`)
* **Base** : Salaire mensuel conventionnel stipulé sur le contrat (`contract.wage`).
* **Formule** : `result = contract.wage`

#### 2. Prime d'ancienneté légale (`ANC`)
* **Législation** : Conformément à la convention collective nationale et au Code du Travail camerounais, l'ancienneté s'applique à partir de deux (2) années de présence effective :
  - Moins de 2 ans : `0 %`
  - 2 ans accomplis : `4 %` du salaire de base
  - Chaque année supplémentaire au-delà de 2 ans : `+ 1 %`
* **Formule Python** :
  ```python
  start = contract.date_start
  if start and payslip.date_to:
      years = (payslip.date_to - start).days // 365
      if years >= 2:
          rate = 0.04 + (years - 2) * 0.01
          result = contract.wage * rate
      else:
          result = 0.0
  else:
      result = 0.0
  ```

#### 3. Primes et indemnités variables saisies (`inputs`)
Les éléments suivants sont alimentés via l'onglet **Entrées** du bulletin de salaire :
* `PRIME_ACC_ENT` : Prime d'accueil et d'entretien (`inputs.PRIME_ACC_ENT.amount`)
* `IND_CONGE` : Indemnité de congé (`inputs.IND_CONGE.amount`)
* `PRIME_RESP` : Prime de responsabilité (`inputs.PRIME_RESP.amount`)
* `HS_20` : Heures supplémentaires majorées à 20% (`inputs.HS_20.amount`)
* `H_ABS` : Déduction d'heures d'absence (`- abs(inputs.H_ABS.amount)`)
* `IND_REP` : Indemnité de représentation (`inputs.IND_REP.amount`)
* `IND_TRANS` : Indemnité de transport (`inputs.IND_TRANS.amount`)
* `IND_LOG` : Indemnité de logement (`inputs.IND_LOG.amount`)
* `IND_EAU` : Indemnité d'eau (`inputs.IND_EAU.amount`)
* `IND_ELEC` : Indemnité d'électricité (`inputs.IND_ELEC.amount`)
* `IND_SALIS` : Indemnité de salissure (`inputs.IND_SALIS.amount`)
* `IND_PANIER` : Indemnité de panier (`inputs.IND_PANIER.amount`)
* `IND_LAIT` : Indemnité de lait (`inputs.IND_LAIT.amount`)

---

### B. Assiettes et Totaux Intermédiaires

#### 1. Salaire Brut Global (`GROSS`)
* Totalise tous les gains, primes et indemnités bruts :
  ```python
  result = categories.BASIC + categories.ALW
  ```

#### 2. Salaire Brut Taxable (`GROSS_TAX`)
* Base de calcul pour le Crédit Foncier Salarial et l'IRPP. L'indemnité de représentation, considérée comme remboursement de frais inhérents à la fonction, est exonérée :
  ```python
  exo_rep = inputs.IND_REP.amount if inputs.IND_REP else 0.0
  result = max(0.0, categories.BASIC + categories.ALW - exo_rep)
  ```

#### 3. Salaire Cotisable CNPS (`GROSS_COTIS`)
* Assiette soumise aux cotisations de la CNPS. Les indemnités de représentation et de transport (frais réels de déplacement) sont exclues de l'assiette.
* **Plafonnement légal** : L'assiette mensuelle cotisable CNPS est impérativement plafonnée à **750 000 FCFA/mois** :
  ```python
  exo_rep = inputs.IND_REP.amount if inputs.IND_REP else 0.0
  exo_trans = inputs.IND_TRANS.amount if inputs.IND_TRANS else 0.0
  base = max(0.0, categories.BASIC + categories.ALW - exo_rep - exo_trans)
  result = min(base, 750000.0)
  ```

#### 4. Base Nette Imposable IRPP (`BASE_IRPP`)
* Calcul de la base nette selon le Code Général des Impôts (CGI) :
  1. Si le salaire brut est inférieur ou égal au SMIG / seuil légal d'exonération (**62 000 FCFA**), la base est nulle.
  2. Déduction préalable de la cotisation salariale CNPS PVI (4,2%).
  3. Abattement légal forfaitaire de **30%** au titre des frais professionnels.
  4. Déduction de l'abattement fixe de **500 000 FCFA / an**, soit **41 666,67 FCFA / mois** :
  ```python
  brut = GROSS_TAX
  if brut <= 62000:
      result = 0.0
  else:
      cnps_val = GROSS_COTIS * 0.042
      net_apres_cnps = brut - cnps_val
      net_apres_frais = net_apres_cnps * 0.70
      abattement_fixe = 500000.0 / 12.0
      result = max(0.0, net_apres_frais - abattement_fixe)
  ```

---

### C. Retenues Salariales (Sociales, Fiscales et Diverses)

* **CNPS Pension Vieillesse Salariale (`CNPS_PVI_SAL`)** :
  - Taux : **4,20 %**
  - Assiette : `GROSS_COTIS` (plafonnée à 750 000 FCFA)
  - Retenue maximale possible : **31 500 FCFA / mois**
  - `result = - round(GROSS_COTIS * 0.042)`

* **Crédit Foncier Salarial (`CFC_SAL`)** :
  - Taux : **1,00 %**
  - Assiette : `GROSS_TAX`
  - `result = - round(GROSS_TAX * 0.01)`

* **Redevance Audio-Visuelle (`RAV`)** :
  - Barème par tranche sur le Salaire Brut Global (`GROSS`) de 0 à 13 000 FCFA *(voir tableau des barèmes ci-après)*.

* **Taxe de Développement Local / Communale (`TDC`)** :
  - Barème par tranche sur le salaire contractuel de base (`contract.wage`) de 0 à 3 000 FCFA *(voir tableau des barèmes ci-après)*.

* **Impôt sur le Revenu des Personnes Physiques (`IRPP`)** :
  - Appliqué sur la tranche mensuelle de `BASE_IRPP` selon le barème progressif à 4 tranches (10%, 15%, 25%, 35%) :
  ```python
  base_imp = BASE_IRPP
  if base_imp <= 0:
      irpp = 0.0
  else:
      t1 = min(base_imp, 166667.0) * 0.10
      t2 = max(0.0, min(base_imp - 166667.0, 83333.0)) * 0.15
      t3 = max(0.0, min(base_imp - 250000.0, 166667.0)) * 0.25
      t4 = max(0.0, base_imp - 416667.0) * 0.35
      irpp = t1 + t2 + t3 + t4
  result = - round(irpp)
  ```

* **Centimes Additionnels Communaux (`CAC`)** :
  - **10 %** du montant de l'IRPP dû au profit de la commune :
  - `result = - round(abs(IRPP) * 0.10)`

* **Avances et Acomptes (`AVANCE`)** :
  - Retenue ponctuelle saisie en entrée variable : `result = - abs(inputs.AVANCE.amount)`

* **Remboursement de prêts (`PRET`)** :
  - Échéance de prêt retenue sur salaire : `result = - abs(inputs.PRET.amount)`

---

### D. Charges Patronales (Coût Employeur)

Les cotisations employeurs sont calculées automatiquement et inscrites sur le bulletin sans impacter le net du collaborateur :

1. **Allocations Familiales (`CNPS_PF_PAT`)** :
   - Taux : **7,00 %**
   - Assiette : `GROSS_COTIS` (plafonnée à 750 000 FCFA)
   - Montant max : 52 500 FCFA / mois
2. **Pension Vieillesse Patronale (`CNPS_PVI_PAT`)** :
   - Taux : **4,20 %**
   - Assiette : `GROSS_COTIS` (plafonnée à 750 000 FCFA)
   - Montant max : 31 500 FCFA / mois
3. **Accidents du Travail (`CNPS_AT_PAT`)** :
   - Taux moyen légal : **2,50 %** (groupe B - risque moyen)
   - Assiette : `GROSS_COTIS` (plafonnée à 750 000 FCFA)
4. **Crédit Foncier Patronal (`CFC_PAT`)** :
   - Taux : **1,50 %**
   - Assiette : `GROSS` (non plafonné)
5. **Fonds National de l'Emploi (`FNE_PAT`)** :
   - Taux : **1,00 %**
   - Assiette : `GROSS` (non plafonné)
6. **Total des charges patronales (`TOTAL_PAT`)** :
   - Somme cumulée des cotisations patronales du mois.

---

### E. Totaux Finaux (Net à Payer)

* **Total des Retenues (`TOTAL_DED`)** :
  - `result = abs(categories.DED)`
* **Salaire Net à Payer (`NET`)** :
  - `result = categories.BASIC + categories.ALW + categories.DED`

---

## 6. Barèmes Officiels en Vigueur (CGI & Réglementations)

### Barème de la Redevance Audio-Visuelle (RAV / CRTV)
Appliqué sur le **Salaire Brut Global** (`GROSS`) :

| Tranche de Salaire Brut (FCFA) | Montant Mensuel (FCFA) |
| :--- | :---: |
| De 0 à 50 000 | **0** |
| De 50 001 à 100 000 | **750** |
| De 100 001 à 200 000 | **1 950** |
| De 200 001 à 300 000 | **3 250** |
| De 300 001 à 400 000 | **4 550** |
| De 400 001 à 500 000 | **5 850** |
| De 500 001 à 600 000 | **7 150** |
| De 600 001 à 700 000 | **8 450** |
| De 700 001 à 800 000 | **9 750** |
| De 800 001 à 900 000 | **11 050** |
| De 900 001 à 1 000 000 | **12 350** |
| Supérieur à 1 000 000 | **13 000** (Plafond max) |

---

### Barème de la Taxe de Développement Communal (TDC)
Appliqué sur le **Salaire Contractuel de Base** (`contract.wage`) :

| Tranche de Salaire de Base (FCFA) | Montant Mensuel (FCFA) | Montant Annuel (FCFA) |
| :--- | :---: | :---: |
| Moins de 62 000 (SMIG) | **0** | 0 |
| De 62 000 à 75 000 | **250** | 3 000 |
| De 75 001 à 100 000 | **500** | 6 000 |
| De 100 001 à 150 000 | **1 000** | 12 000 |
| De 150 001 à 200 000 | **1 500** | 18 000 |
| De 200 001 à 300 000 | **2 000** | 24 000 |
| De 300 001 à 500 000 | **2 500** | 30 000 |
| Supérieur à 500 000 | **3 000** | 36 000 (Plafond max) |

---

### Barème Progressif Mensuel de l'IRPP
Calculé sur la **Base Nette Imposable** (`BASE_IRPP`) :

| Tranche Mensuelle Imposable (FCFA) | Taux d'Imposition |
| :--- | :---: |
| De 0 à 166 667 | **10 %** |
| De 166 668 à 250 000 | **15 %** |
| De 250 001 à 416 667 | **25 %** |
| Supérieure à 416 667 | **35 %** |

*Note : Les Centimes Additionnels Communaux (**CAC**) s'ajoutent systématiquement au taux de **10%** du montant total d'IRPP déterminé par ce barème.*

---

## 7. Guide Opérationnel du Gestionnaire de Paie

### 1. Configuration du Contrat
* Aller dans **Employés > Contrats**.
* Dans le champ **Structure Salariale**, sélectionner impérativement :  
  `Structure Salariale Standard - Cameroun (SYSCOHADA)` (`CM_STD`).
* Renseigner le **Salaire contractuel** (`wage`) en FCFA.
* Vérifier la **Date de début de contrat** afin que la prime d'ancienneté soit automatiquement calculée dès la 2ème année révolue.

### 2. Saisie des Éléments Variables du Mois
* Ouvrir le bulletin de paie du salarié (**Paie > Bulletins de paie**).
* Dans l'onglet **Autres entrées** / **Entrées** :
  - Pour ajouter une prime ou indemnité (ex: indemnité de transport, prime de responsabilité, etc.) :
    - Sélectionner le type d'entrée correspondant (ex: `IND_TRANS`, `PRIME_RESP`).
    - Saisir le montant en FCFA.
  - Pour imputer un acompte ou une retenue de prêt :
    - Ajouter une ligne avec le code `AVANCE` ou `PRET`.

### 3. Calcul & Validation
* Cliquer sur le bouton **Calculer la feuille**.
* Vérifier les lignes générées :
  - La base cotisable CNPS est bien plafonnée si le salaire dépasse 750 000 FCFA.
  - Les retenues fiscales (IRPP, CAC, RAV, TDC, CFC) correspondent aux tranches du salarié.
* Confirmer et valider le bulletin (**Confirmer**).

### 4. Impression du Bulletin Officiel
* Cliquer sur **Imprimer > Bulletin de paie officiel MOBACH**.
* Le document PDF généré présente fidèlement l'en-tête de l'entreprise, les informations administratives (matricule, N° CNPS, qualification), la grille détaillée des gains et retenues, ainsi que le récapitulatif patronal et le net à payer en lettres.

---

## 8. Cas Pratiques & Jeux de Données de Démonstration

Le module inclut deux profils types pré-configurés pour tester et auditer la chaîne de calcul :

### Cas 1 : Paul TCHAMBA (Technicien - Salaire Intermédiaire)
* **Salaire de base** : `250 000 FCFA`
* **Ancienneté** : Moins de 2 ans
* **Détail des calculs** :
  - Salaire Brut : `250 000 FCFA`
  - Base Cotisable CNPS : `250 000 FCFA`
  - CNPS PVI Salariale (4,2%) : `- 10 500 FCFA`
  - Crédit Foncier Salarial (1%) : `- 2 500 FCFA`
  - RAV (tranche 200k - 300k) : `- 3 250 FCFA`
  - TDC (tranche 200k - 300k) : `- 2 000 FCFA`
  - Base IRPP : `(250 000 - 10 500) * 0.70 - 41 667 = 125 983 FCFA`
  - IRPP (Tranche 1 à 10%) : `- 12 598 FCFA`
  - CAC (10% de l'IRPP) : `- 1 260 FCFA`
  - **Total Retenues** : `32 108 FCFA`
  - **Net à Payer** : **`217 892 FCFA`**

---

### Cas 2 : Aminatou BOUBA (Cadre Financier - Salaire Plafonné avec Ancienneté)
* **Salaire de base** : `850 000 FCFA`
* **Ancienneté** : 3 ans révolus (`Taux = 4% + (3 - 2) * 1% = 5%`)
* **Détail des calculs** :
  - Prime d'ancienneté (5%) : `42 500 FCFA`
  - Salaire Brut Total : `892 500 FCFA`
  - **Plafonnement CNPS** : L'assiette est automatiquement ramenée au plafond de **750 000 FCFA**
  - CNPS PVI Salariale (4,2% plafonné) : `- 31 500 FCFA` *(Plafond légal respecté)*
  - Crédit Foncier Salarial (1% sur brut) : `- 8 925 FCFA`
  - RAV (tranche 800k - 900k) : `- 11 050 FCFA`
  - TDC (tranche > 500k) : `- 3 000 FCFA`
  - IRPP & CAC calculés sur les tranches progressives supérieures
  - **Charges Patronales CNPS** : Calculées sur la base plafonnée de 750 000 FCFA (PF: 52 500 FCFA, PVI: 31 500 FCFA, AT: 18 750 FCFA).
