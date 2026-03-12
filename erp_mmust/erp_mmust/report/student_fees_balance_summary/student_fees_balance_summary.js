frappe.query_reports["Student Fees Balance Summary"] = {
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
            "fieldname": "student",
            "label": __("Student"),
            "fieldtype": "Link",
            "options": "Customer",
            "get_query": function () {
                return {
                    "filters": {
                        "customer_group": "Student"
                    }
                };
            }
        },
        {
            "fieldname": "student_name",
            "label": __("Student Name"),
            "fieldtype": "Data",
        }
    ]
};
