# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

# Types de comptes SYSCOHADA qui constituent le chiffre d'affaires (classe 7)
# et les charges (classe 6), tels que typés par Odoo.
REVENUE_ACCOUNT_TYPES = ('income', 'income_other')
EXPENSE_ACCOUNT_TYPES = ('expense', 'expense_depreciation', 'expense_direct_cost')


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # ------------------------------------------------------------------
    # SUIVI FINANCIER & ANALYTIQUE (TRÉSORERIE & ENCOURS)
    # ------------------------------------------------------------------
    mobach_invoiced_revenue = fields.Monetary(
        string='CA Facturé (TTC)',
        currency_field='mobach_currency_id',
        compute='_compute_mobach_analytic_totals',
        help="Montant total TTC facturé aux clients pour ce projet.",
    )
    mobach_revenue = fields.Monetary(
        string='CA Encaissé (TTC)',
        currency_field='mobach_currency_id',
        compute='_compute_mobach_analytic_totals',
        help="Montant total TTC encaissé (paiements clients effectifs) alloué à ce projet "
             "selon la règle de répartition séquentielle (cascade).",
    )
    mobach_customer_encours = fields.Monetary(
        string='Encours Client (Reste à percevoir)',
        currency_field='mobach_currency_id',
        compute='_compute_mobach_analytic_totals',
        help="Montant TTC facturé au client en attente de paiement (reste à percevoir). "
             "Formule : CA Facturé TTC - CA Encaissé TTC.",
    )
    mobach_collection_rate = fields.Float(
        string="Taux de Recouvrement",
        compute='_compute_mobach_analytic_totals',
        help="Ratio CA Encaissé TTC / CA Facturé TTC (taux de recouvrement client).",
    )
    mobach_invoiced_expense = fields.Monetary(
        string='Dépenses Facturées (TTC)',
        currency_field='mobach_currency_id',
        compute='_compute_mobach_analytic_totals',
        help="Montant total TTC facturé par les fournisseurs pour ce projet.",
    )
    mobach_expense = fields.Monetary(
        string='Dépenses Décaissées (TTC)',
        currency_field='mobach_currency_id',
        compute='_compute_mobach_analytic_totals',
        help="Montant total TTC décaissé (règlements fournisseurs effectués) alloué à ce projet "
             "selon la règle de répartition séquentielle (cascade).",
    )
    mobach_vendor_encours = fields.Monetary(
        string='Encours Fournisseur (Reste à payer)',
        currency_field='mobach_currency_id',
        compute='_compute_mobach_analytic_totals',
        help="Montant facturé par les fournisseurs en attente de règlement (reste à payer). "
             "Formule : Dépenses Facturées TTC - Dépenses Décaissées TTC.",
    )
    mobach_margin = fields.Monetary(
        string='Marge Réalisée (Trésorerie)',
        currency_field='mobach_currency_id',
        compute='_compute_mobach_analytic_totals',
        help="Marge nette de trésorerie du projet : CA Encaissé TTC diminué des Dépenses Décaissées TTC. "
             "Pour le projet Générique, la marge est fixée à 0.",
    )
    mobach_margin_rate = fields.Float(
        string="Taux de Marge",
        compute='_compute_mobach_analytic_totals',
        help="Ratio Marge Réalisée / CA Encaissé TTC du projet.",
    )
    mobach_profitability_status = fields.Selection(
        [
            ('profitable', 'Rentable'),
            ('loss', 'Déficitaire'),
            ('neutral', 'Sans mouvement'),
        ],
        string='Santé Financière',
        compute='_compute_mobach_analytic_totals',
        help="Indicateur de rentabilité basé sur la marge réalisée du projet.",
    )
    mobach_analytic_line_count = fields.Integer(
        string='Écritures Analytiques',
        compute='_compute_mobach_analytic_totals',
    )
    mobach_customer_invoice_count = fields.Integer(
        string='Factures Clients',
        compute='_compute_mobach_analytic_totals',
    )
    mobach_vendor_bill_count = fields.Integer(
        string='Factures Fournisseurs',
        compute='_compute_mobach_analytic_totals',
    )
    mobach_delivery_picking_count = fields.Integer(
        string='Bons de Livraison',
        compute='_compute_mobach_analytic_totals',
    )
    mobach_receipt_picking_count = fields.Integer(
        string='Bons de Réception',
        compute='_compute_mobach_analytic_totals',
    )
    mobach_currency_id = fields.Many2one(
        'res.currency',
        compute='_compute_mobach_currency_id',
        string='Devise du Suivi',
    )

    # XML IDs des 4 projets génériques définis dans data/project_data.xml (noupdate=1)
    GENERIC_PROJECT_XMLIDS = (
        'mobach_project_analytic.project_generic_mobach',
        'mobach_project_analytic.project_generic_nas_et_fils',
        'mobach_project_analytic.project_generic_mohamadou_bachirou',
        'mobach_project_analytic.project_generic_afridrive',
    )

    @api.depends('company_id')
    def _compute_mobach_currency_id(self):
        for project in self:
            project.mobach_currency_id = (project.company_id or self.env.company).currency_id

    @api.model
    def _mobach_get_generic_projects_by_company(self):
        """Retourne un dictionnaire {company_id: generic_project_id} à partir des XML IDs de data/project_data.xml."""
        mapping = {}
        for xmlid in self.GENERIC_PROJECT_XMLIDS:
            proj = self.env.ref(xmlid, raise_if_not_found=False)
            if proj and proj.exists():
                proj_sudo = proj.sudo()
                if proj_sudo.company_id:
                    mapping[proj_sudo.company_id.id] = proj_sudo.id
        return mapping

    @api.model
    def _mobach_get_generic_project(self, company=None):
        """Retourne le projet Générique de la société passée en paramètre (ou de la société active)."""
        target_company = company or self.env.company
        mapping = self._mobach_get_generic_projects_by_company()
        gen_id = mapping.get(target_company.id)
        return self.browse(gen_id) if gen_id else self.browse()

    def _compute_mobach_analytic_totals(self):
        """Calcule le CA Encaissé (TTC), l'Encours Client, les Dépenses Décaissées (TTC),
        l'Encours Fournisseur et la Marge Réalisée par projet.

        Règles métier :
        1. Base TTC : Les encaissements et décaissements sont suivis sur les montants TTC
           des lignes de facturation.
        2. Cascade séquentielle (FIFO) :
           - Les paiements d'une facture s'imputent ligne par ligne dans l'ordre de la facture.
           - Les lignes affectées à un projet spécifique sont traitées en priorité.
           - Les lignes sans projet (ou affectées au projet Générique de la société) sont traitées
             en dernier et ventilées sur le projet « Générique - <Nom de la Société> » de la pièce.
        3. Projet Générique par société :
           - Chaque société possède son propre projet « Générique - <Nom de la Société> ».
           - Il réceptionne uniquement les lignes sans projet de SA société.
        4. Encours :
           - Encours Client = CA Facturé TTC - CA Encaissé TTC (reste à percevoir).
           - Encours Fournisseur = Dépenses Facturées TTC - Dépenses Décaissées TTC (reste à payer).
        """
        generic_by_company = self._mobach_get_generic_projects_by_company()
        all_generic_ids = set(generic_by_company.values())

        totals = {
            project.id: {
                'invoiced_revenue': 0.0,
                'revenue': 0.0,
                'customer_encours': 0.0,
                'invoiced_expense': 0.0,
                'expense': 0.0,
                'vendor_encours': 0.0,
                'analytic_count': 0,
                'customer_invoices': set(),
                'vendor_bills': set(),
                'delivery_pickings': set(),
                'receipt_pickings': set(),
            }
            for project in self
        }

        # 1. Compter les écritures analytiques standard
        accounts = self.mapped('account_id')
        if accounts:
            analytic_groups = self.env['account.analytic.line']._read_group(
                domain=[('account_id', 'in', accounts.ids)],
                groupby=['account_id'],
                aggregates=['__count'],
            )
            account_to_project = {p.account_id.id: p.id for p in self if p.account_id}
            for account, count in analytic_groups:
                pid = account_to_project.get(account.id)
                if pid and pid in totals:
                    totals[pid]['analytic_count'] = count

        # 2. Rechercher les factures clients et fournisseurs impactant les projets demandés
        generic_company_ids = [
            cid for cid, gid in generic_by_company.items() if gid in totals
        ]
        project_ids = self.ids

        domain_move_lines = [
            ('move_id.state', '=', 'posted'),
            ('display_type', 'not in', ('line_section', 'line_note', 'line_subsection')),
        ]
        if generic_company_ids:
            domain_move_lines.extend([
                '|',
                ('analytic_project_id', 'in', project_ids),
                '&',
                ('analytic_project_id', '=', False),
                ('company_id', 'in', generic_company_ids),
            ])
        else:
            domain_move_lines.append(('analytic_project_id', 'in', project_ids))

        move_lines = self.env['account.move.line'].search(domain_move_lines)
        moves = move_lines.mapped('move_id')

        # Traitement facture par facture avec l'algorithme cascade
        for move in moves:
            move_type = move.move_type
            if move_type not in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'entry'):
                continue

            move_generic_id = generic_by_company.get(move.company_id.id)

            if move_type == 'entry':
                # Opérations diverses / Écritures manuelles
                for line in move.line_ids.filtered(lambda l: l.display_type in (False, 'product')):
                    proj_id = line.analytic_project_id.id or (move_generic_id if not line.analytic_project_id else None)
                    if proj_id in all_generic_ids and move_generic_id:
                        proj_id = move_generic_id
                    if proj_id not in totals:
                        continue
                    if line.account_id.internal_group == 'income':
                        amt = -line.balance
                        totals[proj_id]['invoiced_revenue'] += amt
                        totals[proj_id]['revenue'] += amt
                    elif line.account_id.internal_group == 'expense':
                        amt = line.balance
                        totals[proj_id]['invoiced_expense'] += amt
                        totals[proj_id]['expense'] += amt
                continue

            is_sale = move_type in ('out_invoice', 'out_refund')
            is_refund = move_type in ('out_refund', 'in_refund')
            sign = -1.0 if is_refund else 1.0

            total_ttc = move.amount_total
            residual = move.amount_residual
            paid_total = max(0.0, min(total_ttc - residual, total_ttc))

            invoice_lines = move.invoice_line_ids.filtered(lambda l: l.display_type in (False, 'product'))
            if not invoice_lines:
                continue

            # Tri séquentiel cascade :
            # Les lignes affectées à un projet spécifique passent d'abord (sequence, id),
            # les lignes sans projet ou du projet Générique passent en dernier.
            sorted_lines = sorted(
                invoice_lines,
                key=lambda l: (
                    1 if (not l.analytic_project_id or l.analytic_project_id.id in all_generic_ids) else 0,
                    l.sequence,
                    l.id,
                )
            )

            remaining_payment = paid_total

            for line in sorted_lines:
                line_proj_id = line.analytic_project_id.id or move_generic_id
                if line_proj_id in all_generic_ids and move_generic_id:
                    line_proj_id = move_generic_id
                line_target = line.price_total

                allocated_paid = min(line_target, remaining_payment)
                remaining_payment = max(0.0, remaining_payment - allocated_paid)
                line_encours = max(0.0, line_target - allocated_paid)

                if line_proj_id not in totals:
                    continue

                proj_record = self.browse(line_proj_id)
                proj_currency = proj_record.mobach_currency_id or move.company_currency_id
                if move.currency_id != proj_currency:
                    rate_date = move.date or fields.Date.context_today(move)
                    allocated_paid_conv = move.currency_id._convert(allocated_paid, proj_currency, move.company_id, rate_date)
                    line_target_conv = move.currency_id._convert(line_target, proj_currency, move.company_id, rate_date)
                    line_encours_conv = move.currency_id._convert(line_encours, proj_currency, move.company_id, rate_date)
                else:
                    allocated_paid_conv = allocated_paid
                    line_target_conv = line_target
                    line_encours_conv = line_encours

                bucket = totals[line_proj_id]
                if is_sale:
                    bucket['invoiced_revenue'] += sign * line_target_conv
                    bucket['revenue'] += sign * allocated_paid_conv
                    bucket['customer_encours'] += sign * line_encours_conv
                    bucket['customer_invoices'].add(move.id)
                else:
                    bucket['invoiced_expense'] += sign * line_target_conv
                    bucket['expense'] += sign * allocated_paid_conv
                    bucket['vendor_encours'] += sign * line_encours_conv
                    bucket['vendor_bills'].add(move.id)

        # 2b. Rechercher les Bons de Livraison (clients) et Bons de Réception (fournisseurs) liés aux projets
        domain_sale_moves = [
            ('picking_id', '!=', False),
            ('picking_id.picking_type_code', '=', 'outgoing'),
            ('state', '!=', 'cancel'),
        ]
        if generic_company_ids:
            domain_sale_moves.extend([
                '|',
                ('sale_line_id.project_id', 'in', project_ids),
                '&',
                '&', ('sale_line_id', '!=', False), ('sale_line_id.project_id', '=', False),
                ('company_id', 'in', generic_company_ids),
            ])
        else:
            domain_sale_moves.append(('sale_line_id.project_id', 'in', project_ids))

        for sm in self.env['stock.move'].search(domain_sale_moves):
            pid = sm.sale_line_id.project_id.id or generic_by_company.get(sm.company_id.id)
            if pid in all_generic_ids:
                pid = generic_by_company.get(sm.company_id.id, pid)
            if pid in totals and sm.picking_id:
                totals[pid]['delivery_pickings'].add(sm.picking_id.id)

        domain_purchase_moves = [
            ('picking_id', '!=', False),
            ('picking_id.picking_type_code', '=', 'incoming'),
            ('state', '!=', 'cancel'),
        ]
        if generic_company_ids:
            domain_purchase_moves.extend([
                '|',
                ('purchase_line_id.project_id', 'in', project_ids),
                '&',
                '&', ('purchase_line_id', '!=', False), ('purchase_line_id.project_id', '=', False),
                ('company_id', 'in', generic_company_ids),
            ])
        else:
            domain_purchase_moves.append(('purchase_line_id.project_id', 'in', project_ids))

        for sm in self.env['stock.move'].search(domain_purchase_moves):
            pid = sm.purchase_line_id.project_id.id or generic_by_company.get(sm.company_id.id)
            if pid in all_generic_ids:
                pid = generic_by_company.get(sm.company_id.id, pid)
            if pid in totals and sm.picking_id:
                totals[pid]['receipt_pickings'].add(sm.picking_id.id)

        # 3. Affectation des valeurs aux projets
        for project in self:
            bucket = totals[project.id]
            currency = project.mobach_currency_id

            inv_rev = currency.round(bucket['invoiced_revenue']) if currency else bucket['invoiced_revenue']
            rev = currency.round(bucket['revenue']) if currency else bucket['revenue']
            cust_encours = currency.round(bucket['customer_encours']) if currency else bucket['customer_encours']

            inv_exp = currency.round(bucket['invoiced_expense']) if currency else bucket['invoiced_expense']
            exp = currency.round(bucket['expense']) if currency else bucket['expense']
            vend_encours = currency.round(bucket['vendor_encours']) if currency else bucket['vendor_encours']

            # Élimination des bruits résiduels d'arrondi
            if abs(cust_encours) < 0.001:
                cust_encours = 0.0
            if abs(vend_encours) < 0.001:
                vend_encours = 0.0

            project.mobach_invoiced_revenue = inv_rev
            project.mobach_revenue = rev
            project.mobach_customer_encours = cust_encours
            project.mobach_collection_rate = (rev / inv_rev) if inv_rev > 0 else 0.0

            project.mobach_invoiced_expense = inv_exp
            project.mobach_expense = exp
            project.mobach_vendor_encours = vend_encours

            project.mobach_analytic_line_count = bucket['analytic_count']
            project.mobach_customer_invoice_count = len(bucket['customer_invoices'])
            project.mobach_vendor_bill_count = len(bucket['vendor_bills'])
            project.mobach_delivery_picking_count = len(bucket['delivery_pickings'])
            project.mobach_receipt_picking_count = len(bucket['receipt_pickings'])


            margin = rev - exp
            project.mobach_margin = margin
            project.mobach_margin_rate = (margin / rev) if rev else 0.0
            if rev or exp:
                project.mobach_profitability_status = 'profitable' if margin > 0 else ('loss' if margin < 0 else 'neutral')
            else:
                project.mobach_profitability_status = 'neutral'

    # ------------------------------------------------------------------
    # COMPTE ANALYTIQUE AUTOMATIQUE
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        projects._mobach_ensure_analytic_account()
        return projects

    def _mobach_ensure_analytic_account(self):
        """Dote d'un compte analytique les projets qui n'en ont pas."""
        to_create = self.filtered(lambda p: not p.account_id and not p.is_template)
        if to_create:
            to_create._create_analytic_account()
        return to_create

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------
    def action_mobach_view_analytic_lines(self):
        """Ouvre les écritures analytiques imputées au projet."""
        self.ensure_one()
        return {
            'name': _('Écritures analytiques — %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'view_mode': 'list,pivot,graph,form',
            'domain': [('account_id', '=', self.account_id.id)],
            'context': {
                'search_default_group_by_general_account': 1,
                'default_account_id': self.account_id.id,
            },
        }

    def action_mobach_view_customer_invoices(self):
        """Ouvre les factures clients imputées au projet."""
        self.ensure_one()
        all_generic_ids = set(self._mobach_get_generic_projects_by_company().values())
        is_generic = (self.id in all_generic_ids)

        domain = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
        ]
        if is_generic:
            if self.company_id:
                domain.append(('company_id', '=', self.company_id.id))
            domain += [
                '|',
                ('invoice_line_ids.analytic_project_id', '=', self.id),
                ('invoice_line_ids.analytic_project_id', '=', False),
            ]
        else:
            domain += [('invoice_line_ids.analytic_project_id', '=', self.id)]

        return {
            'name': _('Factures Clients — %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'default_move_type': 'out_invoice'},
        }

    def action_mobach_view_vendor_bills(self):
        """Ouvre les factures fournisseurs imputées au projet."""
        self.ensure_one()
        all_generic_ids = set(self._mobach_get_generic_projects_by_company().values())
        is_generic = (self.id in all_generic_ids)

        domain = [
            ('move_type', 'in', ('in_invoice', 'in_refund')),
        ]
        if is_generic:
            if self.company_id:
                domain.append(('company_id', '=', self.company_id.id))
            domain += [
                '|',
                ('invoice_line_ids.analytic_project_id', '=', self.id),
                ('invoice_line_ids.analytic_project_id', '=', False),
            ]
        else:
            domain += [('invoice_line_ids.analytic_project_id', '=', self.id)]

        return {
            'name': _('Factures Fournisseurs — %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'default_move_type': 'in_invoice'},
        }

    def action_mobach_view_delivery_pickings(self):
        """Ouvre les Bons de Livraison clients liés au projet."""
        self.ensure_one()
        all_generic_ids = set(self._mobach_get_generic_projects_by_company().values())
        is_generic = (self.id in all_generic_ids)

        domain_moves = [
            ('picking_id', '!=', False),
            ('picking_id.picking_type_code', '=', 'outgoing'),
            ('state', '!=', 'cancel'),
        ]
        if is_generic:
            if self.company_id:
                domain_moves.append(('company_id', '=', self.company_id.id))
            domain_moves += [
                '|',
                ('sale_line_id.project_id', '=', self.id),
                '&', ('sale_line_id', '!=', False), ('sale_line_id.project_id', '=', False),
            ]
        else:
            domain_moves += [('sale_line_id.project_id', '=', self.id)]

        picking_ids = self.env['stock.move'].search(domain_moves).mapped('picking_id').ids
        return {
            'name': _('Bons de Livraison Clients — %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', picking_ids)],
            'context': {'create': False},
        }

    def action_mobach_view_receipt_pickings(self):
        """Ouvre les Bons de Réception fournisseurs liés au projet."""
        self.ensure_one()
        all_generic_ids = set(self._mobach_get_generic_projects_by_company().values())
        is_generic = (self.id in all_generic_ids)

        domain_moves = [
            ('picking_id', '!=', False),
            ('picking_id.picking_type_code', '=', 'incoming'),
            ('state', '!=', 'cancel'),
        ]
        if is_generic:
            if self.company_id:
                domain_moves.append(('company_id', '=', self.company_id.id))
            domain_moves += [
                '|',
                ('purchase_line_id.project_id', '=', self.id),
                '&', ('purchase_line_id', '!=', False), ('purchase_line_id.project_id', '=', False),
            ]
        else:
            domain_moves += [('purchase_line_id.project_id', '=', self.id)]

        picking_ids = self.env['stock.move'].search(domain_moves).mapped('picking_id').ids
        return {
            'name': _('Bons de Réception Fournisseurs — %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', picking_ids)],
            'context': {'create': False},
        }

    def action_mobach_view_margin_report(self):
        """Ouvre le tableau croisé de rentabilité, cadré sur ce projet."""
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'mobach_project_analytic.action_mobach_project_margin_report'
        )
        action['display_name'] = _('Rentabilité — %s', self.name)
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {'search_default_group_project': 1}
        return action

    def action_mobach_create_analytic_account(self):
        """Crée le compte analytique manquant depuis la fiche projet."""
        created = self._mobach_ensure_analytic_account()
        return bool(created)
