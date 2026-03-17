import frappe
from frappe import _
from frappe.utils import flt, fmt_money


def execute(filters=None):
    columns = get_columns()
    data, summary = get_data(filters)
    report_summary = get_report_summary(summary)
    return columns, data, None, None, report_summary


def get_columns():
    return [
        {
            "label": _("Allocation ID"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Sponsorship Allocation",
            "width": 190,
        },
        {
            "label": _("Date"),
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": _("Donor"),
            "fieldname": "donor",
            "fieldtype": "Link",
            "options": "Donor",
            "width": 130,
        },
        {
            "label": _("Donor Name"),
            "fieldname": "donor_name",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("Receipt No"),
            "fieldname": "receipt_no",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Invoice Type"),
            "fieldname": "invoice_type",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Financial Aid"),
            "fieldname": "financial_aid",
            "fieldtype": "Data",
            "width": 130,
        },
        {
            "label": _("Student Reg No"),
            "fieldname": "student",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 170,
        },
        {
            "label": _("Student Name"),
            "fieldname": "student_name",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("Allocated Amount"),
            "fieldname": "allocated_amount",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": _("Description"),
            "fieldname": "description",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Available Donation Amount"),
            "fieldname": "total",
            "fieldtype": "Currency",
            "width": 190,
        },
        {
            "label": _("Total Allocated"),
            "fieldname": "total_allocated",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Balance"),
            "fieldname": "balance",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": _("Status"),
            "fieldname": "docstatus",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Journal Entry"),
            "fieldname": "journal_entry",
            "fieldtype": "Link",
            "options": "Journal Entry",
            "width": 160,
        },
    ]


def get_report_summary(summary):
    """
    Returns summary cards shown at the top of the report,
    similar to the Student Fee Balance Report style.
    """
    currency = frappe.get_cached_value("Company", summary.get("company"), "default_currency") or "KES"

    return [
        {
            "value": summary.get("total_allocations", 0),
            "label": _("Total Allocations"),
            "datatype": "Int",
            "indicator": "blue",
        },
        {
            "value": summary.get("total_donors", 0),
            "label": _("Unique Donors"),
            "datatype": "Int",
            "indicator": "blue",
        },
        {
            "value": summary.get("total_beneficiaries", 0),
            "label": _("Total Beneficiaries"),
            "datatype": "Int",
            "indicator": "blue",
        },
        {
            "value": summary.get("total_donation_amount", 0),
            "label": _("Total Donation Amount"),
            "datatype": "Currency",
            "currency": currency,
            "indicator": "green",
        },
        {
            "value": summary.get("total_allocated_amount", 0),
            "label": _("Total Allocated Amount"),
            "datatype": "Currency",
            "currency": currency,
            "indicator": "green",
        },
        {
            "value": summary.get("total_balance", 0),
            "label": _("Total Balance"),
            "datatype": "Currency",
            "currency": currency,
            "indicator": "orange" if summary.get("total_balance", 0) > 0 else "red",
        },
    ]


def get_data(filters):
    conditions, values = get_conditions(filters)

    docstatus_label_map = {0: "Draft", 1: "Submitted", 2: "Cancelled"}

    allocations = frappe.db.sql(
        """
        SELECT
            sa.name,
            sa.date,
            sa.donor,
            sa.donor_name,
            sa.receipt_no,
            sa.invoice_type,
            sa.financial_aid,
            sa.total,
            sa.total_allocated,
            sa.balance,
            sa.docstatus,
            sa.journal_entry
        FROM
            `tabSponsorship Allocation` sa
        WHERE
            {conditions}
        ORDER BY
            sa.date DESC, sa.name DESC
        """.format(
            conditions=conditions
        ),
        values=values,
        as_dict=True,
    )

    if not allocations:
        return [], {
            "company": filters.get("company"),
            "total_allocations": 0,
            "total_donors": 0,
            "total_beneficiaries": 0,
            "total_donation_amount": 0,
            "total_allocated_amount": 0,
            "total_balance": 0,
        }

    allocation_names = [d.name for d in allocations]

    # Beneficiary-level filters
    bene_conditions = ["sab.parent IN ({})".format(", ".join(["%s"] * len(allocation_names)))]
    bene_values = list(allocation_names)

    if filters.get("student"):
        bene_conditions.append("sab.student = %s")
        bene_values.append(filters.get("student"))

    beneficiaries = frappe.db.sql(
        """
        SELECT
            sab.parent,
            sab.student,
            sab.student_name,
            sab.amount,
            sab.description
        FROM
            `tabSponsorship Allocation Beneficiary` sab
        WHERE
            {conditions}
        ORDER BY
            sab.student_name ASC
        """.format(
            conditions=" AND ".join(bene_conditions)
        ),
        bene_values,
        as_dict=True,
    )

    # Group beneficiaries by parent
    beneficiary_map = {}
    for b in beneficiaries:
        beneficiary_map.setdefault(b.parent, []).append(b)

    # If student filter active, only show allocations with matching beneficiaries
    if filters.get("student"):
        allocations = [a for a in allocations if a.name in beneficiary_map]

    # Apply allocated_amount and balance post-filters
    balance_op = filters.get("balance_operator")
    balance_val = filters.get("balance_value")
    allocated_op = filters.get("allocated_operator")
    allocated_val = filters.get("allocated_value")

    def passes_numeric_filter(actual, operator, threshold):
        if not operator or threshold is None:
            return True
        actual = flt(actual)
        threshold = flt(threshold)
        return {
            "=": actual == threshold,
            "<": actual < threshold,
            ">": actual > threshold,
            "<=": actual <= threshold,
            ">=": actual >= threshold,
        }.get(operator, True)

    data = []
    summary_donors = set()
    total_donation_amount = 0.0
    total_allocated_amount = 0.0
    total_balance = 0.0
    total_beneficiaries = 0

    for alloc in allocations:
        # Apply balance filter at allocation level
        if not passes_numeric_filter(alloc.balance, balance_op, balance_val):
            continue

        # Apply allocated filter at allocation level
        if not passes_numeric_filter(alloc.total_allocated, allocated_op, allocated_val):
            continue

        alloc_label = docstatus_label_map.get(alloc.docstatus, "")
        benes = beneficiary_map.get(alloc.name, [])

        summary_donors.add(alloc.donor)
        total_donation_amount += flt(alloc.total)
        total_balance += flt(alloc.balance)
        total_allocated_amount += flt(alloc.total_allocated)
        total_beneficiaries += len(benes)

        if benes:
            for idx, bene in enumerate(benes):
                row = frappe._dict(
                    {
                        "name": alloc.name if idx == 0 else "",
                        "date": alloc.date if idx == 0 else None,
                        "donor": alloc.donor if idx == 0 else "",
                        "donor_name": alloc.donor_name if idx == 0 else "",
                        "receipt_no": alloc.receipt_no if idx == 0 else "",
                        "invoice_type": alloc.invoice_type if idx == 0 else "",
                        "financial_aid": alloc.financial_aid if idx == 0 else "",
                        "total": alloc.total if idx == 0 else 0,
                        "total_allocated": alloc.total_allocated if idx == 0 else 0,
                        "balance": alloc.balance if idx == 0 else 0,
                        "raw_balance": flt(alloc.balance),
                        "docstatus": alloc_label if idx == 0 else "",
                        "journal_entry": alloc.journal_entry if idx == 0 else "",
                        "student": bene.student,
                        "student_name": bene.student_name,
                        "allocated_amount": flt(bene.amount),
                        "description": bene.description,
                    }
                )
                data.append(row)
        else:
            row = frappe._dict(
                {
                    "name": alloc.name,
                    "date": alloc.date,
                    "donor": alloc.donor,
                    "donor_name": alloc.donor_name,
                    "receipt_no": alloc.receipt_no,
                    "invoice_type": alloc.invoice_type,
                    "financial_aid": alloc.financial_aid,
                    "total": alloc.total,
                    "total_allocated": alloc.total_allocated,
                    "balance": alloc.balance,
                    "raw_balance": flt(alloc.balance),
                    "docstatus": alloc_label,
                    "journal_entry": alloc.journal_entry,
                    "student": "",
                    "student_name": "",
                    "allocated_amount": 0,
                    "description": "",
                }
            )
            data.append(row)

    summary = {
        "company": filters.get("company"),
        "total_allocations": len(set(r.name for r in data if r.name)),
        "total_donors": len(summary_donors),
        "total_beneficiaries": total_beneficiaries,
        "total_donation_amount": total_donation_amount,
        "total_allocated_amount": total_allocated_amount,
        "total_balance": total_balance,
    }

    return data, summary


def get_conditions(filters):
    conditions = [
        "sa.company = %(company)s",
        "sa.date BETWEEN %(from_date)s AND %(to_date)s",
    ]
    values = {
        "company": filters.get("company"),
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
    }

    if filters.get("donor"):
        conditions.append("sa.donor = %(donor)s")
        values["donor"] = filters.get("donor")

    if filters.get("invoice_type"):
        conditions.append("sa.invoice_type = %(invoice_type)s")
        values["invoice_type"] = filters.get("invoice_type")

    if filters.get("financial_aid"):
        conditions.append("sa.financial_aid LIKE %(financial_aid)s")
        values["financial_aid"] = f"%{filters.get('financial_aid')}%"

    if filters.get("docstatus"):
        docstatus_map = {"Draft": 0, "Submitted": 1, "Cancelled": 2}
        values["docstatus"] = docstatus_map.get(filters.get("docstatus"), 1)
        conditions.append("sa.docstatus = %(docstatus)s")
    else:
        conditions.append("sa.docstatus IN (0, 1)")

    return " AND ".join(conditions), values