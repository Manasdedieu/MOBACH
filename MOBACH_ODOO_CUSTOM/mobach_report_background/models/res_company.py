from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    layout_background = fields.Selection(
        selection_add=[('full_page', 'Pleine page')],
        ondelete={'full_page': 'set default'},
    )
