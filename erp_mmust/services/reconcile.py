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

        # cancel JE so references can be added
        if je.docstatus == 1:
            je.cancel()

        for beneficiary in doc.beneficiaries:

            student = beneficiary.student
            remaining = beneficiary.amount

            if not student or remaining <= 0:
                continue

            # find JE account row for this student
            account_row = None
            for row in je.accounts:
                if row.party_type == "Customer" and row.party == student:
                    account_row = row
                    break

            if not account_row:
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
                fields=[
                    "name",
                    "outstanding_amount",
                    "posting_date"
                ],
                order_by="posting_date asc"
            )

            for inv in invoices:

                if remaining <= 0:
                    break

                allocate = min(inv.outstanding_amount, remaining)

                account_row.append("references", {
                    "reference_doctype": "Sales Invoice",
                    "reference_name": inv.name,
                    "allocated_amount": allocate
                })

                remaining -= allocate

        je.save(ignore_permissions=True)
        je.submit()

    except Exception:
        frappe.log_error(
            title="Sponsorship Allocation Auto Reconciliation Failed",
            message=frappe.get_traceback()
        )