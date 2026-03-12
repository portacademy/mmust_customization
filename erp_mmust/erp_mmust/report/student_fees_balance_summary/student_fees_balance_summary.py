import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)
    
    return columns, data, None, None, None

def get_columns():
    return [
        {
            "label": _("Student ID"),
            "fieldname": "student_id",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200
        },
        {
            "label": _("Student Name"),
            "fieldname": "student_name",
            "fieldtype": "Data",
            "width": 300
        },
        {
            "label": _("Balance"),
            "fieldname": "balance",
            "fieldtype": "Currency",
            "width": 150
        }
    ]

def get_data(filters):
    conditions = ""
    values = {}

    if filters.get("student"):
        conditions += " AND c.name = %(student)s"
        values["student"] = filters.get("student")
        
    if filters.get("student_name"):
        conditions += " AND c.customer_name LIKE %(student_name)s"
        values["student_name"] = "%" + filters.get("student_name") + "%"
        
    if filters.get("faculty"):
        conditions += " AND c.custom_faculty = %(faculty)s"
        values["faculty"] = filters.get("faculty")

    if filters.get("custom_program_of_study"):
        conditions += " AND c.custom_program_of_study = %(custom_program_of_study)s"
        values["custom_program_of_study"] = filters.get("custom_program_of_study")

    if filters.get("custom_campus"):
        conditions += " AND c.custom_campus = %(custom_campus)s"
        values["custom_campus"] = filters.get("custom_campus")

    if filters.get("custom_student_type"):
        conditions += " AND c.custom_student_type = %(custom_student_type)s"
        values["custom_student_type"] = filters.get("custom_student_type")

    company_receivable_account = frappe.db.get_value("Company", filters.get("company"), "default_receivable_account")
    
    if not company_receivable_account:
        frappe.throw(_("Please set the default receivable account for the company {0}").format(filters.get("company")))

    values["receivable_account"] = company_receivable_account

    students_data = frappe.db.sql(f"""
        SELECT
            c.name AS student_id,
            c.customer_name AS student_name,
            (SELECT SUM(debit) - SUM(credit) FROM `tabGL Entry` WHERE party = c.name AND party_type = 'Customer' AND account = %(receivable_account)s) as balance
        FROM
            `tabCustomer` AS c
        WHERE
            c.customer_group = 'Student'
            {conditions}
        HAVING balance IS NOT NULL AND balance != 0
    """, values, as_dict=True)

    return students_data
