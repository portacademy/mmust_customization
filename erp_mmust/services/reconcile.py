import frappe
from erpnext.accounts.utils import reconcile_against_document


def auto_reconcile_sponsorship(doc, method):

    try:

        if not doc.journal_entry or not doc.invoice_type:
            return

        je = frappe.get_doc("Journal Entry", doc.journal_entry)

        invoice_map = {
            "Tuition Fee": ["Tuition Fee", "Tuition Adjustment"],
            "Scholarship Fee": ["Scholarship Fee", "Scholarship Adjustment"],
            "Loan Fee": ["Loan Fee", "Loan Adjustment"]
        }

        invoice_filters = invoice_map.get(doc.invoice_type, [doc.invoice_type])

        for row in je.accounts:

            if row.party_type != "Customer":
                continue

            student = row.party
            remaining = row.credit_in_account_currency or 0

            if remaining <= 0:
                continue

            invoices = frappe.get_all(
                "Sales Invoice",
                filters={
                    "customer": student,
                    "docstatus": 1,
                    "is_return": 0,
                    "outstanding_amount": (">", 0),
                    "custom_desc": ["in", invoice_filters]
                },
                fields=["name", "outstanding_amount", "posting_date"],
                order_by="posting_date asc"
            )

            for inv in invoices:

                if remaining <= 0:
                    break

                allocate = min(inv.outstanding_amount, remaining)

                reconcile_against_document(
                    "Sales Invoice",
                    inv.name,
                    "Journal Entry",
                    je.name,
                    allocate
                )

                remaining -= allocate

    except Exception:
        frappe.log_error(
            title="Sponsorship Allocation Auto Reconciliation Failed",
            message=frappe.get_traceback()
        )