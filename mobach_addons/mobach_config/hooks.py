# -*- coding: utf-8 -*-
"""
Post-init hook du module mobach_config.

Actions exécutées après l'installation du module :
1. Application du plan comptable SYSCOHADA (OHADA) sur chaque société
2. Création / renommage des journaux standard OHADA par société
3. Configuration des entrepôts par société (noms, flux logistiques)
"""
import logging

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Définition des journaux OHADA par type de société
# ---------------------------------------------------------------------------

# Journaux communs à toutes les sociétés commerciales (ventes + achats + stock)
JOURNALS_TRADE = [
    {
        'code': 'JV',
        'name': 'Journal des Ventes',
        'type': 'sale',
        'color': 11,  # vert
    },
    {
        'code': 'JA',
        'name': "Journal des Achats",
        'type': 'purchase',
        'color': 3,   # rouge
    },
    {
        'code': 'BQ',
        'name': 'Banque Principale',
        'type': 'bank',
        'color': 7,   # bleu
    },
    {
        'code': 'CAI',
        'name': 'Caisse',
        'type': 'cash',
        'color': 6,   # bleu clair
    },
    {
        'code': 'OD',
        'name': 'Opérations Diverses',
        'type': 'general',
        'color': 2,   # gris
    },
    {
        'code': 'AN',
        'name': "Journal d'A Nouveaux",
        'type': 'general',
        'color': 0,
    },
    {
        'code': 'NDF',
        'name': 'Notes de Frais',
        'type': 'purchase',
        'color': 4,
    },
]

# Journaux spécifiques au transport (AFRIDRIVE)
JOURNALS_TRANSPORT = JOURNALS_TRADE + [
    {
        'code': 'FR',
        'name': 'Frais Routiers',
        'type': 'purchase',
        'color': 5,  # orange
    },
    {
        'code': 'FAD',
        'name': 'Facturation Transport',
        'type': 'sale',
        'color': 10,
    },
]

# Mapping société -> journaux
COMPANY_JOURNALS = {
    'MOBACH SARL': JOURNALS_TRADE,
    'NAS ET FILS SARL': JOURNALS_TRADE,
    'MOHAMADOU BACHIROU SARL': JOURNALS_TRADE,
    'AFRIDRIVE SARL': JOURNALS_TRANSPORT,
}

# ---------------------------------------------------------------------------
# Configuration des entrepôts par société
# ---------------------------------------------------------------------------
WAREHOUSE_CONFIG = {
    'MOBACH SARL': {
        'name': 'Entrepôt MOBACH',
        'code': 'MOB',
        'reception_steps': 'two_steps',   # Réception en 2 étapes : BL + BL interne
        'delivery_steps': 'pick_ship',    # Livraison en 2 étapes : préparation + livraison
    },
    'NAS ET FILS SARL': {
        'name': 'Entrepôt NAS',
        'code': 'NAS',
        'reception_steps': 'one_step',    # Réception directe (structure simple)
        'delivery_steps': 'ship_only',    # Livraison directe
    },
    'MOHAMADOU BACHIROU SARL': {
        'name': 'Entrepôt M&B',
        'code': 'MB',
        'reception_steps': 'one_step',
        'delivery_steps': 'ship_only',
    },
    'AFRIDRIVE SARL': {
        'name': 'Parc Transport AFRIDRIVE',
        'code': 'AFD',
        'reception_steps': 'one_step',    # Pas de stock physique complexe (transport)
        'delivery_steps': 'ship_only',    # Départ direct
    },
}


def _load_french_language(env):
    """
    Active et charge la langue française (fr_FR) si elle n'est pas encore active.
    La définit ensuite comme langue par défaut pour tous les utilisateurs et partenaires.
    """
    LANG_CODE = 'fr_FR'

    # Active la langue (crée l'entrée res.lang si absente)
    lang = env['res.lang']._activate_lang(LANG_CODE)
    if not lang:
        _logger.warning("  Langue '%s' introuvable dans Odoo, chargement ignoré.", LANG_CODE)
        return

    _logger.info("  Langue '%s' activée avec succès.", LANG_CODE)

    # Charge les traductions depuis le fichier .po du module base
    try:
        env['ir.translation'].load_module_terms(['base'], [LANG_CODE])
        _logger.info("  Traductions de base '%s' chargées.", LANG_CODE)
    except Exception as e:
        _logger.warning("  Impossible de charger les traductions base pour '%s' : %s", LANG_CODE, e)

    # Applique le français à tous les utilisateurs internes existants
    users = env['res.users'].search([('share', '=', False)])
    users.write({'lang': LANG_CODE})
    _logger.info("  Langue '%s' définie sur %d utilisateur(s).", LANG_CODE, len(users))

    # Applique aussi aux partenaires déjà créés (sociétés, contacts)
    env['res.partner'].search([]).write({'lang': LANG_CODE})
    _logger.info("  Langue '%s' propagée aux partenaires.", LANG_CODE)


def post_init_hook(env):
    """
    Hook exécuté après l'installation du module mobach_config.
    1. Chargement de la langue française par défaut
    2. Applique le plan comptable SYSCOHADA et configure journaux + entrepôts
       pour chaque société du groupe MOBACH.
    """
    _logger.info("=== MOBACH : début de la configuration post-installation ===")

    # 0. Langue française par défaut
    _logger.info("--- Chargement de la langue française (fr_FR) ---")
    _load_french_language(env)

    # Récupère les 4 sociétés MOBACH par leur XML ID
    company_refs = {
        'MOBACH SARL': env.ref('base.main_company', raise_if_not_found=False),
        'NAS ET FILS SARL': env.ref('mobach_config.company_nas_et_fils', raise_if_not_found=False),
        'MOHAMADOU BACHIROU SARL': env.ref('mobach_config.company_mohamadou_bachirou', raise_if_not_found=False),
        'AFRIDRIVE SARL': env.ref('mobach_config.company_afridrive', raise_if_not_found=False),
    }

    for company_name, company in company_refs.items():
        if not company:
            _logger.warning("MOBACH Hook : société '%s' introuvable, ignorée.", company_name)
            continue

        _logger.info("--- Configuration de : %s ---", company.name)

        # 1. Appliquer le plan comptable SYSCOHADA si pas encore fait
        _apply_chart_template(env, company)

        # 2. Créer / renommer les journaux OHADA
        journals_def = COMPANY_JOURNALS.get(company_name, JOURNALS_TRADE)
        _setup_journals(env, company, journals_def)

        # 3. Configurer l'entrepôt
        wh_config = WAREHOUSE_CONFIG.get(company_name, {})
        if wh_config:
            _setup_warehouse(env, company, wh_config)

    _logger.info("=== MOBACH : configuration post-installation terminée ===")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_chart_template(env, company):
    """
    Applique le plan comptable SYSCOHADA (via le code template du pays) sur
    la société si aucun plan n'est encore défini.
    On utilise _load() directement pour contourner la restriction de try_loading()
    sur le template 'syscohada' (qui lève UserError quand appelé directement).
    """
    if company.chart_template:
        _logger.info("  Plan comptable déjà appliqué (%s), skip.", company.chart_template)
        return

    # Détermine le template adapté au pays (Cameroun → 'cm' or 'syscohada')
    chart_tmpl_env = env['account.chart.template']
    template_code = chart_tmpl_env._guess_chart_template(company.country_id)

    if not template_code:
        _logger.warning("  Aucun template trouvé pour %s, skip.", company.name)
        return

    try:
        _logger.info("  Application du plan comptable '%s' sur %s...", template_code, company.name)
        chart_tmpl_env.with_context(
            default_company_id=company.id,
            allowed_company_ids=[company.id],
            tracking_disable=True,
        )._load(template_code, company, install_demo=False)
        _logger.info("  Plan comptable appliqué avec succès.")
    except Exception as e:
        _logger.warning("  Impossible d'appliquer le plan comptable sur %s : %s", company.name, str(e))


def _setup_journals(env, company, journals_def):
    """
    Pour chaque définition de journal :
    - Cherche un journal existant du même type
    - S'il existe et n'a pas encore le bon code OHADA → le renomme
    - Sinon crée un nouveau journal

    Les journaux généraux de type 'AN' (À Nouveaux) sont créés s'ils n'existent pas.
    """
    Journal = env['account.journal']

    for jdef in journals_def:
        code = jdef['code']
        name = jdef['name']
        jtype = jdef['type']
        color = jdef.get('color', 0)

        # Cherche d'abord par code exact dans cette société
        existing = Journal.with_context(
            default_company_id=company.id
        ).search([
            ('company_id', '=', company.id),
            ('code', '=', code),
        ], limit=1)

        if existing:
            _logger.info("  Journal '%s' déjà existant (%s), skip.", code, company.name)
            continue

        # Cherche un journal du même type qu'on peut renommer
        # (seulement pour les types uniques : sale, purchase, bank, cash)
        renamed = False
        if jtype in ('sale', 'bank', 'cash') and code in ('JV', 'BQ', 'CAI'):
            candidate = Journal.search([
                ('company_id', '=', company.id),
                ('type', '=', jtype),
            ], limit=1)
            if candidate and candidate.code not in [j['code'] for j in journals_def if j != jdef]:
                _logger.info(
                    "  Renommage journal '%s' → '%s / %s' chez %s",
                    candidate.code, code, name, company.name
                )
                candidate.write({'code': code, 'name': name, 'color': color})
                renamed = True

        if not renamed:
            # Récupère les comptes par défaut selon le type
            default_account = _get_default_account(env, company, jtype, code)
            vals = {
                'name': name,
                'code': code,
                'type': jtype,
                'company_id': company.id,
                'color': color,
                'show_on_dashboard': code in ('JV', 'JA', 'BQ', 'CAI'),
            }
            if default_account:
                vals['default_account_id'] = default_account.id

            try:
                Journal.create(vals)
                _logger.info("  Journal '%s (%s)' créé pour %s.", name, code, company.name)
            except Exception as e:
                _logger.warning(
                    "  Impossible de créer le journal '%s' pour %s : %s",
                    code, company.name, str(e)
                )


def _get_default_account(env, company, jtype, code):
    """
    Retourne le compte comptable SYSCOHADA par défaut selon le type de journal.
    Les codes sont issus du Plan Comptable OHADA.
    """
    Account = env['account.account']
    account_code_map = {
        'sale':     ['701', '706', '707'],   # Ventes de marchandises/prestations
        'purchase': ['601', '604', '613'],   # Achats de marchandises/services
        'bank':     ['521'],                  # Banques
        'cash':     ['571'],                  # Caisses
        'general':  ['471'],                  # Divers
    }

    if code == 'AN':    # À Nouveaux → pas de compte par défaut
        return None
    if code == 'FR':    # Frais Routiers → charges transport
        codes_to_try = ['6241', '624']
    elif code == 'FAD': # Facturation transport → produits transport
        codes_to_try = ['7071', '707']
    elif code == 'NDF': # Notes de frais → charges personnel
        codes_to_try = ['6251', '625']
    else:
        codes_to_try = account_code_map.get(jtype, [])

    for code_prefix in codes_to_try:
        account = Account.search([
            ('company_ids', 'in', [company.id]),
            ('code', 'like', code_prefix + '%'),
        ], limit=1)
        if account:
            return account
    return None


def _setup_warehouse(env, company, wh_config):
    """
    Configure l'entrepôt automatiquement créé par le module stock pour la société.
    Si l'entrepôt n'a pas encore le bon nom/code OHADA, on le met à jour.
    On configure aussi les étapes de réception et livraison.
    """
    Warehouse = env['stock.warehouse']

    warehouse = Warehouse.search([
        ('company_id', '=', company.id),
    ], limit=1)

    if not warehouse:
        _logger.info("  Aucun entrepôt trouvé pour %s, création...", company.name)
        try:
            Warehouse.create({
                'name': wh_config['name'],
                'code': wh_config['code'],
                'company_id': company.id,
                'reception_steps': wh_config.get('reception_steps', 'one_step'),
                'delivery_steps': wh_config.get('delivery_steps', 'ship_only'),
            })
            _logger.info("  Entrepôt '%s' créé.", wh_config['name'])
        except Exception as e:
            _logger.warning("  Impossible de créer l'entrepôt pour %s : %s", company.name, str(e))
        return

    # Met à jour le nom et les étapes logistiques si nécessaire
    update_vals = {}
    if warehouse.name != wh_config['name']:
        update_vals['name'] = wh_config['name']
    if warehouse.reception_steps != wh_config.get('reception_steps'):
        update_vals['reception_steps'] = wh_config['reception_steps']
    if warehouse.delivery_steps != wh_config.get('delivery_steps'):
        update_vals['delivery_steps'] = wh_config['delivery_steps']

    if update_vals:
        try:
            warehouse.write(update_vals)
            _logger.info(
                "  Entrepôt '%s' mis à jour : %s",
                warehouse.name, list(update_vals.keys())
            )
        except Exception as e:
            _logger.warning(
                "  Impossible de mettre à jour l'entrepôt de %s : %s",
                company.name, str(e)
            )
    else:
        _logger.info("  Entrepôt '%s' déjà configuré.", warehouse.name)

