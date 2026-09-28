# -*- coding: utf-8 -*-
from odoo import fields, models

PROJECT_DOMAIN = "['|', ('company_id', '=', False), ('company_id', '=', company_id), ('is_template', '=', False)]"


class MobachAnalyticProjectMixin(models.AbstractModel):
    """Affectation d'un projet à une ligne, traduite en distribution analytique.

    Odoo pilote l'analytique par `analytic_distribution`, un JSON
    ``{"<ids de comptes>": pourcentage}`` saisi dans un widget dédié. Le champ
    est exact mais inutilisable au quotidien : personne ne saisit une répartition
    à la main sur chaque ligne de facture.

    Ce mixin pose un simple Many2one vers project.project et se charge de la
    traduction. Rien n'est stocké en parallèle de l'analytique standard : la
    distribution reste la source de vérité comptable, et tous les états natifs
    d'Odoo continuent de fonctionner.

    Les modèles qui l'héritent doivent porter `analytic_distribution`
    (via `analytic.mixin`) et `company_id`.
    """
    _name = 'mobach.analytic.project.mixin'
    _description = 'Affectation analytique par projet'

    def _mobach_get_project(self):
        """Retourne le projet associé à la ligne (project_id ou analytic_project_id)."""
        self.ensure_one()
        if 'project_id' in self._fields and self.project_id:
            return self.project_id
        if 'analytic_project_id' in self._fields and self.analytic_project_id:
            return self.analytic_project_id
        return self.env['project.project']

    def _mobach_project_plan(self):
        """Plan analytique porteur des comptes de projet.

        `project.project.account_id` vit toujours sur le plan racine retourné par
        `_get_all_plans()` — celui qu'Odoo nomme « Project ». C'est le plan dont
        ce mixin prend la responsabilité : il y écrit et y efface, sans jamais
        toucher aux autres plans que l'utilisateur aurait renseignés à la main.
        """
        project_plan, _other_plans = self.env['account.analytic.plan']._get_all_plans()
        return project_plan

    def _mobach_project_distribution(self):
        """Distribution analytique de la ligne, alignée sur son projet.

        Les comptes du plan projet sont remplacés par ceux du projet choisi — ou
        purement retirés si le projet est vidé. Les comptes des autres plans sont
        conservés tels quels, y compris leurs pourcentages : une ligne répartie
        60/40 sur deux départements le reste après affectation à un projet.
        """
        self.ensure_one()
        Account = self.env['account.analytic.account']
        distribution = self.analytic_distribution or {}
        project = self._mobach_get_project()
        accounts = project._get_analytic_accounts() if project else self.env['account.analytic.account']
        target_plans = accounts.root_plan_id or self._mobach_project_plan()

        if not distribution:
            return {','.join(map(str, accounts.ids)): 100} if accounts else {}

        new_distribution = {}
        for key, percentage in distribution.items():
            kept = Account.browse(
                [int(part) for part in key.split(',') if part.strip().isdigit()]
            ).exists().filtered(lambda a: a.root_plan_id not in target_plans)
            ids = kept.ids + accounts.ids
            if not ids:
                # Plus aucun compte : la clé disparaît, la ligne n'est plus ventilée.
                continue
            new_key = ','.join(map(str, ids))
            new_distribution[new_key] = new_distribution.get(new_key, 0.0) + percentage
        return new_distribution

    def _mobach_sync_analytic_distribution(self):
        """Réaligne `analytic_distribution` sur le projet."""
        for line in self:
            distribution = line._mobach_project_distribution()
            if distribution != (line.analytic_distribution or {}):
                line.analytic_distribution = distribution
