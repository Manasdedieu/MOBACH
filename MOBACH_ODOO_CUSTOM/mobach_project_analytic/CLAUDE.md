# Documentation Technique — `mobach_project_analytic`

**Version** : 19.0.1.4.0 · **Odoo** : 19.0 · **Licence** : LGPL-3

Ce document décrit l'implémentation et **pourquoi** elle est faite ainsi. Le
guide d'utilisation est dans `README.md`.

---

## 🎯 Le problème

Odoo 19 gère l'analytique par `analytic_distribution` : un champ JSON porté par
`analytic.mixin`, de la forme `{"12,45": 60, "12,46": 40}` — les clés listent des
identifiants de `account.analytic.account`, les valeurs des pourcentages. Il est
saisi par un widget dédié.

Le modèle est juste, mais il ne correspond pas au besoin d'un suivi de chantier :

1. **Aucun champ lisible.** On ne peut ni filtrer, ni grouper, ni imprimer « les
   lignes du projet X » sans passer par une recherche sur du JSON.
2. **Le projet n'est affectable qu'en en-tête.** `sale_project` ajoute bien
   `sale.order.project_id` et `project_purchase` `purchase.order.project_id`,
   mais rien au niveau de la **ligne**. Une commande qui alimente trois chantiers
   n'est pas représentable.
3. **`sale.order.line.project_id` existe mais ne veut pas dire ça.** Dans
   `sale_project`, c'est le *Generated Project* — le projet **créé par** la vente
   d'un produit de service. Le réutiliser comme centre de coût casserait la
   génération de projets.
4. **Rien sur la facture.** `account.move.line` n'a que la distribution.
5. **Le compte analytique d'un projet n'est pas créé automatiquement.**
   `project.project.create()` ne touche pas `account_id` ; seuls certains
   parcours (vente de service, bouton dédié) le remplissent. Un projet sans
   compte n'est imputable nulle part.

---

## 🏗️ Architecture

```
mobach_project_analytic/
├── __manifest__.py
├── hooks.py                              # rattrapage des projets existants
├── models/
│   ├── analytic_project_mixin.py         # le cœur : champ + traduction
│   ├── project_project.py                # compte analytique auto + KPI
│   ├── sale_order.py                     # SO + SOL
│   ├── purchase_order.py                 # PO + POL
│   └── account_move.py                   # pièce + lignes
├── report/
│   ├── mobach_project_margin_report.py       # vue SQL : rentabilité par projet
│   └── mobach_project_margin_report_views.xml
├── security/
│   ├── ir.model.access.csv
│   └── mobach_project_margin_report_security.xml
└── views/
    ├── project_views.xml
    ├── project_menus.xml                     # les 2 entrées de l'app + menus natifs masqués
    ├── sale_order_views.xml
    ├── purchase_order_views.xml
    └── account_move_views.xml
```

Sur les modèles métier, le module n'ajoute que des champs et des vues. Le seul
modèle qui lui appartient est la vue SQL de reporting — d'où le
`ir.model.access.csv` et la règle multi-sociétés, qui ne concernent qu'elle.

---

## 🧩 Le mixin — `mobach.analytic.project.mixin`

Un `AbstractModel` monté sur les trois modèles de ligne. Il porte le champ et,
surtout, la traduction vers l'analytique standard.

```python
class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line', 'mobach.analytic.project.mixin']
    _name = 'sale.order.line'
```

### `_mobach_project_distribution()`

Le point délicat : **quelle part de la distribution le module a-t-il le droit de
réécrire ?**

Réponse : **le seul plan racine où vivent les comptes de projet**, celui
qu'Odoo nomme « Project » et que `_get_all_plans()` renvoie en premier.
`project.project.account_id` y est toujours rattaché.

```python
for key, percentage in distribution.items():
    kept = Account.browse(...).filtered(lambda a: a.root_plan_id not in target_plans)
    ids = kept.ids + accounts.ids
    new_distribution[','.join(map(str, ids))] = percentage
```

Conséquences, toutes voulues :

- affecter un projet **remplace** le compte du plan projet — changer de projet ne
  laisse pas l'ancien derrière lui ;
- vider le champ **retire** le compte, et supprime la clé si plus rien ne reste ;
- les comptes des **autres plans** (départements, activités…) et leurs
  pourcentages sont conservés à l'identique.

Ce dernier point distingue le module du comportement de `sale_project` et
`project_purchase`, qui **ajoutent** le compte du projet sans jamais en retirer :
chez eux, changer de projet accumule les comptes.

---

## 🔗 La chaîne de propagation

```
project.project.create()
   └─> _create_analytic_account()          (compte analytique du projet)

sale.order.project_id
   └─> sale.order.line.project_id                     (compute, store, readonly=False)
         └─> analytic_distribution                    (compute surchargé)
               └─> _prepare_invoice_line()            (facturation)
                     └─> account.move.line.analytic_project_id
                           └─> analytic_distribution
                                 └─> _create_analytic_lines()   (à la validation)
                                       └─> account.analytic.line
                                             └─> KPI du projet
```

Côté achats, `_prepare_account_move_line()` joue le rôle de
`_prepare_invoice_line()`. C'est ce maillon qui alimente le volet **dépenses** :
sans lui, seule la facture client serait imputée et la marge du projet vaudrait
toujours son chiffre d'affaires.

### Champs calculés stockés et modifiables

`project_id` / `analytic_project_id` sur les lignes est `compute=..., store=True,
readonly=False`. C'est le patron Odoo du champ « pré-rempli mais modifiable » :
la valeur saisie à la main tient, jusqu'à ce qu'une dépendance change — ici le
projet d'en-tête. La ligne suit alors le document, comme pour le reste des
champs de ligne.

---

## ⚠️ Deux pièges Odoo à connaître

### 1. `@api.depends` n'est pas cumulatif

Odoo lit les dépendances de la méthode **la plus dérivée**. Surcharger
`_compute_analytic_distribution` sans reprendre les `depends` du parent les
détruit silencieusement : le champ cesse de se recalculer quand le produit ou le
partenaire change, et personne ne s'en aperçoit avant la production.

Les trois surcharges répètent donc la liste complète :

| Modèle | `depends` repris | Origine |
|---|---|---|
| `sale.order.line` | `order_id.partner_id`, `product_id`, `order_id.project_id` | `sale` + `sale_project` |
| `purchase.order.line` | `product_id`, `order_id.partner_id`, `order_id.project_id` | `purchase` + `project_purchase` |
| `account.move.line` | `account_id`, `partner_id`, `product_id` | `account` |

…auxquels s'ajoute `analytic_project_id`.

### 2. L'héritage d'en-tête ne vise que les comptes de gestion

```python
elif line.account_id.internal_group in ('income', 'expense'):
    project = line.move_id.analytic_project_id or project
```

Une écriture équilibrée porte toujours sa contrepartie de bilan : TVA, compte de
tiers, banque. L'imputer aussi au projet créerait **deux lignes analytiques de
signe opposé**. Les totaux resteraient justes — les comptes de bilan ne sont
comptés ni en produits ni en charges — mais le détail du projet deviendrait
illisible : une OD de 300 y apparaîtrait en quatre lignes au lieu d'une.

Vérifié sur le scénario de recette : 3 lignes analytiques au lieu de 4, totaux
inchangés.

L'affectation **manuelle** d'une ligne de bilan reste possible : la règle ne
gouverne que la descente automatique depuis l'en-tête.

---

## 📊 Les indicateurs financiers et de trésorerie du projet

`_compute_mobach_analytic_totals()` pilote désormais la rentabilité de chantier
selon un modèle de **comptabilité de trésorerie et d'encours** :

1. **Base TTC & Encaissements réels** :
   - Le chiffre d'affaires reconnu (`mobach_revenue`) n'est pas le montant facturé
     mais le **CA Encaissé (TTC)** issu des paiements effectifs lettrés.
   - Tant qu'un projet ne fait l'objet d'aucun paiement, son CA Encaissé reste à **0**.
2. **Encours Client (Reste à percevoir)** :
   - `mobach_customer_encours` = `mobach_invoiced_revenue - mobach_revenue`.
   - Représente le reliquat client TTC restant à recouvrer.
3. **Dépenses Décaissées & Encours Fournisseur** :
   - Symétriquement, `mobach_expense` suit les **décaissements réels** (règlements fournisseurs).
   - `mobach_vendor_encours` = `mobach_invoiced_expense - mobach_expense` (reste à payer).
4. **Algorithme de cascade séquentielle (FIFO)** :
   - Pour chaque facture partiellement réglée, les paiements s'imputent ligne par ligne.
   - Les lignes affectées à un projet spécifique sont couvertes en premier.
   - Les lignes sans projet (ou assignées au projet **Générique**) sont couvertes en tout dernier.
5. **Projet « Générique »** :
   - Créé automatiquement dans `data/project_data.xml`.
   - Réceptionne les lignes sans affectation de chantier.
   - Sa marge est fixée à **0** pour ne pas fausser le pilotage de rentabilité des vrais projets.
6. **Marge Réalisée (Trésorerie)** :
   - `mobach_margin` = `mobach_revenue - mobach_expense`.
   - Non stockée pour garantir une fraîcheur instantanée dès chaque lettrage.

---

## 🔲 Le tableau croisé — `mobach.project.margin.report`

Ce choix de ne rien stocker a un prix : **le pivot et le graphique agrègent en
SQL**, ils ne savent pas additionner un champ calculé. Les trois indicateurs de
la fiche projet sont donc inutilisables comme mesures.

D'où un modèle `_auto = False` : une ligne par écriture analytique imputée à un
projet, le montant déjà ventilé en trois colonnes sommables — `revenue`,
`expense`, `margin`. Le pivot n'a plus qu'à faire un `SUM`.

```sql
CASE WHEN aa.account_type IN %(revenue_types)s THEN aal.amount ELSE 0.0 END AS revenue,
CASE WHEN aa.account_type IN %(expense_types)s THEN -aal.amount ELSE 0.0 END AS expense,
CASE WHEN aa.account_type IN %(revenue_types)s
       OR aa.account_type IN %(expense_types)s THEN aal.amount ELSE 0.0 END AS margin
```

`margin` vaut `amount` tel quel sur les lignes d'exploitation : un produit
(crédit) l'a déjà positif, une charge (débit) déjà négatif. C'est exactement
`revenue - expense`, écrit sans la soustraction.

Les constantes `REVENUE_ACCOUNT_TYPES` / `EXPENSE_ACCOUNT_TYPES` sont **importées
de `models/project_project.py`** : le rapport et la fiche projet doivent rendre
les mêmes totaux, une seule liste les gouverne.

### `_table_query` plutôt que `init()`

C'est le patron des rapports d'Odoo 19 (`sale.report`, `purchase.report`) : la
requête est injectée à chaque lecture au lieu d'être figée dans une vue
PostgreSQL. Un changement de constante prend effet au redémarrage, sans
`-u mobach_project_analytic`.

### Le dédoublonnage des comptes analytiques

```sql
JOIN (SELECT account_id, MIN(id) AS id FROM project_project
       WHERE account_id IS NOT NULL GROUP BY account_id) dedup
  ON dedup.account_id = aal.account_id
```

Rien n'interdit à deux projets de pointer le même compte analytique : aucune
contrainte d'unicité sur `project_project.account_id`. Une jointure directe
dupliquerait alors chaque écriture — donc les identifiants de la vue, que le
client Odoo suppose uniques, avec des totaux doublés à la clé. La sous-requête
retient le projet le plus ancien, comme le fait déjà le dictionnaire
`{account_id: project_id}` de `_compute_mobach_analytic_totals()`.

### La règle multi-sociétés

Une vue SQL n'hérite d'**aucune** `ir.rule` des tables qu'elle interroge. Sans la
règle posée dans `security/`, une société verrait la marge des chantiers des
autres. C'est le piège classique des modèles `_auto = False`.

### Vérification

Testé sur `bd_mobach_odoo19` : les totaux du `_read_group` par projet du rapport
sont identiques, au centime, à `mobach_revenue` / `mobach_expense` /
`mobach_margin` de chaque fiche projet.

---

## 🚪 L'application Projet réduite à deux entrées

`views/project_menus.xml` désactive les cinq menus de premier niveau de
`project.menu_main_pm` et pose les deux qui restent, accrochées à la racine de
l'application : « Projet » (la liste des projets) et « Rentabilité » (le pivot,
déclaré avec son action dans `report/`).

### Une action propre plutôt qu'une surcharge de `open_view_project_all`

L'action native impose son kanban par `view_id` — un `view_mode` réordonné ne
suffirait pas, il faudrait aussi vider ce champ. Et la détourner priverait de
leur vue d'origine tous les autres chemins qui l'ouvrent : raccourcis
utilisateur, lien `/odoo/project` (elle porte `path = 'project'`). D'où
`action_mobach_project_all`, qui reprend le domaine et le contexte de l'action
native mais démarre sur `list,form`.

### Pourquoi `active = False` et pas une surcharge de `groups_id`

Vider les groupes d'un menu le rend visible à tout le monde ; y mettre un groupe
technique vide fonctionne, mais laisse un menu bien vivant qu'un administrateur
retrouvera dans les droits d'accès sans comprendre son rôle. Le drapeau `active`
dit exactement ce qu'on veut dire, se lit dans l'interface (filtre *Archivé*) et
se défait d'un clic.

### Désactiver le parent suffit

`load_menus()` construit l'arbre depuis les racines et **écarte tout menu
inaccessible depuis une application** (`ir_ui_menu.py:254-259`). Les enfants d'un
menu désactivé ne sont donc pas remontés à la racine : ils disparaissent avec
lui. D'où cinq enregistrements au lieu de dix-huit.

### Un `-u project` ne réveille pas les menus

La balise `<menuitem>` d'Odoo construit son dictionnaire de valeurs à partir de
`name`, `parent_id`, `action`, `sequence`, `groups_id`, `web_icon` — **jamais
`active`**. Recharger le module `project` ne peut donc pas écraser le drapeau.

### Vérification

`load_menus()` appelé en shell après mise à jour ne renvoie que deux enfants
sous `project.menu_main_pm` — « Projet » puis « Rentabilité » — et les actions
résolvent bien sur `['list', 'form']` et `['pivot', 'graph', 'list']`. La racine
de l'application n'ayant pas d'action propre, cliquer sur son icône ouvre la
liste des projets, premier menu par séquence.

---

## 🚀 Installation et rattrapage

`post_init_hook` dote d'un compte analytique tous les projets antérieurs à
l'installation :

```python
projects = env['project.project'].with_context(active_test=False).search([
    ('account_id', '=', False), ('is_template', '=', False),
])
projects._mobach_ensure_analytic_account()
```

`active_test=False` est délibéré : un projet archivé porte des écritures
passées, et son suivi doit rester consultable.

Les **modèles de projet** (`is_template`) sont écartés partout : ils ne portent
aucune écriture, leur donner un compte polluerait le plan analytique.

---

## 🔧 Points d'attention pour la maintenance

- **Ajouter le champ à un nouveau modèle de ligne** : hériter du mixin
  (`_inherit = ['<modèle>', 'mobach.analytic.project.mixin']` + `_name`), et
  surcharger `_compute_analytic_distribution` en **reprenant les `depends` du
  parent**. Le modèle doit porter `analytic_distribution` et `company_id`.
- **Plusieurs plans analytiques.** Le module n'écrit que sur le plan racine des
  projets. Si le groupe crée un second plan (départements, activités), il
  cohabite sans conflit — c'est testé par construction dans
  `_mobach_project_distribution()`, mais pas par un test automatisé.
- **`<group string="...">` est refusé dans une vue `search` en Odoo 19.** Le RNG
  (`odoo/addons/base/rng/common.rng`) n'autorise pas l'attribut ; le message
  d'erreur pointe une ligne sans rapport. Le libellé « Regrouper par » est
  fourni par le client.
- **Il n'y a pas de tests automatisés.** Le scénario de recette du `README.md` a
  été exécuté à la main sur `test_mobach_kpi` et il passe, mais rien ne protège
  les calculs d'une régression. Les points les plus fragiles sont les `depends`
  repris à la main et la règle d'héritage sur `internal_group`.
- **`sale.order.line.project_id` existe déjà** et signifie *Generated Project*.
  Ne jamais confondre les deux ; c'est la raison du nom `analytic_project_id`.
- **`purchase.order.project_id` et `sale.order.project_id` existent aussi.** Le
  module ne les remplace pas : ils continuent d'ajouter leur compte à la
  distribution via `project_purchase` / `sale_project`. Les deux mécanismes
  cohabitent, mais renseigner les deux sur le même document est source de
  confusion — préférer le champ du module.
