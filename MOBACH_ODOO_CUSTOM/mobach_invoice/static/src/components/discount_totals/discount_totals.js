/** @odoo-module **/

import { TaxTotalsComponent } from "@account/components/tax_totals/tax_totals";
import {
    SectionAndNoteListRenderer,
    getSectionRecords,
} from "@account/components/section_and_note_fields_backend/section_and_note_fields_backend";
import { patch } from "@web/core/utils/patch";
import { registry } from "@web/core/registry";
import { formatMonetary } from "@web/views/fields/formatters";

/**
 * Patch du widget TaxTotalsComponent pour afficher la Remise et le Nouveau HT
 * juste en dessous du Montant HT dans le résumé des totaux (factures et devis).
 */
patch(TaxTotalsComponent.prototype, {
    get discountData() {
        const t = this.totals;
        if (!t || !t.has_global_discount) {
            return {
                hasDiscount: false,
                grossUntaxedAmount: 0,
                discountAmount: 0,
                netUntaxedAmount: 0,
            };
        }
        return {
            hasDiscount: true,
            grossUntaxedAmount: t.gross_untaxed_amount || 0,
            discountAmount: t.global_discount_amount || 0,
            netUntaxedAmount: t.net_untaxed_amount || 0,
        };
    },

    formatDiscountMonetary(value) {
        return formatMonetary(value, { currencyId: this.totals.currency_id });
    },
});

/**
 * Patch du renderer des lignes (devis/commandes et factures) pour masquer
 * visuellement les lignes d'articles de remise globale ou fixe tout en les
 * conservant dans le modèle pour la justesse des écritures et calculs.
 */
patch(SectionAndNoteListRenderer.prototype, {
    getRowClass(record) {
        let classNames = super.getRowClass(record);
        if (record.data?.is_global_discount_line) {
            classNames = `${classNames} d-none`;
        }
        return classNames;
    },

    getFormattedValue(column, record) {
        if (this.isSection(record) && this.props.aggregatedFields.includes(column.name)) {
            const total = getSectionRecords(this.props.list, record)
                .filter((rec) => !this.isSection(rec) && !rec.data?.is_global_discount_line)
                .reduce((sum, rec) => sum + rec.data[column.name], 0);
            const formatter = registry.category("formatters").get(column.fieldType, (val) => val);
            return formatter(total, {
                ...formatter.extractOptions?.(column),
                data: record.data,
                field: record.fields[column.name],
            });
        }
        return super.getFormattedValue(column, record);
    },
});
