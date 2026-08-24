# Documentation Technique — `mobach_financial_portal`

**Version** : 19.0.1.1.0 · **Odoo** : 19.0 · **Licence** : LGPL-3

Ce document décrit l'implémentation et, surtout, **pourquoi** elle est faite ainsi.
Le guide d'utilisation est dans `README.md`.

---

## 📋 Ce que fait le module

Un tableau de bord de performance financière par société du Groupe MOBACH, exposé
à la fois dans le backend Odoo (kanban + formulaire) et sur un portail web
(`/financial_performance`).

Il produit **17 indicateurs** répartis en deux familles :

- **Flux** — filtrés sur la période : `ca_realise`, `ca_encaisse_cash`,
  `ca_compense_avoir`, `ca_annule_perte`, `depenses_totales`, `depenses_cash`,
  `depenses_compense_avoir`, `depenses_annulees`, `marge_nette`, `marge_cash`,
  `marge_taux`.
- **Encours** — photo à la date du jour : `creances_brutes`,
  `avoirs_clients_a_imputer`, `creances_en_cours`, `dettes_brutes`,
  `avoirs_fournisseurs_a_imputer`, `dettes_en_cours`.

La liste fait foi dans `KPI_FIELD_NAMES` (`models/res_company.py`). Elle est
explicite et n'inclut pas `currency_id`, qui figure dans le dictionnaire retourné
mais existe déjà sur `res.company` : l'affecter depuis le compute écraserait la
devise de la société.

---

## 🏗️ Architecture

```
mobach_financial_portal/
├── __manifest__.py
├── controllers/
│   └── main.py                      # Route portail + API JSON-RPC
├── models/
│   ├── res_company.py               # TOUT le calcul des KPI
│   └── financial_performance.py     # Modèle de présentation (société × période)
├── views/
│   ├── financial_dashboard_views.xml   # Kanban, formulaire, recherche, menus
│   ├── financial_portal_templates.xml  # Template QWeb du portail web
│   └── res_company_views.xml           # Onglet KPI sur la fiche société
├── data/
│   ├── financial_performance_data.xml  # 16 fiches (4 sociétés × 4 périodes)
│   └── ir_cron_data.xml                # Cron historique, désactivé
├── migrations/19.0.1.1.0/
│   └── pre-migrate.py
├── security/
│   ├── financial_portal_security.xml    # Groupe + règle multi-société
│   └── ir.model.access.csv
└── static/src/scss/financial_kanban.scss
```

Le calcul vit **entièrement** dans `res.company`. `mobach.financial.performance`
n'est qu'une couche de présentation : il choisit une période, appelle
`get_financial_kpis()` et recopie le résultat dans ses champs.

---

## ⚙️ Le calcul

### Point d'entrée

```python
# models/res_company.py
def get_financial_kpis(self, date_from=None, date_to=None):
    self.ensure_one()
    self._check_financial_kpi_access()
    company = self.sudo()

    flows = company._get_reconciliation_flows(date_from=date_from, date_to=date_to)
    outstanding = company._get_outstanding_amounts()
    ...
```

Deux requêtes agrégées par société et par période. Rien n'est chargé en mémoire.

### `_get_reconciliation_flows()` — les flux

Une seule requête SQL (un `UNION ALL` de deux sens de lecture, la pièce analysée
pouvant être au débit comme au crédit du rapprochement) qui parcourt
`account_partial_reconcile` et classe chaque montant selon la **nature de la
contrepartie** :

```sql
CASE
    WHEN cp_move.origin_payment_id IS NOT NULL
      OR cp_move.statement_line_id  IS NOT NULL THEN 'cash'
    WHEN cp_move.move_type IN ('out_refund', 'in_refund') THEN 'refund'
    WHEN cp_move.move_type IN ('out_invoice', 'in_invoice',
                               'out_receipt', 'in_receipt') THEN 'invoice'
    ELSE 'entry'
END AS counterpart_kind
```

Le résultat alimente six accumulateurs : `ca_cash`, `ca_avoir`, `ca_ecart`,
`dep_cash`, `dep_avoir`, `dep_ecart`.

**Pourquoi partir des lettrages et non du résiduel.** Le résiduel d'une facture
tombe à zéro aussi bien parce qu'elle a été payée que parce qu'elle a été passée en
perte. L'ancien calcul (`amount_total - amount_residual` sur les factures en état
`paid`) comptait donc une créance irrécouvrable comme du chiffre d'affaires
encaissé. La nature de la contrepartie est la seule information qui permette de
faire la différence.

**Pourquoi `max_date`.** Chaque lettrage porte sa propre date. Filtrer la période
là-dessus rend les KPI justes **et stables** : le CA d'un mois clos ne bouge plus
quand un règlement tombe le mois suivant. L'ancien filtre sur `invoice_date` faisait
exactement l'inverse — le chiffre de janvier changeait rétroactivement à chaque
règlement ultérieur.

**Les signes négatifs sont voulus.** Un avoir source lettré contre du cash est de
l'argent qui repart dans l'autre sens :

```python
elif source_type in SUPPLIER_REFUND_TYPES:
    if kind == 'cash':
        result['dep_cash'] -= amount        # le fournisseur rembourse : l'argent entre
    elif kind in ('invoice', 'refund'):
        continue                            # déjà compté du côté de la facture
    else:
        result['dep_ecart'] -= amount
```

Le `continue` évite le double comptage : le lettrage facture ↔ avoir est déjà
enregistré quand la facture est la pièce source. Un `max(..., 0)` figurait autrefois
sur le total : un avoir fournisseur de 10 000 remboursé s'affichait comme 0 de
dépenses, et la marge était fausse d'autant.

### `_get_outstanding_amounts()` — les encours

Un `_read_group` sur `account.move`, agrégeant `amount_residual_signed` par
`move_type`, puis :

```python
'creances_brutes':      total_for(CUSTOMER_INVOICE_TYPES),
'avoirs_clients':      -total_for(CUSTOMER_REFUND_TYPES),
'dettes_brutes':       -total_for(SUPPLIER_INVOICE_TYPES),
'avoirs_fournisseurs':  total_for(SUPPLIER_REFUND_TYPES),
```

Les signes viennent du core : `amount_residual_signed` est le solde brut de la
ligne d'échéance — positif pour une créance client et pour un avoir fournisseur
(débit), négatif pour une dette fournisseur et pour un avoir client (crédit). Les
négations ramènent les quatre grandeurs à des montants positifs.

Les nets se calculent ensuite dans `get_financial_kpis()` :

```python
'creances_en_cours': rnd(outstanding['creances_brutes'] - outstanding['avoirs_clients']),
'dettes_en_cours':   rnd(outstanding['dettes_brutes']   - outstanding['avoirs_fournisseurs']),
```

**`dettes_en_cours` peut être négatif, c'est correct.** Un avoir fournisseur
confirmé et non imputé n'est pas une dette : c'est un crédit que le fournisseur
doit. Avec 9 000 de factures et 10 000 d'avoir, la réponse à « combien dois-je
sortir pour solder mes fournisseurs ? » est −1 000, pas 0. Une fois l'avoir
remboursé en argent, son résiduel tombe à zéro, il sort des encours et la dette
nette remonte au brut — le crédit est devenu de la trésorerie, le compter deux fois
serait l'erreur.

**Aucun filtre sur `payment_state`.** Le résiduel d'une pièce soldée vaut zéro, il
n'y a rien à exclure. L'ancien filtre écartait au passage les états `blocked` et
`invoicing_legacy`, dont les reliquats disparaissaient purement et simplement des
encours.

### Bornes de période

```python
# models/financial_performance.py
def _get_period_bounds(self, period, today=None):
```

La borne haute est **plafonnée à aujourd'hui** : un tableau de bord de performance
montre ce qui est réalisé, jamais des flux postdatés. « Année en cours » s'arrête
donc à la date du jour, pas au 31 décembre.

Les **encours** ignorent complètement ces bornes : ce sont des stocks. Un encours
« du mois de mars » n'a pas de sens — le résiduel d'une facture est un état
courant, pas un flux.

### Multi-devises

`account.partial.reconcile.amount` et `balance` sont déjà exprimés en devise de la
société : les écarts de change sont pris au taux réel du règlement. Côté portail,
les totaux de groupe ne sont affichés que si toutes les sociétés partagent la même
devise (`totals_comparable` dans `controllers/main.py`).

---

## 🧩 Décisions de conception

### Les KPI ne sont pas stockés

`mobach.financial.performance` n'a **aucun lien relationnel** avec `account.move`,
`account.move.line` ou `account.partial.reconcile` : aucun `@api.depends` ne peut
les atteindre. Les stocker imposait donc un cron de rafraîchissement — et des
chiffres faux entre deux passages, jusqu'à quinze minutes. Inacceptable pour un
tableau de bord de direction.

Non stockés (`compute` sans `store=True`), ils sont recalculés à chaque affichage
et toujours exacts. `action_refresh_kpis()` ne fait plus qu'invalider le cache de
session.

Corollaires : le modèle `account.payment` n'est plus étendu (le hook
`account_payment.py` a été supprimé), et le cron `cron_refresh_financial_kpis` est
désactivé. Son enregistrement XML est conservé avec `noupdate="0"` — délibérément :
c'est ce qui permet à la mise à jour du module de désactiver le cron **déjà présent
en base**. Avec `noupdate="1"`, l'enregistrement existant aurait été laissé intact,
donc toujours actif.

### Une fiche par couple société × période

```python
_unique_company_period = models.Constraint(
    'UNIQUE(company_id, period)',
    "Un seul tableau de bord par couple société / période d'analyse.",
)
```

Auparavant il n'existait qu'une fiche par société, avec un champ `period`
modifiable depuis le kanban : le premier utilisateur qui basculait sur « Année en
cours » changeait la période **pour tout le monde**. Les seize couples sont
désormais préinstanciés par `data/financial_performance_data.xml` (`noupdate="1"`,
pour ne pas réécraser les fiches existantes à chaque mise à jour).

`migrations/19.0.1.1.0/pre-migrate.py` prépare les bases existantes : il réaligne
les quatre fiches historiques sur `period = 'all'`, supprime les doublons créés à
la main, nettoie les `ir_model_data` orphelins et lève le `noupdate` du cron. Sans
lui, la mise à jour échouerait sur une violation de clé unique.

### `sudo()` et son garde-fou

`get_financial_kpis()` agrège en `sudo()` — nécessaire, car la règle multi-société
native sur `account.move` filtre sur `env.companies` (les sociétés **cochées** dans
le sélecteur), et une société décochée afficherait zéro sans le moindre message
d'erreur.

D'où `_check_financial_kpi_access()`, appelé **avant** le `sudo()` :

```python
def _check_financial_kpi_access(self):
    if self.env.su:
        return
    if not self.env.user.has_group('account.group_account_readonly') \
            and not self.env.user.has_group('account.group_account_invoice'):
        raise AccessError(...)
```

Sans ce contrôle, n'importe quel utilisateur pouvant lire `res.company` — donc tout
le monde — obtiendrait par RPC le chiffre d'affaires de n'importe quelle société du
groupe.

### Le portail part de `company_ids`, pas de `env.companies`

```python
# controllers/main.py
user_companies = request.env.user.company_ids
```

Même raison : on veut les sociétés **rattachées** à l'utilisateur, pas celles
cochées dans le sélecteur du haut de page.

---

## 🔒 Sécurité

### Trois niveaux

| Niveau | Mécanisme | Fichier |
|---|---|---|
| Menus | `groups="…group_financial_portal_user"` sur les 3 menuitems | `views/financial_dashboard_views.xml` |
| Route HTTP et API JSON-RPC | `_check_access()` → `account.group_account_invoice` ou `account.group_account_readonly` | `controllers/main.py` |
| Modèle | `ir.model.access.csv` + règle globale `[('company_id', 'in', company_ids)]` | `security/` |

Le groupe `group_financial_portal_user` hérite de `account.group_account_invoice`.

La règle `financial_performance_company_rule` est **globale** : sans elle, tout
titulaire du groupe « Facturation » lisait les indicateurs des quatre sociétés du
groupe, y compris celles auxquelles il n'est pas rattaché.

### Fuite d'information par l'API

L'API JSON-RPC ne renvoie jamais le détail technique d'une exception au client :

```python
except Exception:
    _logger.exception("Echec du calcul des KPI financiers (periode=%s, societe=%s)", ...)
    return {'status': 'error', 'message': _("Impossible de calculer les indicateurs financiers.")}
```

Le traceback part dans les logs serveur.

---

## 📊 Performances

| Élément | Coût |
|---|---|
| `_get_reconciliation_flows()` | 1 requête SQL (UNION ALL de 2 SELECT groupés) |
| `_get_outstanding_amounts()` | 1 `_read_group` |
| **Total par société × période** | **2 requêtes agrégées** |

Aucun enregistrement n'est chargé en mémoire : tout est agrégé côté PostgreSQL.
Les trois `flush_model()` en tête de `_get_reconciliation_flows()` sont
indispensables — la requête est du SQL brut et ne verrait pas les écritures encore
en cache ORM.

Le portail appelle `get_financial_kpis()` une fois par société affichée, soit
2 × N requêtes pour N sociétés.

---

## 🔧 Points d'attention pour la maintenance

- **Ajouter un KPI** : le champ doit être déclaré sur `res.company` **et** sur
  `mobach.financial.performance`, la clé ajoutée au dictionnaire de retour de
  `get_financial_kpis()`, **et** le nom inscrit dans `KPI_FIELD_NAMES`. Oublier le
  dernier point laisse le champ à zéro sans erreur.
- **Le contrôleur calcule `total_cash_in`, `total_cash_out` et `total_marge_cash`**
  (`controllers/main.py`) qui ne sont rendus nulle part dans le template du portail.
  Soit ce sont des valeurs mortes à supprimer, soit il manque la tuile côté portail.
- **`marge_cash` s'appelle « Marge de Trésorerie »** alors qu'aucun KPI de
  trésorerie ne subsiste. C'est un **flux** (encaissements réels − décaissements
  réels sur la période), issu des lettrages, et non un solde de compte. Le kanban
  l'affiche sous le libellé plus juste de « Cash net ». Un renommage du champ
  clarifierait la lecture.
- **Les KPI de trésorerie ont été retirés** en 19.0.1.1.0 :
  `tresorerie_disponible`, `tresorerie_en_attente` et la méthode
  `_get_treasury_amounts()` qui lisait les comptes SYSCOHADA 52/53 et les comptes
  d'attente de règlement. C'étaient les seuls indicateurs à ne pas dériver du cycle
  client/fournisseur.
- **Il n'y a plus de tests automatisés** dans le module. Les calculs les plus
  délicats — nature de la contrepartie, avoir supérieur à la facture, avoir
  remboursé, créance irrécouvrable, date de lettrage — n'ont donc aucun filet de
  sécurité contre une régression. À valider manuellement après toute modification
  de `res_company.py`.

---

## 📝 Historique

### 19.0.1.1.0 — Refonte du calcul

- Flux reconstitués depuis `account.partial.reconcile` au lieu du résiduel des
  factures ; ventilation cash / avoir / écriture diverse.
- Période calée sur la date de lettrage (`max_date`) et non sur `invoice_date`.
- Suppression du `max(..., 0)` qui masquait les avoirs remboursés.
- Suppression du filtre sur `payment_state` dans les encours.
- Encours ventilés factures / avoirs ; nets = brut − avoirs à imputer.
- KPI non stockés ; suppression de `account_payment.py` ; cron désactivé ;
  migration `pre-migrate.py`.
- Ajout de `_check_financial_kpi_access()` et de la règle de cloisonnement
  multi-société.
- Contrainte d'unicité société × période et préinstanciation des 16 fiches.
- Retrait des KPI de trésorerie (`tresorerie_disponible`, `tresorerie_en_attente`).

### 19.0.1.0.x — Versions antérieures

- Groupe de sécurité unique `group_financial_portal_user` et hiérarchie de menus à
  deux niveaux.
- Passage de `search()` + `sum()` à `read_group()`.
- Contrôles `has_group()` sur les routes web.
