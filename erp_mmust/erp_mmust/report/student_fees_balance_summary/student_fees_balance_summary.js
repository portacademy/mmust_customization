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
        },
        {
            "fieldname": "faculty",
            "label": __("Faculty/School"),
            "fieldtype": "Link",
            "options": "Faculty"
        },
        {
            "fieldname": "custom_program_of_study",
            "label": __("Programme"),
            "fieldtype": "Link",
            "options": "Programme"
        },
        {
            "fieldname": "custom_campus",
            "label": __("Campus"),
            "fieldtype": "Link",
            "options": "Campus"
        },
        {
            "fieldname": "custom_student_type",
            "label": __("Student Type"),
            "fieldtype": "Select",
            "options": "\nPSSP\nGSSP\nPSSP2023\nGSSP2023"
        }
    ]
};
