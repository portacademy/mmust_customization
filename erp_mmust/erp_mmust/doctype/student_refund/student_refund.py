# import frappe
# from frappe.utils import flt
# from frappe.model.document import Document


# class StudentRefund(Document):

#     def validate(self):
#         self.calculate_total()
#         self.validate_beneficiaries()
#         self.calculate_amount_refunded_to_donor()

#     def calculate_total(self):
#         if self.request_type == "Hostel":
#             self.total_amount = sum(flt(row.refundable_amount) for row in (self.items or []))

#     def validate_beneficiaries(self):
#         if self.request_type not in ("HELB", "CDF", "Scholarship"):
#             return
#         if not self.beneficiaries:
#             return

#         total_to_refund = 0

#         for row in self.beneficiaries:
#             original  = flt(row.original_allocated_amount)
#             to_refund = flt(row.amount_to_be_refunded)

#             if to_refund <= 0:
#                 continue

#             # ── Get current GL balance for this student ────────────────────
#             gl_balance = self._get_student_gl_balance(row.student)

#             # ── Rule 1: Student must have a credit balance (negative/zero) ─
#             # Positive balance = student owes money = cannot refund
#             if gl_balance > 0:
#                 frappe.throw(
#                     f"Row {row.idx} — <b>{row.student_name}</b>: "
#                     f"This student has an outstanding debit balance of "
#                     f"<b>₦{gl_balance:,.2f}</b> (they owe money). "
#                     f"A refund cannot be processed for students with an outstanding balance."
#                 )

#             # Credit balance = absolute value of the negative GL balance
#             credit_balance = abs(gl_balance) if gl_balance < 0 else 0

#             # ── Rule 2: Cannot exceed original allocated amount ────────────
#             if to_refund > original:
#                 frappe.throw(
#                     f"Row {row.idx} — <b>{row.student_name}</b>: "
#                     f"Amount to be Refunded (<b>₦{to_refund:,.2f}</b>) cannot exceed "
#                     f"Original Allocated Amount (<b>₦{original:,.2f}</b>)."
#                 )

#             # ── Rule 3: Cannot exceed student's credit balance in ledger ──
#             if to_refund > credit_balance:
#                 frappe.throw(
#                     f"Row {row.idx} — <b>{row.student_name}</b>: "
#                     f"Amount to be Refunded (<b>₦{to_refund:,.2f}</b>) cannot exceed "
#                     f"the student's available credit balance in the ledger "
#                     f"(<b>₦{credit_balance:,.2f}</b>)."
#                 )

#             total_to_refund += to_refund

#         # ── Rule 4: Sum cannot exceed total allocated in sponsorship ──────
#         total_allocated = flt(self.total_allocated_in_donation)
#         if total_to_refund > total_allocated + 0.01:
#             frappe.throw(
#                 f"Sum of Amounts to be Refunded (<b>₦{total_to_refund:,.2f}</b>) "
#                 f"cannot exceed Total Allocated in Sponsorship Allocation "
#                 f"(<b>₦{total_allocated:,.2f}</b>)."
#             )

#     def _get_student_gl_balance(self, customer):
#         """
#         Returns the net GL balance for a student (Customer).
#         Positive = debit balance (student owes money).
#         Negative = credit balance (student has overpaid / has funds available).
#         Zero     = balanced.
#         """
#         result = frappe.db.sql("""
#             SELECT COALESCE(SUM(debit - credit), 0)
#             FROM `tabGL Entry`
#             WHERE party_type = 'Customer'
#               AND party = %s
#               AND is_cancelled = 0
#         """, (customer,))
#         return flt(result[0][0]) if result else 0.0

#     def calculate_amount_refunded_to_donor(self):
#         if self.request_type not in ("HELB", "CDF", "Scholarship"):
#             return
#         total_to_refund = sum(
#             flt(row.amount_to_be_refunded) for row in (self.beneficiaries or [])
#         )
#         self.amount_refunded_to_donor = total_to_refund
#         self.total_amount = total_to_refund

#     def on_cancel(self):
#         if self.journal_entry:
#             je = frappe.get_doc("Journal Entry", self.journal_entry)
#             if je.docstatus == 1:
#                 je.cancel()
#         if self.payment_entry:
#             pe = frappe.get_doc("Payment Entry", self.payment_entry)
#             if pe.docstatus == 1:
#                 pe.cancel()







import frappe
from frappe.utils import flt
from frappe.model.document import Document


class StudentRefund(Document):

    def validate(self):
        self.calculate_total()
        
        if self.action_type == "Refund to Funder":
            self.validate_beneficiaries()
            self.calculate_amount_refunded_to_donor()
        elif self.action_type == "Reallocate to Student":
            self.validate_reallocations()
            self.calculate_reallocation_total()

    def calculate_total(self):
        if self.request_type == "Hostel":
            self.total_amount = sum(flt(row.refundable_amount) for row in (self.items or []))

    def validate_mandatory_fields(self):

        if self.request_type in ('HELB', 'CDF', 'Scholarship'):
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

    def on_cancel(self):
        if self.journal_entry:
            je = frappe.get_doc("Journal Entry", self.journal_entry)
            if je.docstatus == 1:
                je.cancel()
        if self.payment_entry:
            pe = frappe.get_doc("Payment Entry", self.payment_entry)
            if pe.docstatus == 1:
                pe.cancel()





# @frappe.whitelist()
# def get_sponsorship_allocations(doctype, txt, searchfield, start, page_len, filters):
#     import json
#     if isinstance(filters, str):
#         filters = json.loads(filters)
    
#     funder = filters.get('funder')
    
#     return frappe.db.sql("""
#         SELECT name, date, total_allocated
#         FROM `tabSponsorship Allocation`
#         WHERE donor = %(funder)s
#         AND docstatus = 1
#         AND (name LIKE %(txt)s OR date LIKE %(txt)s)
#         ORDER BY creation DESC
#         LIMIT %(page_len)s OFFSET %(start)s
#     """, {
#         'funder': funder,
#         'txt': f'%{txt}%',
#         'page_len': int(page_len),
#         'start': int(start)
#     })


# @frappe.whitelist()
# def get_sponsorship_allocations(doctype, txt, searchfield, start, page_len, filters):
#     funder = filters.get("funder")

#     # Get donations already used in a Refund to Funder Student Refund
#     used_donations = frappe.db.sql("""
#         SELECT DISTINCT sa.donation
#         FROM `tabSponsorship Allocation` sa
#         INNER JOIN `tabStudent Refund` sr ON sr.sponsorship_allocation = sa.name
#         WHERE sr.action_type = 'Refund to Funder'
#         AND sr.docstatus = 1
#         AND sa.donation IS NOT NULL
#         AND sa.donation != ''
#     """, as_list=True)

#     used_donation_list = [d[0] for d in used_donations] if used_donations else []

#     # Build exclusion clause
#     exclusion_clause = ""
#     if used_donation_list:
#         placeholders = ", ".join(["%s"] * len(used_donation_list))
#         exclusion_clause = f"AND sa.donation NOT IN ({placeholders})"

#     values = [funder, f"%{txt}%"]
#     if used_donation_list:
#         values.extend(used_donation_list)

#     return frappe.db.sql(f"""
#         SELECT sa.name, sa.donor_name, sa.receipt_no, sa.amount
#         FROM `tabSponsorship Allocation` sa
#         WHERE sa.donor = %s
#         AND sa.docstatus = 1
#         AND (sa.name LIKE %s OR sa.donor_name LIKE %s OR sa.receipt_no LIKE %s)
#         {exclusion_clause}
#         ORDER BY sa.creation DESC
#         LIMIT %s OFFSET %s
#     """, values + [f"%{txt}%", f"%{txt}%", page_len, start])


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

