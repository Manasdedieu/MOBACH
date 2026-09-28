# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    accounting_nature = fields.Selection(related='product_id.accounting_nature')
