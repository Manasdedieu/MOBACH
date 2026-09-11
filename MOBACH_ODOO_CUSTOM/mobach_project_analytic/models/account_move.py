# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .analytic_project_mixin import PROJECT_DOMAIN


class AccountMove(models.Model):
    _inherit = 'account.move'

    analytic_project_id = fields.Many2one(
        'project.project',
        string='Projet analytique',
        domain=PROJECT_DOMAIN,
        copy=True,
        tracking=True,
        help="Projet appliqué par défaut aux lignes de la pièce. Chaque ligne "
             "reste modifiable individuellement.",
    )
    project_id = fields.Many2one(
        'project.project',
        related='analytic_project_id',
        string='Projet',
        readonly=False,
        store=True,
    )

    def action_mobach_apply_project_to_lines(self):
        """Force le projet d'en-tête sur TOUTES les lignes de la pièce.

        Le calcul automatique respecte les lignes déjà affectées ; ce bouton sert
        au cas inverse — reprendre une pièce dont les lignes portent un projet
        devenu faux et tout réaligner d'un coup.
        """
        for move in self:
            lines = move.line_ids.filtered(
                lambda line: line.account_id.internal_group in ('income', 'expense')
            )
            lines.analytic_project_id = move.analytic_project_id
        return True


class AccountMoveLine(models.Model):
    _inherit = ['account.move.line', 'mobach.analytic.project.mixin']
    _name = 'account.move.line'

    analytic_project_id = fields.Many2one(
        'project.project',
        string='Projet analytique',
        domain=PROJECT_DOMAIN,
        compute='_compute_analytic_project_id',
        store=True,
        readonly=False,
    )
    project_id = fields.Many2one(
        'project.project',
        related='analytic_project_id',
        string='Projet',
        readonly=False,
        store=True,
    )

    @api.depends('move_id.analytic_project_id', 'account_id')
    def _compute_analytic_project_id(self):
        """Hérite du projet d'en-tête, sans écraser un choix explicite.

        L'héritage ne vise QUE les lignes de gestion — comptes de produits et de
        charges. Une écriture équilibrée porte toujours sa contrepartie de bilan
        (TVA, tiers, banque) : la lui imputer aussi créerait deux lignes
        analytiques de signe opposé, un bruit qui ne change pas les totaux mais
        rend le détail du projet illisible. Rien n'empêche d'affecter une ligne
        de bilan à la main si le cas l'exige.
        """
        for line in self:
            project = line.analytic_project_id
            if line.display_type in ('line_section', 'line_subsection', 'line_note'):
                project = self.env['project.project']
            elif line.account_id.internal_group in ('income', 'expense'):
                project = line.move_id.analytic_project_id or project
            line.analytic_project_id = project

    @api.depends('account_id', 'partner_id', 'product_id', 'analytic_project_id')
    def _compute_analytic_distribution(self):
        """Traduit le projet de la ligne en distribution analytique.

        Le parent ne calcule que les lignes de produit d'une facture et toutes
        les lignes d'une pièce qui n'en est pas une (opérations diverses). La
        synchronisation, elle, s'applique à toute ligne portant un projet : c'est
        ce qui permet d'imputer une OD, une écriture de paie ou une dotation.
        """
        super()._compute_analytic_distribution()
        self.filtered('analytic_project_id')._mobach_sync_analytic_distribution()
