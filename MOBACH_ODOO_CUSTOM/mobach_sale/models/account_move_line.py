# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    accounting_nature = fields.Selection(related='product_id.accounting_nature')
