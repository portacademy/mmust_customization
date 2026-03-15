const SALES_INVOICE_BULK_PAYMENT_REQUEST_METHOD = "erp_mmust.services.payment_request_service.bulk_create_and_send";

function showSalesInvoiceBulkPaymentRequestSummary(summary) {
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

frappe.listview_settings["Sales Invoice"] = {
    onload: function (listview) {
        listview.page.add_action_item(__("Bulk Payment Request"), function () {
            const checkedItems = listview.get_checked_items();

            if (!checkedItems.length) {
                frappe.msgprint(__("Please select at least one Sales Invoice."));
                return;
            }

            frappe.call({
                method: SALES_INVOICE_BULK_PAYMENT_REQUEST_METHOD,
                args: {
                    invoice_names: checkedItems.map((item) => item.name),
                },
                freeze: true,
                freeze_message: __("Creating and sending Payment Requests..."),
                callback: function (r) {
                    showSalesInvoiceBulkPaymentRequestSummary(r.message || {});
                    listview.refresh();
                },
            });
        });
    },
};
