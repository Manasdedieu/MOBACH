# mobach_report_background — Fond de page pleine page des rapports PDF

## Objectif

Afficher une image de fond sur **toute la page PDF** (en-tête + corps + pied de page),
compatible avec tous les `external_layout_*` (standard, boxed, bold, striped, folder, wave, bubble).

**Périmètre voulu (décision utilisateur) :** seuls le **devis / bon de commande** et les
**factures** ont le fond et le format A4 MOBACH. **Tous les autres rapports restent natifs**
(format papier de la société, sans fond), y compris le pro-forma.

| Rapport | xmlid |
|---|---|
| Devis / Bon de commande | `sale.action_report_saleorder` |
| Facture (avec paiements) | `account.account_invoices` |
| Facture (sans paiement) | `account.account_invoices_without_payment` |
| Devis / Bon de commande (Quote Builder) | `sale_pdf_quote_builder.action_report_saleorder_raw` |

`sale_pdf_quote_builder` s'installe automatiquement avec `sale_management`. Quand il est installé,
c'est ce rapport « raw » qui est imprimé pour le devis, d'où la dépendance du module.

Configuration dans `data/ir_actions_report_data.xml` : `paperformat_id` = A4 MOBACH et
`mobach_full_page_background = True`. Pour ajouter un rapport, cocher « Fond pleine page
MOBACH » sur sa fiche (Paramètres → Technique → Rapports) ou l'ajouter dans ce fichier XML.
Les rapports natifs de `sale` et `account` ne définissent pas `paperformat_id`, donc une mise à jour de
ces modules n'écrase pas la configuration.

## Pourquoi `layout_background_url` (standard Odoo) ne suffit pas

Dans `ir.actions.report._prepare_html` (Odoo), le HTML est découpé en trois documents
rendus **séparément** par wkhtmltopdf :

- `div.header` → fichier passé en `--header-html` (rendu dans la marge haute) ;
- `div.footer` → fichier passé en `--footer-html` (rendu dans la marge basse) ;
- chaque `div.article` → corps, limité à la zone entre les marges.

Le `background-image` posé par les layouts sur `div.article` ne peut donc **jamais**
couvrir l'en-tête ni le pied : aucun CSS ne peut déborder d'un document à l'autre.
→ Ne pas chercher de solution QWeb/CSS, la seule voie fiable est de traiter le PDF après sa génération.

## Fonctionnement du module

1. **`models/res_company.py`** : `selection_add` de `('full_page', 'Pleine page')` sur
   `layout_background`, qui réutilise `layout_background_image`. Les templates Odoo ne sont
   pas modifiés : leurs conditions (`== 'Custom'` / `'Demo logo'`) ne mettent plus de
   fond sur l'article, donc l'image n'apparaît pas en double.
2. **`models/ir_actions_report.py`** : champ `mobach_full_page_background` (booléen, visible
   sur la fiche rapport à côté du format papier) et surcharge de `_run_wkhtmltopdf`. Rien n'est
   fait si le rapport (`report_ref`) n'est pas coché. Une fois le PDF
   généré, l'image est dessinée avec reportlab (une page de fond par page, aux mêmes
   dimensions, image étirée sur toute la feuille), puis le contenu du rapport est fusionné
   **par-dessus** avec `mergePage`.
   - La société est retrouvée par la classe `o_company_<id>_layout` (présente seulement
     dans les external layouts, donc `internal_layout` et étiquettes ne sont pas touchés).
   - Si l'image est illisible, l'erreur est journalisée et le PDF est rendu sans fond
     (l'impression ne doit jamais échouer).
3. **`static/src/scss/report_full_background.scss`** (`web.report_assets_pdf`) :
   `html, body { background: transparent !important; }`, sinon le fond blanc de
   Bootstrap masque l'image posée dessous.
4. **`views/base_document_layout_views.xml`** : champ image visible et requis pour
   `full_page` dans l'assistant de mise en page, et onglet « Fond des rapports » sur la fiche société.

## En-tête MOBACH (devis et factures)

`views/report_templates.xml` :

- `report_header_mobach` : bloc adresse de la société à gauche ; à droite, un bloc sur fond
  `#451d1c` (texte blanc) avec le NUMERO CONTRIBUABLE (`company.nui`) et le RCCM, qui est écrit en dur.
- Les 7 `web.external_layout_*` sont hérités : le `div.header` natif reçoit
  `t-if="not mobach_header"`, suivi d'un `div.header` en `t-else` qui appelle `report_header_mobach`.
  L'en-tête MOBACH fonctionne donc **quel que soit le layout** choisi par la société.
- `mobach_header` est posé dans le corps du `t-call="web.external_layout"` (juste après
  `forced_vat`, même mécanisme) de `sale.report_saleorder_document` (valeur `not is_pro_forma`)
  et de `account.report_invoice_document` (valeur `True`). Tous les autres documents gardent l'en-tête natif.
- **Début du corps** (`report_document_title_mobach`, inséré en **premier élément** de
  `div.article` dans les 7 layouts quand `mobach_document_title` est défini) :
  1. titre centré dans un cadre gris clair arrondi, texte noir : `'BON DE COMMANDE'` (devis,
     rien pour le pro-forma), `'FACTURE'`, ou `'AVOIR'` pour `out_refund` / `in_refund` ;
  2. `report_document_info_mobach` : « **OBJET :** » souligné + champ `object` (défini par `mobach_sale`),
     puis deux cadres à bord carré (48,5 % / 48,5 %, espacement de 3 %) :
     - gauche : client (`partner_id`, widget contact nom / adresse / téléphone / e-mail, + TVA) ;
     - droite, devis : Réf. PROFORMA = `client_order_ref`, N° commande = `name`,
       Date d'émission = `date_order` ;
     - droite, facture : Réf. PROFORMA = `ref` (reçoit le `client_order_ref` du devis),
       N° facture = `name`, N° commande = `invoice_origin`, Date d'émission = `invoice_date` ;
     - devis et facture : Lieu de livraison = `partner_shipping_id.city`, Adresse de livraison =
       `partner_shipping_id` (widget contact, adresse seule).
  - `mobach_doc` (`doc` pour le devis, `o` pour la facture) est posé dans les documents, à côté de `mobach_header`.
- **Masqué entre l'en-tête et le tableau** en mode MOBACH : `web.address_layout` (`t-if`
  étendu avec `not mobach_header`), le titre natif (`layout_document_title` vidé), `h2#informations`
  et la ligne « Objet » ajoutés par `mobach_sale`. Le `div#informations` natif est déjà supprimé
  par `mobach_sale`. D'où la **dépendance à `mobach_sale`** : nos héritages s'appliquent après les siens.
- **Espace en-tête / titre** : `margin_top` et `header_spacing` du format A4 MOBACH = 40 mm
  (au lieu de 52). Si l'en-tête grandit (adresse société plus longue), remonter ces valeurs.
- **Piège XPath** : `hasclass('header')` ne trouve pas les classes posées en `t-attf-class`. Il faut utiliser
  `//div[contains(concat(' ', @t-attf-class, ' '), ' header ')]`, qui ne correspond pas
  aux `report_header` des pieds de page.
- `nui` vient de `mobach_config`, qui n'est **pas** une dépendance : son installation sur une base neuve
  échoue à cause de `mobach_invoice_ir`, qui référence `mobach_config.company_nas_et_fils`.
  D'où la garde `t-if="'nui' in company._fields"`.

## Image par défaut MOBACH

`static/img/Composition1.png` (1240×1754 px, bande bordeaux à gauche) est le fond par défaut :

- **Sociétés existantes** : `hooks.py` → `post_init_hook` passe toutes les sociétés en
  `full_page` avec cette image. Il ne s'exécute **qu'à l'installation** (pas sur `-u`).
- **Nouvelles sociétés** : `default='full_page'` sur `layout_background` et
  `default=get_default_background_image()` sur `layout_background_image`.
- À la désinstallation, `ondelete` remet `'Blank'` explicitement : `'set default'`
  reprendrait `'full_page'`, qui est le défaut défini par ce module.
- La bande occupe environ 2 à 9 % de la largeur (≈ 5–18 mm sur A4). D'où le format
  **`paperformat_mobach_a4`** (`data/report_paperformat_data.xml`), une copie de
  `base.paperformat_euro` avec `margin_left = 14` : 14 mm de marge wkhtmltopdf + 11 mm de
  marge CSS (`css_margins`) mettent le texte à ≈ 25 mm du bord ; `margin_top` et `header_spacing` = 40 mm. `base.paperformat_euro` est
  en `noupdate` et appartient au module base : ne pas le modifier.
- Ce format est affecté **uniquement aux rapports devis et facture** (voir le tableau plus haut),
  **pas aux sociétés** : le format papier de la société reste natif pour les autres rapports.
- Les rapports qui ont leur propre `paperformat_id` (par exemple la « Facture Mobach » de
  `mobach_sale`, avec `mobach_sale_invoice_paperformat`) ne sont pas concernés : régler leur marge séparément si besoin.

## Pièges techniques (à ne pas casser)

- **PyPDF2 2.12.1** est la version réellement utilisée (`odoo.tools.pdf` choisit
  `_pypdf2_2`). Rester compatible 1.x / 2.x / pypdf 3+ en passant par les alias de
  `odoo.tools.pdf` (`OdooPdfFileReader`, `OdooPdfFileWriter`, `NameObject`,
  `getPage`, `mergePage`, `mediaBox`…).
- `reader.getPage(i)` renvoie une **copie aplatie** de la page : la modifier ne change
  rien au PDF écrit. Il faut écrire `/Contents` et `/Resources` dans les **nœuds réels**
  de l'arbre `/Root/Pages` (`_get_pdf_page_nodes`), puis utiliser
  `writer.cloneReaderDocumentRoot(reader)`.
- On garde les objets page d'origine et la racine du document pour **préserver
  `/Outlines` et `/Dests`** : Odoo s'en sert dans `_render_qweb_pdf_prepare_streams`
  pour découper un PDF multi-enregistrements en pièces jointes. Ne pas passer par
  `writer.addPage()` sur de nouvelles pages, sinon on perd ces signets.
- `mergePage` n'a pas de paramètre `over` en PyPDF2 2.x : on fusionne donc le contenu
  sur la page de fond (`background.mergePage(page)`), puis on recopie le résultat dans la page d'origine.

## Limites connues

- L'aperçu de l'assistant « Mise en page du document » est en HTML : il ne montre pas
  le fond pleine page. Seul le PDF l'affiche.
- Si un même lot d'impression mélange plusieurs sociétés, c'est le fond de la première
  société trouvée qui s'applique à tout le lot (wkhtmltopdf ne permet pas de savoir quelle page vient de quel document).
- L'image est étirée sans garder ses proportions : prévoir une image au format de la
  feuille (A4 portrait ≈ 2480×3508 px à 300 dpi).

## Tester

**Tester sur une copie de la vraie base** : `mobach_sale`, `mobach_config` et `mobach_invoice_ir` ne
s'installent pas sur une base neuve. `odoo-bin db -c ../odoo-mobach.conf duplicate mobach mobach_bgtest2`,
puis **`-u`** (et non `-i`, sans effet si le module est déjà installé dans la base copiée).


Démarrer un serveur (wkhtmltopdf doit charger le CSS via `report.url`), puis dans `odoo-bin shell` :

```python
c = env.company
c.write({'layout_background': 'full_page', 'layout_background_image': <b64 png>})
c.external_report_layout_id = env.ref('web.external_layout_bold')
pdf, _ = env['ir.actions.report']._render_qweb_pdf('web.action_report_externalpreview', [c.id])
```

Validé le 2026-09-25 sur les 7 layouts (standard, boxed, bold, striped, folder, wave, bubble).
