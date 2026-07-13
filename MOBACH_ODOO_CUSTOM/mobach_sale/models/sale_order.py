# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    object = fields.Text(string="Objet")

    def _prepare_invoice(self):
        result = super()._prepare_invoice()
        if self.object:
            result.update({
                'object': self.object,
            })
        return result