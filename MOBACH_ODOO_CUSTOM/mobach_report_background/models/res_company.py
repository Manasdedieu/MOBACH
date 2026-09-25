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
