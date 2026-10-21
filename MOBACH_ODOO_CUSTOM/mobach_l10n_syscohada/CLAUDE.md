# mobach_l10n_syscohada — Plan comptable SYSCOHADA du client et immobilisations

## Plan comptable

Source : fichier du client « PLAN COMPTABLE.xlsx » (feuille unique, colonnes BASE / N CPTE / libellé / Classe / Type).
`tools/generate_account_csv.py` le convertit en `data/template/account.account-syscohada.csv` ; le relancer
quand le client envoie une nouvelle version (usage en tête du script).

- **On ne modifie pas `l10n_syscohada`** (module standard, écrasé à chaque mise à jour d'Odoo) : on complète
  son template. `l10n_cm` (template `cm`, Cameroun) a `syscohada` pour parent, donc en profite aussi.
- Règles du script :
  - compte présent dans `l10n_syscohada` → pas recréé, libellé français remplacé par celui du client (les
    traductions Odoo sont approximatives : « Réservations facultatives »…) ;
  - compte de base à 3 chiffres **sans sous-compte** (`111`) pour un code client à 4 chiffres (`1111`) → même compte,
    il prend le code et le libellé du client (41 cas) ;
  - sinon nouveau compte, type et lettrage du compte de base le plus proche (seuls **5211** et **5215**, type banque).
  - Corrections du fichier : `1291` en double (gardé « Perte nette à reporter »), `8451` en double, espaces
    insécables devant `4621` / `6161`, coquille « EXEDITION ».
- **Codes à 4 chiffres** (`code_digits` = 4) : les comptes à 3 chiffres restants sont complétés par un 0 (`331` → `3310`).
  Sur une société qui a déjà un plan, on garde sa longueur de code (`_mobach_code_digits`) pour ne pas mélanger.
- **Ordre des fonctions `@template`** : Odoo les applique par ordre alphabétique de nom (`getmembers`) ;
  le suffixe `_mobach` les fait passer après celles de `l10n_syscohada`. `cm` est traité avant `syscohada`.
- Journal Banque → **5211**. Odoo crée d'abord un compte « Bank » (521001) pour le journal :
  `_post_load_data` le supprime s'il n'est pas utilisé.
- Les comptes techniques d'Odoo restent à part : 5212 (attente banque), 5213 / 5214 (paiements en suspens),
  5851 (virements), 9991 / 9992 (écarts de caisse), 999999 (affectation du résultat).
- `post_init_hook` : recharge le plan (`try_loading`) des sociétés déjà en `cm` / `syscohada` ; les comptes
  existants sont rattachés par leur code, rien n'est recréé.
- `mobach_config` dépend de ce module : sur base vierge, le plan est appliqué **avec** les comptes du client.

## Immobilisations (factures fournisseur)

La nature comptable du produit (`accounting_nature`, défini par `mobach_sale`) devient active :

- `property_account_immobilisation_id` (produit) et `property_account_immobilisation_categ_id` (catégorie),
  dépendants de la société, onglet Comptabilité. Le produit prime, puis la catégorie (et ses parents).
- `account.move.line._compute_account_id` : sur un document d'achat (facture, avoir, reçu), ligne de produit
  « Immobilisation » → compte de classe 2 au lieu de la charge.
- TVA : `19.25% G` / `19.25% S` (4452) → **`19.25% I`** (4451, TVA récupérable sur immobilisations, tag CM_18),
  taxe ajoutée au template `cm` (`data/template/account.tax-cm.csv`). Remplacement dans
  `account.move.line._get_computed_taxes` et `purchase.order.line._compute_tax_id` (les taxes de la commande
  sont recopiées sur la facture).
  - Piège : à la création d'une ligne, `display_type` n'est pas encore calculé → ne pas filtrer dessus pour les taxes.
  - Piège : dans un formulaire, les taxes d'une ligne sont des NewId → comparer `tax._origin.id`.
- `account.move._post` bloque une facture fournisseur dont une ligne « Immobilisation » n'est pas en classe 2
  (produit sans compte d'immobilisation, ni sur sa catégorie).
- **Ventes non concernées** : vendre un bien reste un produit (classe 7), même de nature « Immobilisation ».
- Pas de fiche d'immobilisation ni d'amortissement automatique (`om_account_asset` est installé si besoin plus tard).
- Fournisseur : reste 4011 (pas de 481 « Fournisseurs d'investissements »).

## Tester

Base vierge : `odoo-bin -d <base> -i mobach_config --load-language=fr_FR --stop-after-init` installe tout et applique
le plan `cm` (avec ce module) sur les 4 sociétés. Validé le 2026-10-21 : plan, factures / avoirs fournisseur,
commande → facture, facture client, blocage, rechargement du plan par le `post_init_hook`.

Pour charger le plan à la main sur une société : `env['account.chart.template']._load('cm', company, install_demo=False)`.
Dans `odoo-bin shell`, lire les journaux / comptes d'une autre société avec `allowed_company_ids`, sinon les
règles multi-sociétés renvoient des champs vides.
