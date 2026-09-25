# -*- coding: utf-8 -*-
import requests
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    def _update_xaf_rates_cron(self):
        """
        Met à jour quotidiennement le taux de change de toutes les devises actives
        par rapport au XAF en utilisant l'API fawazahmed0.
        """
        base_url = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/xaf.json"
        
        # Récupérer toutes les devises actives dans le système, à l'exception du XAF
        active_currencies = self.search([('active', '=', True), ('name', '!=', 'XAF')])
        if not active_currencies:
            return

        try:
            response = requests.get(base_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            xaf_rates = data.get('xaf', {})

            for currency in active_currencies:
                target_code = currency.name.lower()
                rate = xaf_rates.get(target_code)

                if rate:
                    self._create_or_update_rate(currency, rate)
                else:
                    _logger.warning("Aucun taux trouvé pour %s par rapport au XAF.", currency.name)

        except requests.RequestException as e:
            _logger.error("Erreur lors de la récupération des taux de change (Base: XAF): %s", e)

    def _create_or_update_rate(self, currency, rate):
        """
        Crée ou met à jour le taux de la devise à la date du jour.
        Dans Odoo, si la devise de la société est le XAF (1.0), le taux d'une devise étrangère
        est exprimé comme: 1 XAF = {rate} Devise Étrangère.
        L'API xaf.json nous donne exactement cette valeur.
        """
        today = fields.Date.context_today(self)

        # Chercher le dernier taux connu pour cette devise
        last_rate = self.env['res.currency.rate'].search([
            ('currency_id', '=', currency.id)
        ], order='name desc', limit=1)

        # Si le taux n'a pas changé de manière significative (6 décimales), on ignore
        if last_rate and abs(last_rate.rate - rate) < 1e-6:
            # Si c'était déjà le taux d'aujourd'hui, rien à faire
            # Si c'est un ancien taux identique, on ne crée pas de ligne inutile pour éviter la saturation
            _logger.info("Taux inchangé pour %s (%s). Ignoré.", currency.name, rate)
            return

        # Si le taux a changé : vérifier s'il y a déjà une ligne pour AUJOURD'HUI
        if last_rate and last_rate.name == today:
            last_rate.write({'rate': rate})
            _logger.info("Taux du jour mis à jour pour %s : %s", currency.name, rate)
        else:
            # Créer une nouvelle ligne car c'est un nouveau jour avec un nouveau taux
            self.env['res.currency.rate'].create({
                'currency_id': currency.id,
                'rate': rate,
                'name': today,
            })
            _logger.info("Nouveau taux créé pour %s : %s", currency.name, rate)
