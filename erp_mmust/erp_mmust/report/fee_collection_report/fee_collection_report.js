frappe.query_reports["Fee Collection Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "paid_to",
            label: __("Bank Account"),
            fieldtype: "Link",
            options: "Account",
            get_query: function () {
                return {
                    filters: {
                        account_type: "Bank",
                        is_group: 0
                    }
                };
            }
        },
        {
            fieldname: "owner",
            label: __("Created By (Personnel)"),
            fieldtype: "Link",
            options: "User"
        },
        {
            fieldname: "mode_of_payment",
            label: __("Mode of Payment"),
            fieldtype: "Link",
            options: "Mode of Payment"
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
        },
        {
            fieldname: "custom_student_type",
            label: __("Student Type"),
            fieldtype: "Select",
            options: "\nPSSP\nGSSP\nPSSP2023\nGSSP2023"
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "paid_amount") {
            value = `<b style="color: green;">${value}</b>`;
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
    }
};