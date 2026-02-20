import frappe
from frappe.utils import flt

@frappe.whitelist()
def get_student_credit(customer):
    balance = frappe.db.sql("""
        SELECT SUM(debit - credit)
        FROM `tabGL Entry`
        WHERE party_type = 'Customer'
        AND party = %s
        AND is_cancelled = 0
    """, (customer,))[0][0] or 0

    # Positive = student owes money (debit balance)
    # Negative = student has overpaid (credit balance)
    return {
        "customer": customer,
        "credit_balance": flt(balance)   # ← return raw balance, not just credits
    }

@frappe.whitelist()
def preview_refund(data):
    data = frappe.parse_json(data)

    total = sum([flt(d["refundable_amount"]) for d in data["items"]])

    if data["action_type"] == "Reallocate to Student":
        debit_account = "Student Debtors - MMUST"
        credit_account = "Student Debtors - MMUST"
    else:
        debit_account = "564575 - kakamega sponsor - TtechD"
        credit_account = "Demo Bank Account - TtechD"

    return {
        "total_amount": total,
        "debit_account": debit_account,
        "credit_account": credit_account
    }


@frappe.whitelist()
def create_refund_doc(payload):
    data = frappe.parse_json(payload)

    doc = frappe.new_doc("Student Refund")
    doc.update({
        "request_type":   data["request_type"],
        "action_type":    data["action_type"],
        "funder":         data.get("funder"),           # Donor
        "batch_number":   data.get("batch_number"),
        "source_student": data["source_student"],       # Customer
        "target_student": data.get("target_student"),   # Customer
        "academic_year":  data.get("academic_year")
    })

    total = 0
    for row in data["items"]:
        doc.append("items", {
            "reference_doctype": row["reference_doctype"],
            "reference_name":    row["reference_name"],
            "refundable_amount": row["refundable_amount"]
        })
        total += flt(row["refundable_amount"])

    doc.total_amount = total

    doc.insert()
    doc.submit()

    return doc.name