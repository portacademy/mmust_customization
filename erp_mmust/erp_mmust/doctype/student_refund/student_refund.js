
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
        // frm.set_query('cheque_donation', function () {
        //     return {
        //         filters: {
        //             donor: frm.doc.funder || '',
        //             docstatus: 1
        //         },
        //         query: 'erp_mmust.erp_mmust.doctype.student_refund.student_refund.get_cheque_donations',
        //         filter_args: {
        //             funder: frm.doc.funder || ''
        //         }
        //     };
        // });
        frm.set_query('cheque_donation', function () {
            return {
                query: 'erp_mmust.erp_mmust.doctype.student_refund.student_refund.get_cheque_donations',
                filters: {
                    funder: frm.doc.funder || '',
                    current_doc: frm.doc.name || ''
                }
            };
        });
        frm.set_query('graduation_student', function () {
            return {
                filters: {
                    customer_group: 'Student'
                }
            };
        });

        frm.set_query('graduation_bank_account', function () {
            return {
                filters: {
                    account_type: 'Bank',
                    is_group: 0,
                    company: frappe.defaults.get_user_default('company')
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

        // if (frm.doc.action_type === 'Receipt Cancellation') {
        //     frappe.after_render(function () {
        //         const grid = frm.get_field('cancellation_beneficiaries').grid;
        //         if (grid) {
        //             grid.cannot_add_rows = true;
        //             grid.cannot_delete_rows = true;
        //             grid.wrapper.find('.grid-add-row').hide();
        //             grid.wrapper.find('.grid-remove-rows').hide();
        //             grid.wrapper.find('.row-check').hide();
        //         }
        //     });
        // }

        if (frm.doc.action_type === 'Receipt Cancellation') {
            setTimeout(function () {
                const grid = frm.get_field('cancellation_beneficiaries') &&
                    frm.get_field('cancellation_beneficiaries').grid;
                if (grid) {
                    grid.cannot_add_rows = true;
                    grid.cannot_delete_rows = true;
                    grid.wrapper.find('.grid-add-row').hide();
                    grid.wrapper.find('.grid-remove-rows').hide();
                    grid.wrapper.find('.row-check').hide();
                }
            }, 300);
        }

        frm.trigger('lock_narration_fields');
        frm.trigger('lock_graduation_fields');
    },

    // lock_narration_fields: function (frm) {
    //     const role_field_map = {
    //         'Student Finance Accountant': 'accountant_narration',
    //         'Finance Officer': 'finance_officer_narration',
    //         'Internal Auditor': 'internal_auditor_narration',
    //         'Payable Accountant': 'payable_accountant_narration',
    //         'DVC Finance': 'dvc_narration',
    //         'Accounts Manager': 'accounts_manager_narration'
    //     };

    //     const user_roles = frappe.user_roles || [];
    //     const is_submitted = frm.doc.docstatus === 1;

    //     // Lock ALL narration fields first — always
    //     Object.values(role_field_map).forEach(function (fieldname) {
    //         frm.set_df_property(fieldname, 'read_only', 1);
    //     });

    //     // Only unlock if document is submitted
    //     if (!is_submitted) return;

    //     // Accounts Manager can edit all
    //     if (user_roles.includes('Accounts Manager')) {
    //         Object.values(role_field_map).forEach(function (fieldname) {
    //             frm.set_df_property(fieldname, 'read_only', 0);
    //         });
    //     } else {
    //         // Unlock ONLY the specific field for the specific role
    //         // If user has Finance Officer → only finance_officer_narration unlocks
    //         // Even if user has multiple roles, each field is independent
    //         Object.entries(role_field_map).forEach(function ([role, fieldname]) {
    //             if (user_roles.includes(role)) {
    //                 frm.set_df_property(fieldname, 'read_only', 0);
    //             }
    //         });
    //     }

    //     frm.refresh_fields(Object.values(role_field_map));
    // },

    // lock_narration_fields: function (frm) {
    //     const role_field_map = {
    //         'Registrar': 'registrar_narration',
    //         'Senior Accountant Students Finance': 'senior_accountant_narration',
    //         'Student Finance Accountant': 'accountant_narration',
    //         'Finance Officer': 'finance_officer_narration',
    //         'Internal Auditor': 'internal_auditor_narration',
    //         'Payable Accountant': 'payable_accountant_narration',
    //         'DVC Finance': 'dvc_narration',
    //         // 'Accounts Manager': 'accounts_manager_narration'
    //     };

    //     const user_roles = frappe.user_roles || [];
    //     const is_submitted = frm.doc.docstatus === 1;

    //     // Lock ALL narration fields first — always
    //     Object.values(role_field_map).forEach(function (fieldname) {
    //         frm.set_df_property(fieldname, 'read_only', 1);
    //     });

    //     // Accounts Manager can edit all regardless of docstatus
    //     if (user_roles.includes('Accounts Manager')) {
    //         Object.values(role_field_map).forEach(function (fieldname) {
    //             frm.set_df_property(fieldname, 'read_only', 0);
    //         });

    //     } else if (!is_submitted) {
    //         // On draft — only Finance Officer can write their narration
    //         // if (user_roles.includes('Finance Officer')) {
    //         //     frm.set_df_property('finance_officer_narration', 'read_only', 0);
    //         // }
    //         // if (user_roles.includes('Registrar')) {
    //         //     frm.set_df_property('registrar_narration', 'read_only', 0);
    //         // }

    //         const is_graduation_refund = frm.doc.request_type === 'Graduation' &&
    //             frm.doc.action_type === 'Refund a Student';

    //         if (is_graduation_refund) {
    //             // Graduation Refund Draft — only Registrar can write
    //             if (user_roles.includes('Registrar')) {
    //                 frm.set_df_property('registrar_narration', 'read_only', 0);
    //                 frm.set_df_property('section_narrations', 'collapsible', 0);
    //                 frm.refresh_field('section_narrations');
    //             }
    //         } else {
    //             // All other drafts — only Finance Officer can write
    //             if (user_roles.includes('Finance Officer')) {
    //                 frm.set_df_property('finance_officer_narration', 'read_only', 0);
    //             }
    //         }

    //     } else {
    //         // On submitted — unlock only the field matching the user's role
    //         Object.entries(role_field_map).forEach(function ([role, fieldname]) {
    //             if (user_roles.includes(role)) {
    //                 frm.set_df_property(fieldname, 'read_only', 0);
    //             }
    //         });
    //     }

    //     frm.refresh_fields(Object.values(role_field_map));
    // },

    // lock_narration_fields: function (frm) {
    //     const role_field_map = {
    //         'Registrar': 'registrar_narration',
    //         'Senior Accountant Students Finance': 'senior_accountant_narration',
    //         'Student Finance Accountant': 'accountant_narration',
    //         'Finance Officer': 'finance_officer_narration',
    //         'Internal Auditor': 'internal_auditor_narration',
    //         'Payable Accountant': 'payable_accountant_narration',
    //         'DVC Finance': 'dvc_narration',
    //     };

    //     const user_roles = frappe.user_roles || [];
    //     const is_submitted = frm.doc.docstatus === 1;
    //     const workflow_state = frm.doc.workflow_state;

    //     // Lock ALL narration fields first — always
    //     Object.values(role_field_map).forEach(function (fieldname) {
    //         frm.set_df_property(fieldname, 'read_only', 1);
    //     });

    //     const terminal_states = ['Closed', 'Receipt Cancelled', 'Hostel Closed'];
    //     const is_closed = terminal_states.includes(workflow_state);

    //     // Hide ALL individual narration fields when Closed — only trail remains
    //     if (is_closed) {
    //         Object.values(role_field_map).forEach(function (fieldname) {
    //             frm.toggle_display(fieldname, false);
    //         });
    //         frm.toggle_display('section_narrations', false);
    //         frm.refresh_fields(Object.values(role_field_map));
    //         return; // exit early
    //     }

    //     // Accounts Manager can edit all regardless of docstatus
    //     if (user_roles.includes('Accounts Manager')) {
    //         Object.values(role_field_map).forEach(function (fieldname) {
    //             frm.set_df_property(fieldname, 'read_only', 0);
    //         });

    //     } else if (!is_submitted) {
    //         const is_graduation_refund = frm.doc.request_type === 'Graduation' &&
    //             frm.doc.action_type === 'Refund a Student';

    //         if (is_graduation_refund) {
    //             if (user_roles.includes('Registrar')) {
    //                 frm.set_df_property('registrar_narration', 'read_only', 0);
    //                 frm.set_df_property('section_narrations', 'collapsible', 0);
    //                 frm.refresh_field('section_narrations');
    //             }
    //         } else {
    //             if (user_roles.includes('Finance Officer')) {
    //                 frm.set_df_property('finance_officer_narration', 'read_only', 0);
    //             }
    //         }

    //     } else {
    //         // On submitted — unlock only the field matching the user's role
    //         Object.entries(role_field_map).forEach(function ([role, fieldname]) {
    //             if (user_roles.includes(role)) {
    //                 frm.set_df_property(fieldname, 'read_only', 0);
    //             }
    //         });
    //     }

    //     frm.refresh_fields(Object.values(role_field_map));
    // },

    lock_narration_fields: function (frm) {
        const role_field_map = {
            'Registrar': 'registrar_narration',
            'Senior Accountant Students Finance': 'senior_accountant_narration',
            'Student Finance Accountant': 'accountant_narration',
            'Finance Officer': 'finance_officer_narration',
            'Internal Auditor': 'internal_auditor_narration',
            'Payable Accountant': 'payable_accountant_narration',
            'DVC Finance': 'dvc_narration',
        };

        const user_roles = frappe.user_roles || [];
        const is_submitted = frm.doc.docstatus === 1;
        const workflow_state = frm.doc.workflow_state;
        const terminal_states = ['Closed', 'Receipt Cancelled', 'Hostel Closed'];
        const is_closed = terminal_states.includes(workflow_state);

        // Lock ALL narration fields first — always
        Object.values(role_field_map).forEach(function (fieldname) {
            frm.set_df_property(fieldname, 'read_only', 1);
        });

        // Hide ALL individual narration fields when Closed — only trail remains
        if (is_closed) {
            Object.values(role_field_map).forEach(function (fieldname) {
                frm.toggle_display(fieldname, false);
            });
            frm.toggle_display('section_narrations', false);
            frm.toggle_display('section_narrations_2', false);
            frm.toggle_display('section_narrations_3', false);
            frm.refresh_fields(Object.values(role_field_map));
            return;
        }

        // Accounts Manager sees and edits all
        if (user_roles.includes('Accounts Manager')) {
            Object.entries(role_field_map).forEach(function ([role, fieldname]) {
                frm.toggle_display(fieldname, true);
                frm.set_df_property(fieldname, 'read_only', 0);
            });

        } else if (!is_submitted) {
            const is_graduation_refund = frm.doc.request_type === 'Graduation' &&
                frm.doc.action_type === 'Refund a Student';

            // Hide all first, then show only relevant
            Object.entries(role_field_map).forEach(function ([role, fieldname]) {
                const belongs_to_user = user_roles.includes(role);
                frm.toggle_display(fieldname, belongs_to_user);
                if (belongs_to_user) {
                    frm.set_df_property(fieldname, 'read_only', 0);
                }
            });

            // Extra: on draft, only Registrar (graduation) or Finance Officer (others) should write
            if (is_graduation_refund) {
                if (user_roles.includes('Registrar')) {
                    frm.set_df_property('section_narrations', 'collapsible', 0);
                    frm.refresh_field('section_narrations');
                }
            }

        } else {
            // On submitted — show only the field for the user's role, hide the rest
            Object.entries(role_field_map).forEach(function ([role, fieldname]) {
                const belongs_to_user = user_roles.includes(role);
                frm.toggle_display(fieldname, belongs_to_user);
                if (belongs_to_user) {
                    frm.set_df_property(fieldname, 'read_only', 0);
                }
            });
        }

        frm.refresh_fields(Object.values(role_field_map));
    },


    // lock_graduation_fields: function (frm) {
    //     const user_roles = frappe.user_roles || [];
    //     const workflow_state = frm.doc.workflow_state;
    //     const is_graduation = frm.doc.request_type === 'Graduation' &&
    //         frm.doc.action_type === 'Refund a Student';

    //     if (!is_graduation) return;

    //     // Lock both fields by default
    //     frm.set_df_property('graduation_amount_to_refund', 'read_only', 1);
    //     frm.set_df_property('graduation_bank_account', 'read_only', 1);

    //     // Lock permanently when Closed — nobody can edit, even Accounts Manager
    //     if (is_closed) {
    //         frm.set_df_property('graduation_amount_to_refund', 'read_only', 1);
    //         frm.set_df_property('graduation_bank_account', 'read_only', 1);
    //         frm.refresh_field('graduation_amount_to_refund');
    //         frm.refresh_field('graduation_bank_account');
    //         return; // exit early — no further unlocking
    //     }

    //     // Only Senior Accountant can edit, and only at their stage
    //     if (
    //         user_roles.includes('Senior Accountant Students Finance') &&
    //         workflow_state === 'Pending Senior Accountant'
    //     ) {
    //         frm.set_df_property('graduation_amount_to_refund', 'read_only', 0);
    //         frm.set_df_property('graduation_bank_account', 'read_only', 0);
    //     }

    //     // Accounts Manager can edit except when Closed (handled above)
    //     if (user_roles.includes('Accounts Manager')) {
    //         frm.set_df_property('graduation_amount_to_refund', 'read_only', 0);
    //         frm.set_df_property('graduation_bank_account', 'read_only', 0);
    //     }

    //     frm.refresh_field('graduation_amount_to_refund');
    //     frm.refresh_field('graduation_bank_account');
    // },

    lock_graduation_fields: function (frm) {
        const user_roles = frappe.user_roles || [];
        const workflow_state = frm.doc.workflow_state;
        const is_graduation = frm.doc.request_type === 'Graduation' &&
            frm.doc.action_type === 'Refund a Student';
        const terminal_states = ['Closed', 'Receipt Cancelled', 'Hostel Closed'];
        const is_closed = terminal_states.includes(workflow_state);

        if (!is_graduation) return;

        // Lock both fields by default
        frm.set_df_property('graduation_amount_to_refund', 'read_only', 1);
        frm.set_df_property('graduation_bank_account', 'read_only', 1);

        if (is_closed) {
            frm.refresh_field('graduation_amount_to_refund');
            frm.refresh_field('graduation_bank_account');
            return;
        }

        if (
            user_roles.includes('Senior Accountant Students Finance') &&
            workflow_state === 'Pending Senior Accountant'
        ) {
            frm.set_df_property('graduation_amount_to_refund', 'read_only', 0);
            frm.set_df_property('graduation_bank_account', 'read_only', 0);
        }

        if (user_roles.includes('Accounts Manager')) {
            frm.set_df_property('graduation_amount_to_refund', 'read_only', 0);
            frm.set_df_property('graduation_bank_account', 'read_only', 0);
        }

        frm.refresh_field('graduation_amount_to_refund');
        frm.refresh_field('graduation_bank_account');
    },

    workflow_state: function (frm) {
        frm.trigger('add_print_cheque_button');
    },


    add_print_cheque_button: function (frm) {
        frm.remove_custom_button('Print Cheque');
        frm.remove_custom_button('Print Receipt Cancellation');
        frm.remove_custom_button('Print Reallocation Receipt');

        if (frm.doc.docstatus !== 1) return;

        frappe.db.get_value('MMUST Donor Settings', 'MMUST Donor Settings', [
            'refund_print_format',
            'receipt_cancellation_print_format',
            'reallocation_print_format',
            'graduation_refund_print_format'
        ], function (settings) {

            if (frm.doc.action_type === 'Refund to Funder' &&
                frm.doc.workflow_state === 'Closed') {

                const format = settings.refund_print_format || 'Sponsorship Cheque Print Format';
                frm.add_custom_button(__('Print Cheque'), function () {
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

            if (frm.doc.action_type === 'Refund a Student' &&
                frm.doc.workflow_state === 'Closed') {

                const format = settings.graduation_refund_print_format || 'Graduation Refund Print Format';
                frm.add_custom_button(__('Print Graduation Refund'), function () {
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

        // if (frm.doc.request_type === 'Graduation' &&
        //     frm.doc.action_type === 'Refund a Student' &&
        //     frm.doc.docstatus === 0 &&
        //     frm.doc.workflow_state === 'Draft') {
        //     frm.set_value('workflow_state', 'Graduation Refund Draft');
        // }
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

        if (frm.doc.action_type !== 'Receipt Cancellation') {
            frm.set_value('cheque_donation', '');
            frm.clear_table('cancellation_allocations');
            frm.clear_table('cancellation_beneficiaries');
            frm.refresh_field('cancellation_allocations');
            frm.refresh_field('cancellation_beneficiaries');
        }

        // Reload sponsorship allocation data if already selected
        if (frm.doc.sponsorship_allocation) {
            frm.trigger('sponsorship_allocation');
        }

        // if (frm.doc.request_type === 'Graduation' &&
        //     frm.doc.action_type === 'Refund a Student' &&
        //     frm.doc.docstatus === 0 &&
        //     frm.doc.workflow_state === 'Draft') {
        //     frm.set_value('workflow_state', 'Graduation Refund Draft');
        // }
    },

    funder: function (frm) {
        // Clear sponsorship allocation when funder changes
        // frm.set_value('sponsorship_allocation', '');

        // // Enable/disable sponsorship_allocation based on whether funder is set
        // frm.set_df_property('sponsorship_allocation', 'read_only', frm.doc.funder ? 0 : 1);
        // frm.refresh_field('sponsorship_allocation');

        frm.set_value('sponsorship_allocation', '');
        frm.set_value('cheque_donation', '');
        frm.clear_table('cancellation_allocations');
        frm.clear_table('cancellation_beneficiaries');
        frm.refresh_field('cancellation_allocations');
        frm.refresh_field('cancellation_beneficiaries');

        frm.set_df_property('sponsorship_allocation', 'read_only', frm.doc.funder ? 0 : 1);
        frm.refresh_field('sponsorship_allocation');

        frm.trigger('toggle_fields');
    },

    // cheque_donation: function (frm) {
    //     if (!frm.doc.cheque_donation) {
    //         frm.clear_table('cancellation_allocations');
    //         frm.clear_table('cancellation_beneficiaries');
    //         frm.refresh_field('cancellation_allocations');
    //         frm.refresh_field('cancellation_beneficiaries');
    //         return;
    //     }

    //     frappe.call({
    //         method: 'erp_mmust.erp_mmust.doctype.student_refund.student_refund.get_cancellation_data',
    //         args: {
    //             donation: frm.doc.cheque_donation,
    //             funder: frm.doc.funder
    //         },
    //         callback: function (r) {
    //             if (!r.message) return;

    //             let data = r.message;

    //             // Fill cancellation_allocations table
    //             frm.clear_table('cancellation_allocations');
    //             (data.allocations || []).forEach(function (sa) {
    //                 let row = frm.add_child('cancellation_allocations');
    //                 row.sponsorship_allocation = sa.name;
    //                 row.receipt_no = sa.receipt_no;
    //                 row.amount = sa.amount;
    //                 row.total_allocated = sa.total_allocated;
    //             });
    //             frm.refresh_field('cancellation_allocations');

    //             // Fill cancellation_beneficiaries table
    //             frm.clear_table('cancellation_beneficiaries');
    //             (data.beneficiaries || []).forEach(function (b) {
    //                 let row = frm.add_child('cancellation_beneficiaries');
    //                 row.student = b.student;
    //                 row.student_name = b.student_name;
    //                 row.original_allocated_amount = b.amount;
    //                 row.student_balance = 0;
    //             });
    //             frm.refresh_field('cancellation_beneficiaries');
    //             frm.refresh();
    //             frm.trigger('load_cancellation_balances');

    //             frappe.show_alert({
    //                 message: `Loaded ${data.allocations.length} allocations and ${data.beneficiaries.length} students`,
    //                 indicator: 'green'
    //             });
    //         }
    //     });
    // },

    // sponsorship_allocation: function (frm) {
    //     if (!frm.doc.sponsorship_allocation) {
    //         frm.set_value('batch_number', '');
    //         frm.set_value('donation_amount', 0);
    //         frm.set_value('custom_cheque_id', '');
    //         frm.set_value('total_allocated_in_donation', 0);
    //         frm.set_value('amount_refunded_to_donor', 0);
    //         frm.clear_table('beneficiaries');
    //         frm.clear_table('reallocations');
    //         frm.clear_table('cancellation_beneficiaries');
    //         frm.refresh_field('beneficiaries');
    //         frm.refresh_field('reallocations');
    //         frm.refresh_field('cancellation_beneficiaries');
    //         return;
    //     }

    //     frappe.call({
    //         method: 'frappe.client.get',
    //         args: {
    //             doctype: 'Sponsorship Allocation',
    //             name: frm.doc.sponsorship_allocation
    //         },
    //         callback: function (r) {
    //             if (!r.message) return;
    //             let sa = r.message;

    //             frm.set_value('donation_amount', sa.amount || 0);
    //             frm.set_value('custom_cheque_id', sa.custom_cheque_id || '');
    //             frm.set_value('total_allocated_in_donation', sa.total_allocated || 0);
    //             frm.set_value('batch_number', frm.doc.sponsorship_allocation || '');

    //             if (frm.doc.action_type === 'Refund to Funder') {
    //                 frm.clear_table('beneficiaries');
    //                 (sa.beneficiaries || []).forEach(function (b) {
    //                     let row = frm.add_child('beneficiaries');
    //                     row.student = b.student;
    //                     row.student_name = b.student_name;
    //                     row.original_allocated_amount = flt(b.amount);
    //                     row.amount_to_be_refunded = 0;
    //                     row.student_balance = 0;
    //                 });
    //                 frm.refresh_field('beneficiaries');
    //                 frm.refresh();
    //                 frm.trigger('load_student_balances');

    //                 frappe.show_alert({
    //                     message: `Loaded ${(sa.beneficiaries || []).length} beneficiaries`,
    //                     indicator: 'green'
    //                 });

    //             } else if (frm.doc.action_type === 'Reallocate to Student') {
    //                 frm.clear_table('reallocations');
    //                 (sa.beneficiaries || []).forEach(function (b) {
    //                     let row = frm.add_child('reallocations');
    //                     row.source_student = b.student;
    //                     row.student_name = b.student_name;
    //                     row.original_allocated_amount = flt(b.amount);
    //                     row.student_balance = 0;
    //                     row.target_student = '';
    //                     row.amount_to_reallocate = 0;
    //                 });
    //                 frm.refresh_field('reallocations');
    //                 frm.refresh();
    //                 frm.trigger('load_reallocation_balances');

    //                 frappe.show_alert({
    //                     message: `Loaded ${(sa.beneficiaries || []).length} source students for reallocation`,
    //                     indicator: 'green'
    //                 });

    //             } else if (frm.doc.action_type === 'Receipt Cancellation') {
    //                 frm.clear_table('cancellation_beneficiaries');
    //                 (sa.beneficiaries || []).forEach(function (b) {
    //                     let row = frm.add_child('cancellation_beneficiaries');
    //                     row.student = b.student;
    //                     row.student_name = b.student_name;
    //                     row.original_allocated_amount = flt(b.amount);
    //                     row.student_balance = 0;
    //                 });
    //                 frm.refresh_field('cancellation_beneficiaries');
    //                 frm.refresh();
    //                 frm.trigger('load_cancellation_balances');

    //                 // ← ADD THIS after load_cancellation_balances
    //                 frappe.after_render(function () {
    //                     const grid = frm.get_field('cancellation_beneficiaries').grid;
    //                     if (grid) {
    //                         grid.cannot_add_rows = true;
    //                         grid.cannot_delete_rows = true;
    //                         grid.wrapper.find('.grid-add-row').hide();
    //                         grid.wrapper.find('.grid-remove-rows').hide();
    //                         grid.wrapper.find('.row-check').hide();
    //                     }
    //                 });

    //                 frappe.show_alert({
    //                     message: `Loaded ${(sa.beneficiaries || []).length} students for cancellation`,
    //                     indicator: 'green'
    //                 });
    //             }
    //         }
    //     });
    // },

    // ─── LOAD BALANCES ────────────────────────────────────────────────────────

    cheque_donation: function (frm) {
        if (!frm.doc.cheque_donation) {
            frm.clear_table('cancellation_allocations');
            frm.clear_table('cancellation_beneficiaries');
            frm.refresh_field('cancellation_allocations');
            frm.refresh_field('cancellation_beneficiaries');
            frm.trigger('toggle_fields');
            return;
        }

        frappe.call({
            method: 'erp_mmust.erp_mmust.doctype.student_refund.student_refund.get_cancellation_data',
            args: {
                donation: frm.doc.cheque_donation,
                funder: frm.doc.funder
            },
            callback: function (r) {
                if (!r.message) return;

                let data = r.message;

                // Clear tables regardless
                frm.clear_table('cancellation_allocations');
                frm.clear_table('cancellation_beneficiaries');

                if (!data.allocations || data.allocations.length === 0) {
                    // No allocations — clear and hide tables
                    frm.refresh_field('cancellation_allocations');
                    frm.refresh_field('cancellation_beneficiaries');
                    frm.toggle_display('section_cancellation_allocations', false);
                    frm.toggle_display('section_cancellation', false);
                    frm.toggle_display('cancellation_beneficiaries', false);
                    return;
                }

                // Fill cancellation_allocations table
                (data.allocations || []).forEach(function (sa) {
                    let row = frm.add_child('cancellation_allocations');
                    row.sponsorship_allocation = sa.name;
                    row.receipt_no = sa.receipt_no;
                    row.amount = sa.amount;
                    row.total_allocated = sa.total_allocated;
                    row.balance = sa.balance;
                });
                frm.refresh_field('cancellation_allocations');

                // Fill cancellation_beneficiaries — no duplicates since Python GROUPs by student
                // (data.beneficiaries || []).forEach(function (b) {
                //     let row = frm.add_child('cancellation_beneficiaries');
                //     row.student = b.student;
                //     row.student_name = b.student_name;
                //     row.original_allocated_amount = b.amount;
                //     row.student_balance = 0;
                // });
                (data.beneficiaries || []).forEach(function (b) {
                    let row = frm.add_child('cancellation_beneficiaries');
                    row.student = b.student;
                    row.student_name = b.student_name;
                    row.original_allocated_amount = b.amount;
                    row.sponsorship_allocation = b.sponsorship_allocation;
                    row.student_balance = 0;
                });
                frm.refresh_field('cancellation_beneficiaries');
                frm.toggle_display('section_cancellation_allocations', true);
                frm.toggle_display('section_cancellation', true);
                frm.toggle_display('cancellation_beneficiaries', true);
                frm.refresh();
                frm.trigger('load_cancellation_balances');

                frappe.show_alert({
                    message: `Loaded ${data.allocations.length} allocations and ${data.beneficiaries.length} students`,
                    indicator: 'green'
                });
            }
        });
    },

    graduation_student: function (frm) {
        if (!frm.doc.graduation_student) {
            frm.set_value('graduation_reg_no', '');
            frm.set_value('graduation_student_name', '');
            frm.set_value('graduation_ledger_balance', 0);
            frm.set_value('graduation_amount_to_refund', 0);
            return;
        }

        // Auto-populate Reg No (same as customer id) and Name
        frm.set_value('graduation_reg_no', frm.doc.graduation_student);

        frappe.db.get_value('Customer', frm.doc.graduation_student, 'customer_name', function (r) {
            if (r) frm.set_value('graduation_student_name', r.customer_name);
        });

        // Fetch ledger balance
        frappe.call({
            method: 'erp_mmust.erp_mmust.doctype.student_refund.student_refund.get_graduation_student_balance',
            args: { customer: frm.doc.graduation_student },
            callback: function (r) {
                if (r.message !== undefined) {
                    let balance = r.message;
                    frm.set_value('graduation_ledger_balance', balance);

                    if (balance >= 0) {
                        frappe.msgprint({
                            title: 'Cannot Refund',
                            indicator: 'red',
                            message: `This student does not have a credit balance in the ledger (Balance: ${balance.toLocaleString()}). Only students the school owes money can be refunded.`
                        });
                        frm.set_value('graduation_student', '');
                        frm.set_value('graduation_ledger_balance', 0);
                    }
                }
            }
        });
    },

    sponsorship_allocation: function (frm) {
        if (!frm.doc.sponsorship_allocation) {
            frm.set_value('batch_number', '');
            frm.set_value('donation_amount', 0);
            frm.set_value('custom_cheque_id', '');
            frm.set_value('total_allocated_in_donation', 0);
            frm.set_value('amount_refunded_to_donor', 0);
            frm.clear_table('beneficiaries');
            frm.clear_table('reallocations');
            frm.refresh_field('beneficiaries');
            frm.refresh_field('reallocations');
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
                frm.set_value('batch_number', frm.doc.sponsorship_allocation || '');

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
                }
                // ← Receipt Cancellation block REMOVED — handled by cheque_donation trigger
            }
        });
    },

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


        // Hide sponsorship_allocation for Receipt Cancellation — use cheque_donation instead
        frm.toggle_display('section_donation', is_funder && !is_cancellation);
        frm.toggle_display('sponsorship_allocation', is_funder && !is_cancellation);
        // frm.toggle_display('section_cheque_cancellation', is_funder && is_cancellation);
        frm.toggle_display('section_cheque_cancellation', is_funder && is_cancellation && !!frm.doc.funder);
        frm.toggle_display('section_cancellation_allocations', is_funder && is_cancellation && !!frm.doc.cheque_donation);


        let is_graduation_refund = frm.doc.request_type === 'Graduation' && frm.doc.action_type === 'Refund a Student';
        frm.toggle_display('section_graduation_refund', is_graduation_refund);
        frm.toggle_display('graduation_student', is_graduation_refund);
        frm.toggle_display('graduation_reg_no', is_graduation_refund);
        frm.toggle_display('graduation_student_name', is_graduation_refund);
        frm.toggle_display('graduation_ledger_balance', is_graduation_refund);
        frm.toggle_display('graduation_amount_to_refund', is_graduation_refund);
        frm.toggle_display('graduation_bank_account', is_graduation_refund);
        frm.toggle_display('col_break_graduation', is_graduation_refund);

        frm.toggle_display('graduation_phone', is_graduation_refund);
        frm.toggle_display('graduation_email', is_graduation_refund);
        frm.toggle_display('graduation_id_number', is_graduation_refund);
        frm.toggle_display('graduation_year_of_study', is_graduation_refund);
        frm.toggle_display('graduation_programme', is_graduation_refund);
        frm.toggle_display('graduation_school', is_graduation_refund);
        frm.toggle_display('graduation_department', is_graduation_refund);
        frm.toggle_display('section_graduation_bank_details', is_graduation_refund);
        frm.toggle_display('graduation_mode_of_refund', is_graduation_refund);
        frm.toggle_display('graduate_bank_name', is_graduation_refund);
        frm.toggle_display('graduate_account_number', is_graduation_refund);
        frm.toggle_display('graduation_swift_code', is_graduation_refund);
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