import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}

    columns = get_columns()
    data = get_data(filters)
    summary = get_summary(data)

    return columns, data, None, None, summary


def get_columns():
    return [
        {
            "label": _("Student ID"),
            "fieldname": "student_id",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 160,
        },
        {
            "label": _("Student Name"),
            "fieldname": "student_name",
            "fieldtype": "Data",
            "width": 240,
        },
        {
            "label": _("Amount Received"),
            "fieldname": "amount_received",
            "fieldtype": "Currency",
            "width": 160,
        },
        {
            "label": _("Account Paid To"),
            "fieldname": "account_paid_to",
            "fieldtype": "Link",
            "options": "Account",
            "width": 220,
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)

    return frappe.db.sql(
        """
        SELECT
            pe.party AS student_id,
            pe.party_name AS student_name,
            pe.received_amount AS amount_received,
            pe.paid_to AS account_paid_to
        FROM `tabPayment Entry` pe
        INNER JOIN `tabCustomer` c ON c.name = pe.party
        WHERE
            pe.docstatus = 1
            AND pe.payment_type = 'Receive'
            AND pe.party_type = 'Customer'
            AND c.customer_group = 'Student'
            {conditions}
        ORDER BY pe.posting_date DESC, pe.creation DESC
        """.format(conditions=conditions),
        filters,
        as_dict=True,
    )


def get_conditions(filters):
    conditions = []

    if filters.get("company"):
        conditions.append("AND pe.company = %(company)s")

    if filters.get("from_date"):
        conditions.append("AND pe.posting_date >= %(from_date)s")

    if filters.get("to_date"):
        conditions.append("AND pe.posting_date <= %(to_date)s")

    if filters.get("account"):
        conditions.append("AND pe.paid_to = %(account)s")

    return " ".join(conditions)


def get_summary(data):
    total_amount = sum(flt(row.get("amount_received")) for row in data)

    return [
        {
            "label": _("Total Amount Received"),
            "value": total_amount,
            "datatype": "Currency",
        },
        {
            "label": _("Total Receipts"),
            "value": len(data),
            "datatype": "Int",
        },
    ]
