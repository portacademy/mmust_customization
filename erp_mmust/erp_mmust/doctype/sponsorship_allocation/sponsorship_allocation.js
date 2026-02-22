// Copyright (c) 2026, Timothy Ajani and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sponsorship Allocation', {
    // refresh: function (frm) {

    //     frm.set_df_property('donation', 'read_only', frm.doc.donor ? 0 : 1);

    //     // Set donation filter if donor already selected
    //     if (frm.doc.donor) {
    //         return {
    //             query: 'erp_mmust.erp_mmust.doctype.sponsorship_allocation.sponsorship_allocation.get_donor_donations',
    //             filters: { donor: frm.doc.donor }
    //         };
    //     }

    //     // Add custom buttons or actions here
    //     if (frm.doc.docstatus === 0 && frm.doc.total_allocated !== frm.doc.total) {
    //         frm.add_custom_button(__('Distribute Equally'), function () {
    //             distribute_equally(frm);
    //         });
    //     }

    //     if (frm.doc.docstatus === 1) {

    //         frm.add_custom_button(__('Print Single Receipt'), function () {
    //             frappe.db.get_single_value('MMUST Donor Settings', 'single_sponsorship_print_format')
    //                 .then(print_format => {
    //                     if (!print_format) {
    //                         frappe.msgprint(__('No Single Sponsorship Print Format set in MMUST Donor Settings.'));
    //                         return;
    //                     }
    //                     const url = frappe.urllib.get_full_url(
    //                         `/printview?doctype=Sponsorship Allocation&name=${frm.doc.name}&format=${print_format}&no_letterhead=0`
    //                     );
    //                     window.open(url, '_blank');
    //                 });
    //         }, __('Print'));

    //         frm.add_custom_button(__('Print Bulk Receipt'), function () {
    //             frappe.db.get_single_value('MMUST Donor Settings', 'bulk_sponsorship_print_format')
    //                 .then(print_format => {
    //                     if (!print_format) {
    //                         frappe.msgprint(__('No Bulk Sponsorship Print Format set in MMUST Donor Settings.'));
    //                         return;
    //                     }

    //                     // Print and attach
    //                     frappe.call({
    //                         method: 'frappe.utils.print_format.download_pdf',
    //                         args: {
    //                             doctype: 'Sponsorship Allocation',
    //                             name: frm.doc.name,
    //                             format: print_format,
    //                             no_letterhead: 0
    //                         },
    //                         callback: function () {
    //                             // Open print view
    //                             const url = frappe.urllib.get_full_url(
    //                                 `/printview?doctype=Sponsorship Allocation&name=${frm.doc.name}&format=${print_format}&no_letterhead=0`
    //                             );
    //                             window.open(url, '_blank');

    //                             // Attach PDF to document
    //                             frappe.call({
    //                                 method: 'frappe.utils.pdf.get_pdf',
    //                                 args: {
    //                                     doctype: 'Sponsorship Allocation',
    //                                     name: frm.doc.name,
    //                                     format: print_format
    //                                 }
    //                             });

    //                             frappe.show_alert({
    //                                 message: __('Bulk receipt printed and attached.'),
    //                                 indicator: 'green'
    //                             });
    //                         }
    //                     });
    //                 });
    //         }, __('Print'));
    //     }
    // },

    refresh: function (frm) {
        frm.set_df_property('donation', 'read_only', frm.doc.donor ? 0 : 1);

        // Set donation query filter (no return — just set_query)
        if (frm.doc.donor) {
            frm.set_query('donation', function () {
                return {
                    query: 'erp_mmust.erp_mmust.doctype.sponsorship_allocation.sponsorship_allocation.get_donor_donations',
                    filters: { donor: frm.doc.donor }
                };
            });
        }

        // Distribute Equally button
        if (frm.doc.docstatus === 0 && frm.doc.total_allocated !== frm.doc.total) {
            frm.add_custom_button(__('Distribute Equally'), function () {
                distribute_equally(frm);
            });
        }

        // Print buttons
        if (frm.doc.docstatus === 1) {
            frappe.db.get_value('MMUST Donor Settings', 'MMUST Donor Settings', [
                'single_sponsorship_print_format',
                'bulk_sponsorship_print_format'
            ], function (settings) {

                // frm.add_custom_button(__('Print Single Receipt'), function () {
                //     const format = settings.single_sponsorship_print_format;
                //     if (!format) {
                //         frappe.msgprint(__('No Single Sponsorship Print Format set in MMUST Donor Settings.'));
                //         return;
                //     }
                //     const url = `/printview?doctype=${encodeURIComponent('Sponsorship Allocation')}&name=${encodeURIComponent(frm.doc.name)}&format=${encodeURIComponent(format)}&no_letterhead=0`;
                //     window.open(url, '_blank');
                // }, __('Print'));

                frm.add_custom_button(__('Print Single Receipt'), function () {
                    const format = settings.single_sponsorship_print_format;
                    if (!format) {
                        frappe.msgprint(__('No Single Sponsorship Print Format set in MMUST Donor Settings.'));
                        return;
                    }

                    if (!frm.doc.beneficiaries || frm.doc.beneficiaries.length === 0) {
                        frappe.msgprint(__('No beneficiaries found on this allocation.'));
                        return;
                    }

                    // Build options for Select field
                    let options = frm.doc.beneficiaries.map(b => ({
                        label: `${b.student_name} (${b.student})`,
                        value: b.student
                    }));

                    let d = new frappe.ui.Dialog({
                        title: __('Select Beneficiary'),
                        fields: [
                            {
                                fieldname: 'student',
                                fieldtype: 'Select',
                                label: __('Beneficiary'),
                                options: options.map(o => o.value),
                                reqd: 1
                            }
                        ],
                        primary_action_label: __('Print'),
                        primary_action: function (values) {
                            d.hide();
                            const url = `/printview?doctype=${encodeURIComponent('Sponsorship Allocation')}&name=${encodeURIComponent(frm.doc.name)}&format=${encodeURIComponent(format)}&no_letterhead=0&_beneficiary=${encodeURIComponent(values.student)}`;
                            window.open(url, '_blank');
                        }
                    });

                    // Set labels properly
                    d.fields_dict.student.df.options = options.map(o => o.value).join('\n');
                    d.fields_dict.student.$wrapper.find('select').empty();
                    options.forEach(o => {
                        d.fields_dict.student.$wrapper.find('select').append(
                            `<option value="${o.value}">${o.label}</option>`
                        );
                    });

                    d.show();
                }, __('Print'));

                frm.add_custom_button(__('Print Bulk Receipt'), function () {
                    const format = settings.bulk_sponsorship_print_format;
                    if (!format) {
                        frappe.msgprint(__('No Bulk Sponsorship Print Format set in MMUST Donor Settings.'));
                        return;
                    }
                    const url = `/printview?doctype=${encodeURIComponent('Sponsorship Allocation')}&name=${encodeURIComponent(frm.doc.name)}&format=${encodeURIComponent(format)}&no_letterhead=0`;
                    window.open(url, '_blank');
                }, __('Print'));

            });
        }
    },

    donation: function (frm) {
        // When donation is selected, fetch the amount
        if (frm.doc.donation) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Donation',
                    filters: { name: frm.doc.donation },
                    fieldname: ['amount', 'donor', 'company', 'date']
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('amount', r.message.amount);
                        if (!frm.doc.donor) {
                            frm.set_value('donor', r.message.donor);
                        }
                        if (!frm.doc.company) {
                            frm.set_value('company', r.message.company);
                        }
                        if (!frm.doc.date) {
                            frm.set_value('date', r.message.date);
                        }
                        if (!frm.doc.total) {
                            frm.set_value('total', r.message.amount);
                        }
                    }
                }
            });
        }
    },

    donor: function (frm) {
        // Clear donation when donor changes
        frm.set_value('donation', '');

        if (frm.doc.donor) {
            // Enable donation and filter by donor
            frm.set_df_property('donation', 'read_only', 0);
            frm.set_query('donation', function () {
                return {
                    query: 'erp_mmust.erp_mmust.doctype.sponsorship_allocation.sponsorship_allocation.get_donor_donations',
                    filters: { donor: frm.doc.donor }
                };
            });

            // Auto-populate account_debited from donor's sponsor GL account
            frappe.db.get_value('Donor', frm.doc.donor, 'custom_sponsor_gl_account', function (r) {
                if (r && r.custom_sponsor_gl_account) {
                    frm.set_value('account_debited', r.custom_sponsor_gl_account);
                } else {
                    frm.set_value('account_debited', '');
                }
            });

        } else {
            frm.set_df_property('donation', 'read_only', 1);
            frm.set_value('account_debited', '');
        }
    },

    total: function (frm) {
        calculate_balance(frm);
    },

    upload_csv: function (frm) {
        // Auto-load when CSV is uploaded
        if (frm.doc.upload_csv && frm.doc.selection_method === 'CSV Upload') {
            load_from_csv(frm);
        }
    },

    get_students_button: function (frm) {
        if (!frm.doc.filter_by_programme && !frm.doc.filter_by_level) {
            frappe.msgprint(__('Please select Programme and/or Level to filter'));
            return;
        }

        frappe.call({
            method: 'erp_mmust.erp_mmust.doctype.sponsorship_allocation.sponsorship_allocation.get_students_by_filter',
            args: {
                programme: frm.doc.filter_by_programme,
                level: frm.doc.filter_by_level
            },
            callback: function (r) {
                if (r.message && r.message.length > 0) {
                    // Show selection dialog
                    let students = r.message;

                    let d = new frappe.ui.Dialog({
                        title: __('Select Students'),
                        fields: [
                            {
                                fieldname: 'students',
                                fieldtype: 'MultiCheck',
                                label: __('Students'),
                                options: students.map(s => ({
                                    label: `${s.customer_name} (${s.name})`,
                                    value: s.name,
                                    checked: false
                                }))
                            }
                        ],
                        primary_action_label: __('Add Students'),
                        primary_action: function (values) {
                            let selected_student_ids = values.students || [];
                            let selected_students = students.filter(s =>
                                selected_student_ids.includes(s.name)
                            );

                            if (selected_students.length === 0) {
                                frappe.msgprint(__('Please select at least one student'));
                                return;
                            }

                            // Call distribute equally
                            frappe.call({
                                method: 'erp_mmust.erp_mmust.doctype.sponsorship_allocation.sponsorship_allocation.distribute_amount_equally',
                                args: {
                                    students: selected_students,
                                    total_amount: frm.doc.total
                                },
                                callback: function (r) {
                                    if (r.message) {
                                        frm.clear_table('beneficiaries');
                                        r.message.forEach(b => {
                                            let row = frm.add_child('beneficiaries');
                                            row.student = b.student;
                                            row.student_name = b.student_name;
                                            row.amount = b.amount;
                                            row.description = b.description;
                                        });
                                        frm.refresh_field('beneficiaries');
                                        calculate_balance(frm);
                                    }
                                }
                            });

                            d.hide();
                        }
                    });

                    d.show();
                } else {
                    frappe.msgprint(__('No students found with the selected filters'));
                }
            }
        });
    }


});

frappe.ui.form.on('Sponsorship Allocation Beneficiary', {
    beneficiaries_add: function (frm) {
        calculate_balance(frm);
    },

    beneficiaries_remove: function (frm) {
        calculate_balance(frm);
    },

    amount: function (frm) {
        calculate_balance(frm);
    }
});

function load_from_csv(frm) {
    if (!frm.doc.upload_csv) {
        return;
    }

    if (!frm.doc.total) {
        frappe.msgprint(__('Please enter Total Available amount first'));
        return;
    }

    frappe.call({
        method: 'erp_mmust.erp_mmust.doctype.sponsorship_allocation.sponsorship_allocation.load_students_from_csv',
        args: {
            csv_file_url: frm.doc.upload_csv,
            total_amount: frm.doc.total
        },
        callback: function (r) {
            if (r.message) {
                frm.clear_table('beneficiaries');
                r.message.forEach(b => {
                    let row = frm.add_child('beneficiaries');
                    row.student = b.student;
                    row.student_name = b.student_name;
                    row.amount = b.amount;
                    row.description = b.description;
                });
                frm.refresh_field('beneficiaries');
                calculate_balance(frm);
                frappe.show_alert({
                    message: __('Students loaded successfully from CSV'),
                    indicator: 'green'
                });
            }
        }
    });
}

function calculate_balance(frm) {
    let total = frm.doc.total || 0;
    let allocated = 0;

    if (frm.doc.beneficiaries) {
        frm.doc.beneficiaries.forEach(function (d) {
            allocated += d.amount || 0;
        });
    }

    frm.set_value('total_allocated', allocated);
    frm.set_value('balance', total - allocated);

    // Highlight balance in red if not zero
    if (Math.abs(total - allocated) > 0.01 && frm.doc.beneficiaries && frm.doc.beneficiaries.length > 0) {
        frm.get_field('balance').$wrapper.css('color', 'red');
    } else {
        frm.get_field('balance').$wrapper.css('color', '');
    }
}

function distribute_equally(frm) {
    if (!frm.doc.beneficiaries || frm.doc.beneficiaries.length === 0) {
        frappe.msgprint(__('Please add beneficiaries first'));
        return;
    }

    let amount_per_student = frm.doc.total / frm.doc.beneficiaries.length;

    frm.doc.beneficiaries.forEach(function (row) {
        frappe.model.set_value(row.doctype, row.name, 'amount', amount_per_student);
    });

    frm.refresh_field('beneficiaries');
    calculate_balance(frm);
}