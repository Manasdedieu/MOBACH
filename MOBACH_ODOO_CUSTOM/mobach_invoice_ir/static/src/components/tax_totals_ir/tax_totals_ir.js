/** @odoo-module **/

/**
 * MOBACH — Patch du widget TaxTotalsComponent (Odoo 19)
 *
 * Stratégie :
 *   Les données IR sont injectées côté Python dans le dict tax_totals
 *   (_compute_tax_totals surcharge). On les lit ici via this.totals
 *   (déjà parsé par formatData() de la classe parente).
 *
 *   On ajoute un getter irData et on patche le template OWL
 *   account.TaxTotalsField via t-inherit dans le fichier .xml.
 */

import { TaxTotalsComponent } from "@account/components/tax_totals/tax_totals";
import { patch } from "@web/core/utils/patch";
import { formatMonetary } from "@web/views/fields/formatters";

patch(TaxTotalsComponent.prototype, {

    /**
     * Lit les données IR depuis this.totals (dict injecté par Python).
     * this.totals est déjà disponible car formatData() est appelé dans setup().
     */
    get irData() {
        const t = this.totals;
        if (!t || (!t.has_ir && !t.retenue_amount)) {
            return { hasIr: false, taxName: '', irAmount: 0, netMandate: 0, hasRetenue: false, retenueAmount: 0 };
        }
        return {
            hasIr: !!t.has_ir,
            taxName: t.ir_tax_name || '',
            irAmount: t.ir_amount || 0,
            netMandate: t.amount_net_mandate || 0,
            hasRetenue: !!t.retenue_amount,
            retenueAmount: t.retenue_amount || 0,
        };
    },

    /**
     * Formate un montant avec la devise de la facture.
     * Utilise currency_id déjà présent dans this.totals.
     */
    formatIRAmount(value) {
        return formatMonetary(value, { currencyId: this.totals.currency_id });
    },
});
