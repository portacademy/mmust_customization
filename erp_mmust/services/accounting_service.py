# # accounting_service.py

# import frappe
# from frappe.utils import flt, nowdate

# # FUNDING_BODY_ACCOUNT = "564575 - kakamega sponsor - TtechD"
# FUNDING_BODY_ACCOUNT = "112233445 - 112233445 - Chevron Sponsor - TtechD"


# def process_accounting(doc, method=None):
#     if doc.docstatus != 1:
#         return

#     state = doc.workflow_state

#     if state == "Receipt Cancelled" and doc.action_type == "Refund to Funder":
#         post_receipt_cancellation(doc)
#     elif state == "Closed" and doc.action_type == "Reallocate to Student":
#         post_reallocation_journal_entry(doc)
#     elif state == "Closed" and doc.action_type == "Refund to Funder":
#         post_refund_payment_entry(doc)
#     elif state == "Receipt Cancelled" and doc.action_type == "Receipt Cancellation":
#         post_full_receipt_cancellation(doc)


# # ─────────────────────────────────────────────────────────────────────────────
# # STEP 6 — RECEIPT CANCELLATION (Refund to Funder path)
# # ─────────────────────────────────────────────────────────────────────────────

# def post_receipt_cancellation(doc):
#     if frappe.db.get_value("Student Refund", doc.name, "journal_entry"):
#         return

#     if doc.request_type not in ("HELB", "CDF", "Scholarship"):
#         _post_hostel_receipt_cancellation(doc)
#         return

#     if not doc.beneficiaries:
#         frappe.throw("No beneficiaries found. Cannot post Receipt Cancellation.")

#     if not doc.sponsorship_allocation:
#         frappe.throw("Sponsorship Allocation must be linked before Receipt Cancellation.")

#     company = get_company()
#     student_debtors_account = frappe.db.get_value(
#         "Account",
#         {"account_name": "Student Debtors", "company": company},
#         "name"
#     )
#     if not student_debtors_account:
#         frappe.throw("Student Debtors account not found. Please create it in Chart of Accounts.")

#     total_refunded_to_donor = flt(doc.amount_refunded_to_donor)

#     if total_refunded_to_donor <= 0:
#         frappe.msgprint(
#             "Amount Refunded to Donor is zero — no receipt cancellation entry needed.",
#             indicator="orange", alert=True
#         )
#         return

#     je = frappe.new_doc("Journal Entry")
#     je.voucher_type  = "Journal Entry"
#     je.company       = company
#     je.posting_date  = nowdate()
#     je.user_remark   = (
#         f"Receipt Cancellation (Reversal of Sponsorship Allocation) | "
#         f"{doc.name} | {doc.request_type} | "
#         f"Sponsorship Allocation: {doc.sponsorship_allocation}"
#     )

#     for row in doc.beneficiaries:
#         refunded_for_this_student = flt(row.amount_to_be_refunded)
#         if refunded_for_this_student <= 0:
#             continue

#         je.append("accounts", {
#             "account":                    student_debtors_account,
#             "party_type":                 "Customer",
#             "party":                      row.student,
#             "debit_in_account_currency":  refunded_for_this_student,
#             "credit_in_account_currency": 0,
#             "user_remark": (
#                 f"Reversal — {row.student_name} | "
#                 f"Original: {flt(row.original_allocated_amount):,.2f} | "
#                 f"Refunding: {refunded_for_this_student:,.2f}"
#             )
#         })

#     je.append("accounts", {
#         "account":                    FUNDING_BODY_ACCOUNT,
#         "party_type":                 "Donor",
#         "party":                      doc.funder,
#         "debit_in_account_currency":  0,
#         "credit_in_account_currency": total_refunded_to_donor,
#         "user_remark": (
#             f"{doc.request_type} Refund Liability | "
#             f"Donor: {doc.funder_name} | "
#             f"Sponsorship Allocation: {doc.sponsorship_allocation}"
#         )
#     })

#     je.insert(ignore_permissions=True)
#     je.submit()

#     frappe.db.set_value("Student Refund", doc.name, "journal_entry",   je.name)
#     frappe.db.set_value("Student Refund", doc.name, "credit_account",  FUNDING_BODY_ACCOUNT)
#     frappe.db.set_value("Student Refund", doc.name, "debit_account",   student_debtors_account)

#     frappe.msgprint(
#         f"✅ Step 6 Complete: Receipt Cancellation posted.<br>"
#         f"Journal Entry: <b>{je.name}</b><br>"
#         f"Reversed refunded portion from Student Debtors → {FUNDING_BODY_ACCOUNT}<br>"
#         f"Total Refunded to Donor: <b>₦{total_refunded_to_donor:,.2f}</b>",
#         title="Receipt Cancellation Posted",
#         indicator="green"
#     )


# def _post_hostel_receipt_cancellation(doc):
#     company            = get_company()
#     abbr               = frappe.db.get_value("Company", company, "abbr")
#     receivable_account = get_receivable_account(company)
#     control_account    = f"Hostel Revenue - {abbr}"

#     je = frappe.new_doc("Journal Entry")
#     je.voucher_type  = "Journal Entry"
#     je.company       = company
#     je.posting_date  = nowdate()
#     je.user_remark   = f"Hostel Receipt Cancellation | {doc.name} | Student: {doc.source_student}"

#     je.append("accounts", {
#         "account":                    receivable_account,
#         "party_type":                 "Customer",
#         "party":                      doc.source_student,
#         "debit_in_account_currency":  flt(doc.total_amount),
#         "credit_in_account_currency": 0
#     })
#     je.append("accounts", {
#         "account":                    control_account,
#         "debit_in_account_currency":  0,
#         "credit_in_account_currency": flt(doc.total_amount)
#     })

#     je.insert(ignore_permissions=True)
#     je.submit()

#     frappe.db.set_value("Student Refund", doc.name, "journal_entry", je.name)
#     frappe.msgprint(f"Hostel Receipt Cancellation posted: {je.name}", alert=True)


# # ─────────────────────────────────────────────────────────────────────────────
# # STEP 7 — REALLOCATION (Reallocate to Student path)
# # CORRECTED: Dr Source Student (take from) / Cr Target Student (give to)
# # ─────────────────────────────────────────────────────────────────────────────

# def post_reallocation_journal_entry(doc):
#     if frappe.db.get_value("Student Refund", doc.name, "journal_entry"):
#         return  # Already posted

#     if doc.request_type not in ("HELB", "CDF", "Scholarship"):
#         return

#     if not doc.reallocations:
#         frappe.throw("No reallocations found. Cannot post Reallocation Journal Entry.")

#     company = get_company()
#     receivable_account = get_receivable_account(company)

#     je = frappe.new_doc("Journal Entry")
#     je.voucher_type  = "Journal Entry"
#     je.company       = company
#     je.posting_date  = nowdate()
#     je.user_remark   = (
#         f"Reallocation | {doc.name} | {doc.request_type} | "
#         f"Sponsorship Allocation: {doc.sponsorship_allocation}"
#     )

#     total_reallocated = 0

#     for row in doc.reallocations:
#         amount = flt(row.amount_to_reallocate)
#         if amount <= 0:
#             continue

#         if not row.target_student:
#             continue

#         # DEBIT Source Student (reduce their credit balance)
#         je.append("accounts", {
#             "account":                    receivable_account,
#             "party_type":                 "Customer",
#             "party":                      row.source_student,
#             "debit_in_account_currency":  amount,
#             "credit_in_account_currency": 0,
#             "user_remark": (
#                 f"Reallocation FROM {row.student_name} → "
#                 f"{row.target_student_name} | ₦{amount:,.2f}"
#             )
#         })

#         # CREDIT Target Student (give them credit balance)
#         je.append("accounts", {
#             "account":                    receivable_account,
#             "party_type":                 "Customer",
#             "party":                      row.target_student,
#             "debit_in_account_currency":  0,
#             "credit_in_account_currency": amount,
#             "user_remark": (
#                 f"Reallocation TO {row.target_student_name} ← "
#                 f"{row.student_name} | ₦{amount:,.2f}"
#             )
#         })

#         total_reallocated += amount

#     if not je.accounts:
#         frappe.msgprint("No reallocations to post.", indicator="orange", alert=True)
#         return

#     je.insert(ignore_permissions=True)
#     je.submit()

#     frappe.db.set_value("Student Refund", doc.name, "journal_entry", je.name)

#     frappe.msgprint(
#         f"✅ Reallocation Complete: Journal Entry posted.<br>"
#         f"Journal Entry: <b>{je.name}</b><br>"
#         f"Total Amount Reallocated: <b>₦{total_reallocated:,.2f}</b>",
#         title="Reallocation Posted",
#         indicator="green"
#     )


# # ─────────────────────────────────────────────────────────────────────────────
# # STEP 10 — REFUND TO FUNDER (DISBURSEMENT)
# # Dr 564575 - kakamega sponsor - TtechD / Cr Bank
# # ─────────────────────────────────────────────────────────────────────────────

# # def post_refund_payment_entry(doc):
# #     if frappe.db.get_value("Student Refund", doc.name, "payment_entry"):
# #         return

# #     company      = get_company()
# #     bank_account = get_bank_account(company)

# #     pe = frappe.new_doc("Payment Entry")
# #     pe.payment_type    = "Pay"
# #     pe.company         = company
# #     pe.posting_date    = nowdate()
# #     pe.mode_of_payment = "Cheque"
# #     pe.paid_from       = FUNDING_BODY_ACCOUNT
# #     pe.paid_to         = bank_account
# #     pe.paid_amount     = flt(doc.amount_refunded_to_donor)
# #     pe.received_amount = flt(doc.amount_refunded_to_donor)
# #     pe.reference_no    = doc.batch_number or doc.name
# #     pe.reference_date  = nowdate()
# #     pe.remarks = (
# #         f"Refund to {doc.request_type} | {doc.name} | "
# #         f"Donor: {doc.funder_name or doc.funder} | "
# #         f"Sponsorship Allocation: {doc.sponsorship_allocation or 'N/A'} | "
# #         f"Batch: {doc.batch_number or 'N/A'}"
# #     )

# #     pe.insert(ignore_permissions=True)
# #     pe.submit()

# #     frappe.db.set_value("Student Refund", doc.name, "payment_entry", pe.name)

# #     frappe.get_doc("Payment Entry", pe.name).add_comment(
# #         "Comment",
# #         f"Cheque Register Entry | Student Refund: {doc.name} | "
# #         f"Donor: {doc.funder_name or doc.funder} | "
# #         f"Amount: {flt(doc.amount_refunded_to_donor):,.2f} | "
# #         f"Date: {nowdate()}"
# #     )

# #     frappe.msgprint(
# #         f"✅ Step 10 Complete: Disbursement posted.<br>"
# #         f"Payment Entry: <b>{pe.name}</b><br>"
# #         f"Dr {FUNDING_BODY_ACCOUNT}<br>"
# #         f"Cr {bank_account}<br>"
# #         f"Amount Refunded to Donor: <b>₦{flt(doc.amount_refunded_to_donor):,.2f}</b>",
# #         title="Disbursement Complete",
# #         indicator="green"
# #     )


# def post_refund_payment_entry(doc):
#     if frappe.db.get_value("Student Refund", doc.name, "disbursement_journal_entry"):
#         return

#     company = get_company()
#     amount  = flt(doc.amount_refunded_to_donor)

#     if amount <= 0:
#         frappe.throw("Amount Refunded to Donor is zero — cannot post disbursement.")

#     bank_account = doc.bank_account or get_bank_account(company)

#     if not bank_account:
#         frappe.throw("No bank account found. Please select a Payment Bank Account on the document.")

#     je = frappe.new_doc("Journal Entry")
#     je.voucher_type  = "Bank Entry"
#     je.company       = company
#     je.posting_date  = nowdate()
#     je.cheque_no     = doc.batch_number or doc.name
#     je.cheque_date   = nowdate()
#     je.user_remark   = (
#         f"Refund Disbursement to {doc.request_type} | {doc.name} | "
#         f"Donor: {doc.funder_name or doc.funder} | "
#         f"Batch: {doc.batch_number or 'N/A'}"
#     )

#     # Dr Sponsor account
#     je.append("accounts", {
#         "account":                    FUNDING_BODY_ACCOUNT,
#         "party_type":                 "Donor",
#         "party":                      doc.funder,
#         "debit_in_account_currency":  amount,
#         "credit_in_account_currency": 0,
#         "user_remark": f"Refund to {doc.funder_name or doc.funder}"
#     })

#     # Cr Bank
#     je.append("accounts", {
#         "account":                    bank_account,
#         "debit_in_account_currency":  0,
#         "credit_in_account_currency": amount,
#         "user_remark": f"Cheque payment to {doc.funder_name or doc.funder}"
#     })

#     je.insert(ignore_permissions=True)
#     je.submit()

#     frappe.db.set_value("Student Refund", doc.name, "disbursement_journal_entry", je.name)

#     frappe.msgprint(
#         f"✅ Step 10 Complete: Disbursement posted.<br>"
#         f"Journal Entry: <b>{je.name}</b><br>"
#         f"Dr {FUNDING_BODY_ACCOUNT}<br>"
#         f"Cr {bank_account}<br>"
#         f"Amount Refunded: <b>₦{amount:,.2f}</b>",
#         title="Disbursement Complete",
#         indicator="green"
#     )


# def post_full_receipt_cancellation(doc):
#     if not doc.sponsorship_allocation:
#         frappe.throw("Sponsorship Allocation is required for Receipt Cancellation.")

#     def log(msg):
#         """Log with message in body to avoid 140 char title truncation"""
#         frappe.log_error(title="Receipt Cancellation", message=msg)

#     log("Step 0: Starting receipt cancellation")

#     sa = frappe.get_doc("Sponsorship Allocation", doc.sponsorship_allocation)
#     donation_name = sa.donation

#     # Step 1: Find and cancel ALL Payment Entries linked to the Donation FIRST
#     try:
#         pe_names = []
#         if donation_name:
#             donation = frappe.get_doc("Donation", donation_name)

#             # Check payment_id field
#             if donation.payment_id:
#                 pe_names.append(donation.payment_id)
#                 frappe.db.set_value("Donation", donation_name, "payment_id", None)
#                 frappe.db.commit()

#             # Find ALL Payment Entry References linking to this Donation
#             all_pe_refs = frappe.db.sql("""
#                 SELECT DISTINCT parent FROM `tabPayment Entry Reference`
#                 WHERE reference_doctype = 'Donation'
#                 AND reference_name = %s
#             """, (donation_name,), as_dict=True)

#             for ref in all_pe_refs:
#                 if ref.parent not in pe_names:
#                     pe_names.append(ref.parent)

#             log(f"Step 1: PE names found: {pe_names}")

#             # Clear ALL reference rows linking to this Donation
#             frappe.db.sql("""
#                 DELETE FROM `tabPayment Entry Reference`
#                 WHERE reference_doctype = 'Donation'
#                 AND reference_name = %s
#             """, (donation_name,))
#             frappe.db.commit()

#             # Also clear Dynamic Links
#             frappe.db.sql("""
#                 DELETE FROM `tabDynamic Link`
#                 WHERE link_doctype = 'Donation'
#                 AND link_name = %s
#                 AND parenttype = 'Payment Entry'
#             """, (donation_name,))
#             frappe.db.commit()

#             # Cancel all found Payment Entries
#             for pe_name in pe_names:
#                 if frappe.db.exists("Payment Entry", pe_name):
#                     pe = frappe.get_doc("Payment Entry", pe_name)
#                     if pe.docstatus == 1:
#                         pe.cancel()
#                         frappe.db.commit()
#                         log(f"Step 1: PE {pe_name} cancelled successfully")
#                         frappe.msgprint(
#                             f"✅ Payment Entry <b>{pe_name}</b> cancelled.",
#                             alert=True, indicator="orange"
#                         )

#     except Exception as e:
#         log(f"Step 1 FAILED: {str(e)}")
#         frappe.throw(f"Failed at Step 1 (Payment Entry): {str(e)}")

#     # Step 2: Cancel the Sponsorship Allocation JE
#     try:
#         if sa.journal_entry:
#             je_name = sa.journal_entry
#             frappe.db.set_value("Sponsorship Allocation", sa.name, "journal_entry", None)
#             frappe.db.commit()

#             je = frappe.get_doc("Journal Entry", je_name)
#             if je.docstatus == 1:
#                 je.cancel()
#                 frappe.db.commit()
#                 log(f"Step 2: JE {je_name} cancelled successfully")
#                 frappe.msgprint(
#                     f"✅ Journal Entry <b>{je_name}</b> cancelled.",
#                     alert=True, indicator="orange"
#                 )
#         else:
#             log("Step 2: No JE linked to SA — skipping")
#     except Exception as e:
#         log(f"Step 2 FAILED: {str(e)}")
#         frappe.throw(f"Failed at Step 2 (Journal Entry): {str(e)}")

#     # Step 3: Clear donation link on Sponsorship Allocation
#     try:
#         if donation_name:
#             frappe.db.set_value("Sponsorship Allocation", sa.name, "donation", None)
#             frappe.db.commit()
#             log("Step 3: Donation link cleared on SA")
#     except Exception as e:
#         log(f"Step 3 FAILED: {str(e)}")
#         frappe.throw(f"Failed at Step 3 (Clear donation link): {str(e)}")

#     # Step 4: Cancel the Donation
#     try:
#         if donation_name:
#             donation = frappe.get_doc("Donation", donation_name)
#             donation.reload()
#             log(f"Step 4: Donation docstatus before cancel: {donation.docstatus}")
#             if donation.docstatus == 1:
#                 donation.cancel()
#                 frappe.db.commit()
#                 log(f"Step 4: Donation {donation_name} cancelled successfully")
#                 frappe.msgprint(
#                     f"✅ Donation <b>{donation_name}</b> cancelled.",
#                     alert=True, indicator="orange"
#                 )
#         else:
#             log("Step 4: No donation linked — skipping")
#     except Exception as e:
#         log(f"Step 4 FAILED: {str(e)}")
#         frappe.throw(f"Failed at Step 4 (Donation): {str(e)}")

#     # Step 5: Clear Student Refund → SA link FIRST, then cancel SA
#     # try:
#     #     # Clear Student Refund → SA link BEFORE cancelling SA
#     #     frappe.db.set_value("Student Refund", doc.name, "sponsorship_allocation", None)
#     #     frappe.db.commit()
#     #     log(f"Step 5: Cleared sponsorship_allocation on Student Refund {doc.name}")

#     #     # Clear any remaining links on SA just in case
#     #     frappe.db.set_value("Sponsorship Allocation", sa.name, "journal_entry", None)
#     #     frappe.db.set_value("Sponsorship Allocation", sa.name, "donation", None)
#     #     frappe.db.commit()

#     #     sa.reload()
#     #     log(f"Step 5: SA docstatus before cancel: {sa.docstatus}")

#     #     if sa.docstatus == 1:
#     #         sa.cancel()
#     #         frappe.db.commit()
#     #         log(f"Step 5: SA {sa.name} cancelled successfully")
#     #         frappe.msgprint(
#     #             f"✅ Sponsorship Allocation <b>{sa.name}</b> cancelled.",
#     #             alert=True, indicator="orange"
#     #         )

#     # except Exception as e:
#     #     log(f"Step 5 FAILED: {str(e)}")
#     #     frappe.throw(f"Failed at Step 5 (Sponsorship Allocation): {str(e)}")
    

#     # Step 5: Clear Student Refund → SA link FIRST, then cancel SA
#     try:
#         # Store SA name before clearing so child table remains visible
#         frappe.db.set_value("Student Refund", doc.name, "cancelled_sponsorship_allocation", sa.name)
#         frappe.db.commit()
#         log(f"Step 5: Stored cancelled_sponsorship_allocation as {sa.name}")

#         # Now clear the actual link to unblock SA cancellation
#         frappe.db.set_value("Student Refund", doc.name, "sponsorship_allocation", None)
#         frappe.db.commit()
#         log(f"Step 5: Cleared sponsorship_allocation on Student Refund {doc.name}")

#         # Clear any remaining links on SA just in case
#         frappe.db.set_value("Sponsorship Allocation", sa.name, "journal_entry", None)
#         frappe.db.set_value("Sponsorship Allocation", sa.name, "donation", None)
#         frappe.db.commit()

#         sa.reload()
#         log(f"Step 5: SA docstatus before cancel: {sa.docstatus}")

#         if sa.docstatus == 1:
#             sa.cancel()
#             frappe.db.commit()
#             log(f"Step 5: SA {sa.name} cancelled successfully")
#             frappe.msgprint(
#                 f"✅ Sponsorship Allocation <b>{sa.name}</b> cancelled.",
#                 alert=True, indicator="orange"
#             )

#     except Exception as e:
#         log(f"Step 5 FAILED: {str(e)}")
#         frappe.throw(f"Failed at Step 5 (Sponsorship Allocation): {str(e)}")

#     frappe.msgprint(
#         f"✅ Receipt Cancellation complete for <b>{doc.sponsorship_allocation}</b>.",
#         title="Receipt Cancellation Complete",
#         indicator="green"
#     )


# # ─────────────────────────────────────────────────────────────────────────────
# # HELPERS
# # ─────────────────────────────────────────────────────────────────────────────

# def get_company():
#     return (
#         frappe.defaults.get_user_default("company") or
#         frappe.db.get_single_value("Global Defaults", "default_company")
#     )

# def get_receivable_account(company):
#     account = frappe.db.get_value("Company", company, "default_receivable_account")
#     if not account:
#         abbr = frappe.db.get_value("Company", company, "abbr")
#         account = f"Debtors - {abbr}"
#     return account

# def get_bank_account(company):
#     account = frappe.db.get_value("Company", company, "default_bank_account")
#     if not account:
#         abbr = frappe.db.get_value("Company", company, "abbr")
#         account = f"Bank - {abbr}"
#     return account







# accounting_service.py

import frappe
from frappe.utils import flt, nowdate


def process_accounting(doc, method=None):
    if doc.docstatus != 1:
        return

    state = doc.workflow_state

    if state == "Receipt Cancelled" and doc.action_type == "Refund to Funder":
        post_receipt_cancellation(doc)
    elif state == "Closed" and doc.action_type == "Reallocate to Student":
        post_reallocation_journal_entry(doc)
    elif state == "Closed" and doc.action_type == "Refund to Funder":
        post_refund_payment_entry(doc)
    elif state == "Receipt Cancelled" and doc.action_type == "Receipt Cancellation":
        post_full_receipt_cancellation(doc)


# ─────────────────────────────────────────────────────────────────────────────
# DONATION — Journal Entry on Donation Submit
# Dr Bank / Cr Sponsor GL Account
# ─────────────────────────────────────────────────────────────────────────────

def post_donation_journal_entry(doc, method=None):
    if frappe.db.get_value("Donation", doc.name, "payment_id"):
        return  # Already has a payment linked, skip

    company      = get_company()
    bank_account = get_bank_account(company)
    funding_account = get_funding_body_account(doc.donor)

    amount = flt(doc.amount)
    if amount <= 0:
        return

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Bank Entry"
    je.company      = company
    je.posting_date = doc.date or nowdate()
    je.cheque_no    = doc.name
    je.cheque_date  = doc.date or nowdate()
    je.user_remark  = (
        f"Donation Received | {doc.name} | "
        f"Donor: {doc.donor_name or doc.donor}"
    )

    # Dr Bank (money arrives in bank)
    je.append("accounts", {
        "account":                    bank_account,
        "debit_in_account_currency":  amount,
        "credit_in_account_currency": 0,
        "user_remark": f"Donation received from {doc.donor_name or doc.donor}"
    })

    # Cr Sponsor GL Account (liability to sponsor created)
    je.append("accounts", {
        "account":                    funding_account,
        "debit_in_account_currency":  0,
        "credit_in_account_currency": amount,
        "user_remark": f"Donation liability | {doc.name}"
    })

    je.insert(ignore_permissions=True)
    je.submit()

    # Store JE name in payment_id field for reference and to prevent duplicate posting
    frappe.db.set_value("Donation", doc.name, "payment_id", je.name)

    frappe.msgprint(
        f"✅ Donation Journal Entry posted: <b>{je.name}</b><br>"
        f"Dr {bank_account}<br>"
        f"Cr {funding_account}<br>"
        f"Amount: <b>₦{amount:,.2f}</b>",
        title="Donation Posted",
        indicator="green"
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — RECEIPT CANCELLATION (Refund to Funder path)
# ─────────────────────────────────────────────────────────────────────────────

def post_receipt_cancellation(doc):
    if frappe.db.get_value("Student Refund", doc.name, "journal_entry"):
        return

    if doc.request_type not in ("HELB", "CDF", "Scholarship"):
        _post_hostel_receipt_cancellation(doc)
        return

    if not doc.beneficiaries:
        frappe.throw("No beneficiaries found. Cannot post Receipt Cancellation.")

    if not doc.sponsorship_allocation:
        frappe.throw("Sponsorship Allocation must be linked before Receipt Cancellation.")

    company = get_company()
    funding_account = get_funding_body_account(doc.funder)

    student_debtors_account = frappe.db.get_value(
        "Account",
        {"account_name": "Student Debtors", "company": company},
        "name"
    )
    if not student_debtors_account:
        frappe.throw("Student Debtors account not found. Please create it in Chart of Accounts.")

    total_refunded_to_donor = flt(doc.amount_refunded_to_donor)

    if total_refunded_to_donor <= 0:
        frappe.msgprint(
            "Amount Refunded to Donor is zero — no receipt cancellation entry needed.",
            indicator="orange", alert=True
        )
        return

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.company      = company
    je.posting_date = nowdate()
    je.user_remark  = (
        f"Receipt Cancellation (Reversal of Sponsorship Allocation) | "
        f"{doc.name} | {doc.request_type} | "
        f"Sponsorship Allocation: {doc.sponsorship_allocation}"
    )

    for row in doc.beneficiaries:
        refunded_for_this_student = flt(row.amount_to_be_refunded)
        if refunded_for_this_student <= 0:
            continue

        je.append("accounts", {
            "account":                    student_debtors_account,
            "party_type":                 "Customer",
            "party":                      row.student,
            "debit_in_account_currency":  refunded_for_this_student,
            "credit_in_account_currency": 0,
            "user_remark": (
                f"Reversal — {row.student_name} | "
                f"Original: {flt(row.original_allocated_amount):,.2f} | "
                f"Refunding: {refunded_for_this_student:,.2f}"
            )
        })

    je.append("accounts", {
        "account":                    funding_account,
        "party_type":                 "Donor",
        "party":                      doc.funder,
        "debit_in_account_currency":  0,
        "credit_in_account_currency": total_refunded_to_donor,
        "user_remark": (
            f"{doc.request_type} Refund Liability | "
            f"Donor: {doc.funder_name} | "
            f"Sponsorship Allocation: {doc.sponsorship_allocation}"
        )
    })

    je.insert(ignore_permissions=True)
    je.submit()

    frappe.db.set_value("Student Refund", doc.name, "journal_entry",  je.name)
    frappe.db.set_value("Student Refund", doc.name, "credit_account", funding_account)
    frappe.db.set_value("Student Refund", doc.name, "debit_account",  student_debtors_account)

    frappe.msgprint(
        f"✅ Step 6 Complete: Receipt Cancellation posted.<br>"
        f"Journal Entry: <b>{je.name}</b><br>"
        f"Reversed refunded portion from Student Debtors → {funding_account}<br>"
        f"Total Refunded to Donor: <b>₦{total_refunded_to_donor:,.2f}</b>",
        title="Receipt Cancellation Posted",
        indicator="green"
    )


def _post_hostel_receipt_cancellation(doc):
    company            = get_company()
    abbr               = frappe.db.get_value("Company", company, "abbr")
    receivable_account = get_receivable_account(company)
    control_account    = f"Hostel Revenue - {abbr}"

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.company      = company
    je.posting_date = nowdate()
    je.user_remark  = f"Hostel Receipt Cancellation | {doc.name} | Student: {doc.source_student}"

    je.append("accounts", {
        "account":                    receivable_account,
        "party_type":                 "Customer",
        "party":                      doc.source_student,
        "debit_in_account_currency":  flt(doc.total_amount),
        "credit_in_account_currency": 0
    })
    je.append("accounts", {
        "account":                    control_account,
        "debit_in_account_currency":  0,
        "credit_in_account_currency": flt(doc.total_amount)
    })

    je.insert(ignore_permissions=True)
    je.submit()

    frappe.db.set_value("Student Refund", doc.name, "journal_entry", je.name)
    frappe.msgprint(f"Hostel Receipt Cancellation posted: {je.name}", alert=True)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — REALLOCATION (Reallocate to Student path)
# Dr Source Student (take from) / Cr Target Student (give to)
# ─────────────────────────────────────────────────────────────────────────────

def post_reallocation_journal_entry(doc):
    if frappe.db.get_value("Student Refund", doc.name, "journal_entry"):
        return

    if doc.request_type not in ("HELB", "CDF", "Scholarship"):
        return

    if not doc.reallocations:
        frappe.throw("No reallocations found. Cannot post Reallocation Journal Entry.")

    company            = get_company()
    receivable_account = get_receivable_account(company)

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.company      = company
    je.posting_date = nowdate()
    je.user_remark  = (
        f"Reallocation | {doc.name} | {doc.request_type} | "
        f"Sponsorship Allocation: {doc.sponsorship_allocation}"
    )

    total_reallocated = 0

    for row in doc.reallocations:
        amount = flt(row.amount_to_reallocate)
        if amount <= 0 or not row.target_student:
            continue

        # Dr Source Student (reduce their credit balance)
        je.append("accounts", {
            "account":                    receivable_account,
            "party_type":                 "Customer",
            "party":                      row.source_student,
            "debit_in_account_currency":  amount,
            "credit_in_account_currency": 0,
            "user_remark": (
                f"Reallocation FROM {row.student_name} → "
                f"{row.target_student_name} | ₦{amount:,.2f}"
            )
        })

        # Cr Target Student (give them credit balance)
        je.append("accounts", {
            "account":                    receivable_account,
            "party_type":                 "Customer",
            "party":                      row.target_student,
            "debit_in_account_currency":  0,
            "credit_in_account_currency": amount,
            "user_remark": (
                f"Reallocation TO {row.target_student_name} ← "
                f"{row.student_name} | ₦{amount:,.2f}"
            )
        })

        total_reallocated += amount

    if not je.accounts:
        frappe.msgprint("No reallocations to post.", indicator="orange", alert=True)
        return

    je.insert(ignore_permissions=True)
    je.submit()

    frappe.db.set_value("Student Refund", doc.name, "journal_entry", je.name)

    frappe.msgprint(
        f"✅ Reallocation Complete: Journal Entry posted.<br>"
        f"Journal Entry: <b>{je.name}</b><br>"
        f"Total Amount Reallocated: <b>₦{total_reallocated:,.2f}</b>",
        title="Reallocation Posted",
        indicator="green"
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 10 — REFUND TO FUNDER (DISBURSEMENT)
# Dr Sponsor GL Account / Cr Bank
# ─────────────────────────────────────────────────────────────────────────────

def post_refund_payment_entry(doc):
    if frappe.db.get_value("Student Refund", doc.name, "disbursement_journal_entry"):
        return

    company         = get_company()
    amount          = flt(doc.amount_refunded_to_donor)
    funding_account = get_funding_body_account(doc.funder)
    bank_account    = get_bank_account(company)

    if amount <= 0:
        frappe.throw("Amount Refunded to Donor is zero — cannot post disbursement.")

    if not bank_account:
        frappe.throw("No bank account found. Please select a Payment Bank Account on the document.")

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Bank Entry"
    je.company      = company
    je.posting_date = nowdate()
    je.cheque_no    = doc.batch_number or doc.name
    je.cheque_date  = nowdate()
    je.user_remark  = (
        f"Refund Disbursement to {doc.request_type} | {doc.name} | "
        f"Donor: {doc.funder_name or doc.funder} | "
        f"Batch: {doc.batch_number or 'N/A'}"
    )

    # Dr Sponsor GL Account (reduce liability to sponsor)
    je.append("accounts", {
        "account":                    funding_account,
        "party_type":                 "Donor",
        "party":                      doc.funder,
        "debit_in_account_currency":  amount,
        "credit_in_account_currency": 0,
        "user_remark": f"Refund to {doc.funder_name or doc.funder}"
    })

    # Cr Bank (money leaves bank to sponsor)
    je.append("accounts", {
        "account":                    bank_account,
        "debit_in_account_currency":  0,
        "credit_in_account_currency": amount,
        "user_remark": f"Cheque payment to {doc.funder_name or doc.funder}"
    })

    je.insert(ignore_permissions=True)
    je.submit()

    frappe.db.set_value("Student Refund", doc.name, "disbursement_journal_entry", je.name)
    frappe.db.set_value("Student Refund", doc.name, "debit_account",  funding_account)
    frappe.db.set_value("Student Refund", doc.name, "credit_account", bank_account)

    frappe.msgprint(
        f"✅ Step 10 Complete: Disbursement posted.<br>"
        f"Journal Entry: <b>{je.name}</b><br>"
        f"Dr {funding_account}<br>"
        f"Cr {bank_account}<br>"
        f"Amount Refunded: <b>₦{amount:,.2f}</b>",
        title="Disbursement Complete",
        indicator="green"
    )


# ─────────────────────────────────────────────────────────────────────────────
# RECEIPT CANCELLATION (Full reversal — Receipt Cancellation action type)
# ─────────────────────────────────────────────────────────────────────────────

def post_full_receipt_cancellation(doc):
    if not doc.sponsorship_allocation:
        frappe.throw("Sponsorship Allocation is required for Receipt Cancellation.")

    def log(msg):
        frappe.log_error(title="Receipt Cancellation", message=msg)

    log("Step 0: Starting receipt cancellation")

    sa            = frappe.get_doc("Sponsorship Allocation", doc.sponsorship_allocation)
    donation_name = sa.donation

    # Step 1: Find and cancel ALL Payment Entries / JEs linked to the Donation
    try:
        pe_names = []
        if donation_name:
            donation = frappe.get_doc("Donation", donation_name)

            if donation.payment_id:
                pe_names.append(donation.payment_id)
                frappe.db.set_value("Donation", donation_name, "payment_id", None)
                frappe.db.commit()

            all_pe_refs = frappe.db.sql("""
                SELECT DISTINCT parent FROM `tabPayment Entry Reference`
                WHERE reference_doctype = 'Donation'
                AND reference_name = %s
            """, (donation_name,), as_dict=True)

            for ref in all_pe_refs:
                if ref.parent not in pe_names:
                    pe_names.append(ref.parent)

            log(f"Step 1: PE/JE names found: {pe_names}")

            frappe.db.sql("""
                DELETE FROM `tabPayment Entry Reference`
                WHERE reference_doctype = 'Donation'
                AND reference_name = %s
            """, (donation_name,))
            frappe.db.commit()

            frappe.db.sql("""
                DELETE FROM `tabDynamic Link`
                WHERE link_doctype = 'Donation'
                AND link_name = %s
                AND parenttype = 'Payment Entry'
            """, (donation_name,))
            frappe.db.commit()

            for pe_name in pe_names:
                # Could be a JE (from post_donation_journal_entry) or PE
                if frappe.db.exists("Journal Entry", pe_name):
                    je = frappe.get_doc("Journal Entry", pe_name)
                    if je.docstatus == 1:
                        je.cancel()
                        frappe.db.commit()
                        log(f"Step 1: JE {pe_name} cancelled successfully")
                        frappe.msgprint(
                            f"✅ Journal Entry <b>{pe_name}</b> cancelled.",
                            alert=True, indicator="orange"
                        )
                elif frappe.db.exists("Payment Entry", pe_name):
                    pe = frappe.get_doc("Payment Entry", pe_name)
                    if pe.docstatus == 1:
                        pe.cancel()
                        frappe.db.commit()
                        log(f"Step 1: PE {pe_name} cancelled successfully")
                        frappe.msgprint(
                            f"✅ Payment Entry <b>{pe_name}</b> cancelled.",
                            alert=True, indicator="orange"
                        )

    except Exception as e:
        log(f"Step 1 FAILED: {str(e)}")
        frappe.throw(f"Failed at Step 1 (Payment Entry/JE): {str(e)}")

    # Step 2: Cancel the Sponsorship Allocation JE
    try:
        if sa.journal_entry:
            je_name = sa.journal_entry
            frappe.db.set_value("Sponsorship Allocation", sa.name, "journal_entry", None)
            frappe.db.commit()

            je = frappe.get_doc("Journal Entry", je_name)
            if je.docstatus == 1:
                je.cancel()
                frappe.db.commit()
                log(f"Step 2: JE {je_name} cancelled successfully")
                frappe.msgprint(
                    f"✅ Journal Entry <b>{je_name}</b> cancelled.",
                    alert=True, indicator="orange"
                )
        else:
            log("Step 2: No JE linked to SA — skipping")
    except Exception as e:
        log(f"Step 2 FAILED: {str(e)}")
        frappe.throw(f"Failed at Step 2 (Journal Entry): {str(e)}")

    # Step 3: Clear donation link on Sponsorship Allocation
    try:
        if donation_name:
            frappe.db.set_value("Sponsorship Allocation", sa.name, "donation", None)
            frappe.db.commit()
            log("Step 3: Donation link cleared on SA")
    except Exception as e:
        log(f"Step 3 FAILED: {str(e)}")
        frappe.throw(f"Failed at Step 3 (Clear donation link): {str(e)}")

    # Step 4: Cancel the Donation
    try:
        if donation_name:
            donation = frappe.get_doc("Donation", donation_name)
            donation.reload()
            log(f"Step 4: Donation docstatus before cancel: {donation.docstatus}")
            if donation.docstatus == 1:
                donation.cancel()
                frappe.db.commit()
                log(f"Step 4: Donation {donation_name} cancelled successfully")
                frappe.msgprint(
                    f"✅ Donation <b>{donation_name}</b> cancelled.",
                    alert=True, indicator="orange"
                )
        else:
            log("Step 4: No donation linked — skipping")
    except Exception as e:
        log(f"Step 4 FAILED: {str(e)}")
        frappe.throw(f"Failed at Step 4 (Donation): {str(e)}")

    # Step 5: Clear Student Refund → SA link FIRST, then cancel SA
    try:
        frappe.db.set_value("Student Refund", doc.name, "cancelled_sponsorship_allocation", sa.name)
        frappe.db.commit()
        log(f"Step 5: Stored cancelled_sponsorship_allocation as {sa.name}")

        frappe.db.set_value("Student Refund", doc.name, "sponsorship_allocation", None)
        frappe.db.commit()
        log(f"Step 5: Cleared sponsorship_allocation on Student Refund {doc.name}")

        frappe.db.set_value("Sponsorship Allocation", sa.name, "journal_entry", None)
        frappe.db.set_value("Sponsorship Allocation", sa.name, "donation", None)
        frappe.db.commit()

        sa.reload()
        log(f"Step 5: SA docstatus before cancel: {sa.docstatus}")

        if sa.docstatus == 1:
            sa.flags.ignore_links = True
            sa.cancel()
            frappe.db.commit()
            log(f"Step 5: SA {sa.name} cancelled successfully")
            frappe.msgprint(
                f"✅ Sponsorship Allocation <b>{sa.name}</b> cancelled.",
                alert=True, indicator="orange"
            )

    except Exception as e:
        log(f"Step 5 FAILED: {str(e)}")
        frappe.throw(f"Failed at Step 5 (Sponsorship Allocation): {str(e)}")

    frappe.msgprint(
        f"✅ Receipt Cancellation complete for <b>{sa.name}</b>.",
        title="Receipt Cancellation Complete",
        indicator="green"
    )


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_funding_body_account(funder):
    account = frappe.db.get_value("Donor", funder, "custom_sponsor_gl_account")
    if not account:
        frappe.throw(
            f"No Sponsor GL Account set on Donor <b>{funder}</b>. "
            f"Please set it in the Donor record before proceeding."
        )
    return account

def get_company():
    return (
        frappe.defaults.get_user_default("company") or
        frappe.db.get_single_value("Global Defaults", "default_company")
    )

def get_receivable_account(company):
    account = frappe.db.get_value("Company", company, "default_receivable_account")
    if not account:
        abbr    = frappe.db.get_value("Company", company, "abbr")
        account = f"Debtors - {abbr}"
    return account

# def get_bank_account(company):
#     account = frappe.db.get_value("Company", company, "default_bank_account")
#     if not account:
#         abbr    = frappe.db.get_value("Company", company, "abbr")
#         account = f"Bank - {abbr}"
#     return account

# def get_bank_account(company):
#     # First try company default
#     account = frappe.db.get_value("Company", company, "default_bank_account")
#     frappe.log_error(title="get_bank_account", message=f"company={company} | default_bank_account={account}")
#     if account:
#         return account

#     # Fall back to first Bank Account record for this company
#     bank_account = frappe.db.get_value(
#         "Bank Account",
#         {"company": company, "is_company_account": 1, "disabled": 0},
#         "account"
#     )
#     frappe.log_error(title="get_bank_account", message=f"fallback bank_account={bank_account}")
#     if bank_account:
#         return bank_account

#     frappe.throw(
#         f"No bank account found for company {company}. "
#         f"Please set a Default Bank Account in Company settings."
#     )



def get_bank_account(company):
    # First try MMUST Donor Settings
    account = frappe.db.get_single_value("MMUST Donor Settings", "default_payment_bank_account")
    if account:
        return account

    # # Fall back to company default
    # account = frappe.db.get_value("Company", company, "default_bank_account")
    # if account:
    #     return account

    # # Fall back to first Bank Account record
    # bank_account = frappe.db.get_value(
    #     "Bank Account",
    #     {"company": company, "is_company_account": 1, "disabled": 0},
    #     "account"
    # )
    # if bank_account:
    #     return bank_account
    else :
        frappe.throw(
            f"No bank account found. Please set a Default Payment Bank Account in MMUST Donor Settings."
        )