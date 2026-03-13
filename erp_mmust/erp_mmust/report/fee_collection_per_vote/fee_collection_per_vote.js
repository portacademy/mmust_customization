frappe.query_reports["Fee Collection Per Vote"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 1
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
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
            "fieldname": "vote",
            "label": __("Vote (Income Account)"),
            "fieldtype": "Link",
            "options": "Account",
            "reqd": 0,
            "get_query": function () {
                return {
                    "filters": {
                        "company": frappe.query_report.get_filter_value('company')
                    }
                };
            }
        }
    ]
};
