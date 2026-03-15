const BULK_PAYMENT_REQUEST_METHOD = "erp_mmust.services.payment_request_service.bulk_create_and_send";

function getMarkedInvoiceNames(report) {
    return Array.from(report.marked_invoice_names || []);
}

function getVisibleInvoiceNames(report) {
    return (report.data || [])
        .map((row) => row.sales_invoice)
        .filter((invoice_name) => Boolean(invoice_name));
}

function showBulkPaymentRequestSummary(summary) {
    const sections = [
        {
            title: __("Created"),
            rows: summary.created || [],
            formatter: (row) => `${row.invoice_name} -> ${row.payment_request}`,
        },
        {
            title: __("Skipped"),
            rows: summary.skipped || [],
            formatter: (row) => `${row.invoice_name} - ${row.reason}`,
        },
        {
            title: __("Failed"),
            rows: summary.failed || [],
            formatter: (row) => `${row.invoice_name} - ${row.reason}`,
        },
    ];

    const body = sections
        .filter((section) => section.rows.length)
        .map((section) => {
            const lines = section.rows.map((row) => `<li>${frappe.utils.escape_html(section.formatter(row))}</li>`).join("");
            return `<p><strong>${section.title}</strong> (${section.rows.length})</p><ul>${lines}</ul>`;
        })
        .join("");

    frappe.msgprint({
        title: __("Bulk Payment Request Result"),
        message:
            body ||
            `<p>${__("Processed {0} invoice(s).", [summary.total_requested || 0])}</p>`,
        wide: true,
    });
}

function addVisibleInvoicesToMarks(report) {
    const visibleInvoiceNames = getVisibleInvoiceNames(report);
    visibleInvoiceNames.forEach((invoice_name) => report.marked_invoice_names.add(invoice_name));
    report.refresh();
    frappe.show_alert({
        message: __("Marked {0} visible invoice(s).", [visibleInvoiceNames.length]),
        indicator: "green",
    });
}

function removeVisibleInvoicesFromMarks(report) {
    const visibleInvoiceNames = getVisibleInvoiceNames(report);
    visibleInvoiceNames.forEach((invoice_name) => report.marked_invoice_names.delete(invoice_name));
    report.refresh();
    frappe.show_alert({
        message: __("Unmarked {0} visible invoice(s).", [visibleInvoiceNames.length]),
        indicator: "orange",
    });
}

function clearMarkedInvoices(report) {
    report.marked_invoice_names.clear();
    report.refresh();
    frappe.show_alert({
        message: __("Cleared all marked invoices."),
        indicator: "blue",
    });
}

function sendMarkedInvoices(report) {
    const invoiceNames = getMarkedInvoiceNames(report);

    if (!invoiceNames.length) {
        frappe.msgprint(__("Please mark at least one invoice first."));
        return;
    }

    frappe.call({
        method: BULK_PAYMENT_REQUEST_METHOD,
        args: { invoice_names: invoiceNames },
        freeze: true,
        freeze_message: __("Creating and sending Payment Requests..."),
        callback: function (r) {
            const summary = r.message || {};
            (summary.created || []).forEach((row) => report.marked_invoice_names.delete(row.invoice_name));
            (summary.skipped || []).forEach((row) => report.marked_invoice_names.delete(row.invoice_name));
            showBulkPaymentRequestSummary(summary);
            report.refresh();
        },
    });
}

frappe.query_reports["Student Invoice Payment Request"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1,
        },
        {
            fieldname: "student",
            label: __("Student"),
            fieldtype: "Link",
            options: "Customer",
            get_query: function () {
                return {
                    filters: {
                        customer_group: "Student",
                    },
                };
            },
        },
        {
            fieldname: "student_name",
            label: __("Student Name"),
            fieldtype: "Data",
        },
        {
            fieldname: "faculty",
            label: __("Faculty/School"),
            fieldtype: "Link",
            options: "Faculty",
        },
        {
            fieldname: "department",
            label: __("Department"),
            fieldtype: "Link",
            options: "Student Department",
        },
        {
            fieldname: "custom_program_of_study",
            label: __("Programme"),
            fieldtype: "Link",
            options: "Programme",
        },
        {
            fieldname: "custom_level",
            label: __("Year of Study"),
            fieldtype: "Select",
            options: "\n100\n200\n300\n400\n500",
        },
        {
            fieldname: "custom_campus",
            label: __("Campus"),
            fieldtype: "Link",
            options: "Campus",
        },
        {
            fieldname: "custom_student_type",
            label: __("Student Type"),
            fieldtype: "Select",
            options: "\nPSSP\nGSSP\nPSSP2023\nGSSP2023",
        },
        {
            fieldname: "payment_state",
            label: __("Payment State"),
            fieldtype: "Select",
            options: "All\nUnpaid\nPartly Paid",
            default: "All",
        },
        {
            fieldname: "invoice_age_min_days",
            label: __("Min Age (Days)"),
            fieldtype: "Int",
        },
        {
            fieldname: "invoice_age_max_days",
            label: __("Max Age (Days)"),
            fieldtype: "Int",
        },
        {
            fieldname: "outstanding_amount_min",
            label: __("Min Outstanding"),
            fieldtype: "Currency",
        },
        {
            fieldname: "outstanding_amount_max",
            label: __("Max Outstanding"),
            fieldtype: "Currency",
        },
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (!data || !data.sales_invoice) {
            return value;
        }

        const report = frappe.query_report;
        const isMarked = report.marked_invoice_names && report.marked_invoice_names.has(data.sales_invoice);

        if (column.fieldname === "marked") {
            return isMarked
                ? '<span class="indicator-pill green ellipsis">' + __("Marked") + "</span>"
                : "";
        }

        if (column.fieldname === "payment_state") {
            if (data.payment_state === "Unpaid") {
                value = `<span class="indicator-pill red ellipsis">${value}</span>`;
            } else if (data.payment_state === "Partly Paid") {
                value = `<span class="indicator-pill orange ellipsis">${value}</span>`;
            }
        }

        if (column.fieldname === "payment_request_status" && data.payment_request_status) {
            value = `<span class="indicator-pill blue ellipsis">${value}</span>`;
        }

        if (isMarked && column.fieldname !== "marked") {
            value = `<strong>${value}</strong>`;
        }

        return value;
    },

    onload: function (report) {
        report.marked_invoice_names = report.marked_invoice_names || new Set();

        report.page.add_inner_button(__("Mark Visible"), function () {
            addVisibleInvoicesToMarks(report);
        });

        report.page.add_inner_button(__("Unmark Visible"), function () {
            removeVisibleInvoicesFromMarks(report);
        });

        report.page.add_inner_button(__("Clear Marks"), function () {
            clearMarkedInvoices(report);
        });

        report.page.add_inner_button(__("Send Payment Requests"), function () {
            sendMarkedInvoices(report);
        });
    },
};
