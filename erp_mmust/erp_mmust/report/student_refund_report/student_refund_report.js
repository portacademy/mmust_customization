frappe.query_reports["Student Refund Report"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -3),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "request_type",
            "label": __("Request Type"),
            "fieldtype": "Select",
            "options": "\nHELB\nCDF\nScholarship\nGraduation\nHostel"
        },
        {
            "fieldname": "action_type",
            "label": __("Action Type"),
            "fieldtype": "Select",
            "options": "\nRefund to Funder\nReallocate to Student\nReceipt Cancellation\nHostel Refund\nRefund a Student"
        },
        {
            "fieldname": "academic_year",
            "label": __("Academic Year"),
            "fieldtype": "Link",
            "options": "Academic Year"
        },
        {
            "fieldname": "workflow_state",
            "label": __("Status"),
            "fieldtype": "Link",
            "options": "Workflow State"
        }
    ],

    "onload": function (report) {
        // Clear Filters Button
        report.page.add_inner_button(__("Clear Filters"), function () {
            report.filters.forEach(f => {
                if (f.df.fieldname == "from_date") {
                    f.set_input(frappe.datetime.add_months(frappe.datetime.get_today(), -3));
                } else if (f.df.fieldname == "to_date") {
                    f.set_input(frappe.datetime.get_today());
                } else {
                    f.set_input("");
                }
            });
            report.refresh();
        });
    }
};