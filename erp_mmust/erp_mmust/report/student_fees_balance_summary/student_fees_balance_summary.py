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
