# mobach_config

Module de configuration initiale multi-sociétés pour le groupe MOBACH (Odoo 19 Community).

---

## Sociétés créées

| Société | NUI | Couleur principale | Secondaire | Agencement | Activité |
|---|---|---|---|---|---|
| MOBACH SARL | M022317978287A | Bleu `#0070C0` | `#003F6B` | Bubble | Commerce général / Holding |
| NAS ET FILS SARL | M032416493739W | Bleu ciel `#00B0F0` | `#006A96` | Bubble | Commerce / Distribution |
| MOHAMADOU BACHIROU SARL | M032416493275W | Orange `#FFB347` | `#C47A00` | Boxed | Affaires personnelles SARL |
| AFRIDRIVE SARL | M032416493275W | Jaune `#FFD700` | `#B8960C` | Boxed | Transport routier / Logistique |

---

## Fonctionnalités

### 1. Sociétés & Partenaires
- Création / mise à jour des 4 sociétés avec leurs partenaires liés
- **Logos** associés depuis `static/image/` via `image_1920`
- **Couleurs primaire + secondaire** par société
- **Police** différente par société (Lato, Roboto, Open_Sans, Montserrat)
- **Agencement de document** (`Bubble` ou `Boxed`)

### 2. En-têtes & Pieds de page OHADA
Chaque société dispose de :
- `report_header` : tagline/slogan branding
- `report_footer` : mentions légales complètes (capital social, RCCM, NUI, adresse, tel, email)
- `company_details` : coordonnées complètes affichées en en-tête de documents imprimés

### 3. Plan comptable SYSCOHADA (via `post_init_hook`)
Le hook applique automatiquement le plan comptable adapté à chaque société (basé sur le pays Cameroun → SYSCOHADA).

### 4. Journaux OHADA (via `post_init_hook`)

| Code | Nom | Type | Sociétés |
|---|---|---|---|
| JV | Journal des Ventes | sale | Toutes |
| JA | Journal des Achats | purchase | Toutes |
| BQ | Banque Principale | bank | Toutes |
| CAI | Caisse | cash | Toutes |
| OD | Opérations Diverses | general | Toutes |
| AN | Journal d'À Nouveaux | general | Toutes |
| NDF | Notes de Frais | purchase | Toutes |
| FR | Frais Routiers | purchase | AFRIDRIVE uniquement |
| FAD | Facturation Transport | sale | AFRIDRIVE uniquement |

Le hook renomme les journaux par défaut créés par Odoo quand c'est possible, ou en crée de nouveaux.

### 5. Entrepôts & Flux logistiques (via `post_init_hook`)

| Société | Entrepôt | Code | Réception | Livraison |
|---|---|---|---|---|
| MOBACH SARL | Entrepôt MOBACH | MOB | 2 étapes (contrôle qualité) | 2 étapes (préparation + livraison) |
| NAS ET FILS SARL | Entrepôt NAS | NAS | 1 étape | 1 étape |
| MOHAMADOU BACHIROU SARL | Entrepôt M&B | MB | 1 étape | 1 étape |
| AFRIDRIVE SARL | Parc Transport AFRIDRIVE | AFD | 1 étape | 1 étape |

### 6. Champ ajouté
- `res.company.nui` (Char) : Numéro Unique d'Identification fiscale

---

## Modules requis (dépendances)

- `account` — Comptabilité
- `sale_management` — Ventes
- `purchase` — Achats
- `hr` — Ressources humaines
- `stock` — Stocks
- `project` — Projets
- `sale_project` — Ventes + Projets
- `l10n_syscohada` — Plan comptable SYSCOHADA (XAF)
- `muk_web_theme` — Thème MUK
- `om_account_accountant` — Comptable étendu

---

## Installation

```bash
./odoo-bin -c /path/to/odoo-mobach.conf -d <base_de_donnees> -i mobach_config --stop-after-init
```

## Mise à jour

Lors d'un `upgrade`, les données marquées `noupdate="1"` ne sont **pas** réécrasées.
Le `post_init_hook` ne tourne qu'à l'installation (pas au `upgrade`).

---

## Notes RCCM

Les numéros RCCM dans les pieds de page sont des **placeholders** à remplacer par les valeurs réelles :
- MOBACH SARL → `MA-MAR-2022-B-0001`
- NAS ET FILS SARL → `MA-MAR-2024-B-0002`
- MOHAMADOU BACHIROU SARL → `MA-MAR-2024-B-0003`
- AFRIDRIVE SARL → `MA-MAR-2024-B-0004`

Modifier directement dans Paramètres → Sociétés → Pied de page du rapport.
