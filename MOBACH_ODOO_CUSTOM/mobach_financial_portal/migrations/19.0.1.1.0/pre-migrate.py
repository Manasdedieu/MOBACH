# -*- coding: utf-8 -*-
"""Prépare la base à la contrainte d'unicité (société, période).

Avant cette version il n'existait qu'UNE fiche par société, avec un champ
`period` librement modifiable depuis le kanban : le premier utilisateur qui
basculait sur « Année en cours » changeait la période pour tout le monde. Les
bases existantes contiennent donc des fiches dont la période a dérivé.

Ce script s'exécute AVANT la création de la contrainte SQL et AVANT le
chargement du fichier de données qui instancie les seize couples
société × période. Sans lui, la mise à jour échouerait sur une violation de
clé unique.
"""
LEGACY_XMLIDS = (
    'financial_performance_mobach_sarl',
    'financial_performance_nas_et_fils',
    'financial_performance_mohamadou_bachirou',
    'financial_performance_afridrive',
)


def migrate(cr, version):
    if not version:
        return

    # 1. Les quatre fiches historiques reprennent la période 'all' qui leur était
    #    assignée à l'origine ; les autres périodes sont créées par le fichier de
    #    données juste après.
    cr.execute("""
        UPDATE mobach_financial_performance p
           SET period = 'all'
          FROM ir_model_data d
         WHERE d.model = 'mobach.financial.performance'
           AND d.module = 'mobach_financial_portal'
           AND d.res_id = p.id
           AND d.name IN %s
    """, (LEGACY_XMLIDS,))

    # 2. Doublons éventuels (fiches créées à la main) : on conserve celle qui porte
    #    un identifiant externe, sinon la plus ancienne.
    cr.execute("""
        DELETE FROM mobach_financial_performance
         WHERE id IN (
             SELECT id FROM (
                 SELECT p.id,
                        ROW_NUMBER() OVER (
                            PARTITION BY p.company_id, p.period
                            ORDER BY (d.id IS NULL), p.id
                        ) AS rang
                   FROM mobach_financial_performance p
                   LEFT JOIN ir_model_data d
                          ON d.model = 'mobach.financial.performance'
                         AND d.res_id = p.id
             ) doublons
             WHERE doublons.rang > 1
         )
    """)

    # 3. Identifiants externes devenus orphelins.
    cr.execute("""
        DELETE FROM ir_model_data
         WHERE model = 'mobach.financial.performance'
           AND res_id NOT IN (SELECT id FROM mobach_financial_performance)
    """)

    # 4. Le cron de rafraîchissement était chargé avec noupdate="1" : sans lever ce
    #    drapeau, Odoo ignore le fichier XML et le laisserait tourner toutes les
    #    quinze minutes alors qu'il n'a plus d'objet (les KPI sont calculés à la
    #    volée). On rend la main au fichier de données, qui le désactive.
    cr.execute("""
        UPDATE ir_model_data
           SET noupdate = FALSE
         WHERE module = 'mobach_financial_portal'
           AND model = 'ir.cron'
           AND name = 'cron_refresh_financial_kpis'
    """)
