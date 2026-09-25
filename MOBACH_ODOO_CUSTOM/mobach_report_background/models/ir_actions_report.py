import base64
import io
import logging
import re

from odoo import models
from odoo.tools.pdf import NameObject, OdooPdfFileReader, OdooPdfFileWriter

_logger = logging.getLogger(__name__)

# Classe posée par tous les external_layout sur l'en-tête, l'article et le pied de page.
COMPANY_LAYOUT_RE = re.compile(r'o_company_(\d+)_layout')


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _run_wkhtmltopdf(self, bodies, report_ref=False, header=None, footer=None, landscape=False,
                         specific_paperformat_args=None, set_viewport_size=False):
        pdf_content = super()._run_wkhtmltopdf(
            bodies,
            report_ref=report_ref,
            header=header,
            footer=footer,
            landscape=landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size,
        )
        company = self._get_full_page_background_company(bodies, header, footer)
        if not company:
            return pdf_content
        try:
            return self._apply_full_page_background(pdf_content, base64.b64decode(company.layout_background_image))
        except Exception:  # noqa: BLE001
            # Un fond illisible ne doit jamais empêcher l'impression du document.
            _logger.exception("Impossible d'appliquer le fond pleine page de la société %s", company.display_name)
            return pdf_content

    def _get_full_page_background_company(self, bodies, header, footer):
        """ Société dont le fond "Pleine page" doit être appliqué, ou un recordset vide.

        Seuls les rapports basés sur un external_layout portent la classe
        o_company_<id>_layout : les autres rapports (internal_layout, étiquettes...)
        ne sont pas concernés. Si un même lot mélange plusieurs sociétés, c'est la
        première rencontrée qui s'applique (wkhtmltopdf ne permet pas de savoir
        quelle page provient de quel document).
        """
        for html in (*bodies, header or '', footer or ''):
            match = COMPANY_LAYOUT_RE.search(str(html))
            if match:
                company = self.env['res.company'].sudo().browse(int(match.group(1))).exists()
                if company.layout_background == 'full_page' and company.layout_background_image:
                    return company
                break
        return self.env['res.company']

    def _apply_full_page_background(self, pdf_content, image_data):
        """ Pose image_data sous le contenu de chaque page, étirée sur toute la feuille.

        Les objets page d'origine sont conservés (seuls /Contents et /Resources sont
        remplacés) afin de garder intacts les signets et destinations utilisés par
        Odoo pour découper un PDF multi-enregistrements.
        """
        from reportlab.lib.utils import ImageReader  # noqa: PLC0415
        from reportlab.pdfgen import canvas  # noqa: PLC0415

        reader = OdooPdfFileReader(io.BytesIO(pdf_content), strict=False)
        pages = [reader.getPage(i) for i in range(reader.getNumPages())]

        # Une page de fond par page du document, aux mêmes dimensions (portrait / paysage).
        # reportlab n'embarque l'image qu'une seule fois pour toutes les pages.
        image = ImageReader(io.BytesIO(image_data))
        background_stream = io.BytesIO()
        can = canvas.Canvas(background_stream)
        for page in pages:
            width = float(abs(page.mediaBox.getWidth()))
            height = float(abs(page.mediaBox.getHeight()))
            can.setPageSize((width, height))
            can.drawImage(image, 0, 0, width, height, mask='auto')
            can.showPage()
        can.save()
        background_reader = OdooPdfFileReader(background_stream, strict=False)

        # getPage() renvoie des copies aplaties : on écrit le résultat dans les nœuds
        # réels de l'arbre /Pages, ceux que cloneReaderDocumentRoot va sérialiser.
        page_nodes = self._get_pdf_page_nodes(reader.trailer['/Root']['/Pages'])
        for index, (page, node) in enumerate(zip(pages, page_nodes)):
            background = background_reader.getPage(index)
            background.mergePage(page)  # le contenu du rapport est dessiné par-dessus le fond
            node[NameObject('/Contents')] = background['/Contents']
            node[NameObject('/Resources')] = background['/Resources']

        writer = OdooPdfFileWriter()
        writer.cloneReaderDocumentRoot(reader)
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()

    def _get_pdf_page_nodes(self, node):
        """ Feuilles de l'arbre /Pages, dans l'ordre des pages du document. """
        node = node.get_object()
        if node.get('/Type') == '/Pages':
            return [leaf for kid in node['/Kids'] for leaf in self._get_pdf_page_nodes(kid)]
        return [node]

