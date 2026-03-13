frappe.query_reports["Fee Collection Per Vote Summary"] = {
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
            "fieldname": "parent_account",
            "label": __("Parent Vote (Account)"),
            "fieldtype": "Link",
            "options": "Account",
            "default": "41-00-000 - Revenue from Exchange Transactions - MMUST",
            "get_query": function () {
                return {
                    "filters": {
                        "is_group": 1,
                        "company": frappe.query_report.get_filter_value('company')
                    }
                };
            }
        }
    ]
};
