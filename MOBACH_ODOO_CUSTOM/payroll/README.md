# Guide Complet d'Utilisation du Module Paie (Payroll) - Odoo 19

Bienvenue dans la documentation complète et opérationnelle du module **Payroll** (`payroll`) d'Odoo 19 (portage OCA).

Ce guide a été spécialement conçu pour accompagner tout utilisateur — qu'il soit débutant, gestionnaire RH ou administrateur — ayant installé **uniquement ce module**. Il décrit la procédure intégrale de A à Z pour configurer le système, créer un salarié, gérer son contrat et éditer son bulletin de paie sans aucune ambiguïté.

---

## Sommaire
1. [Comprendre le Fonctionnement de la Paie dans Odoo 19](#1-comprendre-le-fonctionnement-de-la-paie-dans-odoo-19)
2. [Étape 1 : Configuration Initiale Obligatoire (Base Vierge)](#2-étape-1--configuration-initiale-obligatoire-base-vierge)
   - 2.1 Catégories de règles salariales
   - 2.2 Règles salariales de base
   - 2.3 Structure salariale
   - 2.4 Paramètres généraux du module
3. [Étape 2 : Préparation de l'Employé et de son Contrat](#3-étape-2--préparation-de-lemployé-et-de-son-contrat)
   - 3.1 Création du salarié
   - 3.2 Configuration du contrat versionné (`hr.version`)
4. [Étape 3 : Création et Calcul du Bulletin de Paie Individuel](#4-étape-3--création-et-calcul-du-bulletin-de-paie-individuel)
   - 4.1 Création de la fiche
   - 4.2 Saisie d'éléments variables (Primes exceptionnelles / Inputs)
   - 4.3 Calcul automatique (*Compute Sheet*)
5. [Étape 4 : Contrôle, Validation et Impression du Bulletin](#5-étape-4--contrôle-validation-et-impression-du-bulletin)
   - 5.1 Contrôle des montants et des jours travaillés
   - 5.2 Confirmation du bulletin (*Action Done*)
   - 5.3 Impression du bulletin PDF et envoi par email
6. [Étape 5 : Cas Pratique Complet et Chiffré (Exemple Pas à Pas)](#6-étape-5--cas-pratique-complet-et-chiffré-exemple-pas-à-pas)
7. [Étape 6 : Traitement en Masse / Lots de Paie (*Payslip Runs*)](#7-étape-6--traitement-en-masse--lots-de-paie-payslip-runs)
8. [Étape 7 : Gestion des Événements Particuliers et Corrections](#8-étape-7--gestion-des-événements-particuliers-et-corrections)
9. [Référence des Formules Python et Variables Disponibles](#9-référence-des-formules-python-et-variables-disponibles)
10. [Guide de Dépannage et Résolution des Erreurs Courantes](#10-guide-de-dépannage-et-résolution-des-erreurs-courantes)

---

## 1. Comprendre le Fonctionnement de la Paie dans Odoo 19

Le module de paie repose sur 4 piliers interconnectés :

```
+-------------------------------------------------------------------+
| 1. CONFIGURATION (Règles & Structures)                           |
|    Catégories (BASIC, GROSS, DED, NET)                           |
|         │                                                         |
|         ▼                                                         |
|    Règles Salariales (Formules, %, Montants fixes)                |
|         │                                                         |
|         ▼                                                         |
|    Structure Salariale (Regroupe les règles d'un profil de poste) |
+---------------------------------+---------------------------------+
                                  │
                                  ▼
+---------------------------------+---------------------------------+
| 2. SALARIÉ ET CONTRAT                                             |
|    Fiche Salarié (Identité, Temps de travail, RIB)                |
|         │                                                         |
|         ▼                                                         |
|    Contrat Actif (Salaire de base wage + Structure associée)      |
+---------------------------------+---------------------------------+
                                  │
                                  ▼
+---------------------------------+---------------------------------+
| 3. BULLETIN DE PAIE (hr.payslip)                                  |
|    • Période (du 1er au 30/31 du mois)                            |
|    • Calendrier & Congés validés -> Jours travaillés (WORK100)    |
|    • Variables du mois -> Primes / Retenues manuelles (Inputs)    |
|    • Calcul séquentiel des règles (Brouillon -> En attente)       |
|    • Confirmation -> Bulletin finalisé (Fait)                     |
+-------------------------------------------------------------------+
```

### Particularité fondamentale d'Odoo 19
Dans Odoo 19, la gestion des contrats s'appuie sur le modèle versionné **`hr.version`** (qui remplace et modernise l'ancien `hr.contract`). Le module `payroll` s'interface directement sur `hr.version`, garantissant un historique précis des salaires sans rupture temporelle.

---

## 2. Étape 1 : Configuration Initiale Obligatoire (Base Vierge)

> [!IMPORTANT]
> Si vous venez d'installer **uniquement** le module dans une base sans données de démonstration, votre base est totalement vierge : il n'y a **aucune catégorie**, **aucune règle** et **aucune structure**.
> Vous devez impérativement réaliser cette étape avant de pouvoir générer le moindre bulletin.

### 2.1 Création des Catégories de Règles Salariales
Les catégories permettent d'ordonner et de totaliser les montants (ex: total du brut, total des déductions).

Allez dans : **Paie > Configuration > Catégories de règles salariales** (cliquez sur **Nouveau**) :

| Nom | Code | Description |
| :--- | :--- | :--- |
| **Salaire de Base** | `BASIC` | Salaire contractuel de base de l'employé |
| **Indemnités et Primes** | `ALW` | Primes, avantages, indemnités de transport ou panier |
| **Salaire Brut** | `GROSS` | Cumul du salaire de base et de l'ensemble des primes |
| **Déductions** | `DED` | Retenues salariales (cotisations sociales, mutuelle, etc.) |
| **Salaire Net** | `NET` | Montant final à verser au salarié |
| **Charges Patronales** | `COMP` | Cotisations à la charge exclusive de l'employeur |

---

### 2.2 Création des Règles Salariales de Base
Chaque règle correspond à une ligne sur le bulletin de paie.

Allez dans : **Paie > Configuration > Règles salariales** (cliquez sur **Nouveau**) :

#### Règle 1 : Salaire de Base
- **Nom** : `Salaire de Base`
- **Catégorie** : `BASIC`
- **Code** : `BASIC`
- **Séquence** : `10`
- **Apparaît sur la fiche de paie** : `Coché`
- **Type de condition** : `Toujours vrai` (*Always True*)
- **Type de montant** : `Code Python`
- **Code Python** :
  ```python
  result = contract.wage
  ```

#### Règle 2 : Indemnité de Transport (Exemple de prime fixe)
- **Nom** : `Indemnité de Transport`
- **Catégorie** : `ALW`
- **Code** : `TRANS`
- **Séquence** : `20`
- **Apparaît sur la fiche de paie** : `Coché`
- **Type de condition** : `Toujours vrai`
- **Type de montant** : `Montant fixe` (*Fixed Amount*)
- **Montant fixe** : `100.00`

#### Règle 3 : Salaire Brut
- **Nom** : `Salaire Brut`
- **Catégorie** : `GROSS`
- **Code** : `GROSS`
- **Séquence** : `100` *(Remarque : la séquence 100 s'exécute après BASIC et ALW)*
- **Apparaît sur la fiche de paie** : `Coché`
- **Type de condition** : `Toujours vrai`
- **Type de montant** : `Code Python`
- **Code Python** :
  ```python
  result = categories.BASIC + categories.ALW
  ```

#### Règle 4 : Cotisations Sociales Salariales (Exemple de déduction à 7.5%)
- **Nom** : `Cotisation Retraite & Sécurité Sociale`
- **Catégorie** : `DED`
- **Code** : `DED_SS`
- **Séquence** : `120`
- **Apparaît sur la fiche de paie** : `Coché`
- **Type de condition** : `Toujours vrai`
- **Type de montant** : `Code Python`
- **Code Python** :
  ```python
  # Les retenues s'enregistrent en valeur négative
  result = -(categories.GROSS * 0.075)
  ```

#### Règle 5 : Mutuelle Santé Salariale (Déduction fixe)
- **Nom** : `Mutuelle Santé Salarié`
- **Catégorie** : `DED`
- **Code** : `DED_MUT`
- **Séquence** : `130`
- **Apparaît sur la fiche de paie** : `Coché`
- **Type de condition** : `Toujours vrai`
- **Type de montant** : `Montant fixe`
- **Montant fixe** : `-35.00`

#### Règle 6 : Salaire Net à Payer
- **Nom** : `Salaire Net`
- **Catégorie** : `NET`
- **Code** : `NET`
- **Séquence** : `200` *(S'exécute en dernier)*
- **Apparaît sur la fiche de paie** : `Coché`
- **Type de condition** : `Toujours vrai`
- **Type de montant** : `Code Python`
- **Code Python** :
  ```python
  # categories.DED est négatif, donc l'addition soustrait la retenue
  result = categories.GROSS + categories.DED
  ```

---

### 2.3 Création de la Structure Salariale
La structure regroupe les règles salariales applicables à un type de contrat ou de poste.

Allez dans : **Paie > Configuration > Structures salariales** (cliquez sur **Nouveau**) :
1. **Nom** : `Structure Standard Cadre / Salarié`
2. **Code de référence** : `BASE_STD`
3. Dans l'onglet **Règles salariales**, cliquez sur **Ajouter une ligne** et cochez :
   - `Salaire de Base` (`BASIC`)
   - `Indemnité de Transport` (`TRANS`)
   - `Salaire Brut` (`GROSS`)
   - `Cotisation Retraite & Sécurité Sociale` (`DED_SS`)
   - `Mutuelle Santé Salarié` (`DED_MUT`)
   - `Salaire Net` (`NET`)
4. **Sauvegardez**.

---

### 2.4 Paramètres Généraux Recommandés
Allez dans **Paie > Configuration > Paramètres** :
- **Autoriser l'annulation des fiches confirmées** (*Allow canceling confirmed payslips*) : `Cocher` (très utile en cas d'erreur).
- **Autoriser la modification manuelle des lignes** (*Allow editing payslip lines*) : `Cocher` si vous souhaitez corriger ponctuellement un montant calculé.
- Cliquez sur **Sauvegarder**.

---

## 3. Étape 2 : Préparation de l'Employé et de son Contrat

Pour que la fiche de paie se calcule, l'employé doit avoir un **contrat actif** couvrant la période de paie.

### 3.1 Création de l'Employé
1. Rendez-vous dans le module **Employés > Employés**.
2. Cliquez sur **Nouveau** et renseignez :
   - **Nom de l'employé** : Ex. `Jean Dupont`
   - **Poste de travail** : Ex. `Ingénieur Logiciel`
   - **Département** : Ex. `R&D`
   - **Adresse email professionnelle** & **Téléphone**.
3. Dans l'onglet **Informations de paie / Informations professionnelles** :
   - Assurez-vous que le **Temps de travail** (*Working Schedule*) est renseigné (ex: `Standard 35 hours/week` ou `Standard 40 hours/week`). C'est ce calendrier qui sert de base au calcul des jours et heures travaillés (`WORK100`).
   - Renseignez le **Compte bancaire** de l'employé pour le virement.

---

### 3.2 Création et Configuration du Contrat (`hr.version`)
1. Depuis la fiche employé, cliquez sur le bouton intelligent **Contrats** (ou via le menu **Employés > Contrats**).
2. Cliquez sur **Nouveau** et renseignez les champs obligatoires :
   - **Titre du contrat** : `CDI - Jean Dupont`
   - **Date de début** : Ex. `01/01/2026`
   - **Date de fin** : Laissez vide s'il s'agit d'un CDI.
   - **Structure salariale** : Sélectionnez `Structure Standard Cadre / Salarié` (créée à l'étape 2.3).
   - **Périodicité de paiement** (*Scheduled Pay*) : `Mensuel` (*Monthly*).
   - **Salaire** (*Wage*) : `3000.00` € (montant mensuel contractuel).
3. **Passez le contrat au statut Actif / En cours**.

---

## 4. Étape 3 : Création et Calcul du Bulletin de Paie Individuel

Tout est prêt pour calculer la paie de l'employé.

### 4.1 Création du Bulletin
1. Allez dans le menu **Paie > Fiches de paie des employés** (*Employee Payslips*).
2. Cliquez sur le bouton **Nouveau**.
3. Sélectionnez l'employé : `Jean Dupont`.
4. **Observez la magie d'Odoo** :
   - Le champ **Contrat** se remplit automatiquement avec le contrat actif.
   - La **Structure salariale** est automatiquement récupérée depuis le contrat.
   - La **Période** (`Date de début` et `Date de fin`) se pré-remplit avec le mois en cours (ex: du `01/09/2026` au `30/09/2026`).
   - Le système interroge le calendrier de travail et remplit l'onglet **Jours travaillés et entrées** avec la ligne `WORK100` (ex: 21,67 jours et 151,67 heures) ainsi que les congés approuvés dans le module Congés s'il y en a.

---

### 4.2 Saisie d'Entrées Variables (Primes, Retenues ponctuelles)
Si vous avez des règles salariales basées sur des entrées manuelles (ex: une prime variable de performance `BONUS`), vous pouvez l'ajouter :
1. Dans la fiche brouillon, allez dans l'onglet **Jours travaillés et entrées**.
2. Dans le tableau inférieur **Entrées** (*Inputs*), cliquez sur **Ajouter une ligne**.
3. Indiquez la désignation (ex: `Prime Exceptionnelle`), le code (ex: `BONUS`) et le montant (ex: `250.00`).

---

### 4.3 Déclenchement du Calcul
1. Cliquez sur le bouton **Calculer la feuille** (*Compute Sheet*) en haut à gauche.
2. Le moteur de calcul évalue chaque règle selon sa séquence.
3. Le statut du bulletin passe de **Brouillon** (*Draft*) à **En attente / Vérification** (*Waiting*).

---

## 5. Étape 4 : Contrôle, Validation et Impression du Bulletin

### 5.1 Contrôle des Onglets
- **Onglet "Calcul du salaire" (*Salary Computation*)** :
  Vérifiez les lignes générées :
  - `BASIC` : 3 000,00 €
  - `TRANS` : 100,00 €
  - `GROSS` : 3 100,00 €
  - `DED_SS` : -232,50 € (7.5% de 3100)
  - `DED_MUT` : -35,00 €
  - `NET` : 2 832,50 €
- **Onglet "Jours travaillés et entrées"** :
  Vérifiez le décompte des heures et des jours effectifs.

---

### 5.2 Confirmation du Bulletin
Une fois les montants vérifiés :
1. Cliquez sur le bouton **Confirmer** (*Confirm / Action Done*).
2. Le statut passe à **Fait** (*Done*).
3. Un numéro de séquence définitif est attribué (ex: `SLIP/2026/09/0001`).

---

### 5.3 Impression et Communication
- **Imprimer** : Cliquez sur le menu **Imprimer** en haut de la page :
  - **Bulletin de paie** (*Payslip*) : Fiche officielle résumée à remettre au salarié.
  - **Détails du bulletin de paie** (*PaySlip Details*) : Rapport technique détaillé catégorie par catégorie.
- **Envoyer par email** : Utilisez l'icône de message ou le bouton d'envoi d'email pour faire parvenir automatiquement le PDF au salarié.

---

## 6. Étape 5 : Cas Pratique Complet et Chiffré (Exemple Pas à Pas)

Prenons une situation concrète d'entreprise pour illustrer le calcul complet.

### Profil de l'employé
- **Salarié** : M. Jean Martin
- **Poste** : Développeur Senior
- **Mois** : Septembre 2026 (du 01/09/2026 au 30/09/2026)
- **Salaire mensuel de base** : 3 200,00 €
- **Éléments particuliers du mois** :
  - Prime de transport fixe : 100,00 €
  - Prime d'assiduité / bonus trimestriel : 250,00 € (saisie en Entrée `BONUS`)
  - 1 jour de congé payé posé et validé le 12 septembre

### Tableau des Règles Appliquées

| Séquence | Code Règle | Nom de la Règle | Catégorie | Méthode de Calcul | Formule / Valeur | Montant Obtenu |
| :---: | :---: | :--- | :---: | :---: | :--- | :---: |
| 10 | `BASIC` | Salaire de base | `BASIC` | Python | `result = contract.wage` | **3 200,00 €** |
| 20 | `TRANS` | Forfait transport | `ALW` | Fixe | Montant fixe 100.00 | **100,00 €** |
| 30 | `BONUS` | Prime de performance | `ALW` | Python | `result = inputs.BONUS and inputs.BONUS.amount or 0.0` | **250,00 €** |
| 100 | `GROSS` | Salaire Brut Global | `GROSS` | Python | `result = categories.BASIC + categories.ALW` | **3 550,00 €** |
| 110 | `DED_SS` | Sécurité Sociale & Retraite | `DED` | Python | `result = -(categories.GROSS * 0.075)` | **-266,25 €** |
| 120 | `DED_MUT` | Mutuelle Entreprise | `DED` | Fixe | Montant fixe -40.00 | **-40,00 €** |
| 130 | `DED_CSG` | Contribution Générale (2.4%)| `DED` | Python | `result = -(categories.GROSS * 0.024)` | **-85,20 €** |
| 150 | `COMP_PAT`| Cotisation Patronale (22%) | `COMP` | Python | `result = categories.GROSS * 0.22` (non imprimé) | *781,00 €* |
| 200 | `NET` | **Net à Payer au Salarié** | `NET` | Python | `result = categories.GROSS + categories.DED` | **3 158,55 €** |

### Résultat du Bulletin de Paie
- **Total Brut** : 3 550,00 €
- **Total Retenues Salariales** : -391,45 €
- **Salaire Net Viré** : **3 158,55 €**
- **Coût Total Employeur** : 3 550,00 € + 781,00 € = 4 331,00 €

---

## 7. Étape 6 : Traitement en Masse / Lots de Paie (*Payslip Runs*)

Lorsque votre entreprise compte plusieurs salariés, il n'est pas nécessaire de créer les fiches une à une. Utilisez les **Lots de paie** :

1. Allez dans **Paie > Lots de paie** (*Payslips Batches*).
2. Cliquez sur **Nouveau** :
   - **Nom du lot** : `Paie de Septembre 2026`
   - **Période** : du `01/09/2026` au `30/09/2026`
3. Sauvegardez le lot.
4. Cliquez sur le bouton **Générer les bulletins de paie** (*Generate Payslips*) :
   - Une fenêtre modale s'ouvre avec la liste de vos employés.
   - Cochez les employés concernés (ou cochez la case d'en-tête pour tous les sélectionner).
   - Cliquez sur le bouton **Générer**.
5. Odoo génère et calcule instantanément l'ensemble des fiches associées au lot !
6. Vous pouvez ensuite contrôler chaque fiche, puis fermer le lot via le bouton **Fermer** (*Close*).
7. Pour valider tous les bulletins en un clic : sélectionnez-les dans la liste des fiches de paie, puis dans le menu **Action**, choisissez **Changer d'état** (*Change state*) et sélectionnez **Fait** (*Done*).

---

## 8. Étape 7 : Gestion des Événements Particuliers et Corrections

### 8.1 Modifier une Fiche en Cours
Si la fiche est à l'état **En attente** (*Waiting*) et que vous devez modifier une prime ou une date :
1. Cliquez sur le bouton **Remettre en brouillon** (*Set to Draft*).
2. Effectuez les ajustements (ex: changer une valeur dans l'onglet Entrées).
3. Cliquez à nouveau sur **Calculer la feuille** (*Compute Sheet*).

### 8.2 Annuler une Fiche Confirmée
Si vous avez activé le paramètre *Allow canceling confirmed payslips* (Étape 2.4) :
1. Ouvrez la fiche confirmée (*Done*).
2. Cliquez sur le bouton **Annuler la fiche** (*Cancel Payslip*).
3. Le statut passe à **Rejeté** (*Rejected/Cancel*).
4. Cliquez sur **Remettre en brouillon** pour corriger ou recalculer.

### 8.3 Émettre un Avoir / Régularisation (*Refund*)
Si un bulletin validé a déjà été versé et comptabilisé :
1. Ouvrez le bulletin à l'état *Done*.
2. Cliquez sur le bouton **Rembourser** (*Refund*).
3. Odoo génère automatiquement une fiche de régularisation miroir (avec montants inverses) portant la mention de note de crédit.

---

## 9. Référence des Formules Python et Variables Disponibles

Dans le champ **Code Python** d'une règle salariale, le résultat final doit **toujours** être assigné à la variable `result`.

### Objets disponibles dans le contexte :
| Variable | Description et Méthodes Clés |
| :--- | :--- |
| `contract` | Objet contrat (`hr.version`). Propriétés : `contract.wage`, `contract.date_start`, `contract.schedule_pay`. |
| `employee` | Objet salarié (`hr.employee`). Propriétés : `employee.name`, `employee.gender`, `employee.marital`, `employee.children`. |
| `payslip` | Objet bulletin (`hr.payslip`). Propriétés : `payslip.date_from`, `payslip.date_to`, `payslip.number`. |
| `categories` | Objet regroupant le total calculé par catégorie : `categories.BASIC`, `categories.ALW`, `categories.GROSS`, `categories.DED`, etc. |
| `rules` | Objet contenant les règles calculées précédemment : `rules.BASIC`, `rules.TRANS`. |
| `worked_days` | Accès aux lignes de temps travaillé : `worked_days.WORK100.number_of_days`, `worked_days.WORK100.number_of_hours`. |
| `inputs` | Accès aux entrées manuelles : `inputs.BONUS.amount` (ou `inputs.BONUS and inputs.BONUS.amount or 0.0`). |
| `tools` | Bibliothèque d'outils mathématiques et utilitaires (`math`). |

### Exemples de formules avancées :

#### A. Prime d'ancienneté (1% par an après 2 ans d'ancienneté)
```python
from dateutil.relativedelta import relativedelta
annees = relativedelta(payslip.date_to, contract.date_start).years
result = (contract.wage * 0.01 * annees) if annees >= 2 else 0.0
```

#### B. Retenue pour Titres-Restaurant (3,50 € salarial par jour réellement travaillé)
```python
jours_travailles = worked_days.WORK100 and worked_days.WORK100.number_of_days or 0
result = -(3.50 * jours_travailles)
```

#### C. Proratisation du salaire en cas d'entrée en cours de mois
```python
# Si l'employé n'a pas travaillé tout le mois
nb_jours_reels = worked_days.WORK100 and worked_days.WORK100.number_of_days or 0
result = (contract.wage / 21.67) * nb_jours_reels
```

---

## 10. Guide de Dépannage et Résolution des Erreurs Courantes

| Symptôme / Message d'erreur | Cause probable | Solution immédiate |
| :--- | :--- | :--- |
| **Aucun contrat trouvé lors de la création du bulletin** | Le contrat de l'employé n'est pas actif ou ses dates ne recouvrent pas la période du bulletin. | Allez sur le contrat du salarié, vérifiez que `Date de début` <= date de début du bulletin et que le contrat est à l'état Actif. |
| **Aucune règle salariale calculée (onglet vide après Calculer)** | 1. La structure salariale n'est pas liée au contrat.<br>2. Les règles ne sont pas cochées dans la structure.<br>3. Le champ `Apparaît sur la fiche de paie` est décoché sur les règles. | Éditez le contrat pour y associer la structure `BASE_STD`. Vérifiez que la structure contient bien vos règles. |
| **Le bouton Confirmer n'apparaît pas** | Le bulletin est encore au statut *Brouillon* (*Draft*). | Vous devez d'abord cliquer sur **Calculer la feuille** (*Compute Sheet*). Une fois le calcul exécuté, le statut passe à *En attente* et le bouton *Confirmer* devient visible. |
| **Erreur Python : `KeyError` ou variable inexistante** | La règle fait référence à un code non encore calculé ou mal orthographié. | Vérifiez les **Séquences** ! Une règle de déduction (séquence 120) ne peut pas utiliser une règle de séquence 150. Vérifiez également la casse exacte des codes (`GROSS` ≠ `gross`). |
| **Impossible d'annuler une fiche confirmée** | L'option d'annulation est désactivée par défaut pour des raisons d'audit comptable. | Allez dans **Paie > Configuration > Paramètres** et cochez **Autoriser l'annulation des fiches confirmées**. |
| **Le Net à payer est supérieur au Brut** | Les règles de déductions ont été configurées avec un montant positif. | Dans Odoo Payroll, les déductions (`DED`) doivent être négatives (ex: `result = -(categories.GROSS * 0.075)` ou montant fixe `-35.00`). |

---

*Document rédigé pour le module `payroll` Odoo 19 (OCA) - Prêt pour l'exploitation en production.*
