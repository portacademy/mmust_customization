# accounting_service.py

import frappe
from frappe.utils import flt, nowdate



def process_accounting(doc, method=None):
    if doc.docstatus != 1:
        return

    state = doc.workflow_state

    frappe.log_error(
        title="process_accounting debug",
        message=f"doc: {doc.name} | state: '{state}' | request_type: '{doc.request_type}' | action_type: '{doc.action_type}'"
    )

    if state ==  "Pending PV" and doc.action_type == "Refund to Funder":
        post_receipt_cancellation(doc)
    elif state == "Closed" and doc.action_type == "Reallocate to Student":
        post_reallocation_journal_entry(doc)
    elif state == "Closed" and doc.action_type == "Refund to Funder":
        post_refund_payment_entry(doc)
    elif state == "Receipt Cancelled" and doc.action_type == "Receipt Cancellation":
        post_full_receipt_cancellation(doc)
    elif state == "Hostel Closed" and doc.request_type == "Hostel":
        post_hostel_credit_note(doc)


# ─────────────────────────────────────────────────────────────────────────────
# DONATION — Journal Entry on Donation Submit
# Dr Bank / Cr Sponsor GL Account
# ─────────────────────────────────────────────────────────────────────────────

def post_donation_journal_entry(doc, method=None):
    currency = get_currency()
    company      = get_company()
    # bank_account = get_bank_account(company)
    bank_account = doc.custom_bank_account
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
        f"Amount: <b>{currency} {amount:,.2f}</b>",
        title="Donation Posted",
        indicator="green"
    )


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — RECEIPT CANCELLATION (Refund to Funder path)
# ─────────────────────────────────────────────────────────────────────────────

def post_receipt_cancellation(doc):
    currency = get_currency()
    company  = get_company()

    if frappe.db.get_value("Student Refund", doc.name, "journal_entry"):
        return

    if doc.request_type not in ("HELB", "CDF", "Scholarship"):
        _post_hostel_receipt_cancellation(doc)
        return

    if not doc.beneficiaries:
        frappe.throw("No beneficiaries found. Cannot post Receipt Cancellation.")

    if not doc.sponsorship_allocation:
        frappe.throw("Sponsorship Allocation must be linked before Receipt Cancellation.")

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
        f"Total Refunded to Donor: <b>{currency} {total_refunded_to_donor:,.2f}</b>",
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

    currency = get_currency()
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
                f"{row.target_student_name} | {currency}{amount:,.2f}"
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
                f"{row.student_name} | {currency}{amount:,.2f}"
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
        f"Total Amount Reallocated: <b>{currency}{total_reallocated:,.2f}</b>",
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

    currency        = get_currency()
    company         = get_company()
    amount          = flt(doc.amount_refunded_to_donor)
    funding_account = get_funding_body_account(doc.funder)
    # bank_account    = get_bank_account(company)
    bank_account    = doc.bank_account

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
        f"Amount Refunded: <b>{currency}{amount:,.2f}</b>",
        title="Disbursement Complete",
        indicator="green"
    )


def post_full_receipt_cancellation(doc):
    if not doc.sponsorship_allocation:
        frappe.throw("Sponsorship Allocation is required for Receipt Cancellation.")

    def log(msg):
        frappe.log_error(title="Receipt Cancellation", message=msg)

    log("Step 0: Starting receipt cancellation")

    sa            = frappe.get_doc("Sponsorship Allocation", doc.sponsorship_allocation)
    donation_name = sa.donation

    # Step 1: Find and cancel ALL JEs linked to the Donation
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
                if frappe.db.exists("Journal Entry", pe_name):
                    je = frappe.get_doc("Journal Entry", pe_name)
                    if je.docstatus == 1:
                        je.flags.ignore_links = True
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

    # Step 1b: Find and cancel any Reallocation Student Refunds linked to this SA
    try:
        reallocation_refunds = frappe.get_all(
            "Student Refund",
            filters={
                "sponsorship_allocation": sa.name,
                "action_type": "Reallocate to Student",
                "docstatus": 1
            },
            fields=["name", "journal_entry"]
        )

        log(f"Step 1b: Found {len(reallocation_refunds)} reallocation refunds to cancel")

        for sr in reallocation_refunds:
            if sr.journal_entry:
                # Clear the link FIRST before cancelling
                frappe.db.set_value("Student Refund", sr.name, "journal_entry", None)
                frappe.db.commit()

                if frappe.db.exists("Journal Entry", sr.journal_entry):
                    je = frappe.get_doc("Journal Entry", sr.journal_entry)
                    if je.docstatus == 1:
                        je.flags.ignore_links = True
                        je.cancel()
                        frappe.db.commit()
                        log(f"Step 1b: Reallocation JE {sr.journal_entry} cancelled")
                        frappe.msgprint(
                            f"✅ Reallocation Journal Entry <b>{sr.journal_entry}</b> cancelled.",
                            alert=True, indicator="orange"
                        )

            # Cancel the Student Refund itself
            sr_doc = frappe.get_doc("Student Refund", sr.name)
            sr_doc.flags.ignore_links = True
            sr_doc.cancel()
            frappe.db.commit()
            log(f"Step 1b: Reallocation Student Refund {sr.name} cancelled")
            frappe.msgprint(
                f"✅ Reallocation Student Refund <b>{sr.name}</b> cancelled.",
                alert=True, indicator="orange"
            )

    except Exception as e:
        log(f"Step 1b FAILED: {str(e)}")
        frappe.throw(f"Failed at Step 1b (Reallocation Refunds): {str(e)}")

    # Step 2: Cancel the Sponsorship Allocation JE
    try:
        if sa.journal_entry:
            je_name = sa.journal_entry
            frappe.db.set_value("Sponsorship Allocation", sa.name, "journal_entry", None)
            frappe.db.commit()

            je = frappe.get_doc("Journal Entry", je_name)
            if je.docstatus == 1:
                je.flags.ignore_links = True
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
    # try:
    #     if donation_name:
    #         donation = frappe.get_doc("Donation", donation_name)
    #         donation.reload()
    #         log(f"Step 4: Donation docstatus before cancel: {donation.docstatus}")
    #         if donation.docstatus == 1:
    #             donation.flags.ignore_links = True
    #             donation.cancel()
    #             frappe.db.commit()
    #             log(f"Step 4: Donation {donation_name} cancelled successfully")
    #             frappe.msgprint(
    #                 f"✅ Donation <b>{donation_name}</b> cancelled.",
    #                 alert=True, indicator="orange"
    #             )
    #     else:
    #         log("Step 4: No donation linked — skipping")
    # except Exception as e:
    #     log(f"Step 4 FAILED: {str(e)}")
    #     frappe.throw(f"Failed at Step 4 (Donation): {str(e)}")

    # Step 4: Cancel the Donation
    try:
        if donation_name:
            donation = frappe.get_doc("Donation", donation_name)
            donation.reload()
            log(f"Step 4: Donation docstatus before cancel: {donation.docstatus}")
            if donation.docstatus == 1:
                donation.flags.ignore_links = True
                donation.flags.ignore_permissions = True
                donation.flags.ignore_validate_update_after_submit = True
                try:
                    donation.cancel()
                    frappe.db.commit()
                    log(f"Step 4: Donation {donation_name} cancelled successfully")
                    frappe.msgprint(
                        f"✅ Donation <b>{donation_name}</b> cancelled.",
                        alert=True, indicator="orange"
                    )
                except Exception as cancel_err:
                    # Force cancel via db if normal cancel fails
                    log(f"Step 4: Normal cancel failed, forcing via db: {str(cancel_err)}")
                    frappe.db.set_value("Donation", donation_name, "docstatus", 2)
                    frappe.db.commit()
                    log(f"Step 4: Donation {donation_name} force-cancelled via db")
                    frappe.msgprint(
                        f"✅ Donation <b>{donation_name}</b> force-cancelled.",
                        alert=True, indicator="orange"
                    )
        else:
            log("Step 4: No donation linked — skipping")
    except Exception as e:
        log(f"Step 4 FAILED: {str(e)}")
        frappe.throw(f"Failed at Step 4 (Donation): {str(e)}")

    # Step 5: Clear Student Refund → SA link FIRST, then cancel SA
    # try:
    #     frappe.db.set_value("Student Refund", doc.name, "cancelled_sponsorship_allocation", sa.name)
    #     frappe.db.commit()
    #     log(f"Step 5: Stored cancelled_sponsorship_allocation as {sa.name}")

    #     frappe.db.set_value("Student Refund", doc.name, "sponsorship_allocation", None)
    #     frappe.db.commit()
    #     log(f"Step 5: Cleared sponsorship_allocation on Student Refund {doc.name}")

    #     frappe.db.set_value("Sponsorship Allocation", sa.name, "journal_entry", None)
    #     frappe.db.set_value("Sponsorship Allocation", sa.name, "donation", None)
    #     frappe.db.commit()

    #     sa.reload()
    #     log(f"Step 5: SA docstatus before cancel: {sa.docstatus}")

    #     if sa.docstatus == 1:
    #         sa.flags.ignore_links = True
    #         sa.cancel()
    #         frappe.db.commit()
    #         log(f"Step 5: SA {sa.name} cancelled successfully")
    #         frappe.msgprint(
    #             f"✅ Sponsorship Allocation <b>{sa.name}</b> cancelled.",
    #             alert=True, indicator="orange"
    #         )

    # except Exception as e:
    #     log(f"Step 5 FAILED: {str(e)}")
    #     frappe.throw(f"Failed at Step 5 (Sponsorship Allocation): {str(e)}")

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
            sa.flags.ignore_permissions = True
            sa.flags.ignore_validate_update_after_submit = True
            try:
                sa.cancel()
                frappe.db.commit()
                log(f"Step 5: SA {sa.name} cancelled successfully")
                frappe.msgprint(
                    f"✅ Sponsorship Allocation <b>{sa.name}</b> cancelled.",
                    alert=True, indicator="orange"
                )
            except Exception as cancel_err:
                log(f"Step 5: Normal cancel failed, forcing via db: {str(cancel_err)}")
                frappe.db.set_value("Sponsorship Allocation", sa.name, "docstatus", 2)
                frappe.db.commit()
                log(f"Step 5: SA {sa.name} force-cancelled via db")
                frappe.msgprint(
                    f"✅ Sponsorship Allocation <b>{sa.name}</b> force-cancelled.",
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
# HOSTEL — Credit Note on Approval
# ─────────────────────────────────────────────────────────────────────────────

def post_hostel_credit_note(doc):
    if doc.request_type != "Hostel":
        return

    if not doc.items:
        frappe.throw("No items found. Cannot post Hostel Credit Note.")

    company  = get_company()
    currency = get_currency()

    for row in doc.items:
        if not row.sales_invoice or not flt(row.refundable_amount) > 0:
            continue

        if row.credit_note:
            continue  # already posted

        si = frappe.get_doc("Sales Invoice", row.sales_invoice)

        cn = frappe.new_doc("Sales Invoice")
        cn.is_return     = 1
        # cn.return_against = row.sales_invoice
        cn.update_outstanding_for_self = 0
        cn.customer      = si.customer
        cn.company       = company
        cn.posting_date  = nowdate()
        cn.due_date      = nowdate()
        cn.title         = f"Credit Note - {doc.name}"
        cn.pay_to_recd_from = si.customer_name

        # Copy custom fields if present
        for field in ["custom_semester", "custom_level", "custom_session"]:
            if frappe.db.has_column("Sales Invoice", field):
                cn.set(field, si.get(field))

        # Proportional credit based on refundable vs original
        ratio = flt(row.refundable_amount) / flt(si.grand_total) if flt(si.grand_total) else 1

        for item in si.items:
            cn.append("items", {
                "item_code":      item.item_code,
                "item_name":      item.item_name,
                "qty":            -1,
                "rate":           flt(row.refundable_amount),
                "income_account": item.income_account,
                "cost_center":    item.cost_center,
                "description":    (
                    f"Credit Note for {doc.name} | "
                    f"Narration: {doc.narration or 'N/A'}"
                )
            })

        cn.insert(ignore_permissions=True)
        cn.submit()

        frappe.db.set_value("Student Refund Item", row.name, "credit_note", cn.name)
        frappe.db.commit()

        frappe.msgprint(
            f"✅ Credit Note <b>{cn.name}</b> created against <b>{row.sales_invoice}</b><br>"
            f"Customer: <b>{si.customer_name}</b><br>"
            f"Amount: <b>{currency} {flt(row.refundable_amount):,.2f}</b>",
            alert=True, indicator="green"
        )

    frappe.msgprint(
        f"✅ Hostel Credit Notes posted for <b>{doc.name}</b>.",
        title="Hostel Credit Notes Complete",
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

def get_currency():
    company = get_company()
    return frappe.db.get_value("Company", company, "default_currency") or "NGN"
