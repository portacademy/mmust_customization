
// Copyright (c) 2026, Timothy Ajani and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student Refund', {

    setup: function (frm) {
        frm.set_query('sponsorship_allocation', function () {
            if (!frm.doc.funder) {
                frappe.msgprint({
                    title: 'Funder Required',
                    indicator: 'orange',
                    message: 'Please select a Funder (Donor) before selecting a Sponsorship Allocation.'
                });
                return { filters: { name: '__none__' } };
            }
            return {
                query: 'erp_mmust.erp_mmust.doctype.student_refund.student_refund.get_sponsorship_allocations',
                filters: {
                    funder: frm.doc.funder,
                    current_doc: frm.doc.name || ''
                }
            };
        });
        frm.set_query('bank_account', function () {
            return {
                filters: {
                    account_type: 'Bank',
                    is_group: 0,
                    company: frappe.defaults.get_user_default('company')
                }
            };
        });
        frm.set_query('sales_invoice', 'items', function () {  // no (frm, cdt, cdn) here
            return {
                query: 'erp_mmust.erp_mmust.doctype.student_refund.student_refund.get_hostel_invoices',
                filters: {
                    customer: frm.doc.source_student || '',
                    custom_session: frm.doc.hostel_session || '',
                    custom_semester: frm.doc.hostel_semester || ''
                }
            };
        });
        frm.set_query('source_student', function () {
            return {
                filters: {
                    customer_group: 'Student'
                }
            };
        });
    },

    source_student: function (frm) {
        frm.clear_table('items');
        frm.refresh_field('items');
    },

    hostel_session: function (frm) {
        frm.refresh_field('items');
    },

    hostel_semester: function (frm) {
        frm.refresh_field('items');
    },

    refresh: function (frm) {

        // if (!frm.doc.bank_account && frm.doc.action_type === 'Refund to Funder') {
        //     frappe.db.get_single_value('MMUST Donor Settings', 'default_payment_bank_account')
        //         .then(value => {
        //             if (value) frm.set_value('bank_account', value);
        //         });
        // }


        frm.trigger('toggle_fields');
        frm.trigger('add_print_cheque_button');

        // Disable sponsorship_allocation if no funder on load
        frm.set_df_property('sponsorship_allocation', 'read_only', frm.doc.funder ? 0 : 1);
        frm.refresh_field('sponsorship_allocation');
    },

    workflow_state: function (frm) {
        frm.trigger('add_print_cheque_button');
    },


    add_print_cheque_button: function (frm) {
        frm.remove_custom_button('Print Refund');
        frm.remove_custom_button('Print Receipt Cancellation');
        frm.remove_custom_button('Print Reallocation Receipt');

        if (frm.doc.docstatus !== 1) return;

        frappe.db.get_value('MMUST Donor Settings', 'MMUST Donor Settings', [
            'refund_print_format',
            'receipt_cancellation_print_format',
            'reallocation_print_format'
        ], function (settings) {

            if (frm.doc.action_type === 'Refund to Funder' &&
                frm.doc.workflow_state === 'Closed') {

                const format = settings.refund_print_format || 'Sponsorship Cheque Print Format';
                frm.add_custom_button(__('Print Refund'), function () {
                    const url = `/printview?doctype=${encodeURIComponent('Student Refund')}&name=${encodeURIComponent(frm.doc.name)}&format=${encodeURIComponent(format)}&no_letterhead=0`;
                    window.open(url, '_blank');
                }, __('Actions'));
            }

            if (frm.doc.action_type === 'Receipt Cancellation' &&
                frm.doc.workflow_state === 'Receipt Cancelled') {

                const format = settings.receipt_cancellation_print_format || 'Receipt Cancellation Print Format';
                frm.add_custom_button(__('Print Receipt Cancellation'), function () {
                    const url = `/printview?doctype=${encodeURIComponent('Student Refund')}&name=${encodeURIComponent(frm.doc.name)}&format=${encodeURIComponent(format)}&no_letterhead=0`;
                    window.open(url, '_blank');
                }, __('Actions'));
            }

            if (frm.doc.action_type === 'Reallocate to Student' &&
                frm.doc.workflow_state === 'Closed') {

                const format = settings.reallocation_print_format || 'Reallocation Print Format';
                frm.add_custom_button(__('Print Reallocation Receipt'), function () {
                    const url = `/printview?doctype=${encodeURIComponent('Student Refund')}&name=${encodeURIComponent(frm.doc.name)}&format=${encodeURIComponent(format)}&no_letterhead=0`;
                    window.open(url, '_blank');
                }, __('Actions'));
            }
        });
    },

    request_type: function (frm) {
        frm.trigger('toggle_fields');
        if (!['HELB', 'CDF', 'Scholarship'].includes(frm.doc.request_type)) {
            frm.set_value('sponsorship_allocation', '');
            frm.set_value('donation_amount', 0);
            frm.set_value('custom_cheque_id', '');
            frm.set_value('total_allocated_in_donation', 0);
            frm.set_value('amount_refunded_to_donor', 0);
            frm.clear_table('beneficiaries');
            frm.clear_table('reallocations');
            frm.clear_table('cancellation_beneficiaries');
            frm.refresh_field('beneficiaries');
            frm.refresh_field('reallocations');
            frm.refresh_field('cancellation_beneficiaries');
        }
    },

    action_type: function (frm) {
        // if (frm.doc.action_type === 'Refund to Funder' && !frm.doc.bank_account) {
        //     frappe.db.get_single_value('MMUST Donor Settings', 'default_payment_bank_account')
        //         .then(value => {
        //             if (value) frm.set_value('bank_account', value);
        //         });
        // }

        frm.trigger('toggle_fields');
        frm.trigger('add_print_cheque_button');

        // Reload sponsorship allocation data if already selected
        if (frm.doc.sponsorship_allocation) {
            frm.trigger('sponsorship_allocation');
        }
    },

    funder: function (frm) {
        // Clear sponsorship allocation when funder changes
        frm.set_value('sponsorship_allocation', '');

        // Enable/disable sponsorship_allocation based on whether funder is set
        frm.set_df_property('sponsorship_allocation', 'read_only', frm.doc.funder ? 0 : 1);
        frm.refresh_field('sponsorship_allocation');
    },

    sponsorship_allocation: function (frm) {
        if (!frm.doc.sponsorship_allocation) {
            frm.set_value('donation_amount', 0);
            frm.set_value('custom_cheque_id', '');
            frm.set_value('total_allocated_in_donation', 0);
            frm.set_value('amount_refunded_to_donor', 0);
            frm.clear_table('beneficiaries');
            frm.clear_table('reallocations');
            frm.clear_table('cancellation_beneficiaries');
            frm.refresh_field('beneficiaries');
            frm.refresh_field('reallocations');
            frm.refresh_field('cancellation_beneficiaries');
            return;
        }

        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Sponsorship Allocation',
                name: frm.doc.sponsorship_allocation
            },
            callback: function (r) {
                if (!r.message) return;
                let sa = r.message;

                frm.set_value('donation_amount', sa.amount || 0);
                frm.set_value('custom_cheque_id', sa.custom_cheque_id || '');
                frm.set_value('total_allocated_in_donation', sa.total_allocated || 0);

                if (frm.doc.action_type === 'Refund to Funder') {
                    frm.clear_table('beneficiaries');
                    (sa.beneficiaries || []).forEach(function (b) {
                        let row = frm.add_child('beneficiaries');
                        row.student = b.student;
                        row.student_name = b.student_name;
                        row.original_allocated_amount = flt(b.amount);
                        row.amount_to_be_refunded = 0;
                        row.student_balance = 0;
                    });
                    frm.refresh_field('beneficiaries');
                    frm.refresh();
                    frm.trigger('load_student_balances');

                    frappe.show_alert({
                        message: `Loaded ${(sa.beneficiaries || []).length} beneficiaries`,
                        indicator: 'green'
                    });

                } else if (frm.doc.action_type === 'Reallocate to Student') {
                    frm.clear_table('reallocations');
                    (sa.beneficiaries || []).forEach(function (b) {
                        let row = frm.add_child('reallocations');
                        row.source_student = b.student;
                        row.student_name = b.student_name;
                        row.original_allocated_amount = flt(b.amount);
                        row.student_balance = 0;
                        row.target_student = '';
                        row.amount_to_reallocate = 0;
                    });
                    frm.refresh_field('reallocations');
                    frm.refresh();
                    frm.trigger('load_reallocation_balances');

                    frappe.show_alert({
                        message: `Loaded ${(sa.beneficiaries || []).length} source students for reallocation`,
                        indicator: 'green'
                    });

                } else if (frm.doc.action_type === 'Receipt Cancellation') {
                    frm.clear_table('cancellation_beneficiaries');
                    (sa.beneficiaries || []).forEach(function (b) {
                        let row = frm.add_child('cancellation_beneficiaries');
                        row.student = b.student;
                        row.student_name = b.student_name;
                        row.original_allocated_amount = flt(b.amount);
                        row.student_balance = 0;
                    });
                    frm.refresh_field('cancellation_beneficiaries');
                    frm.refresh();
                    frm.trigger('load_cancellation_balances');

                    frappe.show_alert({
                        message: `Loaded ${(sa.beneficiaries || []).length} students for cancellation`,
                        indicator: 'green'
                    });
                }
            }
        });
    },

    // ─── LOAD BALANCES ────────────────────────────────────────────────────────

    load_student_balances: function (frm) {
        (frm.doc.beneficiaries || []).forEach(function (row) {
            if (!row.student) return;
            frappe.call({
                method: 'erp_mmust.services.refund_service.get_student_credit',
                args: { customer: row.student },
                callback: function (r) {
                    if (!r.message) return;
                    let balance = r.message.credit_balance || 0;
                    frappe.model.set_value(row.doctype, row.name, 'student_balance', balance);
                    if (balance > 0) {
                        frappe.show_alert({
                            message: `⚠️ ${row.student_name} has an outstanding balance of ₦${balance.toLocaleString()} — refund not allowed.`,
                            indicator: 'red'
                        }, 8);
                    }
                }
            });
        });
    },

    load_reallocation_balances: function (frm) {
        (frm.doc.reallocations || []).forEach(function (row) {
            if (!row.source_student) return;
            frappe.call({
                method: 'erp_mmust.services.refund_service.get_student_credit',
                args: { customer: row.source_student },
                callback: function (r) {
                    if (!r.message) return;
                    let balance = r.message.credit_balance || 0;
                    frappe.model.set_value(row.doctype, row.name, 'student_balance', balance);
                    if (balance > 0) {
                        frappe.show_alert({
                            message: `⚠️ ${row.student_name} has an outstanding balance of ₦${balance.toLocaleString()} — reallocation not allowed.`,
                            indicator: 'red'
                        }, 8);
                    }
                }
            });
        });
    },

    load_cancellation_balances: function (frm) {
        (frm.doc.cancellation_beneficiaries || []).forEach(function (row) {
            if (!row.student) return;
            frappe.call({
                method: 'erp_mmust.services.refund_service.get_student_credit',
                args: { customer: row.student },
                callback: function (r) {
                    if (!r.message) return;
                    frappe.model.set_value(
                        row.doctype, row.name,
                        'student_balance', r.message.credit_balance || 0
                    );
                }
            });
        });
    },

    // ─── RECALCULATE SUMMARIES ────────────────────────────────────────────────

    recalculate_refund_summary: function (frm) {
        let sum_to_refund = 0;
        (frm.doc.beneficiaries || []).forEach(function (row) {
            sum_to_refund += flt(row.amount_to_be_refunded);
        });
        frm.set_value('amount_refunded_to_donor', sum_to_refund);
        frm.set_value('total_amount', sum_to_refund);
    },

    recalculate_reallocation_summary: function (frm) {
        let sum_to_reallocate = 0;
        (frm.doc.reallocations || []).forEach(function (row) {
            sum_to_reallocate += flt(row.amount_to_reallocate);
        });
        frm.set_value('total_amount', sum_to_reallocate);
    },

    // ─── TOGGLE FIELDS ────────────────────────────────────────────────────────

    toggle_fields: function (frm) {
        let is_hostel = frm.doc.request_type === 'Hostel';
        let is_funder = ['HELB', 'CDF', 'Scholarship'].includes(frm.doc.request_type);
        let is_reallocation = frm.doc.action_type === 'Reallocate to Student';
        let is_refund = frm.doc.action_type === 'Refund to Funder';
        let is_cancellation = frm.doc.action_type === 'Receipt Cancellation';



        // Hostel items
        frm.toggle_display('section_items', is_hostel);
        frm.toggle_display('items', is_hostel);

        // Funder / sponsorship section (shared by all funder types)
        frm.toggle_display('section_funder', is_funder);
        frm.toggle_display('section_donation', is_funder);

        // Beneficiaries — Refund to Funder only
        frm.toggle_display('section_beneficiaries', is_funder && is_refund);
        frm.toggle_display('beneficiaries', is_funder && is_refund);

        // Reallocations — Reallocate to Student only
        frm.toggle_display('section_reallocation', is_funder && is_reallocation);
        frm.toggle_display('reallocations', is_funder && is_reallocation);

        // Cancellation beneficiaries — Receipt Cancellation only
        frm.toggle_display('section_cancellation', is_funder && is_cancellation);
        frm.toggle_display('cancellation_beneficiaries', is_funder && is_cancellation);

        // Cancellation info labels
        frm.toggle_display('cancellation_label_helb', is_cancellation && frm.doc.request_type === 'HELB');
        frm.toggle_display('cancellation_label_cdf', is_cancellation && frm.doc.request_type === 'CDF');

        // amount_refunded_to_donor only relevant for Refund to Funder
        frm.toggle_display('amount_refunded_to_donor', is_refund);

        frm.toggle_display('bank_account', is_funder && is_refund);
        // frm.set_df_property('bank_account', 'reqd', is_funder && is_refund ? 1 : 0);

        frm.toggle_display('section_hostel_details', is_hostel);
        frm.toggle_display('source_student', is_hostel);
        frm.toggle_display('hostel_session', is_hostel);
        frm.toggle_display('hostel_semester', is_hostel);
        frm.toggle_display('narration', is_hostel);
    }

});


// ─── CHILD TABLE — Student Refund Beneficiary ────────────────────────────────

frappe.ui.form.on('Student Refund Beneficiary', {

    amount_to_be_refunded: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        let original = flt(row.original_allocated_amount);
        let student_balance = flt(row.student_balance);
        let to_refund = flt(row.amount_to_be_refunded);

        if (student_balance > 0) {
            frappe.msgprint({
                title: 'Refund Not Allowed',
                indicator: 'red',
                message: `<b>${row.student_name}</b> has an outstanding balance of <b>₦${student_balance.toLocaleString()}</b> (they owe money). Refunds cannot be processed for students with outstanding balances.`
            });
            frappe.model.set_value(cdt, cdn, 'amount_to_be_refunded', 0);
            return;
        }

        let credit_balance = Math.abs(student_balance);

        if (to_refund > original) {
            frappe.msgprint({
                title: 'Validation Error',
                indicator: 'red',
                message: `<b>${row.student_name}</b>: Amount to be Refunded (₦${to_refund.toLocaleString()}) cannot exceed Original Allocated Amount (₦${original.toLocaleString()}).`
            });
            frappe.model.set_value(cdt, cdn, 'amount_to_be_refunded', original);
            return;
        }

        if (to_refund > credit_balance) {
            frappe.msgprint({
                title: 'Validation Error',
                indicator: 'red',
                message: `<b>${row.student_name}</b>: Amount to be Refunded (₦${to_refund.toLocaleString()}) cannot exceed the student's available credit balance (₦${credit_balance.toLocaleString()}).`
            });
            frappe.model.set_value(cdt, cdn, 'amount_to_be_refunded', credit_balance);
            return;
        }

        frm.trigger('recalculate_refund_summary');
    },

    beneficiaries_remove: function (frm) {
        frm.trigger('recalculate_refund_summary');
    }
});


// ─── CHILD TABLE — Student Refund Reallocation ───────────────────────────────

frappe.ui.form.on('Student Refund Reallocation', {

    target_student: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.target_student === row.source_student) {
            frappe.msgprint({
                title: 'Invalid Selection',
                indicator: 'red',
                message: 'Target student cannot be the same as source student.'
            });
            frappe.model.set_value(cdt, cdn, 'target_student', '');
            return;
        }

        let source_students = (frm.doc.reallocations || []).map(r => r.source_student);
        if (source_students.includes(row.target_student)) {
            frappe.msgprint({
                title: 'Invalid Selection',
                indicator: 'orange',
                message: `<b>${row.target_student}</b> is already a source student in this sponsorship allocation. Please select a different target student.`
            });
            frappe.model.set_value(cdt, cdn, 'target_student', '');
        }
    },

    amount_to_reallocate: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        let original = flt(row.original_allocated_amount);
        let student_balance = flt(row.student_balance);
        let to_reallocate = flt(row.amount_to_reallocate);

        if (student_balance > 0) {
            frappe.msgprint({
                title: 'Reallocation Not Allowed',
                indicator: 'red',
                message: `<b>${row.student_name}</b> has an outstanding balance of <b>₦${student_balance.toLocaleString()}</b> (they owe money). Reallocations cannot be processed for students with outstanding balances.`
            });
            frappe.model.set_value(cdt, cdn, 'amount_to_reallocate', 0);
            return;
        }

        let credit_balance = Math.abs(student_balance);

        if (to_reallocate > original) {
            frappe.msgprint({
                title: 'Validation Error',
                indicator: 'red',
                message: `<b>${row.student_name}</b>: Amount to Reallocate (₦${to_reallocate.toLocaleString()}) cannot exceed Original Allocated Amount (₦${original.toLocaleString()}).`
            });
            frappe.model.set_value(cdt, cdn, 'amount_to_reallocate', original);
            return;
        }

        if (to_reallocate > credit_balance) {
            frappe.msgprint({
                title: 'Validation Error',
                indicator: 'red',
                message: `<b>${row.student_name}</b>: Amount to Reallocate (₦${to_reallocate.toLocaleString()}) cannot exceed the student's available credit balance (₦${credit_balance.toLocaleString()}).`
            });
            frappe.model.set_value(cdt, cdn, 'amount_to_reallocate', credit_balance);
            return;
        }

        frm.trigger('recalculate_reallocation_summary');
    },

    reallocations_remove: function (frm) {
        frm.trigger('recalculate_reallocation_summary');
    }
});


// ─── CHILD TABLE — Student Refund Item (Hostel) ──────────────────────────────

frappe.ui.form.on('Student Refund Item', {
    sales_invoice: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.sales_invoice) return;

        frappe.call({
            method: 'frappe.client.get',
            args: { doctype: 'Sales Invoice', name: row.sales_invoice },
            callback: function (r) {
                if (!r.message) return;
                let si = r.message;
                frappe.model.set_value(cdt, cdn, 'original_amount', si.grand_total);
                frappe.model.set_value(cdt, cdn, 'customer_name', si.customer_name);
                frappe.model.set_value(cdt, cdn, 'custom_semester', si.custom_semester || '');
                frappe.model.set_value(cdt, cdn, 'custom_level', si.custom_level || '');
                frappe.model.set_value(cdt, cdn, 'custom_session', si.custom_session || '');
            }
        });
    },

    refundable_amount: function (frm) {
        let total = 0;
        (frm.doc.items || []).forEach(row => {
            total += flt(row.refundable_amount || 0);
        });
        frm.set_value('total_amount', total);
        frm.refresh_field('total_amount');
    },

    items_remove: function (frm) {
        let total = 0;
        (frm.doc.items || []).forEach(row => {
            total += flt(row.refundable_amount || 0);
        });
        frm.set_value('total_amount', total);
    },

    refundable_amount: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let original = flt(row.original_amount);
        let refundable = flt(row.refundable_amount);

        if (refundable > original && original > 0) {
            frappe.msgprint({
                title: 'Validation Error',
                indicator: 'red',
                message: `<b>${row.customer_name || 'Row ' + row.idx}</b>: 
                    Amount Due for Refund (<b>${format_currency(refundable)}</b>) 
                    cannot exceed Invoice Amount (<b>${format_currency(original)}</b>).`
            });
            frappe.model.set_value(cdt, cdn, 'refundable_amount', original);
            return;
        }

        // recalculate total
        let total = 0;
        (frm.doc.items || []).forEach(r => {
            total += flt(r.refundable_amount || 0);
        });
        frm.set_value('total_amount', total);
        frm.refresh_field('total_amount');
    },
});