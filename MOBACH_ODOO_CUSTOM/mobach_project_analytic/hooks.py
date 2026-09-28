# -*- coding: utf-8 -*-
"""Post-init hook du module mobach_project_analytic."""
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Dote d'un compte analytique les projets déjà créés et garantit le projet Générique.

    À partir de l'installation, `project.project.create()` s'en charge. Les
    projets antérieurs, eux, ont été créés par l'Odoo standard qui laisse
    `account_id` vide : sans rattrapage ils resteraient non imputables, et le
    champ « Projet analytique » des lignes ne ventilerait rien pour eux.
    """
    # Garantit l'existence du projet Générique pour les lignes sans projet
    env['project.project']._mobach_get_generic_project()

    projects = env['project.project'].with_context(active_test=False).search([
        ('account_id', '=', False),
        ('is_template', '=', False),
    ])
    if not projects:
        _logger.info("MOBACH analytique : tous les projets ont déjà un compte analytique.")
        return

    projects._mobach_ensure_analytic_account()
    _logger.info(
        "MOBACH analytique : compte analytique créé pour %d projet(s) : %s",
        len(projects), ', '.join(projects.mapped('name')),
    )

    # Migration de rattrapage : copier analytic_project_id vers project_id si le champ existait
    cr = env.cr
    for table in ('sale_order', 'sale_order_line', 'purchase_order', 'purchase_order_line'):
        cr.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = %s AND column_name = 'analytic_project_id'
        """, (table,))
        if cr.fetchone():
            cr.execute(f"""
                UPDATE {table}
                   SET project_id = analytic_project_id
                 WHERE project_id IS NULL AND analytic_project_id IS NOT NULL
            """)
