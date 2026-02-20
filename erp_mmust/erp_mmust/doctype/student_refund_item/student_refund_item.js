// student_refund.js

frappe.ui.form.on('Student Refund', {
    // parent form events here
    refresh: function (frm) {
        // ...
    }
});

// ─── CHILD TABLE EVENTS — must be in the PARENT's JS file ───
frappe.ui.form.on('Student Refund Item', {

    refundable_amount: function (frm, cdt, cdn) {
        // fires when refundable_amount changes in any row
        calculate_total(frm);
    },

    reference_name: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.reference_doctype && row.reference_name) {
            frappe.call({
                method: 'erp_mmust.services.refund_service.get_reference_amount',
                args: {
                    reference_doctype: row.reference_doctype,
                    reference_name: row.reference_name
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'original_amount', r.message.amount);
                        frappe.model.set_value(cdt, cdn, 'refundable_amount', r.message.amount);
                        calculate_total(frm);
                    }
                }
            });
        }
    },

    items_remove: function (frm) {
        // fires when a row is deleted
        calculate_total(frm);
    }
});

// ─── HELPER ───
function calculate_total(frm) {
    let total = 0;
    (frm.doc.items || []).forEach(row => {
        total += flt(row.refundable_amount || 0);
    });
    frm.set_value('total_amount', total);
    frm.refresh_field('total_amount');
}