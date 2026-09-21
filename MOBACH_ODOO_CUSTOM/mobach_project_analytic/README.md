# MOBACH — Comptabilité Analytique par Projet

![Version](https://img.shields.io/badge/version-19.0.1.0.0-blue)
![Odoo](https://img.shields.io/badge/Odoo-19.0-purple)
![License](https://img.shields.io/badge/license-LGPL--3-green)
![SYSCOHADA](https://img.shields.io/badge/SYSCOHADA-Compatible-orange)

## 📊 Ce que fait le module

Affecter un **projet** à une ligne de commande, de facture ou d'écriture, et
suivre sur ce projet le **chiffre d'affaires réalisé** et les **dépenses
engagées**.

Odoo pilote l'analytique par un champ `analytic_distribution` : un dictionnaire
JSON `{compte: pourcentage}` saisi dans un widget dédié. C'est exact, mais
inutilisable au quotidien — personne ne saisit une répartition à la main sur
chaque ligne de facture.

Ce module pose un simple champ **« Projet analytique »** et se charge de la
traduction. **Rien n'est stocké en parallèle de l'analytique standard** : la
distribution reste la source de vérité comptable, et tous les états analytiques
natifs d'Odoo continuent de fonctionner.

---

## ✅ Ce que le module ajoute à Odoo standard

| Besoin | Odoo 19 standard | Avec ce module |
|---|---|---|
| Compte analytique d'un projet | Créé seulement par certains parcours ; `account_id` reste souvent vide | **Créé automatiquement** à la création du projet |
| Projet sur une commande client | En **en-tête** uniquement (`sale.order.project_id`, limité aux projets facturables) | En en-tête **et ligne par ligne**, sans restriction |
| Projet sur un bon de commande fournisseur | En **en-tête** uniquement (`purchase.order.project_id`) | En en-tête **et ligne par ligne** |
| Projet sur une facture | Aucun : uniquement le widget de distribution analytique | Champ **« Projet analytique »** sur chaque ligne |
| Projet sur une écriture diverse | Aucun | Champ sur chaque ligne, avec héritage depuis l'en-tête |
| Commande → facture | La distribution suit, le lien au projet n'est pas lisible | Le **projet** suit, visible sur la ligne facturée |
| CA / dépenses par projet | À reconstruire depuis les rapports analytiques | **Trois champs** sur la fiche projet |
| Comparer la rentabilité des chantiers | Aucun état dédié | **Tableau croisé dynamique** CA / Dépenses / Marge, croisable par mois, compte, client |

---

## 🚀 Installation

### Prérequis

Odoo 19.0, avec : `account`, `analytic`, `project`, `sale_management`,
`sale_project`, `purchase`, `project_purchase`.

### Étapes

```bash
odoo -c /path/to/odoo.conf -d <base> -i mobach_project_analytic --stop-after-init
```

Le `post_init_hook` crée le compte analytique manquant de **tous les projets
déjà existants**. Sans ce rattrapage, ils resteraient non imputables et le champ
« Projet analytique » ne ventilerait rien pour eux.

### Droits requis

Le champ n'apparaît qu'aux utilisateurs du groupe **Comptabilité analytique**
(`analytic.group_analytic_accounting`). Pour l'activer :
*Paramètres → Comptabilité → Analytique → cocher « Comptabilité analytique »*.

---

## 📖 Guide d'Utilisation

### 1️⃣ Créer un projet

*Projet → Nouveau*. Le compte analytique est créé dans la foulée, sur le plan
« Project ». Rien à faire de plus.

L'onglet **Configuration** de la fiche projet affiche le compte analytique et,
juste en dessous, les trois indicateurs de suivi. Si un projet ancien n'a pas de
compte, un bouton **Créer le compte analytique** apparaît au même endroit.

### 2️⃣ Affecter un projet à une commande client

Deux niveaux, au choix :

- **En-tête** : champ *Projet analytique*, à côté des conditions de paiement.
  Il descend sur toutes les lignes qui n'ont pas déjà un projet.
- **Ligne par ligne** : colonne *Projet analytique* dans la liste des lignes.
  C'est le cas d'usage principal — une commande qui alimente plusieurs chantiers.

Le choix fait sur une ligne l'emporte, jusqu'à ce que le projet d'en-tête change.

### 3️⃣ Facturer

Rien de particulier à faire. Que la facture soit créée depuis la commande
(*Créer une facture*), après livraison, ou par lot, **la ligne facturée hérite du
projet de la ligne de commande**. L'écriture comptable générée à la validation
alimente le suivi du projet.

### 4️⃣ Facturer manuellement

*Comptabilité → Factures fournisseurs → Nouveau*, puis colonne *Projet
analytique* sur chaque ligne. Le champ est également disponible en en-tête, avec
le même comportement de descente.

Même chose pour une facture client saisie à la main.

### 5️⃣ Imputer une écriture diverse

Onglet **Écritures comptables** d'une opération diverse : la colonne *Projet
analytique* y figure. Utile pour une dotation, une quote-part de frais généraux,
une régularisation de chantier.

L'héritage depuis l'en-tête ne vise **que les comptes de produits et de
charges** : la contrepartie de bilan (TVA, tiers, banque) n'est pas imputée.
Rien n'empêche de le faire à la main si le cas l'exige.

### 6️⃣ Lire le suivi

Sur la fiche projet, onglet **Configuration**, groupe *Analytique* :

| Indicateur | Contenu |
|---|---|
| **Chiffre d'Affaires du Projet** | Produits imputés au projet (comptes de classe 7 SYSCOHADA) |
| **Dépenses du Projet** | Charges imputées au projet (comptes de classe 6) |
| **Marge du Projet** | CA − Dépenses, en vert si positive, en rouge sinon |

Les trois colonnes sont aussi disponibles dans la **liste des projets**, pour
comparer les chantiers d'un coup d'œil.

Le bouton **Écritures analytiques** en haut de la fiche ouvre le détail, groupé
par compte général, avec les vues liste, pivot et graphique.

---

### 7️⃣ Le tableau croisé dynamique

**Application Projet → Rentabilité**

Le tableau s'ouvre groupé par projet, avec trois mesures : **Chiffre
d'Affaires**, **Dépenses**, **Marge**. Les totaux sont, projet par projet, ceux
de la fiche.

Ce sont les axes qui font l'intérêt de la vue — sur les lignes comme sur les
colonnes :

| Axe | Ce qu'il répond |
|---|---|
| **Mois** (`date`) | Comment la marge du chantier évolue dans le temps |
| **Compte général** | Quelle nature de charge pèse sur le chantier |
| **Nature** | Le CA et les dépenses en deux colonnes lisibles |
| **Partenaire** | Quel fournisseur consomme le budget du chantier |
| **Client du projet** / **Chef de projet** / **Étape** | La rentabilité par portefeuille |

Filtres fournis : *Chiffre d'affaires*, *Dépenses*, *Exploitation seule* (écarte
les comptes de bilan affectés à la main) et un filtre de période sur la date.

L'onglet **liste** donne le détail écriture par écriture, avec un lien vers la
pièce comptable ; l'onglet **graphique** compare les marges en barres. Le bouton
d'export tableur d'Odoo fonctionne sur les trois.

Depuis une fiche projet, le lien **Tableau croisé de rentabilité** (onglet
*Configuration*, groupe *Analytique*) ouvre le même tableau cadré sur ce projet.

---

## 🚪 L'application Projet réduite à deux entrées

Les projets ne servent ici que de **centres de coût** : ils sont alimentés par
les commandes et les factures, pas par des tâches saisies à la main.

| Menu | Ce qu'il ouvre |
|---|---|
| **Projet** | La **liste** des projets — créer un chantier, le tenir, comparer les colonnes CA / Dépenses / Marge |
| **Rentabilité** | Le **tableau croisé** décrit ci-dessus |

Le menu *Projet* ouvre la liste et non le kanban natif : les colonnes de suivi
du module y sont visibles, et le bouton **Nouveau** crée un projet comme
ailleurs — avec son compte analytique dans la foulée.

Les menus natifs, eux, n'ont pas d'emploi ici et sont masqués :

| Menu masqué | Ce qu'il contenait |
|---|---|
| Projets | Liste et vue kanban des projets |
| Tâches | Mes tâches, Toutes les tâches |
| Analyse | Analyse des tâches, Évaluations clients |
| Configuration | Paramètres, Étapes, Étiquettes, Rôles, Types et plans d'activité |

### Ce que cela ne retire pas

Rien n'est supprimé : les menus sont simplement désactivés. Les tâches et les
paramètres de l'application existent toujours et restent accessibles :

- par la **recherche globale** d'Odoo ;
- depuis les autres applications (le champ *Projet analytique* d'une facture
  ouvre la fiche projet d'un clic) ;
- par **Paramètres → Technique → Interface → Menus**, en réactivant les menus.

### Revenir à l'application complète

Ouvrir `views/project_menus.xml`, passer les `eval="False"` à `eval="True"`,
puis mettre le module à jour :

```bash
odoo -c /etc/odoo/odoo.conf -d <base> -u mobach_project_analytic --stop-after-init
```

Ou, sans toucher au code, réactiver les cinq menus depuis **Paramètres →
Technique → Interface → Menus** (filtre *Archivé*).

---

## 📐 Détail des Calculs

### Traduction projet → distribution analytique

Le module prend la responsabilité **du seul plan analytique « Project »** —
celui où vit `project.project.account_id`. Sur ce plan :

- affecter un projet **remplace** le compte qui s'y trouvait ;
- vider le champ **retire** le compte du plan ;
- les comptes des **autres plans** sont conservés tels quels, pourcentages
  compris. Une ligne répartie 60/40 sur deux départements le reste après
  affectation à un projet.

### Chiffre d'affaires et dépenses

Le classement se fait sur le **type du compte général**, jamais sur le signe du
montant :

| Type de compte Odoo | Classe SYSCOHADA | Compté en |
|---|---|---|
| `income`, `income_other` | 7 — Produits | Chiffre d'affaires |
| `expense`, `expense_depreciation`, `expense_direct_cost` | 6 — Charges | Dépenses |
| tout le reste | 1 à 5 | Ignoré |

C'est indispensable : un avoir fournisseur porte un montant de signe inverse
d'une facture fournisseur, mais reste une **dépense** — négative. Le classer sur
son signe le ferait basculer en chiffre d'affaires.

`account.analytic.line.amount` vaut `-balance` : un produit (crédit) donne un
montant positif, une charge (débit) un montant négatif. Les dépenses sont donc
renvoyées en **valeur positive**, et la marge se lit directement.

---

## 🧪 Scénario de recette

| Étape | Action | Attendu |
|---|---|---|
| 1 | Créer un projet **CHANTIER TEST** | Le compte analytique existe, sur le plan « Project » |
| 2 | Commande client, 1 ligne de **3 × 1 000**, projet **CHANTIER TEST** sur la ligne | La distribution analytique affiche le compte du projet à 100 % |
| 3 | Confirmer, puis **Créer une facture** | La ligne de facture porte le projet **et** la distribution |
| 4 | Valider la facture | CA du projet = **3 000** |
| 5 | Facture fournisseur manuelle de **1 200**, projet sur la ligne, valider | Dépenses = **1 200** |
| 6 | Écriture diverse de **300** en charge, projet en en-tête, valider | Dépenses = **1 500**, marge = **1 500** |
| 7 | Ouvrir les écritures analytiques du projet | **3 lignes** : la contrepartie de bilan de l'OD n'en génère pas |

Scénario exécuté et vérifié sur la base `test_mobach_kpi`.

---

## 🐛 Dépannage

### Le champ « Projet analytique » n'apparaît nulle part

Le groupe **Comptabilité analytique** n'est pas activé. *Paramètres →
Comptabilité → Analytique*.

### Un projet n'apparaît pas dans la liste déroulante

Trois filtres s'appliquent : le projet ne doit pas être un **modèle**
(`is_template`), et sa société doit être vide ou identique à celle du document.

### La distribution analytique reste vide après avoir choisi un projet

Le projet n'a pas de compte analytique. Ouvrez sa fiche, onglet *Configuration*,
bouton **Créer le compte analytique**.

### Le CA du projet est à zéro alors que la facture est validée

Vérifiez sur la ligne de facture que la **distribution analytique** est
renseignée : c'est elle qui génère les écritures analytiques, pas le champ
projet. Si elle est vide, le projet a été posé après la validation — repassez la
facture en brouillon, réaffectez, revalidez.

### Le montant du projet a changé sans que rien ne bouge

Les indicateurs ne sont pas stockés : ils sont recalculés à chaque affichage
depuis les écritures analytiques. Un lettrage, une annulation ou une écriture
saisie ailleurs les fait bouger — c'est le comportement voulu.

---

## 📜 Licence

**LGPL-3**. Auteur : ATTALA / MOBACH SARL — [https://www.mobach.cm](https://www.mobach.cm)

Les détails d'implémentation sont documentés dans `CLAUDE.md`.
