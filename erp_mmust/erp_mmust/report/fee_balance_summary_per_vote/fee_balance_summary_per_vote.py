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
            "width": 180,
        },
        {
            "label": _("Student Name"),
            "fieldname": "student_name",
            "fieldtype": "Data",
            "width": 240,
        },
        {
            "label": _("Invoiced Amount"),
            "fieldname": "invoiced_amount",
            "fieldtype": "Currency",
            "width": 160,
        },
        {
            "label": _("Paid Amount"),
            "fieldname": "paid_amount",
            "fieldtype": "Currency",
            "width": 160,
        },
        {
            "label": _("Balance"),
            "fieldname": "balance",
            "fieldtype": "Currency",
            "width": 160,
        },
    ]


def get_data(filters):
    if not filters.get("vote"):
        return []

    return frappe.db.sql(
        """
        SELECT
            si.customer AS student_id,
            c.customer_name AS student_name,
            ROUND(SUM(vote_totals.vote_total), 2) AS invoiced_amount,
            ROUND(
                SUM(
                    COALESCE(
                        si.outstanding_amount
                        * (vote_totals.vote_total / NULLIF(invoice_totals.invoice_total, 0)),
                        0
                    )
                ),
                2
            ) AS balance,
            ROUND(
                SUM(vote_totals.vote_total)
                - SUM(
                    COALESCE(
                        si.outstanding_amount
                        * (vote_totals.vote_total / NULLIF(invoice_totals.invoice_total, 0)),
                        0
                    )
                ),
                2
            ) AS paid_amount
        FROM `tabSales Invoice` si
        INNER JOIN `tabCustomer` c
            ON c.name = si.customer
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
            si.docstatus = 1
            AND si.is_return = 0
            AND si.company = %(company)s
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND c.customer_group = 'Student'
            AND vote_totals.vote = %(vote)s
        GROUP BY
            si.customer,
            c.customer_name
        HAVING
            invoiced_amount != 0 OR balance != 0 OR paid_amount != 0
        ORDER BY
            c.customer_name ASC,
            si.customer ASC
        """,
        filters,
        as_dict=True,
    )


def get_summary(data):
    return [
        {
            "label": _("Total Students"),
            "value": len(data),
            "datatype": "Int",
        },
        {
            "label": _("Grand Total"),
            "value": sum(flt(row.get("invoiced_amount")) for row in data),
            "datatype": "Currency",
        },
        {
            "label": _("Grand Paid Amount"),
            "value": sum(flt(row.get("paid_amount")) for row in data),
            "datatype": "Currency",
        },
        {
            "label": _("Grand Balance"),
            "value": sum(flt(row.get("balance")) for row in data),
            "datatype": "Currency",
        },
    ]
