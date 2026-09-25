import base64

from odoo import fields, models
from odoo.tools import file_open

DEFAULT_BACKGROUND_IMAGE_PATH = 'mobach_report_background/static/img/Composition1.png'


def get_default_background_image():
    """ Image de fond MOBACH par défaut (base64), fournie avec le module. """
    with file_open(DEFAULT_BACKGROUND_IMAGE_PATH, 'rb') as image:
        return base64.b64encode(image.read())


class ResCompany(models.Model):
    _inherit = 'res.company'

    layout_background = fields.Selection(
        selection_add=[('full_page', 'Pleine page')],
        default='full_page',
        # 'set default' reprendrait 'full_page' (défaut de ce module) pendant la désinstallation.
        ondelete={'full_page': lambda companies: companies.write({'layout_background': 'Blank'})},
    )
    layout_background_image = fields.Binary(default=lambda self: get_default_background_image())
    paperformat_id = fields.Many2one(default=lambda self: self._default_mobach_paperformat())

    def _default_mobach_paperformat(self):
        return (self.env.ref('mobach_report_background.paperformat_mobach_a4', raise_if_not_found=False)
                or self.env.ref('base.paperformat_euro', raise_if_not_found=False))
