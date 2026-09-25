from .models.res_company import get_default_background_image


def post_init_hook(env):
    """ Applique le fond pleine page MOBACH et le format A4 MOBACH à toutes les sociétés existantes. """
    env['res.company'].with_context(active_test=False).search([]).write({
        'layout_background': 'full_page',
        'layout_background_image': get_default_background_image(),
        'paperformat_id': env.ref('mobach_report_background.paperformat_mobach_a4').id,
    })
