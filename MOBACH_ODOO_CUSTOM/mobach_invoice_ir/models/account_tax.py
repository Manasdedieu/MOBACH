# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountTax(models.Model):
    """Ajout du flag is_withholding_ir pour identifier les taxes IR."""
    _inherit = 'account.tax'

    is_withholding_ir = fields.Boolean(
        string="Retenue IR",
        default=False,
        help="Cocher pour les taxes IR (Impôt sur le Revenu) : IR 2,2% et IR 5,5%.\n"
             "Ces taxes seront proposées dans l'en-tête de la facture.",
    )
