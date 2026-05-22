# MOBACH - Odoo 19 Custom Modules

Projet Odoo 19 contenant des modules personnalisés pour MOBACH.

## Structure du Projet

```
MOBACH/
├── mobach_addons/          # Modules Odoo personnalisés
│   └── mobach_config/      # Module de configuration
├── mobach_commun_addons/   # Modules partagés
└── .git/
```

## Tech Stack

- **Framework**: Odoo 19
- **Langage**: Python
- **Manifests Odoo**: Python dict format (`__manifest__.py`)

## Commands

- Voir fichiers de configuration: `odoo-mobach.conf` (à la racine du projet parent)
- Modules structure standard: `models/`, `views/`, `security/`, `static/`, `data/`

## Important Files

- `mobach_addons/mobach_config/__manifest__.py` - Points d'entrée des modules
- Configuration Odoo: `/home/landry/WORKSTATION/odoo19/odoo-mobach.conf`

## Rules

- **Modules Odoo**: Respecter la structure standard (models, views, security, data)
- **__manifest__.py**: Déclarer tous les modèles, vues et dépendances
- **Chemins**: Utiliser des chemins relatifs dans les modules
- **Localisation**: Suporter i18n dans les views et données

