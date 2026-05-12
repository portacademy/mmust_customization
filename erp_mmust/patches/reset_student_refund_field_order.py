import frappe


def execute():
    """
    Resets the Student Refund DocType field order in the database to match
    the canonical order defined in the JSON. This is needed because Frappe's
    migrate only appends new fields without correcting the idx of existing ones.
    """
    if not frappe.db.exists("DocType", "Student Refund"):
        return

    correct_order = [
        "section_header",
        "request_type",
        "action_type",
        "refund_type",
        "cancellation_label_helb",
        "cancellation_label_cdf",
        "col_break_1",
        "academic_year",
        "posting_date",
        "section_graduation_refund",
        "graduation_student",
        "graduation_reg_no",
        "graduation_student_name",
        "graduation_phone",
        "graduation_email",
        "graduation_id_number",
        "col_break_graduation",
        "graduation_year_of_study",
        "graduation_programme",
        "graduation_school",
        "graduation_department",
        "graduation_ledger_balance",
        "graduation_amount_to_refund",
        "graduation_bank_account",
        "section_graduation_bank_details",
        "graduation_mode_of_refund",
        "graduate_bank_name",
        "graduate_account_number",
        "graduation_swift_code",
        "graduation_column_break_2",
        "reason_for_graduation_refund",
        "custom_portal_refund_id",
        "section_funder",
        "funder",
        "funder_name",
        "constituency_code",
        "col_break_3",
        "batch_number",
        "request_reference",
        "section_cheque_cancellation",
        "cheque_donation",
        "cheque_id",
        "cheque_donation_amount",
        "col_break_cheque",
        "cheque_donation_date",
        "cheque_donation_mode",
        "section_cancellation_allocations",
        "cancellation_allocations",
        "section_donation",
        "sponsorship_allocation",
        "cancelled_sponsorship_allocation",
        "donation_amount",
        "custom_cheque_id",
        "sponsorship_allocation_date",
        "col_break_donation",
        "total_allocated_in_donation",
        "amount_refunded_to_donor",
        "bank_account",
        "section_beneficiaries",
        "beneficiaries",
        "section_reallocation",
        "reallocations",
        "section_cancellation",
        "cancellation_beneficiaries",
        "section_hostel_details",
        "source_student",
        "hostel_session",
        "hostel_semester",
        "col_break_hostel",
        "narration",
        "section_items",
        "items",
        "total_amount",
        "section_excess_allocation",
        "excess_sponsorship_allocation",
        "excess_funder",
        "excess_funder_name",
        "col_break_excess_1",
        "excess_total_donated",
        "excess_sa_balance",
        "section_excess_accounts",
        "excess_school_bank_account",
        "excess_school_bank_gl_balance",
        "col_break_excess_2",
        "excess_sponsor_gl_account",
        "excess_previously_returned",
        "section_excess_amount",
        "excess_max_transferable",
        "excess_amount_to_return",
        "col_break_excess_3",
        "excess_narration",
        "excess_return_je",
        "section_accounting",
        "debit_account",
        "credit_account",
        "col_break_4",
        "journal_entry",
        "disbursement_journal_entry",
        "sponsorship_reversal_je",
        "reallocation_je",
        "payment_entry",
        "section_narrations",
        "registrar_narration",
        "accountant_narration",
        "col_break_narration_1",
        "finance_officer_narration",
        "section_narrations_2",
        "internal_auditor_narration",
        "col_break_narration_2",
        "payable_accountant_narration",
        "senior_accountant_narration",
        "section_narrations_3",
        "dvc_narration",
        "col_break_narration_3",
        "section_remarks_trail",
        "remarks_trail_placeholder",
        "remarks_trail",
        "workflow_state",
        "amended_from",
    ]

    order_map = {fn: idx for idx, fn in enumerate(correct_order)}

    doctype_doc = frappe.get_doc("DocType", "Student Refund")

    for field in doctype_doc.fields:
        if field.fieldname in order_map:
            field.idx = order_map[field.fieldname] + 1

    doctype_doc.fields.sort(key=lambda f: f.idx)

    doctype_doc.save(ignore_permissions=True)
    frappe.db.commit()

    print("Student Refund field order reset successfully.")
