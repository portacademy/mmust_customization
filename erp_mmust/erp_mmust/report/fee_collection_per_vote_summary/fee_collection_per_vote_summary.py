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
            "label": _("Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 150
        }
    ]

def get_data(filters):
    if not filters.get("account"):
        return []

    data = frappe.db.sql("""
        SELECT
            gle.party as student_id,
            c.customer_name as student_name,
            SUM(gle.credit) - SUM(gle.debit) as amount
        FROM `tabGL Entry` gle
        LEFT JOIN `tabCustomer` c ON gle.party = c.name
        WHERE
            gle.company = %(company)s
            AND gle.account = %(account)s
            AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND gle.party_type = 'Customer'
            AND c.customer_group = 'Student'
        GROUP BY
            gle.party, c.customer_name
        HAVING
            amount != 0
    """, values=filters, as_dict=True)

    return data
