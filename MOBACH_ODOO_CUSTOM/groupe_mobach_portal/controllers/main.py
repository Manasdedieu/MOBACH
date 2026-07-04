# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home

_logger = logging.getLogger(__name__)

# ── Descriptions par défaut ───────────────────────────────────────────
DEFAULT_DESCRIPTIONS = {
    'base.main_company':                        'Prestation de Services & Commerce Général',
    'mobach_config.company_nas_et_fils':        'Prestation de Services & Commerce Général',
    'mobach_config.company_mohamadou_bachirou': 'Prestation de Services & Commerce Général',
    'mobach_config.company_afridrive':          'Logistique & Transport',
}

XML_IDS = list(DEFAULT_DESCRIPTIONS.keys())


class CompanyPortalController(Home):

    # ------------------------------------------------------------------
    # Route / — redirection vers portail ou Odoo
    # ------------------------------------------------------------------
    @http.route('/', type='http', auth='none')
    def index(self, s_action=None, db=None, **kw):
        if request.db and request.session.uid:
            return request.redirect_query('/odoo', query=request.params)
        return self.portal_landing(**kw)

    # ------------------------------------------------------------------
    # Déconnexion → retour au portail
    # ------------------------------------------------------------------
    @http.route('/web/session/logout', type='http', auth='public', website=True)
    def session_logout(self, redirect='/', **kw):
        request.session.logout()
        return request.redirect('/')

    # ------------------------------------------------------------------
    # Login : mémoriser company_id (GET) et switcher après login (POST)
    # ------------------------------------------------------------------
    @http.route('/web/login', type='http', auth='none', readonly=False)
    def web_login(self, redirect=None, **kw):
        if request.httprequest.method == 'GET':
            cid = kw.get('company_id')
            if cid:
                request.session['selected_portal_company_id'] = cid

        response = super().web_login(redirect=redirect, **kw)

        if request.httprequest.method == 'POST' and request.session.uid:
            cid = (
                kw.get('company_id')
                or request.session.get('selected_portal_company_id')
            )
            if cid:
                try:
                    user = request.env.user
                    cid_int = int(cid)
                    if cid_int in user.company_ids.ids:
                        user.sudo().write({'company_id': cid_int})
                        request.session['allowed_company_ids'] = [cid_int]
                        request.session.pop('selected_portal_company_id', None)
                        resp = request.redirect(f'/odoo?cids={cid_int}')
                        resp.set_cookie('cids', str(cid_int))
                        return resp
                    else:
                        request.session.logout()
                        return request.redirect(
                            f'/?access_denied=1&company_id={cid_int}'
                        )
                except Exception as e:
                    _logger.error('Erreur switch société: %s', e)

        return response

    # ------------------------------------------------------------------
    # Redirection post-login
    # ------------------------------------------------------------------
    def _login_redirect(self, uid, redirect=None):
        cid = (
            request.params.get('company_id')
            or request.session.get('selected_portal_company_id')
        )
        if cid:
            try:
                user = request.env['res.users'].sudo().browse(uid)
                cid_int = int(cid)
                if cid_int in user.company_ids.ids:
                    user.write({'company_id': cid_int})
                    request.session['allowed_company_ids'] = [cid_int]
                    request.session.pop('selected_portal_company_id', None)
                    return f'/odoo?cids={cid_int}'
                else:
                    request.session.logout()
                    return f'/?access_denied=1&company_id={cid_int}'
            except Exception as e:
                _logger.error('_login_redirect error: %s', e)
        return super()._login_redirect(uid, redirect=redirect)

    # ------------------------------------------------------------------
    # Route logo : /company_portal/logo/<id>
    #
    # Lit TOUJOURS le champ logo natif de res.company en base de données.
    # → Si l'admin change le logo via Odoo, le changement est visible
    #   immédiatement sur le portail (pas de cache fixe).
    #
    # Le cache-busting est géré côté portail via le paramètre ?unique=
    # calculé à partir de company.write_date (voir portal_landing).
    # Quand le logo change, write_date change → URL change → le navigateur
    # fait une nouvelle requête au lieu d'utiliser le cache.
    # ------------------------------------------------------------------
    @http.route(
        '/company_portal/logo/<int:company_id>',
        type='http', auth='public', methods=['GET']
    )
    def company_portal_logo(self, company_id, unique=None, **kw):
        """
        Sert le logo natif Odoo de la société (champ logo_web de res.company).

        Cache-Control :
          - Si ?unique=<write_date> est présent dans l'URL → cache 24 h
            (l'URL change dès que le logo change, donc le cache est toujours
            cohérent avec la réalité).
          - Sans paramètre unique → no-cache (revalide à chaque requête).
        """
        company = request.env['res.company'].sudo().browse(company_id)
        if not company.exists():
            return request.not_found()

        if company.logo_web:
            import base64
            raw = base64.b64decode(company.logo_web)

            # Détection MIME (PNG, JPEG, SVG)
            if raw[:4] == b'\x89PNG':
                mime = 'image/png'
            elif raw[:2] in (b'\xff\xd8', b'FF'):
                mime = 'image/jpeg'
            elif raw[:4] == b'<svg' or raw[:5] == b'<?xml':
                mime = 'image/svg+xml'
            else:
                mime = 'image/png'  # fallback

            # Cache long si unique présent, sinon revalidation systématique
            if unique:
                cache = 'public, max-age=86400, immutable'
            else:
                cache = 'no-cache'

            return request.make_response(
                raw,
                headers=[
                    ('Content-Type', mime),
                    ('Cache-Control', cache),
                ]
            )

        # Aucun logo en base → logo par défaut Odoo
        return request.redirect(
            f'/web/binary/company_logo?company={company_id}'
        )

    # ------------------------------------------------------------------
    # Portail de sélection des sociétés
    # ------------------------------------------------------------------
    @http.route('/company_portal', type='http', auth='public', website=True)
    def portal_landing(self, **kw):
        access_denied = kw.get('access_denied') == '1'
        denied_company_name = ''

        if access_denied and kw.get('company_id'):
            try:
                comp = request.env['res.company'].sudo().browse(
                    int(kw['company_id'])
                )
                if comp.exists():
                    denied_company_name = comp.name
            except Exception:
                pass

        # Sociétés dans l'ordre du mapping
        companies_records = []
        for xml_id in XML_IDS:
            try:
                company = request.env.ref(xml_id, raise_if_not_found=False)
                if company:
                    companies_records.append((xml_id, company.sudo()))
            except Exception:
                pass

        # Fallback : toutes les sociétés actives
        if not companies_records:
            for c in request.env['res.company'].sudo().search(
                [('active', '=', True)]
            ):
                companies_records.append(('', c))

        portal_companies = []
        for xml_id, company in companies_records:
            description = (
                company.portal_description
                or DEFAULT_DESCRIPTIONS.get(
                    xml_id, 'Prestation de Services & Commerce Général'
                )
            )

            # ── Cache-busting par write_date ──────────────────────────
            # Quand le logo change dans Odoo, write_date est mis à jour.
            # L'URL du logo change donc → le navigateur charge la nouvelle
            # image immédiatement, sans avoir à vider son cache.
            # ─────────────────────────────────────────────────────────
            if company.write_date:
                unique = company.write_date.strftime('%Y%m%d%H%M%S')
            else:
                unique = '0'
            logo_url = f'/company_portal/logo/{company.id}?unique={unique}'

            portal_companies.append({
                'id':            str(company.id),
                'name':          company.name,
                'subtitle':      description,
                'logo_url':      logo_url,
                'collaborators': request.env['res.users'].sudo().search_count(
                    [('company_ids', 'in', company.id)]
                ),
            })

        return request.render(
            'groupe_mobach_portal.portal_landing_template',
            {
                'companies':           portal_companies,
                'access_denied':       access_denied,
                'denied_company_name': denied_company_name,
                'current_year':        datetime.date.today().year,
            }
        )
