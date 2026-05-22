# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    nui = fields.Char(
        string='NUI',
        help='Numéro Unique d\'Identification fiscale de la société',
        copy=False,
    )

