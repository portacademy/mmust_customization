import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns(filters)
    data = get_data(filters)
    summary = get_summary(data)
    return columns, data, None, None, summary


def get_columns(filters):
    columns = [
        {
            "label": _("Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Payment Entry"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Payment Entry",
            "width": 160
        },
        {
            "label": _("Student ID"),
            "fieldname": "party",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 130
        },
        {
            "label": _("Student Name"),
            "fieldname": "party_name",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Mode of Payment"),
            "fieldname": "mode_of_payment",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Bank Account"),
            "fieldname": "paid_to",
            "fieldtype": "Link",
            "options": "Account",
            "width": 180
        },
        {
            "label": _("Reference No"),
            "fieldname": "reference_no",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "label": _("Amount (KES)"),
            "fieldname": "paid_amount",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Created By"),
            "fieldname": "owner",
            "fieldtype": "Data",
            "width": 160
        },
        {
            "label": _("Faculty"),
            "fieldname": "custom_faculty",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Department"),
            "fieldname": "custom_department",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Programme"),
            "fieldname": "custom_program_of_study",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Year of Study"),
            "fieldname": "custom_level",
            "fieldtype": "Data",
            "width": 110
        },
        {
            "label": _("Campus"),
            "fieldname": "custom_campus",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Student Type"),
            "fieldname": "custom_student_type",
            "fieldtype": "Data",
            "width": 120
        },
    ]
    return columns


def get_data(filters):
    conditions = get_conditions(filters)

    data = frappe.db.sql("""
        SELECT
            pe.posting_date,
            pe.name,
            pe.party,
            pe.party_name,
            pe.mode_of_payment,
            pe.paid_to,
            pe.reference_no,
            pe.paid_amount,
            pe.owner,
            c.custom_faculty,
            c.custom_department,
            c.custom_program_of_study,
            c.level as custom_level,
            c.custom_campus,
            c.custom_student_type
        FROM
            `tabPayment Entry` pe
        LEFT JOIN
            `tabCustomer` c ON c.name = pe.party
        WHERE
            pe.docstatus = 1
            AND pe.payment_type = 'Receive'
            AND pe.party_type = 'Customer'
            AND c.customer_group = 'Student'
            {conditions}
        ORDER BY
            pe.posting_date DESC, pe.creation DESC
    """.format(conditions=conditions), filters, as_dict=True)

    return data


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("AND pe.posting_date >= %(from_date)s")

    if filters.get("to_date"):
        conditions.append("AND pe.posting_date <= %(to_date)s")

    if filters.get("paid_to"):
        conditions.append("AND pe.paid_to = %(paid_to)s")

    if filters.get("owner"):
        conditions.append("AND pe.owner = %(owner)s")

    if filters.get("mode_of_payment"):
        conditions.append("AND pe.mode_of_payment = %(mode_of_payment)s")

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
    total = sum(flt(row.get("paid_amount")) for row in data)
    return [
        {
            "label": _("Total Collections"),
            "value": total,
            "datatype": "Currency",
            "currency": "KES"
        },
        {
            "label": _("Total Transactions"),
            "value": len(data),
            "datatype": "Int"
        }
    ]