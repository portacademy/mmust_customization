import frappe
from frappe.utils import flt, now_datetime, get_fullname
from frappe.model.document import Document


class StudentRefund(Document):

    def before_save(self):
        self.capture_remark_trail()

    def before_submit(self):
        self.capture_remark_trail()

    def validate(self):
        self.calculate_total()
        if self.docstatus == 1:
            return
        self.validate_mandatory_fields()
        
        if self.action_type == "Refund to Funder":
            self.validate_beneficiaries()
            self.calculate_amount_refunded_to_donor()
        elif self.action_type == "Reallocate to Student":
            self.validate_reallocations()
            self.calculate_reallocation_total()
        elif self.request_type == "Hostel":
            self.validate_hostel_items()
    
    def capture_remark_trail(self):
        remark_fields = [
            ("accountant_narration", "Student Finance Accountant"),
            ("finance_officer_narration", "Finance Officer"),
            ("internal_auditor_narration", "Internal Auditor"),
            ("payable_accountant_narration", "Payable Accountant"),
            ("dvc_narration", "DVC Finance"),
            ("accounts_manager_narration", "Accounts Manager"),
        ]

        # Load the saved (old) version from DB to compare
        if self.is_new():
            old_doc = None
        else:
            try:
                old_doc = frappe.get_doc(self.doctype, self.name)
            except Exception:
                old_doc = None

        new_entries = []

        for fieldname, role_label in remark_fields:
            new_value = (self.get(fieldname) or "").strip()
            old_value = (old_doc.get(fieldname) or "").strip() if old_doc else ""

            if new_value and new_value != old_value:
                timestamp = now_datetime().strftime("%d %b %Y %H:%M")
                user = get_fullname(frappe.session.user)
                state = self.workflow_state or ""
                entry = f"[{timestamp}] {user} ({role_label}) [{state}]:\n{new_value}"
                new_entries.append(entry)

        if new_entries:
            existing = (self.remarks_trail or "").strip()
            separator = "\n\n" + "─" * 60 + "\n\n"
            appended = separator.join(new_entries)
            self.remarks_trail = (existing + separator + appended).strip() if existing else appended.strip()


    def calculate_total(self):
        if self.request_type == "Hostel":
            self.total_amount = sum(flt(row.refundable_amount) for row in (self.items or []))

    # def validate_mandatory_fields(self):

    #     if self.request_type in ('HELB', 'CDF', 'Scholarship'):
    #         if not self.sponsorship_allocation:
    #             frappe.throw(
    #                 "Sponsorship Allocation is required for HELB, CDF, and Scholarship requests.",
    #                 title="Missing Field"
    #             )

    #     if self.action_type == 'Refund to Funder' and \
    #        self.request_type in ('HELB', 'CDF', 'Scholarship'):
    #         if not self.bank_account:
    #             frappe.throw(
    #                 "Payment Bank Account is required for Refund to Funder.",
    #                 title="Missing Field"
    #             )

    def validate_mandatory_fields(self):
        if self.request_type in ('HELB', 'CDF', 'Scholarship'):
            if self.action_type == 'Receipt Cancellation':
                # Receipt Cancellation uses cheque_donation instead
                if not self.cheque_donation:
                    frappe.throw(
                        "Donation (Cheque) is required for Receipt Cancellation.",
                        title="Missing Field"
                    )
            else:
                if not self.sponsorship_allocation:
                    frappe.throw(
                        "Sponsorship Allocation is required for HELB, CDF, and Scholarship requests.",
                        title="Missing Field"
                    )

        if self.action_type == 'Refund to Funder' and \
        self.request_type in ('HELB', 'CDF', 'Scholarship'):
            if not self.bank_account:
                frappe.throw(
                    "Payment Bank Account is required for Refund to Funder.",
                    title="Missing Field"
                )

    # ─── REFUND TO FUNDER VALIDATIONS ────────────────────────────────────────

    def validate_beneficiaries(self):
        if self.request_type not in ("HELB", "CDF", "Scholarship"):
            return
        if not self.beneficiaries:
            return
        
        has_any_refund = any(flt(row.amount_to_be_refunded) > 0 for row in self.beneficiaries)
        if not has_any_refund:
            frappe.throw(
                "At least one beneficiary must have an Amount to be Refunded greater than zero.",
                title="Missing Refund Amount"
            )

        total_to_refund = 0

        for row in self.beneficiaries:
            original  = flt(row.original_allocated_amount)
            to_refund = flt(row.amount_to_be_refunded)

            if to_refund <= 0:
                continue

            gl_balance = self._get_student_gl_balance(row.student)

            if gl_balance > 0:
                frappe.throw(
                    f"Row {row.idx} — <b>{row.student_name}</b>: "
                    f"This student has an outstanding debit balance of "
                    f"<b>₦{gl_balance:,.2f}</b> (they owe money). "
                    f"A refund cannot be processed for students with an outstanding balance."
                )

            credit_balance = abs(gl_balance) if gl_balance < 0 else 0

            if to_refund > original:
                frappe.throw(
                    f"Row {row.idx} — <b>{row.student_name}</b>: "
                    f"Amount to be Refunded (<b>₦{to_refund:,.2f}</b>) cannot exceed "
                    f"Original Allocated Amount (<b>₦{original:,.2f}</b>)."
                )

            if to_refund > credit_balance:
                frappe.throw(
                    f"Row {row.idx} — <b>{row.student_name}</b>: "
                    f"Amount to be Refunded (<b>₦{to_refund:,.2f}</b>) cannot exceed "
                    f"the student's available credit balance in the ledger "
                    f"(<b>₦{credit_balance:,.2f}</b>)."
                )

            total_to_refund += to_refund

        total_allocated = flt(self.total_allocated_in_donation)
        if total_to_refund > total_allocated + 0.01:
            frappe.throw(
                f"Sum of Amounts to be Refunded (<b>₦{total_to_refund:,.2f}</b>) "
                f"cannot exceed Total Allocated in Sponsorship Allocation "
                f"(<b>₦{total_allocated:,.2f}</b>)."
            )

    def calculate_amount_refunded_to_donor(self):
        if self.request_type not in ("HELB", "CDF", "Scholarship"):
            return
        total_to_refund = sum(
            flt(row.amount_to_be_refunded) for row in (self.beneficiaries or [])
        )
        self.amount_refunded_to_donor = total_to_refund
        self.total_amount = total_to_refund

    # ─── REALLOCATE TO STUDENT VALIDATIONS ───────────────────────────────────

    def validate_reallocations(self):
        if self.request_type not in ("HELB", "CDF", "Scholarship"):
            return
        if not self.reallocations:
            return
        
        has_any_reallocation = any(flt(row.amount_to_reallocate) > 0 for row in self.reallocations)
        if not has_any_reallocation:
            frappe.throw(
                "At least one row must have an Amount to Reallocate greater than zero.",
                title="Missing Reallocation Amount"
            )

        total_to_reallocate = 0

        for row in self.reallocations:
            original      = flt(row.original_allocated_amount)
            to_reallocate = flt(row.amount_to_reallocate)

            if to_reallocate <= 0:
                continue

            if not row.target_student:
                frappe.throw(
                    f"Row {row.idx} — <b>{row.student_name}</b>: "
                    f"Target Student is required when Amount to Reallocate is greater than zero."
                )

            # Prevent reallocating to self
            if row.target_student == row.source_student:
                frappe.throw(
                    f"Row {row.idx} — <b>{row.student_name}</b>: "
                    f"Target Student cannot be the same as Source Student."
                )

            # Get source student GL balance
            gl_balance = self._get_student_gl_balance(row.source_student)

            if gl_balance > 0:
                frappe.throw(
                    f"Row {row.idx} — <b>{row.student_name}</b>: "
                    f"This student has an outstanding debit balance of "
                    f"<b>₦{gl_balance:,.2f}</b> (they owe money). "
                    f"A reallocation cannot be processed for students with an outstanding balance."
                )

            credit_balance = abs(gl_balance) if gl_balance < 0 else 0

            if to_reallocate > original:
                frappe.throw(
                    f"Row {row.idx} — <b>{row.student_name}</b>: "
                    f"Amount to Reallocate (<b>₦{to_reallocate:,.2f}</b>) cannot exceed "
                    f"Original Allocated Amount (<b>₦{original:,.2f}</b>)."
                )

            if to_reallocate > credit_balance:
                frappe.throw(
                    f"Row {row.idx} — <b>{row.student_name}</b>: "
                    f"Amount to Reallocate (<b>₦{to_reallocate:,.2f}</b>) cannot exceed "
                    f"the student's available credit balance in the ledger "
                    f"(<b>₦{credit_balance:,.2f}</b>)."
                )

            total_to_reallocate += to_reallocate

        total_allocated = flt(self.total_allocated_in_donation)
        if total_to_reallocate > total_allocated + 0.01:
            frappe.throw(
                f"Sum of Amounts to Reallocate (<b>₦{total_to_reallocate:,.2f}</b>) "
                f"cannot exceed Total Allocated in Sponsorship Allocation "
                f"(<b>₦{total_allocated:,.2f}</b>)."
            )

    def calculate_reallocation_total(self):
        if self.request_type not in ("HELB", "CDF", "Scholarship"):
            return
        total_to_reallocate = sum(
            flt(row.amount_to_reallocate) for row in (self.reallocations or [])
        )
        self.total_amount = total_to_reallocate

    # ─── HELPER METHODS ───────────────────────────────────────────────────────

    def _get_student_gl_balance(self, customer):
        """
        Returns the net GL balance for a student (Customer).
        Positive = debit balance (student owes money).
        Negative = credit balance (student has overpaid / has funds available).
        Zero     = balanced.
        """
        result = frappe.db.sql("""
            SELECT COALESCE(SUM(debit - credit), 0)
            FROM `tabGL Entry`
            WHERE party_type = 'Customer'
              AND party = %s
              AND is_cancelled = 0
        """, (customer,))
        return flt(result[0][0]) if result else 0.0

    # def on_cancel(self):
    #     if self.journal_entry:
    #         je = frappe.get_doc("Journal Entry", self.journal_entry)
    #         if je.docstatus == 1:
    #             je.cancel()
    #     if self.payment_entry:
    #         pe = frappe.get_doc("Payment Entry", self.payment_entry)
    #         if pe.docstatus == 1:
    #             pe.cancel()

    def on_cancel(self):
        for field in [
            "journal_entry",
            "sponsorship_reversal_je",
            "reallocation_je",
            "disbursement_journal_entry",
            "payment_entry"
        ]:
            doc_name = self.get(field)
            if not doc_name:
                continue
            if frappe.db.exists("Journal Entry", doc_name):
                je = frappe.get_doc("Journal Entry", doc_name)
                if je.docstatus == 1:
                    je.cancel()
            elif frappe.db.exists("Payment Entry", doc_name):
                pe = frappe.get_doc("Payment Entry", doc_name)
                if pe.docstatus == 1:
                    pe.cancel()

    
    def validate_hostel_items(self):
        if self.request_type != "Hostel":
            return
        if not self.items:
            return

        for row in self.items:
            if not row.sales_invoice:
                continue
            original = flt(row.original_amount)
            refundable = flt(row.refundable_amount)

            if refundable <= 0:
                frappe.throw(
                    f"Row {row.idx} — <b>{row.customer_name}</b>: "
                    f"Amount Due for Refund must be greater than zero."
                )

            if refundable > original:
                frappe.throw(
                    f"Row {row.idx} — <b>{row.customer_name}</b>: "
                    f"Amount Due for Refund (<b>{refundable:,.2f}</b>) cannot exceed "
                    f"Invoice Amount (<b>{original:,.2f}</b>)."
                )







@frappe.whitelist()
def get_sponsorship_allocations(doctype, txt, searchfield, start, page_len, filters):
    funder = filters.get("funder")
    current_doc = filters.get("current_doc")  # pass current doc name to exclude self

    # Get SA names already used in a closed Refund to Funder
    # used_sa_names = frappe.db.sql("""
    #     SELECT DISTINCT sponsorship_allocation
    #     FROM `tabStudent Refund`
    #     WHERE action_type = 'Refund to Funder'
    #     AND docstatus = 1
    #     AND sponsorship_allocation IS NOT NULL
    #     AND sponsorship_allocation != ''
    #     AND name != %s
    # """, (current_doc or "",), as_list=True)

    used_sa_names = frappe.db.sql("""
        SELECT DISTINCT sponsorship_allocation
        FROM `tabStudent Refund`
        WHERE action_type = 'Refund to Funder'
        AND workflow_state = 'Closed'
        AND docstatus = 1
        AND sponsorship_allocation IS NOT NULL
        AND sponsorship_allocation != ''
        AND name != %s
    """, (current_doc or "",), as_list=True)

    used_sa_list = [d[0] for d in used_sa_names] if used_sa_names else []

    exclusion_clause = ""
    values = [funder, f"%{txt}%", f"%{txt}%", f"%{txt}%"]

    if used_sa_list:
        placeholders = ", ".join(["%s"] * len(used_sa_list))
        exclusion_clause = f"AND sa.name NOT IN ({placeholders})"
        values.extend(used_sa_list)

    values.extend([page_len, start])

    return frappe.db.sql(f"""
        SELECT sa.name, sa.donor_name, sa.receipt_no, sa.amount
        FROM `tabSponsorship Allocation` sa
        WHERE sa.donor = %s
        AND sa.docstatus = 1
        AND (sa.name LIKE %s OR sa.donor_name LIKE %s OR sa.receipt_no LIKE %s)
        {exclusion_clause}
        ORDER BY sa.creation DESC
        LIMIT %s OFFSET %s
    """, values)





@frappe.whitelist()
def get_hostel_invoices(doctype, txt, searchfield, start, page_len, filters):
    customer = filters.get("customer") or ""
    session  = filters.get("custom_session") or ""
    semester = filters.get("custom_semester") or ""

    conditions = [
        "si.docstatus = 1",
        "si.outstanding_amount >= 0",
        "si.is_return = 0",
        "si.status IN ('Paid', 'Partly Paid')",
        "si.custom_desc LIKE %s"
    ]
    values = ["%Accommodation Fee%"]

    if customer:
        conditions.append("si.customer = %s")
        values.append(customer)

    if session:
        conditions.append("si.custom_session LIKE %s")
        values.append(f"%{session}%")

    if semester:
        conditions.append("si.custom_semester LIKE %s")
        values.append(f"%{semester}%")

    if txt:
        conditions.append("""
            (si.name LIKE %s
            OR si.customer_name LIKE %s
            OR si.custom_session LIKE %s
            OR si.custom_semester LIKE %s
            OR si.custom_level LIKE %s)
        """)
        values += [f"%{txt}%"] * 5

    where_clause = " AND ".join(conditions)

    return frappe.db.sql(f"""
        SELECT
            si.name,
            si.customer_name,
            si.custom_session,
            si.custom_semester,
            si.grand_total
        FROM `tabSales Invoice` si
        WHERE {where_clause}
        ORDER BY si.posting_date DESC
        LIMIT %s OFFSET %s
    """, values + [int(page_len), int(start)])


def before_update_after_submit(self, method=None):
    self.flags.ignore_mandatory = True
    # self._protect_narration_fields()
    self.capture_remark_trail()


def append_remark_to_trail(doc, remark_field, role_label):
    """
    Call this whenever a remark field is updated.
    Appends a timestamped entry to remarks_trail.
    """
    new_remark = doc.get(remark_field)
    if not new_remark:
        return

    user = frappe.session.user
    fullname = get_fullname(user)
    timestamp = now_datetime().strftime("%d %b %Y %H:%M")

    entry = f"[{timestamp}] {role_label} — {fullname}:\n{new_remark}\n{'-'*60}"

    existing = doc.remarks_trail or ""
    doc.remarks_trail = f"{existing}\n{entry}".strip()

#  def _protect_narration_fields(self):
#     """Ensure users can only update their own narration field after submit"""
#     role_field_map = {
#         'Student Finance Accountant': 'accountant_narration',
#         'Finance Officer':            'finance_officer_narration',
#         'Internal Auditor':           'internal_auditor_narration',
#         'Payable Accountant':         'payable_accountant_narration',
#         'DVC Finance':                'dvc_narration',
#         'Accounts Manager':           'accounts_manager_narration'
#     }

#     user_roles = frappe.get_roles(frappe.session.user)

#     # Accounts Manager can edit all — skip protection
#     if 'Accounts Manager' in user_roles:
#         return

#     # Get the saved (original) values from DB
#     saved = frappe.db.get_value(
#         "Student Refund",
#         self.name,
#         list(role_field_map.values()),
#         as_dict=True
#     )

#     for role, fieldname in role_field_map.items():
#         # If user does NOT have this role, revert field to saved value
#         if role not in user_roles:
#             saved_value = saved.get(fieldname) if saved else None
#             self.set(fieldname, saved_value)

















@frappe.whitelist()
def get_cheque_donations(doctype, txt, searchfield, start, page_len, filters):
    import json

    if isinstance(filters, str):
        filters = json.loads(filters)

    funder = filters.get("funder") or ""
    current_doc = filters.get("current_doc") or ""

    txt_clause = "AND (d.name LIKE %s OR d.custom_cheque_id LIKE %s)" if txt else ""
    values = [funder]

    if txt:
        values.extend([f"%{txt}%", f"%{txt}%"])

    values.extend([int(page_len), int(start)])

    return frappe.db.sql(f"""
        SELECT d.name, d.custom_cheque_id, d.amount, d.date
        FROM `tabDonation` d
        WHERE d.docstatus = 1
        AND d.donor = %s
        AND d.name != %s
        AND d.name NOT IN (
            SELECT DISTINCT sa.donation
            FROM `tabSponsorship Allocation` sa
            INNER JOIN `tabStudent Refund` sr ON sr.sponsorship_allocation = sa.name
            WHERE sa.donor = %s
            AND sa.docstatus = 1
            AND sr.action_type IN ('Refund to Funder', 'Receipt Cancellation')
            AND sr.docstatus != 2
            AND sa.donation IS NOT NULL
            AND sa.donation != ''
        )
        {txt_clause}
        ORDER BY d.date DESC
        LIMIT %s OFFSET %s
    """, [funder, current_doc, funder] + ([f"%{txt}%", f"%{txt}%"] if txt else []) + [int(page_len), int(start)])


# @frappe.whitelist()
# def get_cancellation_data(donation, funder):
#     """
#     Given a Donation, return:
#     - All Sponsorship Allocations linked to it
#     - All unique beneficiaries across those allocations
#     """
#     # Get all Sponsorship Allocations for this donation
#     allocations = frappe.db.sql("""
#         SELECT sa.name, sa.receipt_no, sa.amount, sa.total_allocated
#         FROM `tabSponsorship Allocation` sa
#         WHERE sa.donation = %s
#         AND sa.docstatus = 1
#     """, (donation,), as_dict=True)

#     if not allocations:
#         frappe.throw(
#             f"No Sponsorship Allocations found for this Donation.",
#             title="No Allocations Found"
#         )

#     # Get all beneficiaries across all those allocations
#     sa_names = [sa['name'] for sa in allocations]
#     placeholders = ", ".join(["%s"] * len(sa_names))

#     beneficiaries_raw = frappe.db.sql(f"""
#         SELECT DISTINCT
#             sab.student,
#             sab.student_name,
#             SUM(sab.amount) as amount
#         FROM `tabSponsorship Allocation Beneficiary` sab
#         WHERE sab.parent IN ({placeholders})
#         GROUP BY sab.student, sab.student_name
#         ORDER BY sab.student_name
#     """, sa_names, as_dict=True)

#     return {
#         "allocations": allocations,
#         "beneficiaries": beneficiaries_raw
#     }


@frappe.whitelist()
def get_cancellation_data(donation, funder):
    # allocations = frappe.db.sql("""
    #     SELECT sa.name, sa.receipt_no, sa.amount, sa.total_allocated
    #     FROM `tabSponsorship Allocation` sa
    #     WHERE sa.donation = %s
    #     AND sa.docstatus = 1
    # """, (donation,), as_dict=True)

    allocations = frappe.db.sql("""
        SELECT sa.name, sa.receipt_no, sa.amount, sa.total_allocated, sa.balance
        FROM `tabSponsorship Allocation` sa
        WHERE sa.donation = %s
        AND sa.docstatus = 1
    """, (donation,), as_dict=True)

    if not allocations:
        frappe.msgprint(
            "No Sponsorship Allocations found for this Donation.",
            title="No Allocations Found",
            indicator="blue"
        )
        return {
            "allocations": [],
            "beneficiaries": []
        }

    sa_names = [sa['name'] for sa in allocations]
    placeholders = ", ".join(["%s"] * len(sa_names))

    # GROUP BY student to prevent duplicates across multiple allocations
    # beneficiaries_raw = frappe.db.sql(f"""
    #     SELECT
    #         sab.student,
    #         sab.student_name,
    #         SUM(sab.amount) as amount
    #     FROM `tabSponsorship Allocation Beneficiary` sab
    #     WHERE sab.parent IN ({placeholders})
    #     GROUP BY sab.student, sab.student_name
    #     ORDER BY sab.student_name
    # """, sa_names, as_dict=True)

    beneficiaries_raw = frappe.db.sql(f"""
        SELECT
            sab.student,
            sab.student_name,
            sab.amount,
            sab.parent as sponsorship_allocation
        FROM `tabSponsorship Allocation Beneficiary` sab
        WHERE sab.parent IN ({placeholders})
        ORDER BY sab.student_name, sab.parent
    """, sa_names, as_dict=True)

    return {
        "allocations": allocations,
        "beneficiaries": beneficiaries_raw
    }
