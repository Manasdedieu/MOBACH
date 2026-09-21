# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import AccessError
from odoo.tools import SQL

# Types de pièces considérées comme des ventes / achats.
CUSTOMER_INVOICE_TYPES = ('out_invoice', 'out_receipt')
CUSTOMER_REFUND_TYPES = ('out_refund',)
SUPPLIER_INVOICE_TYPES = ('in_invoice', 'in_receipt')
SUPPLIER_REFUND_TYPES = ('in_refund',)

CUSTOMER_TYPES = CUSTOMER_INVOICE_TYPES + CUSTOMER_REFUND_TYPES
SUPPLIER_TYPES = SUPPLIER_INVOICE_TYPES + SUPPLIER_REFUND_TYPES
ALL_TRADE_TYPES = CUSTOMER_TYPES + SUPPLIER_TYPES

# Clés de `get_financial_kpis()` qui sont aussi des champs de res.company.
# La liste est explicite : le dictionnaire porte aussi `currency_id`, qui existe
# sur res.company mais n'est PAS calculé ici — l'affecter depuis le compute
# écraserait la devise de la société.
KPI_FIELD_NAMES = (
    'ca_realise', 'ca_encaisse_cash', 'ca_compense_avoir', 'ca_annule_perte',
    'depenses_totales', 'depenses_cash', 'depenses_compense_avoir', 'depenses_annulees',
    'marge_nette', 'marge_cash', 'marge_taux',
    'creances_brutes', 'avoirs_clients_a_imputer', 'creances_en_cours',
    'dettes_brutes', 'avoirs_fournisseurs_a_imputer', 'dettes_en_cours',
)


class ResCompany(models.Model):
    _inherit = 'res.company'

    # ------------------------------------------------------------------
    # FLUX (dépendent de la période analysée)
    # ------------------------------------------------------------------
    ca_realise = fields.Monetary(
        string="Chiffre d'Affaires Encaissé",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Montant des factures clients effectivement soldé : encaissements réels "
             "en banque/caisse + montants compensés par un avoir client (lettrage).",
    )
    ca_encaisse_cash = fields.Monetary(
        string="dont Encaissements Réels",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Argent réellement entré : paiements reçus sur factures clients, "
             "diminué des avoirs clients remboursés au client.",
    )
    ca_compense_avoir = fields.Monetary(
        string="dont Compensé par Avoir (ventes)",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Montant des factures clients soldé par lettrage avec un avoir client. "
             "Aucun mouvement de trésorerie ne correspond à ce montant.",
    )
    ca_annule_perte = fields.Monetary(
        string="CA Annulé / Passé en Perte",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Montant des factures clients soldé par une écriture diverse : créance "
             "irrécouvrable, escompte, écart de règlement. Exclu du CA encaissé.",
    )

    depenses_totales = fields.Monetary(
        string="Total Dépenses Réglées",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Montant des factures fournisseurs effectivement soldé : décaissements "
             "réels + montants compensés par un avoir fournisseur (lettrage).",
    )
    depenses_cash = fields.Monetary(
        string="dont Décaissements Réels",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Argent réellement sorti : paiements émis sur factures fournisseurs, "
             "diminué des avoirs fournisseurs remboursés par le fournisseur.",
    )
    depenses_compense_avoir = fields.Monetary(
        string="dont Compensé par Avoir (achats)",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Montant des factures fournisseurs soldé par lettrage avec un avoir "
             "fournisseur. Aucun mouvement de trésorerie ne correspond à ce montant.",
    )
    depenses_annulees = fields.Monetary(
        string="Dépenses Annulées / Abandonnées",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Montant des factures fournisseurs soldé par une écriture diverse. "
             "Exclu des dépenses réglées.",
    )

    marge_nette = fields.Monetary(
        string="Marge Nette Réalisée",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Différence entre le CA encaissé et les dépenses réglées.",
    )
    marge_taux = fields.Float(
        string="Taux de Marge (%)",
        compute='_compute_financial_kpis',
        digits=(16, 2),
        help="Ratio de la Marge Nette sur le CA encaissé, en pourcentage.",
    )
    marge_cash = fields.Monetary(
        string="Marge de Trésorerie",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Encaissements réels moins décaissements réels : le cash net généré "
             "par l'exploitation sur la période.",
    )

    # ------------------------------------------------------------------
    # ENCOURS ET TRÉSORERIE (photo à la date du jour, hors période)
    # ------------------------------------------------------------------
    creances_brutes = fields.Monetary(
        string="Factures Clients Impayées",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Restant dû sur les factures clients, avant imputation des avoirs.",
    )
    avoirs_clients_a_imputer = fields.Monetary(
        string="Avoirs Clients à Imputer",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Avoirs clients émis, ni remboursés ni encore lettrés : montant dû au client.",
    )
    creances_en_cours = fields.Monetary(
        string="Créances Clients Nettes",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Factures clients impayées diminuées des avoirs clients à imputer.",
    )

    dettes_brutes = fields.Monetary(
        string="Factures Fournisseurs Impayées",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Restant dû aux fournisseurs, avant imputation des avoirs.",
    )
    avoirs_fournisseurs_a_imputer = fields.Monetary(
        string="Avoirs Fournisseurs à Imputer",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Avoirs fournisseurs obtenus, ni remboursés ni encore lettrés : "
             "crédit encore en circulation chez le fournisseur.",
    )
    dettes_en_cours = fields.Monetary(
        string="Dettes Fournisseurs Nettes",
        currency_field='currency_id',
        compute='_compute_financial_kpis',
        help="Factures fournisseurs impayées diminuées des avoirs fournisseurs à imputer.",
    )

    def _compute_financial_kpis(self):
        """Expose les KPI sur la fiche société, sur l'intégralité de l'historique."""
        for company in self:
            kpis = company.get_financial_kpis()
            for fname in KPI_FIELD_NAMES:
                company[fname] = kpis[fname]

    # ------------------------------------------------------------------
    # MOTEUR DE CALCUL
    # ------------------------------------------------------------------
    def _check_financial_kpi_access(self):
        """Réserve la lecture des KPI aux profils comptables.

        `get_financial_kpis` agrège ensuite en sudo() : sans ce garde-fou, n'importe
        quel utilisateur pouvant lire res.company (donc tout le monde) obtiendrait
        par RPC le chiffre d'affaires de n'importe quelle société du groupe.
        """
        if self.env.su:
            return
        if not self.env.user.has_group('account.group_account_readonly') \
                and not self.env.user.has_group('account.group_account_invoice'):
            raise AccessError(_(
                "Vous n'avez pas les droits d'accès aux données financières de %s.",
                self.display_name,
            ))

    def get_financial_kpis(self, date_from=None, date_to=None):
        """Retourne les indicateurs financiers de la société.

        ── Principe de calcul ────────────────────────────────────────────────
        Les FLUX (CA encaissé, dépenses) sont reconstitués à partir des LETTRAGES
        (`account.partial.reconcile`) et non du résiduel des factures. Pour chaque
        lettrage on regarde la NATURE DE LA CONTREPARTIE :

          - paiement / relevé bancaire → encaissement (ou décaissement) réel
          - avoir de même sens         → compensation, aucun mouvement de trésorerie
          - écriture diverse (OD)      → perte, escompte, écart de règlement

        C'est indispensable : le résiduel d'une facture tombe à zéro aussi bien
        parce qu'elle a été payée que parce qu'elle a été passée en perte. Se fier
        au résiduel revient à compter une créance irrécouvrable comme du chiffre
        d'affaires encaissé.

        Chaque lettrage porte sa propre date (`max_date`), ce qui rend les KPI de
        période justes ET stables : le CA d'un mois clos ne bouge plus quand un
        règlement tombe le mois suivant. L'ancien filtre sur `invoice_date` faisait
        exactement l'inverse.

        ── Définition du CA encaissé ─────────────────────────────────────────
        CA encaissé = encaissements réels + compensations par avoir.

        Exemple de référence (validé avec la direction) : avoir client AC1 de 1 000,
        facture F1 de 2 000. Après lettrage F1/AC1, F1 a un reliquat de 1 000 et le
        CA encaissé vaut 1 000. Après règlement du reliquat, il vaut 2 000.

        Les deux composantes restent exposées séparément (`ca_encaisse_cash` et
        `ca_compense_avoir`) : la première est le cash réellement entré, la seconde
        le chiffre soldé sans mouvement de trésorerie.

        ── Périmètre ─────────────────────────────────────────────────────────
        - Flux : filtrés sur la période via la date de lettrage.
        - Encours : ce sont des STOCKS, toujours donnés à la date du jour. Un
          encours « du mois de mars » n'a pas de sens : le résiduel d'une facture
          est un état courant, pas un flux.
        - Multi-devises : `account.partial.reconcile.amount` et `balance` sont déjà
          exprimés en devise de la société ; les écarts de change sont donc pris au
          taux réel du règlement.
        - Montants TTC : ce sont des encaissements, TVA comprise.
        """
        self.ensure_one()
        self._check_financial_kpi_access()
        company = self.sudo()
        currency = company.currency_id

        flows = company._get_reconciliation_flows(date_from=date_from, date_to=date_to)
        outstanding = company._get_outstanding_amounts()

        ca_realise = flows['ca_cash'] + flows['ca_avoir']
        depenses_totales = flows['dep_cash'] + flows['dep_avoir']
        marge_nette = ca_realise - depenses_totales
        marge_cash = flows['ca_cash'] - flows['dep_cash']

        if ca_realise > 0:
            marge_taux = marge_nette / ca_realise * 100.0
        elif marge_nette < 0:
            marge_taux = -100.0
        else:
            marge_taux = 0.0

        def rnd(value):
            # `+ 0.0` normalise -0.0 en 0.0 : sans lui l'écran affiche « -0 ».
            return currency.round(value) + 0.0

        return {
            'company_id': company.id,
            'company_name': company.name,
            'currency_id': currency.id,
            'currency_symbol': currency.symbol or 'FCFA',

            'ca_realise': rnd(ca_realise),
            'ca_encaisse_cash': rnd(flows['ca_cash']),
            'ca_compense_avoir': rnd(flows['ca_avoir']),
            'ca_annule_perte': rnd(flows['ca_ecart']),

            'depenses_totales': rnd(depenses_totales),
            'depenses_cash': rnd(flows['dep_cash']),
            'depenses_compense_avoir': rnd(flows['dep_avoir']),
            'depenses_annulees': rnd(flows['dep_ecart']),

            'marge_nette': rnd(marge_nette),
            'marge_cash': rnd(marge_cash),
            'marge_taux': round(marge_taux, 2) + 0.0,

            'creances_brutes': rnd(outstanding['creances_brutes']),
            'avoirs_clients_a_imputer': rnd(outstanding['avoirs_clients']),
            'creances_en_cours': rnd(outstanding['creances_brutes'] - outstanding['avoirs_clients']),

            'dettes_brutes': rnd(outstanding['dettes_brutes']),
            'avoirs_fournisseurs_a_imputer': rnd(outstanding['avoirs_fournisseurs']),
            'dettes_en_cours': rnd(outstanding['dettes_brutes'] - outstanding['avoirs_fournisseurs']),
        }

    def _get_reconciliation_flows(self, date_from=None, date_to=None):
        """Ventile les montants lettrés par nature de contrepartie.

        Une seule requête, qui parcourt les lettrages dans les deux sens (la pièce
        analysée pouvant être au débit comme au crédit du rapprochement).
        """
        self.ensure_one()
        result = {
            'ca_cash': 0.0, 'ca_avoir': 0.0, 'ca_ecart': 0.0,
            'dep_cash': 0.0, 'dep_avoir': 0.0, 'dep_ecart': 0.0,
        }

        self.env['account.partial.reconcile'].flush_model()
        self.env['account.move'].flush_model()
        self.env['account.move.line'].flush_model()

        date_clause = SQL("")
        if date_from:
            date_clause = SQL("%s AND part.max_date >= %s", date_clause, date_from)
        if date_to:
            date_clause = SQL("%s AND part.max_date <= %s", date_clause, date_to)

        queries = []
        for source_field, counterpart_field in (
            ('debit_move_id', 'credit_move_id'),
            ('credit_move_id', 'debit_move_id'),
        ):
            queries.append(SQL(
                """
                SELECT
                    src_move.move_type AS source_type,
                    CASE
                        WHEN cp_move.origin_payment_id IS NOT NULL
                          OR cp_move.statement_line_id IS NOT NULL THEN 'cash'
                        WHEN cp_move.move_type IN ('out_refund', 'in_refund') THEN 'refund'
                        WHEN cp_move.move_type IN ('out_invoice', 'in_invoice',
                                                   'out_receipt', 'in_receipt') THEN 'invoice'
                        ELSE 'entry'
                    END AS counterpart_kind,
                    SUM(part.amount) AS amount
                FROM account_partial_reconcile part
                JOIN account_move_line src_line ON src_line.id = part.%(source)s
                JOIN account_move_line cp_line ON cp_line.id = part.%(counterpart)s
                JOIN account_account src_account ON src_account.id = src_line.account_id
                JOIN account_move src_move ON src_move.id = src_line.move_id
                JOIN account_move cp_move ON cp_move.id = cp_line.move_id
                WHERE src_move.company_id = %(company)s
                  AND src_move.state = 'posted'
                  AND src_move.move_type IN %(trade_types)s
                  AND src_account.account_type IN ('asset_receivable', 'liability_payable')
                  AND cp_line.move_id != src_line.move_id
                  %(dates)s
                GROUP BY src_move.move_type, 2
                """,
                source=SQL.identifier(source_field),
                counterpart=SQL.identifier(counterpart_field),
                company=self.id,
                trade_types=ALL_TRADE_TYPES,
                dates=date_clause,
            ))

        rows = self.env.execute_query_dict(SQL(" UNION ALL ").join(queries))

        for row in rows:
            source_type = row['source_type']
            kind = row['counterpart_kind']
            amount = row['amount'] or 0.0

            if source_type in CUSTOMER_INVOICE_TYPES:
                # Une facture client est soldée à hauteur de `amount`.
                if kind == 'cash':
                    result['ca_cash'] += amount
                elif kind == 'refund':
                    result['ca_avoir'] += amount
                else:
                    result['ca_ecart'] += amount

            elif source_type in CUSTOMER_REFUND_TYPES:
                # Un avoir client est soldé à hauteur de `amount`.
                if kind == 'cash':
                    # Avoir remboursé au client : de l'argent ressort.
                    result['ca_cash'] -= amount
                elif kind in ('invoice', 'refund'):
                    # Déjà compté du côté de la facture : ne pas compter deux fois.
                    continue
                else:
                    result['ca_ecart'] -= amount

            elif source_type in SUPPLIER_INVOICE_TYPES:
                if kind == 'cash':
                    result['dep_cash'] += amount
                elif kind == 'refund':
                    result['dep_avoir'] += amount
                else:
                    result['dep_ecart'] += amount

            elif source_type in SUPPLIER_REFUND_TYPES:
                if kind == 'cash':
                    # Avoir remboursé par le fournisseur : de l'argent rentre.
                    result['dep_cash'] -= amount
                elif kind in ('invoice', 'refund'):
                    continue
                else:
                    result['dep_ecart'] -= amount

        return result

    def _get_outstanding_amounts(self):
        """Encours à la date du jour, ventilés factures / avoirs.

        Aucun filtre sur `payment_state` : le résiduel d'une pièce soldée vaut zéro,
        il n'y a donc rien à exclure. L'ancien filtre écartait au passage les états
        `blocked` et `invoicing_legacy`, dont les reliquats disparaissaient des encours.
        """
        self.ensure_one()
        groups = self.env['account.move']._read_group(
            domain=[
                ('company_id', '=', self.id),
                ('state', '=', 'posted'),
                ('move_type', 'in', ALL_TRADE_TYPES),
            ],
            groupby=['move_type'],
            aggregates=['amount_residual_signed:sum'],
        )
        residual_by_type = {move_type: (total or 0.0) for move_type, total in groups}

        def total_for(types):
            return sum(residual_by_type.get(t, 0.0) for t in types)

        # amount_residual_signed : positif pour une créance client, négatif pour une
        # dette fournisseur. On ramène chaque indicateur à un montant positif.
        return {
            'creances_brutes': total_for(CUSTOMER_INVOICE_TYPES),
            'avoirs_clients': -total_for(CUSTOMER_REFUND_TYPES),
            'dettes_brutes': -total_for(SUPPLIER_INVOICE_TYPES),
            'avoirs_fournisseurs': total_for(SUPPLIER_REFUND_TYPES),
        }

