# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    """
    Extension de res.company pour le portail MOBACH.

    Seul champ ajouté :
      - portal_description : description affichée sous le nom de la société
                             sur le portail de sélection.

    Pour le logo : on utilise directement le logo natif de la société
    (champ `logo` / `logo_web` de res.company), servi via la route
    /company_portal/logo/<id> → /web/binary/company_logo?company=<id>.
    Cela évite tout champ Binary supplémentaire et tout conflit de vue.
    """
    _inherit = 'res.company'

    portal_description = fields.Char(
        string='Description Portail',
        translate=True,
        help=(
            "Description courte affichée sous le nom de la société "
            "sur le portail de sélection du Groupe MOBACH.\n"
            "Ex : « Prestation de Services & Commerce Général »\n"
            "Si vide, une description par défaut est utilisée."
        ),
    )
