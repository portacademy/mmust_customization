// Copyright (c) 2026, Timothy Ajani and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sponsorship Allocation', {
    refresh: function (frm) {
        frm.set_df_property('donation', 'read_only', frm.doc.donor ? 0 : 1);

        if (frm.doc.donor) {
            frm.set_query('donation', function () {
                return {
                    query: 'erp_mmust.erp_mmust.doctype.sponsorship_allocation.sponsorship_allocation.get_donor_donations',
                    filters: { donor: frm.doc.donor }
                };
            });
        }

        // Update available balance on load
        update_available_balance(frm);

        if (frm.doc.docstatus === 0 && frm.doc.total_allocated !== frm.doc.total) {
            frm.add_custom_button(__('Distribute Equally'), function () {
                distribute_equally(frm);
            });
        }

        if (frm.doc.docstatus === 1) {
            frappe.db.get_value('MMUST Donor Settings', 'MMUST Donor Settings', [
                'single_sponsorship_print_format',
                'bulk_sponsorship_print_format'
            ], function (settings) {

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

    // donation: function (frm) {
    //     if (frm.doc.donation) {
    //         frappe.call({
    //             method: 'frappe.client.get_value',
    //             args: {
    //                 doctype: 'Donation',
    //                 filters: { name: frm.doc.donation },
    //                 fieldname: ['amount', 'donor', 'company', 'date']
    //             },
    //             callback: function (r) {
    //                 if (r.message) {
    //                     frm.set_value('amount', r.message.amount);
    //                     if (!frm.doc.donor) frm.set_value('donor', r.message.donor);
    //                     if (!frm.doc.company) frm.set_value('company', r.message.company);
    //                     if (!frm.doc.date) frm.set_value('date', r.message.date);
    //                     if (!frm.doc.total) frm.set_value('total', r.message.amount);
    //                     update_available_balance(frm);
    //                 }
    //             }
    //         });
    //     } else {
    //         frm.set_value('available_balance', 0);
    //     }
    // },

    donation: function (frm) {
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
                        if (!frm.doc.donor) frm.set_value('donor', r.message.donor);
                        if (!frm.doc.company) frm.set_value('company', r.message.company);
                        if (!frm.doc.date) frm.set_value('date', r.message.date);

                        // Fetch available balance and use THAT as total, not full donation amount
                        frappe.call({
                            method: 'erp_mmust.erp_mmust.doctype.sponsorship_allocation.sponsorship_allocation.get_donation_available_balance',
                            args: {
                                donation: frm.doc.donation,
                                exclude_doc: frm.doc.name || ""
                            },
                            callback: function (res) {
                                if (res.message !== undefined) {
                                    const available = res.message;
                                    frm.set_value('available_balance', available);
                                    // Set total to available balance, not full donation amount
                                    if (!frm.doc.total) {
                                        frm.set_value('total', available);
                                    }
                                    if (available <= 0) {
                                        frm.get_field('available_balance').$wrapper.css('color', 'red');
                                    } else {
                                        frm.get_field('available_balance').$wrapper.css('color', 'green');
                                    }
                                }
                            }
                        });
                    }
                }
            });
        } else {
            frm.set_value('available_balance', 0);
        }
    },

    donor: function (frm) {
        frm.set_value('donation', '');
        frm.set_value('available_balance', 0);

        if (frm.doc.donor) {
            frm.set_df_property('donation', 'read_only', 0);
            frm.set_query('donation', function () {
                return {
                    query: 'erp_mmust.erp_mmust.doctype.sponsorship_allocation.sponsorship_allocation.get_donor_donations',
                    filters: { donor: frm.doc.donor }
                };
            });

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

                            frappe.call({
                                method: 'erp_mmust.erp_mmust.doctype.sponsorship_allocation.sponsorship_allocation.distribute_amount_equally',
                                args: {
                                    students: selected_students,
                                    // total_amount: frm.doc.total
                                    total_amount: frm.doc.available_balance || frm.doc.total
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

function update_available_balance(frm) {
    if (!frm.doc.donation) {
        frm.set_value('available_balance', 0);
        return;
    }

    frappe.call({
        method: 'erp_mmust.erp_mmust.doctype.sponsorship_allocation.sponsorship_allocation.get_donation_available_balance',
        args: {
            donation: frm.doc.donation,
            exclude_doc: frm.doc.name || ""
        },
        callback: function (r) {
            if (r.message !== undefined) {
                frm.set_value('available_balance', r.message);
                if (r.message <= 0) {
                    frm.get_field('available_balance').$wrapper.css('color', 'red');
                } else {
                    frm.get_field('available_balance').$wrapper.css('color', 'green');
                }
            }
        }
    });
}

function load_from_csv(frm) {
    if (!frm.doc.upload_csv) return;

    if (!frm.doc.total) {
        frappe.msgprint(__('Please enter Total Available amount first'));
        return;
    }

    frappe.call({
        method: 'erp_mmust.erp_mmust.doctype.sponsorship_allocation.sponsorship_allocation.load_students_from_csv',
        args: {
            csv_file_url: frm.doc.upload_csv,
            total_amount: frm.doc.available_balance || frm.doc.total
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
                frappe.show_alert({ message: __('Students loaded successfully from CSV'), indicator: 'green' });
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

    // Update available balance as user allocates
    update_available_balance(frm);

    if (Math.abs(total - allocated) > 0.01 && frm.doc.beneficiaries && frm.doc.beneficiaries.length > 0) {
        frm.get_field('balance').$wrapper.css('color', 'red');
    } else {
        frm.get_field('balance').$wrapper.css('color', '');
    }
}

// function distribute_equally(frm) {
//     if (!frm.doc.beneficiaries || frm.doc.beneficiaries.length === 0) {
//         frappe.msgprint(__('Please add beneficiaries first'));
//         return;
//     }

//     let amount_per_student = frm.doc.total / frm.doc.beneficiaries.length;

//     frm.doc.beneficiaries.forEach(function (row) {
//         frappe.model.set_value(row.doctype, row.name, 'amount', amount_per_student);
//     });

//     frm.refresh_field('beneficiaries');
//     calculate_balance(frm);
// }

function distribute_equally(frm) {
    if (!frm.doc.beneficiaries || frm.doc.beneficiaries.length === 0) {
        frappe.msgprint(__('Please add beneficiaries first'));
        return;
    }

    const split_amount = frm.doc.available_balance || frm.doc.total || 0;
    let amount_per_student = split_amount / frm.doc.beneficiaries.length;

    frm.doc.beneficiaries.forEach(function (row) {
        frappe.model.set_value(row.doctype, row.name, 'amount', amount_per_student);
    });

    frm.refresh_field('beneficiaries');
    calculate_balance(frm);
}