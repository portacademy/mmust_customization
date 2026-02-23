# Copyright (c) 2026, Timothy Ajani and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate
import csv
from io import StringIO


class SponsorshipAllocation(Document):

	def before_save(self):
		if not self.receipt_no:
			self.receipt_no = self.name


	def validate(self):
		self.validate_donation_amount()
		self.calculate_totals()
		self.validate_donation_balance()
		# self.validate_allocation_total()

	def validate_donation_balance(self):
		if not self.donation:
			return

		donation_amount = frappe.db.get_value("Donation", self.donation, "amount") or 0

		# Sum all submitted/saved SAs using this donation, excluding current doc
		total_used = frappe.db.sql("""
			SELECT COALESCE(SUM(total_allocated), 0)
			FROM `tabSponsorship Allocation`
			WHERE donation = %s
			AND docstatus != 2
			AND name != %s
		""", (self.donation, self.name or ""))[0][0] or 0

		available = frappe.utils.flt(donation_amount) - frappe.utils.flt(total_used)

		if frappe.utils.flt(self.total_allocated) > available:
			frappe.throw(
				f"Total Allocated (<b>₦{frappe.utils.flt(self.total_allocated):,.2f}</b>) "
				f"exceeds available balance on Donation <b>{self.donation}</b>.<br>"
				f"Donation Amount: <b>₦{frappe.utils.flt(donation_amount):,.2f}</b><br>"
				f"Already Allocated: <b>₦{frappe.utils.flt(total_used):,.2f}</b><br>"
				f"Available: <b>₦{available:,.2f}</b>",
				title="Insufficient Donation Balance"
			)
	
	def validate_donation_amount(self):
		"""Validate that total does not exceed donation amount if donation is linked"""
		if self.donation and self.amount:
			if self.total > self.amount:
				frappe.throw(
					f"Total allocation ({self.total}) cannot exceed donation amount ({self.amount})"
				)
	
	def calculate_totals(self):
		"""Calculate total allocated and balance from beneficiaries"""
		total_allocated = 0
		if self.beneficiaries:
			total_allocated = sum(flt(d.amount) for d in self.beneficiaries)
		
		self.total_allocated = total_allocated
		self.balance = self.total - total_allocated
	
	# def validate_allocation_total(self):
	# 	"""Validate that total allocated matches total before submit"""
	# 	if self.docstatus == 1:  # On submit
	# 		if abs(self.total_allocated - self.total) > 0.01:  # Allow for rounding
	# 			frappe.throw(
	# 				f"Total allocated ({self.total_allocated}) must equal total available ({self.total}). "
	# 				f"Current balance: {self.balance}"
	# 			)
	
	def on_submit(self):
		"""Create journal entry on submit"""
		self.create_journal_entry()
	
	def on_cancel(self):
		"""Cancel related journal entry on cancel"""
		self.cancel_journal_entry()
	
	def create_journal_entry(self):
		"""
		Create Journal Entry:
		- Debit: Account Debited with Donor as party (Total Allocated)
		- Credits: Student Debtors account with each Customer as party (Amount per beneficiary)
		"""
		if not self.beneficiaries:
			frappe.throw("Cannot create journal entry without beneficiaries")
		
		# Validate total allocated equals sum of beneficiary amounts
		total_beneficiary_amount = sum(flt(d.amount) for d in self.beneficiaries)
		if abs(total_beneficiary_amount - self.total_allocated) > 0.01:
			frappe.throw(
				f"Sum of beneficiary amounts ({total_beneficiary_amount}) must equal total allocated ({self.total_allocated})"
			)
		
		# Get Student Debtors account
		student_debtors_account = frappe.db.get_value(
			"Account",
			{
				"account_name": "Student Debtors",
				"company": self.company
			},
			"name"
		)
		
		if not student_debtors_account:
			frappe.throw("Student Debtors account not found. Please create it first.")
		
		# Create Journal Entry
		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Journal Entry"
		je.posting_date = self.date or nowdate()
		je.company = self.company
		je.user_remark = f"Sponsorship allocation for {self.donor_name} - {self.name}"
		
		# Debit Entry - Debit the account with Donor as party
		je.append("accounts", {
			"account": self.account_debited,
			"debit_in_account_currency": self.total_allocated,
			"credit_in_account_currency": 0,
			"party_type": "Donor",
			"party": self.donor,
			"user_remark": f"Sponsorship from {self.donor_name} - {self.name}"
		})
		
		# Credit Entries - Credit Student Debtors account with each Customer as party
		for beneficiary in self.beneficiaries:
			if not beneficiary.student:
				frappe.throw(f"Student is required in row {beneficiary.idx}")
			
			if flt(beneficiary.amount) <= 0:
				frappe.throw(f"Amount must be greater than 0 in row {beneficiary.idx}")
			
			je.append("accounts", {
				"account": student_debtors_account,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": flt(beneficiary.amount),
				"party_type": "Customer",
				"party": beneficiary.student,
				"user_remark": f"Sponsorship allocation to {beneficiary.student_name} - {self.name}"
			})
		
		# Save and submit the journal entry
		je.insert()
		je.submit()
		
		# Link the journal entry to this document
		self.db_set("journal_entry", je.name)
		
		frappe.msgprint(
			f"Journal Entry {je.name} created successfully",
			alert=True,
			indicator="green"
		)

	def cancel_journal_entry(self):
		"""Cancel the linked journal entry when this document is cancelled"""
		if self.journal_entry:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			if je.docstatus == 1:
				je.cancel()
				frappe.msgprint(
					f"Journal Entry {self.journal_entry} cancelled",
					alert=True,
					indicator="orange"
				)


def get_party_account(party_type, party, company):
	"""Get the party account (Receivable/Payable)"""
	from erpnext.accounts.party import get_party_account as get_account
	return get_account(party_type, party, company)


@frappe.whitelist()
def get_students_by_filter(programme=None, level=None):
	"""Get students (customers) filtered by programme and/or level"""
	filters = {
		"customer_group": "Student"
	}

	if programme:
		filters["custom_program_of_study"] = programme

	if level:
		filters["custom_level"] = level

	students = frappe.get_all(
		"Customer",
		filters=filters,
		fields=["name", "customer_name", "custom_program_of_study", "custom_level"],
	)

	return students


@frappe.whitelist()
def load_students_from_csv(csv_file_url, total_amount):
	"""Load students from CSV file and distribute amount equally"""
	try:
		# Get the file content
		file_doc = frappe.get_doc("File", {"file_url": csv_file_url})
		content = file_doc.get_content()
		
		# Parse CSV
		csv_data = StringIO(content.decode('utf-8') if isinstance(content, bytes) else content)
		reader = csv.DictReader(csv_data)
		
		students = []
		customer_ids = []
		
		for row in reader:
			customer_id = row.get('customer_id', '').strip()
			if customer_id:
				customer_ids.append(customer_id)
		
		if not customer_ids:
			frappe.throw("No valid customer IDs found in CSV file")
		
		# Validate customers exist and are students
		for customer_id in customer_ids:
			if frappe.db.exists("Customer", customer_id):
				customer = frappe.get_doc("Customer", customer_id)
				if customer.customer_group == "Student":
					students.append({
						"customer_id": customer.name,
						"customer_name": customer.customer_name
					})
				else:
					frappe.msgprint(f"Warning: {customer_id} is not in Student customer group. Skipped.")
			else:
				frappe.msgprint(f"Warning: Customer {customer_id} not found. Skipped.")
		
		if not students:
			frappe.throw("No valid student customers found from CSV")
		
		# Distribute amount equally
		total_amount = float(total_amount)
		amount_per_student = total_amount / len(students)
		
		beneficiaries = []
		for student in students:
			beneficiaries.append({
				"student": student["customer_id"],
				"student_name": student["customer_name"],
				"amount": amount_per_student,
				"description": f"Equal allocation from total {total_amount}"
			})
		
		return beneficiaries
	
	except Exception as e:
		frappe.throw(f"Error processing CSV file: {str(e)}")


@frappe.whitelist()
def distribute_amount_equally(students, total_amount):
	"""Distribute total amount equally among students"""
	import json
	
	if isinstance(students, str):
		students = json.loads(students)
	
	total_amount = float(total_amount)
	
	if not students:
		frappe.throw("No students selected")
	
	amount_per_student = total_amount / len(students)
	
	beneficiaries = []
	for student in students:
		beneficiaries.append({
			"student": student["name"],
			"student_name": student.get("customer_name") or student.get("name"),
			"amount": amount_per_student,
			"description": f"Equal allocation from total {total_amount}"
		})
	
	return beneficiaries








# @frappe.whitelist()
# @frappe.validate_and_sanitize_search_inputs
# def get_donor_donations(doctype, txt, searchfield, start, page_len, filters):
#     donor = filters.get('donor')
#     return frappe.db.sql("""
#         SELECT name, amount, date 
#         FROM `tabDonation`
#         WHERE donor = %(donor)s 
#         AND docstatus = 1
#         AND (name LIKE %(txt)s OR amount LIKE %(txt)s)
#         ORDER BY date DESC, creation DESC
#         LIMIT %(page_len)s OFFSET %(start)s
#     """, {
#         'donor': donor,
#         'txt': f'%{txt}%',
#         'page_len': page_len,
#         'start': start
#     })


@frappe.whitelist()
def get_donor_donations(doctype, txt, searchfield, start, page_len, filters):
    import json
    if isinstance(filters, str):
        filters = json.loads(filters)

    donor = filters.get("donor")

    return frappe.db.sql("""
        SELECT 
            d.name,
            d.amount,
            d.date,
            (d.amount - COALESCE(used.total_used, 0)) AS available
        FROM `tabDonation` d
        LEFT JOIN (
            SELECT 
                donation,
                SUM(total_allocated) AS total_used
            FROM `tabSponsorship Allocation`
            WHERE docstatus != 2
            AND donation IS NOT NULL
            AND donation != ''
            GROUP BY donation
        ) used ON used.donation = d.name
        WHERE d.donor = %s
        AND d.docstatus = 1
        AND (d.amount - COALESCE(used.total_used, 0)) > 0
        AND (d.name LIKE %s OR d.amount LIKE %s)
        ORDER BY d.date DESC
        LIMIT %s OFFSET %s
    """, (donor, f"%{txt}%", f"%{txt}%", int(page_len), int(start)))

	
@frappe.whitelist()
def get_beneficiary_for_print(docname, student):
    doc = frappe.get_doc("Sponsorship Allocation", docname)
    for row in doc.beneficiaries:
        if row.student == student:
            return row.as_dict()
    frappe.throw(f"Beneficiary {student} not found in {docname}")


@frappe.whitelist()
def get_donation_available_balance(donation, exclude_doc=""):
    from frappe.utils import flt

    donation_amount = flt(frappe.db.get_value("Donation", donation, "amount") or 0)

    total_used = frappe.db.sql("""
        SELECT COALESCE(SUM(total_allocated), 0)
        FROM `tabSponsorship Allocation`
        WHERE donation = %s
        AND docstatus != 2
        AND name != %s
    """, (donation, exclude_doc))[0][0] or 0

    return flt(donation_amount) - flt(total_used)