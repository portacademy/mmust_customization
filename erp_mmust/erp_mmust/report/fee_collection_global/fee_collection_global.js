frappe.query_reports["Fee Collection Global"] = {
    "filters": [
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
            "fieldname": "account",
            "label": __("Account"),
            "fieldtype": "Link",
            "options": "Account",
            "default": "41-00-000 - Revenue from Exchange Transactions - MMUST",
            "get_query": function () {
                return {
                    "filters": {
                        "is_group": 1
                    }
                };
            }
        },
        {
            "fieldname": "account_name",
            "label": __("Account Name"),
            "fieldtype": "Data"
        },
        {
            "fieldname": "account_number",
            "label": __("Account Number"),
            "fieldtype": "Data"
        }
    ]
};
