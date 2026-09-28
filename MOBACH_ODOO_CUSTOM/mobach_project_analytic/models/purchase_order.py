# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .analytic_project_mixin import PROJECT_DOMAIN


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_id = fields.Many2one(
        'project.project',
        domain=PROJECT_DOMAIN,
        copy=True,
        help="Projet appliqué par défaut à toutes les lignes du bon de commande. "
             "Chaque ligne reste modifiable individuellement.",
    )

    def _mobach_propagate_project_to_lines(self):
        """Repousse le projet d'en-tête sur les lignes qui n'en ont pas."""
        for order in self:
            if not order.project_id:
                continue
            lines = order.order_line.filtered(
                lambda line: not line.display_type and not line.project_id
            )
            lines.project_id = order.project_id


class PurchaseOrderLine(models.Model):
    _inherit = ['purchase.order.line', 'mobach.analytic.project.mixin']
    _name = 'purchase.order.line'

    project_id = fields.Many2one(
        'project.project',
        string='Projet',
        compute='_compute_project_id',
        store=True,
        readonly=False,
        copy=True,
        domain=PROJECT_DOMAIN,
    )
    analytic_project_id = fields.Many2one(
        'project.project',
        related='project_id',
        string='Projet analytique',
        readonly=False,
        store=True,
    )

    @api.depends('order_id.project_id')
    def _compute_project_id(self):
        for line in self:
            if line.display_type:
                line.project_id = False
            else:
                line.project_id = (
                    line.order_id.project_id or line.project_id
                )

    @api.depends('product_id', 'order_id.partner_id', 'order_id.project_id', 'project_id')
    def _compute_analytic_distribution(self):
        """Traduit le projet de la ligne en distribution analytique.

        Les `depends` de `purchase` et de `project_purchase` sont répétés : Odoo
        ne lit que ceux de la méthode la plus dérivée.
        """
        super()._compute_analytic_distribution()
        self.filtered('project_id')._mobach_sync_analytic_distribution()

    def _prepare_account_move_line(self, move=False):
        """Transmet le projet à la ligne de facture fournisseur.

        C'est ce qui alimente le volet DÉPENSES du suivi projet : sans cette
        propagation, seule la facture client serait imputée et la marge du projet
        vaudrait toujours son chiffre d'affaires.
        """
        values = super()._prepare_account_move_line(move=move)
        if self.project_id and not self.display_type:
            values['analytic_project_id'] = self.project_id.id
        return values
