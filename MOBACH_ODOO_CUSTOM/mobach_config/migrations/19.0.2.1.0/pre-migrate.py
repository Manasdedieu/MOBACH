# -*- coding: utf-8 -*-
"""Les taxes et groupes de taxes des autres sociétés (NAS ET FILS, MOHAMADOU BACHIROU, AFRIDRIVE)
étaient déclarés par mobach_invoice_ir, qui ne s'installait pas sur une base neuve (il référençait
les sociétés de mobach_config). Les fichiers sont passés dans mobach_config : on lui transfère les
identifiants existants pour réutiliser les enregistrements au lieu d'en créer des doublons."""

NAMES = [
    'tax_group_tva_19_25_nas', 'tax_group_ir_2_2_nas', 'tax_group_ir_5_5_nas',
    'tax_group_tva_19_25_mb', 'tax_group_ir_2_2_mb', 'tax_group_ir_5_5_mb',
    'tax_group_tva_19_25_afridrive', 'tax_group_ir_2_2_afridrive', 'tax_group_ir_5_5_afridrive',
    'tax_tva_19_25_vente_nas', 'tax_tva_19_25_achat_nas', 'tax_ir_2_2_nas', 'tax_ir_5_5_nas',
    'tax_tva_19_25_vente_mb', 'tax_tva_19_25_achat_mb', 'tax_ir_2_2_mb', 'tax_ir_5_5_mb',
    'tax_tva_19_25_vente_afridrive', 'tax_tva_19_25_achat_afridrive', 'tax_ir_2_2_afridrive', 'tax_ir_5_5_afridrive',
]


def migrate(cr, version):
    cr.execute("""
        UPDATE ir_model_data
           SET module = 'mobach_config'
         WHERE module = 'mobach_invoice_ir'
           AND name IN %s
           AND NOT EXISTS (
               SELECT 1 FROM ir_model_data d2
                WHERE d2.module = 'mobach_config' AND d2.name = ir_model_data.name
           )
    """, [tuple(NAMES)])
