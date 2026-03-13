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
            "label": _("Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 160,
        },
        {
            "label": _("Vote (Income Account)"),
            "fieldname": "vote",
            "fieldtype": "Link",
            "options": "Account",
            "width": 220,
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
            ROUND(
                SUM(
                    COALESCE(
                        per.allocated_amount
                        * (vote_totals.vote_total / NULLIF(invoice_totals.invoice_total, 0)),
                        0
                    )
                ),
                2
            ) AS amount,
            vote_totals.vote,
            pe.paid_to AS account_paid_to
        FROM `tabPayment Entry` pe
        INNER JOIN `tabCustomer` c ON c.name = pe.party
        INNER JOIN `tabPayment Entry Reference` per
            ON per.parent = pe.name
            AND per.parenttype = 'Payment Entry'
            AND per.reference_doctype = 'Sales Invoice'
        INNER JOIN `tabSales Invoice` si
            ON si.name = per.reference_name
            AND si.docstatus = 1
        INNER JOIN (
            SELECT
                parent AS invoice_name,
                income_account AS vote,
                SUM(net_amount) AS vote_total
            FROM `tabSales Invoice Item`
            GROUP BY parent, income_account
        ) AS vote_totals
            ON vote_totals.invoice_name = si.name
        INNER JOIN (
            SELECT
                parent AS invoice_name,
                SUM(net_amount) AS invoice_total
            FROM `tabSales Invoice Item`
            GROUP BY parent
        ) AS invoice_totals
            ON invoice_totals.invoice_name = si.name
        WHERE
            pe.docstatus = 1
            AND pe.payment_type = 'Receive'
            AND pe.party_type = 'Customer'
            AND c.customer_group = 'Student'
            {conditions}
        GROUP BY
            pe.party,
            pe.party_name,
            vote_totals.vote,
            pe.paid_to
        HAVING amount != 0
        ORDER BY
            pe.party ASC,
            vote_totals.vote ASC,
            pe.paid_to ASC
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
        conditions.append("AND vote_totals.vote = %(account)s")

    if filters.get("paid_to"):
        conditions.append("AND pe.paid_to = %(paid_to)s")

    return " ".join(conditions)


def get_summary(data):
    total_amount = sum(flt(row.get("amount")) for row in data)

    return [
        {
            "label": _("Total Amount Received"),
            "value": total_amount,
            "datatype": "Currency",
        },
        {
            "label": _("Total Rows"),
            "value": len(data),
            "datatype": "Int",
        },
    ]
