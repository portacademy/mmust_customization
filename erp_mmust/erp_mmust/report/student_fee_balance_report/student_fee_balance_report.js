frappe.query_reports["Student Fee Balance Report"] = {
    filters: [
        {
            fieldname: "balance_type",
            label: __("Balance Type"),
            fieldtype: "Select",
            options: "\nAll\nOverpaid\nZero Balance\nOutstanding",
            default: ""
        },
        {
            fieldname: "amount_operator",
            label: __("Balance Operator"),
            fieldtype: "Select",
            options: "\n>\n>=\n<\n<=\n=",
            description: "Use with Amount Value to drill into balances e.g. > 100,000"
        },
        {
            fieldname: "amount_value",
            label: __("Amount Value (KES)"),
            fieldtype: "Currency",
            description: "e.g. 100000 — used with Balance Operator"
        },
        {
            fieldname: "custom_student_type",
            label: __("Student Type"),
            fieldtype: "Select",
            options: "\nPSSP\nGSSP\nPSSP2023\nGSSP2023"
        },
        {
            fieldname: "faculty",
            label: __("Faculty"),
            fieldtype: "Link",
            options: "Faculty"
        },
        {
            fieldname: "department",
            label: __("Department"),
            fieldtype: "Link",
            options: "Student Department"
        },
        {
            fieldname: "custom_program_of_study",
            label: __("Programme"),
            fieldtype: "Link",
            options: "Programme"
        },
        {
            fieldname: "custom_level",
            label: __("Year of Study"),
            fieldtype: "Select",
            options: "\n100\n200\n300\n400\n500"
        },
        {
            fieldname: "custom_campus",
            label: __("Campus"),
            fieldtype: "Link",
            options: "Campus"
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "balance_type") {
            if (data.balance_type === "Overpaid") {
                value = `<span class="badge" style="background:green;color:white;padding:3px 8px;">${value}</span>`;
            } else if (data.balance_type === "Zero Balance") {
                value = `<span class="badge" style="background:grey;color:white;padding:3px 8px;">${value}</span>`;
            } else if (data.balance_type === "Outstanding") {
                value = `<span class="badge" style="background:red;color:white;padding:3px 8px;">${value}</span>`;
            }
        }

        if (column.fieldname === "balance") {
            if (data.balance_type === "Overpaid") {
                value = `<b style="color:green;">${value}</b>`;
            } else if (data.balance_type === "Outstanding") {
                value = `<b style="color:red;">${value}</b>`;
            }
        }

        return value;
    },

    onload: function (report) {
        report.page.add_inner_button(__("Export to Excel"), function () {
            report.export_report("Excel");
        });

        report.page.add_inner_button(__("Clear Filters"), function () {
            report.filters.forEach(function (filter) {
                filter.set_value(filter.df.default || "");
            });
            report.refresh();
        });

        // Style the Clear Filters button black
        report.page.inner_toolbar.find("button").filter(function () {
            return $(this).text().trim() === "Clear Filters";
        }).css({ "background-color": "#000", "color": "#fff", "border-color": "#000" });
    }
};