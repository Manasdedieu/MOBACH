# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .analytic_project_mixin import PROJECT_DOMAIN


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_id = fields.Many2one(
        'project.project',
        domain=PROJECT_DOMAIN,
        copy=True,
        help="Projet appliqué par défaut à toutes les lignes de la commande. "
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


class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line', 'mobach.analytic.project.mixin']
    _name = 'sale.order.line'

    project_id = fields.Many2one(
        'project.project',
        compute='_compute_project_id',
        store=True,
        readonly=False,
        copy=True,
        domain=PROJECT_DOMAIN,
    )

    @api.depends('order_id.project_id')
    def _compute_project_id(self):
        """Hérite du projet d'en-tête, sans écraser un choix explicite.

        Champ calculé stocké et modifiable : la valeur saisie à la main tient,
        jusqu'à ce que le projet d'en-tête change — la ligne suit alors la
        commande, comme le fait Odoo pour le reste des champs de ligne.
        """
        for line in self:
            if line.display_type:
                line.project_id = False
            else:
                line.project_id = (
                    line.order_id.project_id or line.project_id
                )

    @api.depends('order_id.partner_id', 'product_id', 'order_id.project_id', 'project_id')
    def _compute_analytic_distribution(self):
        """Traduit le projet de la ligne en distribution analytique.

        Les `depends` du parent sont répétés : Odoo lit ceux de la méthode la
        plus dérivée, ceux de `sale` et de `sale_project` seraient perdus sans
        cette reprise.
        """
        super()._compute_analytic_distribution()
        self.filtered('project_id')._mobach_sync_analytic_distribution()

    def _prepare_invoice_line(self, **optional_values):
        """Transmet le projet à la ligne de facture.

        C'est le point qui rend le suivi utilisable : la facture générée depuis
        la commande — à la livraison comme à la facturation manuelle — porte le
        projet de la ligne d'origine, donc l'écriture comptable l'alimente.
        """
        values = super()._prepare_invoice_line(**optional_values)
        if self.project_id and not self.display_type:
            values['analytic_project_id'] = self.project_id.id
        return values
