# mobach_report_background — Fond de page pleine page des rapports PDF

## Objectif

Afficher une image de fond sur **toute la page PDF** (en-tête + corps + pied de page)
pour tous les `external_layout_*` (standard, boxed, bold, striped, folder, wave, bubble).

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
2. **`models/ir_actions_report.py`** : surcharge de `_run_wkhtmltopdf`. Une fois le PDF
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

Démarrer un serveur (wkhtmltopdf doit charger le CSS via `report.url`), puis dans `odoo-bin shell` :

```python
c = env.company
c.write({'layout_background': 'full_page', 'layout_background_image': <b64 png>})
c.external_report_layout_id = env.ref('web.external_layout_bold')
pdf, _ = env['ir.actions.report']._render_qweb_pdf('web.action_report_externalpreview', [c.id])
```

Validé le 2026-09-25 sur les 7 layouts (standard, boxed, bold, striped, folder, wave, bubble).
