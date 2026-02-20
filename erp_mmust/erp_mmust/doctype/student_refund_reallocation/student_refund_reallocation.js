{
    "doctype": "DocType",
        "name": "Student Refund Reallocation",
            "module": "Erp Mmust",
                "custom": 0,
                    "istable": 1,
                        "editable_grid": 1,
                            "track_changes": 0,
                                "fields": [
                                    {
                                        "fieldname": "source_student",
                                        "label": "Source Student (Customer)",
                                        "fieldtype": "Link",
                                        "options": "Customer",
                                        "reqd": 1,
                                        "in_list_view": 1,
                                        "read_only": 1,
                                        "columns": 2
                                    },
                                    {
                                        "fieldname": "student_name",
                                        "label": "Student Name",
                                        "fieldtype": "Data",
                                        "fetch_from": "source_student.customer_name",
                                        "read_only": 1,
                                        "in_list_view": 1,
                                        "columns": 2
                                    },
                                    {
                                        "fieldname": "original_allocated_amount",
                                        "label": "Original Allocated Amount",
                                        "fieldtype": "Currency",
                                        "read_only": 1,
                                        "in_list_view": 1,
                                        "columns": 2,
                                        "description": "Amount originally allocated to this student in the Sponsorship Allocation"
                                    },
                                    {
                                        "fieldname": "student_balance",
                                        "label": "Student Balance",
                                        "fieldtype": "Currency",
                                        "read_only": 1,
                                        "in_list_view": 1,
                                        "columns": 1,
                                        "description": "Current balance in the student's account ledger (GL Entry)"
                                    },
                                    {
                                        "fieldname": "target_student",
                                        "label": "Target Student",
                                        "fieldtype": "Link",
                                        "options": "Customer",
                                        "reqd": 1,
                                        "in_list_view": 1,
                                        "columns": 2,
                                        "description": "Student receiving the reallocation. Cannot be same as source student."
                                    },
                                    {
                                        "fieldname": "target_student_name",
                                        "label": "Target Student Name",
                                        "fieldtype": "Data",
                                        "fetch_from": "target_student.customer_name",
                                        "read_only": 1,
                                        "in_list_view": 1,
                                        "columns": 2
                                    },
                                    {
                                        "fieldname": "amount_to_reallocate",
                                        "label": "Amount to Reallocate",
                                        "fieldtype": "Currency",
                                        "reqd": 1,
                                        "in_list_view": 1,
                                        "columns": 2,
                                        "description": "Amount to transfer from source to target student. Cannot exceed original allocated amount or student balance."
                                    }
                                ]
}