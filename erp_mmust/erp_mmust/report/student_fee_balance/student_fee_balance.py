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
            "width": 140
        },
        {
            "label": _("Student Name"),
            "fieldname": "student_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Student Type"),
            "fieldname": "custom_student_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Faculty"),
            "fieldname": "custom_faculty",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Department"),
            "fieldname": "custom_department",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Programme"),
            "fieldname": "custom_program_of_study",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Year of Study"),
            "fieldname": "level",
            "fieldtype": "Data",
            "width": 110
        },
        {
            "label": _("Campus"),
            "fieldname": "custom_campus",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Email"),
            "fieldname": "email_id",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Balance (KES)"),
            "fieldname": "balance",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "label": _("Balance Type"),
            "fieldname": "balance_type",
            "fieldtype": "Data",
            "width": 120
        },
    ]


def get_data(filters):
    balance_type = filters.get("balance_type")
    amount_operator = filters.get("amount_operator")
    amount_value = flt(filters.get("amount_value") or 0)

    conditions = get_customer_conditions(filters)

    # Get all student balances from GL Entry
    raw = frappe.db.sql("""
        SELECT
            c.name AS student_id,
            c.customer_name AS student_name,
            c.custom_student_type,
            c.custom_faculty,
            c.custom_department,
            c.custom_program_of_study,
            c.level,
            c.custom_campus,
            c.email_id,
            COALESCE(SUM(gl.debit - gl.credit), 0) AS balance
        FROM
            `tabCustomer` c
        LEFT JOIN
            `tabGL Entry` gl ON gl.party = c.name
            AND gl.party_type = 'Customer'
            AND gl.is_cancelled = 0
        WHERE
            c.customer_group = 'Student'
            AND c.disabled = 0
            {conditions}
        GROUP BY
            c.name
    """.format(conditions=conditions), filters, as_dict=True)

    data = []
    for row in raw:
        balance = flt(row.balance)

        # Determine balance type label
        if balance < 0:
            row.balance_type = "Overpaid"
            row.balance = abs(balance)  # show as positive for overpaid
        elif balance == 0:
            row.balance_type = "Zero Balance"
        else:
            row.balance_type = "Outstanding"

        # Apply balance_type filter
        if balance_type == "Overpaid" and balance >= 0:
            continue
        elif balance_type == "Zero Balance" and balance != 0:
            continue
        elif balance_type == "Outstanding" and balance <= 0:
            continue

        # Apply amount operator filter (drilling)
        if amount_operator and amount_value:
            check_balance = abs(balance)
            if amount_operator == ">" and not check_balance > amount_value:
                continue
            elif amount_operator == ">=" and not check_balance >= amount_value:
                continue
            elif amount_operator == "<" and not check_balance < amount_value:
                continue
            elif amount_operator == "<=" and not check_balance <= amount_value:
                continue
            elif amount_operator == "=" and not check_balance == amount_value:
                continue

        data.append(row)

    # Sort by balance descending
    data.sort(key=lambda x: flt(x.balance), reverse=True)
    return data


def get_customer_conditions(filters):
    conditions = []

    if filters.get("faculty"):
        filters["faculty"] = "%" + filters["faculty"] + "%"
        conditions.append("AND c.custom_faculty LIKE %(faculty)s")

    if filters.get("department"):
        filters["department"] = "%" + filters["department"] + "%"
        conditions.append("AND c.custom_department LIKE %(department)s")

    if filters.get("custom_program_of_study"):
        conditions.append("AND c.custom_program_of_study = %(custom_program_of_study)s")

    if filters.get("custom_level"):
        conditions.append("AND c.level = %(custom_level)s")

    if filters.get("custom_campus"):
        filters["custom_campus"] = "%" + filters["custom_campus"] + "%"
        conditions.append("AND c.custom_campus LIKE %(custom_campus)s")

    if filters.get("custom_student_type"):
        conditions.append("AND c.custom_student_type = %(custom_student_type)s")

    return " ".join(conditions)


def get_summary(data):
    overpaid = [r for r in data if r.balance_type == "Overpaid"]
    zero = [r for r in data if r.balance_type == "Zero Balance"]
    outstanding = [r for r in data if r.balance_type == "Outstanding"]

    return [
        {
            "label": _("Total Students"),
            "value": len(data),
            "datatype": "Int"
        },
        {
            "label": _("Overpaid Students"),
            "value": len(overpaid),
            "datatype": "Int"
        },
        {
            "label": _("Total Overpaid Amount"),
            "value": sum(flt(r.balance) for r in overpaid),
            "datatype": "Currency",
            "currency": "KES"
        },
        {
            "label": _("Zero Balance Students"),
            "value": len(zero),
            "datatype": "Int"
        },
        {
            "label": _("Outstanding Students"),
            "value": len(outstanding),
            "datatype": "Int"
        },
        {
            "label": _("Total Outstanding Amount"),
            "value": sum(flt(r.balance) for r in outstanding),
            "datatype": "Currency",
            "currency": "KES"
        },
    ]