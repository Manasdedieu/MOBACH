# Module `mobach_invoice` — Gestion Centrale de la Facturation & des Remises MOBACH

Ce module centralise la logique métier de facturation du groupe **MOBACH** sous **Odoo 19** :
1. **Gestion unifiée des remises** sur les **Devis / Commandes de vente** (`sale.order`) et les **Factures clients / Avoirs** (`account.move`).
2. **Affichage de la remise dans le bloc des totaux** (interface Odoo et impressions PDF).
3. **Conversion automatique des prix** lors du changement de devise sur les factures.

---

## 1. Gestion des Remises (Devis, Commandes & Factures)

### 1.1. Bouton « Remise » et Assistant (Wizard)
Sur les devis/commandes (bouton natif étendu) ainsi que sur les factures clients en brouillon non issues d'une commande (bouton **Remise** ajouté par ce module), l'utilisateur dispose de 3 modes de remise :
- **Sur toutes les lignes (%)** : applique le pourcentage dans la colonne `% Remise` (`discount`) de chaque ligne d'article.
- **Remise globale (%)** : crée une ligne de remise négative calculée sur la somme HT des lignes d'articles.
- **Montant fixe** : crée une ligne de remise négative avec le montant exact saisi dans l'assistant.

### 1.2. Écrasement automatique des anciennes remises (Une seule remise active)
À chaque nouvelle application d'une remise via l'assistant (`_clear_previous_discounts`), **toute remise précédente est automatiquement supprimée** avant d'appliquer la nouvelle afin de ne jamais cumuler deux remises par erreur :
- Les éventuelles lignes d'article « Remise » existantes sont supprimées.
- Les pourcentages de remise (`discount`) présents sur les lignes d'articles sont remis à `0%`.

#### Exemple de cycle d'utilisation :
1. **1ʳᵉ application — 10 % sur toutes les lignes** (sur une pièce de `200 000 FCFA` HT) :
   - Chaque ligne passe à `10 %` de remise.
   - `Montant hors taxes` = `180 000 FCFA`, `Remise` = `20 000 FCFA`.
2. **2ᵉ application — 5 % sur toutes les lignes** :
   - Les `10 %` précédents sont remplacés par `5 %`.
   - `Montant hors taxes` = `190 000 FCFA`, `Remise` = `10 000 FCFA`.
3. **3ᵉ application — Remise fixe de `50 000 FCFA`** :
   - Les `5 %` sur toutes les lignes sont remis à `0 %`.
   - Une ligne avec l'article **Remise** est créée au prix unitaire de `-50 000 FCFA`.
   - `Montant hors taxes` = `150 000 FCFA`, `Remise` = `50 000 FCFA`.

### 1.3. Ligne d'article « Remise » invisible pour l'utilisateur et non impactée par les taxes
Lorsqu'une remise globale (%) ou une remise fixe est appliquée :
- **Exactitude du montant (sans impact des taxes)** : la ligne de remise est créée **sans taxe** (`tax_ids` vide) avec un prix unitaire strictement égal à `-montant` (ex. `-50 000 FCFA`). La TVA reste ainsi calculée sur les lignes d'articles d'origine et le montant de la remise correspond exactement à la valeur saisie dans l'assistant.
- **Équilibre comptable** : la ligne existe réellement dans `order_line` / `invoice_line_ids` (identifiée par le champ booléen `is_global_discount_line = True`), ce qui garantit l'exactitude du `Montant hors taxes` (`amount_untaxed`), du calcul de l'IR et de l'équilibre des écritures comptables (`account.move.line`).
- **Masquage visuel** :
  - **Dans le formulaire Odoo (UI)** : le renderer OWL (`SectionAndNoteListRenderer`) masque automatiquement les lignes ayant `is_global_discount_line = True` (`d-none`) et les exclut des sous-totaux de sections.
  - **Dans les rapports PDF** : les méthodes `_get_order_lines_to_report()` (devis/commandes) et `_get_move_lines_to_report()` (factures) filtrent ces lignes pour qu'elles n'apparaissent jamais dans le tableau des articles imprimés.
  - **Propagation Devis → Facture** : lors de la création d'une facture depuis une commande (`_prepare_invoice_line`), le marqueur `is_global_discount_line` est automatiquement transféré sur la ligne de facture.

### 1.4. Affichage dans le résumé des totaux (UI & PDF)
Dès qu'une remise est active sur un devis ou une facture (`global_discount_amount > 0`), le bloc des totaux affiche :
1. **Montant hors taxes** (*Untaxed Amount* traduit nativement) : affiche directement le **nouveau HT** (HT net après déduction de la remise).
2. **Remise** : affichée juste en dessous du *Montant hors taxes* (en rouge), indiquant la valeur totale de la remise appliquée.
3. **Taxes (TVA, IR, Net à Mandater, Retenue de garantie)** puis **Total TTC**.

---

## 2. Gestion Multi-Devises sur les Factures

### 2.1. Conversion automatique des prix unitaires
Lorsqu'un utilisateur change la devise (`currency_id`) sur une facture en brouillon :
- La méthode `_onchange_currency_id_convert_prices` convertit automatiquement le prix unitaire (`price_unit`) de chaque ligne à l'aide du taux de change à la date de facturation.
- Le champ technique `ui_last_currency_id` mémorise la dernière devise utilisée à l'écran pour permettre plusieurs changements successifs avant enregistrement sans perte de précision.

---

## 3. Structure du Module

```text
mobach_invoice/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── account_move.py                   # Conversion devises, calcul remise/HT, masquage PDF & injection tax_totals (Factures)
│   └── sale_order.py                     # Calcul remise/HT, masquage PDF, propagation facture & injection tax_totals (Devis/Commandes)
├── report/
│   └── report_discount_totals.xml        # Héritage QWeb PDF (account.document_tax_totals & sale.document_tax_totals)
├── security/
│   └── ir.model.access.csv               # Droits d'accès à l'assistant account.move.discount
├── static/
│   └── src/
│       └── components/
│           └── discount_totals/
│               ├── discount_totals.js    # Patch OWL TaxTotalsComponent + masquage des lignes de remise dans ListRenderer
│               └── discount_totals.xml   # Patch OWL du template account.TaxTotalsField (ligne Remise sous Montant HT)
├── views/
│   ├── account_move_views.xml            # Bouton Remise et champs techniques sur le formulaire de facture
│   └── sale_order_views.xml              # Champs techniques sur le formulaire de devis/commande
└── wizard/
    ├── __init__.py
    ├── account_move_discount.py          # Assistant de remise sur facture (écrasement ancienne remise + ligne sans taxe)
    ├── account_move_discount_views.xml   # Vue formulaire de l'assistant de remise sur facture
    └── sale_order_discount.py            # Extension de l'assistant de remise sur devis (écrasement ancienne remise + ligne sans taxe)
```
