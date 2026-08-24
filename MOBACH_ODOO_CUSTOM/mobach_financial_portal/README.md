# MOBACH — Portail de Performance Financière

![Version](https://img.shields.io/badge/version-19.0.1.1.0-blue)
![Odoo](https://img.shields.io/badge/Odoo-19.0-purple)
![License](https://img.shields.io/badge/license-LGPL--3-green)
![SYSCOHADA](https://img.shields.io/badge/SYSCOHADA-Compatible-orange)

## 📊 Vue d'Ensemble

Module Odoo 19 de tableau de bord et de portail web pour le suivi de la performance
financière par société du Groupe MOBACH. Conforme au référentiel comptable
**SYSCOHADA** utilisé dans la zone CEMAC (Cameroun).

Le principe de calcul tient en une phrase : **les flux sont reconstitués à partir
des lettrages comptables, pas du résiduel des factures.** Pour chaque rapprochement,
le module regarde la nature de la contrepartie — un règlement, un avoir, ou une
écriture diverse — et classe le montant en conséquence. Une créance passée en perte
n'est donc jamais comptée comme du chiffre d'affaires encaissé.

### Indicateurs Fournis

**Flux de la période** (filtrés sur la date de règlement)

| Indicateur | Ce qu'il mesure |
|---|---|
| **Chiffre d'Affaires Encaissé** | Factures clients soldées : encaissements réels + compensations par avoir |
| dont Encaissements Réels | L'argent effectivement entré en banque ou en caisse |
| dont Compensé par Avoir | Soldé par lettrage avec un avoir client, sans mouvement de trésorerie |
| **CA Annulé / Passé en Perte** | Soldé par écriture diverse (créance irrécouvrable, escompte, écart) — exclu du CA |
| **Dépenses Réglées** | Même ventilation, côté fournisseurs |
| **Marge Nette** et **Taux de Marge** | CA encaissé − Dépenses réglées, et le ratio correspondant |
| **Marge de Trésorerie** | Encaissements réels − Décaissements réels : le cash net de la période |

**Encours** (photo à la date du jour, indépendante de la période)

| Indicateur | Ce qu'il mesure |
|---|---|
| **Factures Clients Impayées** | Restant dû par les clients, avant imputation des avoirs |
| **Avoirs Clients à Imputer** | Avoirs émis, ni remboursés ni lettrés : dû au client |
| **Créances Clients Nettes** | Impayés − avoirs à imputer |
| **Factures Fournisseurs Impayées** | Restant dû aux fournisseurs, avant imputation des avoirs |
| **Avoirs Fournisseurs à Imputer** | Crédit encore en circulation chez le fournisseur |
| **Dettes Fournisseurs Nettes** | Impayés − avoirs à imputer (peut être **négatif** : voir plus bas) |

### Filtrage Temporel

- 📅 **Mois en CoursCe** — du 1er du mois à aujourd'hui
- 📅 **Trimestre en Cours** — du 1er jour du trimestre à aujourd'hui
- 📅 **Année en Cours** — du 1er janvier à aujourd'hui
- 📅 **Historique Global** — sans borne

La borne haute est toujours plafonnée à **aujourd'hui** : un tableau de bord de
performance montre ce qui est réalisé, jamais des flux postdatés.

---

## 🚀 Installation

### Prérequis

- Odoo 19.0
- Modules dépendants : `account`, `analytic`, `portal`, `groupe_mobach_portal`, `mobach_config`

### Étapes

1. **Copier le module** dans le dossier `addons` :
   ```bash
   cp -r mobach_financial_portal /path/to/odoo/addons/
   ```
2. **Mettre à jour la liste des applications** (Odoo > Applications).
3. **Installer** « MOBACH - Portail de Performance Financière ».
4. **Vérifier les données initiales** : le module crée **16 fiches**, soit les
   4 périodes d'analyse pour chacune des 4 sociétés (MOBACH SARL, NAS ET FILS SARL,
   MOHAMADOU BACHIROU SARL, AFRIDRIVE SARL).

### Mise à jour depuis une version antérieure à 19.0.1.1.0

```bash
odoo -d <base> -u mobach_financial_portal --stop-after-init
```

Un script de migration (`migrations/19.0.1.1.0/pre-migrate.py`) s'exécute
automatiquement : il aligne les fiches historiques sur la période `all`, supprime
les doublons société × période et désactive le cron de rafraîchissement devenu
inutile.

---

## 📖 Guide d'Utilisation

### 1️⃣ Menus

Le module ajoute une hiérarchie dans **Comptabilité > Analyse** :

```
Performance Financière
  ├─ Tableaux de bord    → Ouvre le portail web (nouvel onglet)
  └─ Configuration       → Ouvre la vue Kanban backend
```

Les trois menus exigent le groupe **« Performance Financière MOBACH : Accès Tableau
de Bord »**.

### 2️⃣ Vue Kanban

Chaque carte affiche :

**En-tête** — logo, nom, secteur d'activité, badge de statut (🟢 Bénéficiaire /
🔴 Déficitaire / ⚪ Neutre).

**KPIs principaux** — trois cartes colorées : CA encaissé, Dépenses réglées, Marge
nette (avec le taux et le cash net en sous-titre).

**Barre secondaire** — Créances nettes et Dettes nettes.

**Barre d'alertes** — Avoirs clients et fournisseurs restant à imputer.

**Actions** — boutons **Factures**, **Paiements** et **Actualiser**.

### 3️⃣ Formulaire Détaillé

Cliquer sur une carte ouvre un formulaire à deux onglets :

- **Flux de la Période** — ventes et achats soldés, avec le détail cash / avoir /
  écriture diverse, puis le résultat de la période.
- **Encours (à ce jour)** — créances et dettes, brutes puis nettes des avoirs.

Le champ **Période d'Analyse** ne se modifie pas depuis le kanban : il existe une
fiche par couple société × période, garantie unique par une contrainte SQL. Pour
changer de période, ouvrez la fiche correspondante.

### 4️⃣ Portail Web

```
https://votre-odoo.com/financial_performance
```

- **Authentification** requise ; droits minimum : `account.group_account_invoice`
  ou `account.group_account_readonly`.
- **Filtres** : période et société.
- **Totaux de groupe** : affichés uniquement si toutes les sociétés partagent la
  même devise — additionner des XAF et des EUR ne voudrait rien dire.
- Les sociétés affichées sont celles **rattachées** à l'utilisateur
  (`user.company_ids`), et non celles cochées dans le sélecteur du haut de page.

Une API JSON-RPC est également exposée sur `/api/financial_kpis`
(paramètres `period` et `company_id`).

### 5️⃣ Fraîcheur des Chiffres

Les indicateurs **ne sont pas stockés en base**. Ils sont recalculés à chaque
affichage à partir des écritures comptables : ils sont donc toujours exacts, sans
cron ni bouton à presser. Le bouton **Actualiser** ne fait qu'invalider le cache de
la session en cours.

---

## 📊 Détails des Calculs

### Principe : la nature de la contrepartie

Pour chaque `account.partial.reconcile` touchant un compte client ou fournisseur,
le module classe la contrepartie :

| Contrepartie | Classement |
|---|---|
| Paiement (`origin_payment_id`) ou ligne de relevé (`statement_line_id`) | **cash** — mouvement de trésorerie réel |
| Avoir (`out_refund` / `in_refund`) | **avoir** — compensation, aucun mouvement de trésorerie |
| Écriture diverse | **écart** — perte, escompte, écart de règlement |

C'est indispensable : le résiduel d'une facture tombe à zéro aussi bien parce
qu'elle a été payée que parce qu'elle a été passée en perte. Se fier au résiduel
revient à compter une créance irrécouvrable comme du chiffre d'affaires.

### 1. Chiffre d'Affaires Encaissé

```
CA Encaissé = Encaissements réels + Compensations par avoir
```

**Exemple de référence (validé avec la direction)** — avoir client AC1 de 1 000,
facture F1 de 2 000 :

| Étape | CA Encaissé | dont cash | dont avoir |
|---|---|---|---|
| F1 et AC1 émis, rien de lettré | 0 | 0 | 0 |
| F1 lettrée avec AC1 | 1 000 | 0 | 1 000 |
| Reliquat de 1 000 encaissé | 2 000 | 1 000 | 1 000 |

Un avoir client **remboursé en argent** vient en **déduction** des encaissements
réels : l'argent est ressorti.

### 2. Dépenses Réglées

Symétrique du CA, côté fournisseurs. Un avoir fournisseur remboursé par le
fournisseur est de l'argent qui entre : il **diminue** les dépenses réglées, et
peut les rendre négatives sur une période.

### 3. Marge Nette et Taux de Marge

```
Marge Nette = CA Encaissé − Dépenses Réglées
Taux (%)    = Marge Nette ÷ CA Encaissé × 100
```

Quand le CA est nul et la marge négative, le taux vaut **−100 %** et non 0 % :
une société en perte sèche ne doit pas s'afficher comme neutre.

### 4. Marge de Trésorerie

```
Marge de Trésorerie = Encaissements réels − Décaissements réels
```

C'est le cash net généré par l'exploitation sur la période. Elle diffère de la
marge nette exactement du net des compensations par avoir : deux sociétés peuvent
afficher la même marge nette alors que l'une a été payée en argent et l'autre a
soldé ses factures par lettrage d'avoirs.

### 5. Créances et Dettes

```
Créances Nettes = Factures clients impayées − Avoirs clients à imputer
Dettes Nettes   = Factures fournisseurs impayées − Avoirs fournisseurs à imputer
```

Les montants viennent du résiduel signé (`amount_residual_signed`) des pièces
postées, sans aucun filtre sur l'état de paiement : le résiduel d'une pièce soldée
vaut zéro, il n'y a donc rien à exclure.

**Un montant négatif est normal et voulu.** Un avoir fournisseur confirmé et non
imputé n'est pas une dette : c'est un crédit que le fournisseur vous doit. Avec
9 000 de factures et 10 000 d'avoir, la dette nette vaut **−1 000** — vous ne devez
rien et il vous reste 1 000 de crédit. Une fois l'avoir remboursé en argent, il
sort des encours et la dette nette remonte à son montant brut : le crédit a été
converti en trésorerie.

### 6. Dates et Périodes

Chaque lettrage porte sa propre date (`max_date`), et c'est **elle** qui rattache
le flux à une période — pas la date de facture. Conséquence : le chiffre d'un mois
clos ne bouge plus quand un règlement tombe le mois suivant.

Les **encours** sont des stocks : ils sont toujours donnés à la date du jour et ne
dépendent pas de la période sélectionnée.

### 7. Multi-Devises

`account.partial.reconcile.amount` est déjà exprimé en devise de la société : les
écarts de change sont donc pris au taux réel du règlement. Les montants sont TTC —
ce sont des encaissements, TVA comprise.

---

## 🔒 Sécurité & Droits d'Accès

### Groupe Unique

| Groupe | XML ID | Hérite de |
|---|---|---|
| Performance Financière MOBACH : Accès Tableau de Bord | `group_financial_portal_user` | `account.group_account_invoice` |

Pour donner l'accès : **Paramètres > Utilisateurs & Sociétés > Utilisateurs**,
onglet **Droits d'accès**, cocher le groupe.

### Trois Niveaux de Contrôle

| Niveau | Mécanisme |
|---|---|
| **Menus** | `groups="mobach_financial_portal.group_financial_portal_user"` sur les 3 menuitems |
| **Route HTTP et API** | `_check_access()` dans le contrôleur — `account.group_account_invoice` ou `account.group_account_readonly` |
| **Modèle** | `ir.model.access.csv` + règle d'enregistrement globale `[('company_id', 'in', company_ids)]` |

### Deux Garde-Fous à Connaître

**Le cloisonnement multi-société** (`financial_performance_company_rule`) est une
règle **globale** : sans elle, tout titulaire du groupe « Facturation » lisait les
indicateurs des quatre sociétés du groupe, y compris celles auxquelles il n'est pas
rattaché.

**Le contrôle sur `get_financial_kpis()`** (`_check_financial_kpi_access`) est
indispensable parce que l'agrégation tourne ensuite en `sudo()` : sans lui,
n'importe quel utilisateur pouvant lire `res.company` — donc tout le monde —
obtiendrait par RPC le chiffre d'affaires de n'importe quelle société.

---

## 🎨 Personnalisation CSS

```
static/src/scss/financial_kanban.scss
```

Classes principales : `.mobach-kanban-card`, `.mobach-kpi-card`, `.kpi-ca`,
`.kpi-depenses`, `.kpi-marge-pos`, `.kpi-marge-neg`, `.mobach-secondary-bar`,
`.mobach-metric-item`.

Après modification, redémarrez Odoo avec `--dev=all` pour recompiler les assets.

---

## 🐛 Dépannage

### Le menu « Performance Financière » n'apparaît pas

L'utilisateur n'a pas le groupe requis. Cochez **« Performance Financière MOBACH :
Accès Tableau de Bord »** sur sa fiche, puis rafraîchissez la page (F5).

### « Vous n'avez pas les droits d'accès aux données financières »

L'utilisateur doit avoir au minimum `account.group_account_invoice` ou
`account.group_account_readonly`. Le groupe du module hérite du premier.

### Une société affiche zéro alors qu'elle a des écritures

Vérifiez que l'utilisateur y est **rattaché** (`company_ids`, onglet Droits
d'accès), et non simplement autorisé à la voir. Le portail part des sociétés
rattachées.

### Les totaux de groupe n'apparaissent pas sur le portail

C'est volontaire : ils sont masqués dès que les sociétés affichées n'ont pas toutes
la même devise.

### Un chiffre semble faux après un lettrage manuel

Les KPI se recalculent à chaque affichage — il n'y a rien à rafraîchir. Vérifiez
plutôt l'état des pièces (`posted`) et la date du lettrage, qui est celle qui
rattache le flux à une période.

### Les vues n'ont pas changé après une modification du module

```bash
odoo -d <base> -u mobach_financial_portal --stop-after-init
```

---

## 🛠️ Support & Maintenance

**ATTALA** — MOBACH SARL
Site : [https://www.mobach.cm](https://www.mobach.cm) · Email : contact@mobach.cm

Pour signaler un bug, joignez la version d'Odoo, le message d'erreur complet, les
étapes de reproduction, et l'extrait pertinent de `/var/log/odoo/odoo.log`.

Les détails d'implémentation sont documentés dans `CLAUDE.md`.

---

## 📜 Licence

Distribué sous licence **LGPL-3**. Mentionner l'auteur original
(ATTALA DOMPTUE THIERRY EMMANUEL) et redistribuer les modifications sous la même
licence.

---

## 🎯 Roadmap

- [ ] Export Excel des KPIs
- [ ] Graphiques d'évolution temporelle (Chart.js)
- [ ] Alertes email si marge < seuil
- [ ] Ventilation par domaine d'activité (analytique)
- [ ] Comparaison période N vs N-1

---

## 📚 Ressources

- [Guide Comptabilité Odoo 19](https://www.odoo.com/documentation/19.0/applications/finance/accounting.html)
- [Développement de modules Odoo 19](https://www.odoo.com/documentation/19.0/developer.html)
- [Référentiel Comptable OHADA](https://www.ohada.org) — plan comptable SYSCOHADA révisé 2017

---

**Version** : 19.0.1.1.0

💼 **Développé pour le Groupe MOBACH** — Cameroun 🇨🇲
