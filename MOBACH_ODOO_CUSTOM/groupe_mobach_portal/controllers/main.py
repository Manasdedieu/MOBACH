# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home

_logger = logging.getLogger(__name__)

class CompanyPortalController(Home):

    @http.route('/', type='http', auth='public')
    def index(self, **kw):
        """
        Surcharge du point d'entrée racine d'Odoo (ex: http://localhost:8069/).
        Redirige ou sert directement le portail de sélection de société pour les utilisateurs non connectés.
        """
        if request.session.uid:
            return request.redirect('/odoo')
        return self.portal_landing(**kw)

    @http.route('/odoo', type='http', auth='none')
    def web_client(self, s_action=None, **kw):
        """
        Surcharge de la route /odoo pour s'assurer qu'un utilisateur non connecté
        est forcé de passer par notre portail de sélection de niveau racine pour choisir son entreprise.
        """
        if not request.session.uid:
            return request.redirect('/')
        return super(CompanyPortalController, self).web_client(s_action=s_action, **kw)

    @http.route('/web/session/logout', type='http', auth="public", website=True)
    def session_logout(self, redirect='/', **x):
        """
        Correctif de Déconnexion : 
        Surcharge de l'action de déconnexion d'Odoo pour rediriger systématiquement 
        l'utilisateur vers le portail de sélection racine '/' après s'être déconnecté.
        """
        request.session.logout()
        return request.redirect('/')

    def _login_redirect(self, uid, redirect=None):
        """
        Surcharge de la redirection après connexion réussie pour appliquer la société choisie.
        """
        cid = request.params.get('company_id') or request.session.get('selected_portal_company_id')
        if cid:
            try:
                user = request.env['res.users'].sudo().browse(uid)
                cid_int = int(cid)
                if cid_int in user.company_ids.ids:
                    _logger.info("Setting company_id = %s for user %s inside _login_redirect", cid_int, user.login)
                    # Force user's preferred company in database to the selected one
                    user.write({'company_id': cid_int})
                    # Set allowed company ids on session
                    request.session['allowed_company_ids'] = [cid_int]
                    # Clean up session
                    request.session.pop('selected_portal_company_id', None)
                    return f"/odoo#cids={cid_int}"
                else:
                    _logger.warning("User %s does not have access to selected company %s", user.login, cid_int)
                    request.session.logout()
                    return f"/?access_denied=1&company_id={cid_int}"
            except Exception as e:
                _logger.error("Error in _login_redirect setting company_id: %s", str(e))
        return super(CompanyPortalController, self)._login_redirect(uid, redirect=redirect)

    @http.route('/web/login', type='http', auth='public', website=True)
    def web_login(self, redirect=None, **kw):
        """
        Surcharge de la page d'authentification native d'Odoo.
        Vérifie si la société sélectionnée est transmise et force la session utilisateur dessus si l'accès est OK.
        """
        # Au GET, on mémorise la société choisie dans la session de l'utilisateur pour la conserver lors de la soumission du formulaire POST
        if request.httprequest.method == 'GET':
            cid = kw.get('company_id')
            if cid:
                request.session['selected_portal_company_id'] = cid
                
        response = super(CompanyPortalController, self).web_login(redirect=redirect, **kw)
        
        # Si la requête est en POST et que la connexion a réussi (uid présent dans la session)
        if request.httprequest.method == 'POST' and request.session.uid:
            cid = kw.get('company_id') or request.session.get('selected_portal_company_id')
            if cid:
                try:
                    user = request.env.user
                    cid_int = int(cid)
                    
                    # Vérifier si l'utilisateur a accès à la société choisie
                    if cid_int in user.company_ids.ids:
                        _logger.info("Accès autorisé. Redirection de l'utilisateur %s vers la société %s", user.login, cid_int)
                        
                        # On force le profil par défaut de l'utilisateur sur la société choisie
                        user.sudo().write({'company_id': cid_int})
                        
                        # On force l'initialisation de la session utilisateur avec cette seule société autorisée
                        request.session['allowed_company_ids'] = [cid_int]
                        
                        # Redirection conforme Odoo 19 en passant l'ID de la société dans l'URL (#cids)
                        response = request.redirect(f"/odoo#cids={cid_int}")
                        
                        # On force le cookie 'cids' d'Odoo pour assurer que le client web charge immédiatement la bonne société active principale
                        response.set_cookie('cids', f"{cid_int}")
                        request.session.pop('selected_portal_company_id', None)
                        return response
                    else:
                        _logger.warning("Accès Refusé. L'utilisateur %s n'a pas accès à la société ID %s", user.login, cid_int)
                        
                        # L'utilisateur n'a pas accès -> déconnexion immédiate pour empêcher la navigation et retour avec erreur
                        request.session.logout()
                        return request.redirect(f"/?access_denied=1&company_id={cid_int}")
                except Exception as e:
                    _logger.error("Erreur lors de l'attribution de la société active dans web_login: %s", str(e))
        
        return response

    @http.route('/company_portal', type='http', auth='public', website=True)
    def portal_landing(self, **kw):
        """
        Contrôleur de la landing page du portail de sélection d'entreprise.
        Résout dynamiquement les sociétés créées par le module 'mobach_config' via request.env.ref.
        """
        # Récupération des paramètres d'erreur d'accès
        access_denied = kw.get('access_denied') == '1'
        denied_company_id = kw.get('company_id')
        denied_company_name = ""
        
        if access_denied and denied_company_id:
            try:
                comp = request.env['res.company'].sudo().browse(int(denied_company_id))
                if comp.exists():
                    denied_company_name = comp.name
            except Exception:
                pass

        # Liste des XML IDs de nos sociétés configurées dans mobach_config
        xml_ids = [
            'base.main_company',
            'mobach_config.company_nas_et_fils',
            'mobach_config.company_mohamadou_bachirou',
            'mobach_config.company_afridrive'
        ]
        
        # Récupération dynamique des sociétés existantes en base de données
        companies_records = []
        for xml_id in xml_ids:
            try:
                company = request.env.ref(xml_id, raise_if_not_found=False)
                if company:
                    companies_records.append(company.sudo())
            except Exception:
                pass
        
        # Si aucune de ces sociétés spécifiques n'est trouvée (ex: pas encore installées), fallback sur toutes les sociétés
        if not companies_records:
            companies_records = request.env['res.company'].sudo().search([])

        portal_companies = []
        for company in companies_records:
            company = company.sudo()
            name_upper = company.name.upper()
            
            # Paramètres par défaut
            subtitle = "Prestation de Services & Commerce Général"
            logo_type = "text"
            logo_text = company.name[:1].upper()
            
            # Enrichissement visuel dynamique basé sur les sociétés définies dans mobach_config
            if "MOBACH" in name_upper:
                subtitle = "Prestation de Services & Commerce Général"
                logo_type = "mobach"
                logo_text = "M"
            elif "NAS" in name_upper:
                subtitle = "Prestation de Services & Commerce Général"
                logo_type = "nas"
                logo_text = "N&F"
            elif "BACHIROU" in name_upper or "MOHAMADOU" in name_upper or "MB" in name_upper:
                subtitle = "Prestation de Services & Commerce Général"
                logo_type = "mb"
                logo_text = "MB"
            elif "AFRI" in name_upper or "DRIVE" in name_upper:
                subtitle = "Logistique & Transport"
                logo_type = "afridrive"
                logo_text = "AD"

            # Calcul dynamique exact des collaborateurs par rapport au res.users de cette société
            # (Habilitation effective : utilisateurs d'Odoo qui appartiennent à la société)
            collaborators_count = request.env['res.users'].sudo().search_count([
                ('company_ids', 'in', company.id)
            ])

            portal_companies.append({
                'id': str(company.id),
                'name': company.name,
                'subtitle': subtitle,
                'collaborators': collaborators_count,
                'logo_type': logo_type,
                'logo_text': logo_text,
                'primary_color': company.primary_color or "#203a54",
            })

        values = {
            'companies': portal_companies,
            'access_denied': access_denied,
            'denied_company_name': denied_company_name,
            'current_year': datetime.date.today().year,
        }
        
        return request.render('groupe_mobach_portal.portal_landing_template', values)
