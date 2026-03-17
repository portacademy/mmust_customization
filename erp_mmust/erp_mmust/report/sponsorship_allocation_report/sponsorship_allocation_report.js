frappe.query_reports["Sponsorship Allocation Report"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            reqd: 1,
            default: frappe.defaults.get_user_default("Company"),
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.get_today(),
        },
        {
            fieldname: "donor",
            label: __("Donor"),
            fieldtype: "Link",
            options: "Donor",
        },
        {
            fieldname: "invoice_type",
            label: __("Invoice Type"),
            fieldtype: "Select",
            options: "\nHouse Hold\nScholarship Fee\nLoan Fee",
        },
        {
            fieldname: "financial_aid",
            label: __("Financial Aid"),
            fieldtype: "Data",
        },
        {
            fieldname: "student",
            label: __("Student Reg No"),
            fieldtype: "Link",
            options: "Customer",
        },
        {
            fieldname: "balance_operator",
            label: __("Balance Operator"),
            fieldtype: "Select",
            options: "\n=\n<\n>\n<=\n>=",
        },
        {
            fieldname: "balance_value",
            label: __("Balance Amount (KES)"),
            fieldtype: "Float",
        },
        {
            fieldname: "allocated_operator",
            label: __("Allocated Operator"),
            fieldtype: "Select",
            options: "\n=\n<\n>\n<=\n>=",
        },
        {
            fieldname: "allocated_value",
            label: __("Allocated Amount (KES)"),
            fieldtype: "Float",
        },
        {
            fieldname: "docstatus",
            label: __("Status"),
            fieldtype: "Select",
            options: "\nDraft\nSubmitted\nCancelled",
            default: "Submitted",
        },
    ],

    onload: function (report) {
        // Add "Clear Filters" button next to the "Refresh" button
        report.page.add_inner_button(__("Clear Filters"), function () {
            report.filters.forEach((f) => {
                // Reset required fields to their original defaults
                if (f.df.fieldname == "company") {
                    f.set_input(frappe.defaults.get_user_default("Company"));
                } else if (f.df.fieldname == "from_date") {
                    f.set_input(frappe.datetime.add_months(frappe.datetime.get_today(), -1));
                } else if (f.df.fieldname == "to_date") {
                    f.set_input(frappe.datetime.get_today());
                } else if (f.df.fieldname == "docstatus") {
                    f.set_input("Submitted");
                } else {
                    // Clear all other optional fields
                    f.set_input("");
                }
            });
            // Automatically refresh the report after clearing
            report.refresh();
        });
    },

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "balance" && data && data.raw_balance < 0) {
            value = `<span style="color: red; font-weight:bold;">${value}</span>`;
        }

        if (column.fieldname === "docstatus") {
            const colors = {
                Draft: "orange",
                Submitted: "green",
                Cancelled: "red",
            };
            const color = colors[data && data.docstatus] || "gray";
            value = `<span style="color: ${color}; font-weight: bold;">${value}</span>`;
        }

        return value;
    },
};