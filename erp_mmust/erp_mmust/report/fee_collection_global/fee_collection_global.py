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
            "label": _("Account Number"),
            "fieldname": "account_number",
            "fieldtype": "Link",
            "options": "Account",
            "width": 200
        },
        {
            "label": _("Account Name"),
            "fieldname": "account_name",
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
    parent_account = filters.get("account")
    if not parent_account:
        return []

    descendants = frappe.db.get_descendants("Account", parent_account)
    descendants.append(parent_account)

    account_filter_values = {"accounts": tuple(descendants)}
    account_conditions = ["name IN %(accounts)s"]

    if filters.get("account_name"):
        account_conditions.append("account_name LIKE %(account_name)s")
        account_filter_values["account_name"] = f"%{filters.get('account_name')}%"

    if filters.get("account_number"):
        account_conditions.append("name LIKE %(account_number)s")
        account_filter_values["account_number"] = f"%{filters.get('account_number')}%"

    accounts_to_process = frappe.db.sql(
        f"""
        SELECT name, account_name
        FROM `tabAccount`
        WHERE {" AND ".join(account_conditions)}
        """,
        account_filter_values,
        as_dict=True,
    )

    if not accounts_to_process:
        return []

    filters = dict(filters)
    filters["accounts"] = tuple(acc.name for acc in accounts_to_process)

    conditions = get_conditions(filters)

    return frappe.db.sql(
        """
        SELECT
            vote_totals.vote AS account_number,
            MAX(acc.account_name) AS account_name,
            ROUND(
                SUM(
                    COALESCE(
                        per.allocated_amount
                        * (vote_totals.vote_total / NULLIF(invoice_totals.invoice_total, 0)),
                        0
                    )
                ),
                2
            ) AS amount
        FROM `tabPayment Entry` pe
        INNER JOIN `tabCustomer` c
            ON c.name = pe.party
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
        LEFT JOIN `tabAccount` acc
            ON acc.name = vote_totals.vote
        WHERE
            pe.docstatus = 1
            AND pe.payment_type = 'Receive'
            AND pe.party_type = 'Customer'
            AND c.customer_group = 'Student'
            AND vote_totals.vote IN %(accounts)s
            {conditions}
        GROUP BY vote_totals.vote
        HAVING amount != 0
        ORDER BY vote_totals.vote ASC
        """.format(conditions=conditions),
        filters,
        as_dict=True,
    )


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("AND pe.posting_date >= %(from_date)s")

    if filters.get("to_date"):
        conditions.append("AND pe.posting_date <= %(to_date)s")

    return " ".join(conditions)


def get_summary(data):
    return [
        {
            "label": _("Total Collections"),
            "value": sum(flt(row.get("amount")) for row in data),
            "datatype": "Currency",
        },
        {
            "label": _("Total Accounts"),
            "value": len(data),
            "datatype": "Int",
        },
    ]
