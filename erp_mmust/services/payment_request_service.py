import frappe
from frappe import _
from frappe.utils import cint, date_diff, flt, fmt_money, getdate, today

from erpnext.accounts.doctype.payment_request.payment_request import make_payment_request


STUDENT_FEES_REDIRECT_URL = "https://mmust.rhocomtech.com/Student/MyFees"
PAYMENT_REQUEST_EMAIL_TEMPLATE = """
<p>Dear {{ doc.contact_person }},</p>

<p>Requesting payment for {{ doc.doctype }}, {{ doc.name }} for {{ doc.grand_total }}.</p>

<a href="{{ payment_url }}"> click here to pay </a>
"""


def normalize_invoice_names(invoice_names):
	if not invoice_names:
		return []

	if isinstance(invoice_names, str):
		try:
			invoice_names = frappe.parse_json(invoice_names)
		except Exception:
			invoice_names = [invoice_names]

	if not isinstance(invoice_names, (list, tuple, set)):
		invoice_names = [invoice_names]

	normalized = []
	seen = set()

	for invoice_name in invoice_names:
		if not invoice_name:
			continue

		name = str(invoice_name).strip()
		if not name or name in seen:
			continue

		seen.add(name)
		normalized.append(name)

	return normalized


def classify_payment_state(grand_total, outstanding_amount):
	grand_total = flt(grand_total)
	outstanding_amount = flt(outstanding_amount)
	paid_amount = flt(grand_total - outstanding_amount)

	if paid_amount <= 0:
		return "Unpaid"

	return "Partly Paid"


def prepare_invoice_rows(rows, current_date=None):
	current_date = getdate(current_date or today())

	for row in rows:
		row.posting_date = getdate(row.posting_date)
		row.due_date = getdate(row.due_date) if row.due_date else None
		row.grand_total = flt(row.grand_total)
		row.outstanding_amount = flt(row.outstanding_amount)
		row.paid_amount = flt(row.grand_total - row.outstanding_amount)
		row.invoice_age_days = date_diff(current_date, row.posting_date)
		row.payment_state = classify_payment_state(row.grand_total, row.outstanding_amount)

	return rows


def apply_invoice_filters(rows, filters=None):
	filters = frappe._dict(filters or {})
	payment_state = filters.get("payment_state")
	invoice_age_min_days = filters.get("invoice_age_min_days")
	invoice_age_max_days = filters.get("invoice_age_max_days")
	outstanding_amount_min = filters.get("outstanding_amount_min")
	outstanding_amount_max = filters.get("outstanding_amount_max")

	filtered_rows = []

	for row in rows:
		if payment_state and payment_state != "All" and row.payment_state != payment_state:
			continue

		if invoice_age_min_days not in (None, "") and row.invoice_age_days < cint(invoice_age_min_days):
			continue

		if invoice_age_max_days not in (None, "") and row.invoice_age_days > cint(invoice_age_max_days):
			continue

		if outstanding_amount_min not in (None, "") and row.outstanding_amount < flt(outstanding_amount_min):
			continue

		if outstanding_amount_max not in (None, "") and row.outstanding_amount > flt(outstanding_amount_max):
			continue

		filtered_rows.append(row)

	return filtered_rows


def get_payment_request_map(invoice_names, include_cancelled=True):
	invoice_names = normalize_invoice_names(invoice_names)

	if not invoice_names:
		return {}

	filters = {
		"reference_doctype": "Sales Invoice",
		"reference_name": ["in", invoice_names],
	}

	if not include_cancelled:
		filters["docstatus"] = ["!=", 2]

	payment_requests = frappe.get_all(
		"Payment Request",
		filters=filters,
		fields=["name", "reference_name", "status", "docstatus", "modified", "creation"],
		order_by="modified desc, creation desc",
	)

	request_map = {}
	for payment_request in payment_requests:
		if payment_request.reference_name not in request_map:
			request_map[payment_request.reference_name] = payment_request

	return request_map


def attach_latest_payment_request_status(rows):
	if not rows:
		return rows

	request_map = get_payment_request_map([row.sales_invoice for row in rows], include_cancelled=True)

	for row in rows:
		payment_request = request_map.get(row.sales_invoice)
		row.payment_request_name = payment_request.name if payment_request else None
		row.payment_request_status = None

		if payment_request:
			row.payment_request_status = payment_request.status
			if cint(payment_request.docstatus) == 2 and row.payment_request_status != "Cancelled":
				row.payment_request_status = "Cancelled"

	return rows


def get_student_invoice_rows(filters=None, invoice_names=None, include_payment_request_status=True):
	filters = frappe._dict(filters or {})
	invoice_names = normalize_invoice_names(invoice_names)

	conditions = [
		"si.docstatus = 1",
		"si.is_return = 0",
		"si.outstanding_amount > 0",
		"c.customer_group = 'Student'",
	]
	values = {}

	field_map = {
		"company": "si.company",
		"student": "si.customer",
		"faculty": "c.custom_faculty",
		"department": "c.custom_department",
		"custom_program_of_study": "c.custom_program_of_study",
		"custom_level": "c.custom_level",
		"custom_campus": "c.custom_campus",
		"custom_student_type": "c.custom_student_type",
	}

	for filter_name, field_name in field_map.items():
		if filters.get(filter_name):
			conditions.append(f"{field_name} = %({filter_name})s")
			values[filter_name] = filters.get(filter_name)

	if filters.get("student_name"):
		conditions.append("c.customer_name LIKE %(student_name)s")
		values["student_name"] = f"%{filters.get('student_name')}%"

	if invoice_names:
		conditions.append("si.name IN %(invoice_names)s")
		values["invoice_names"] = tuple(invoice_names)

	rows = frappe.db.sql(
		f"""
		SELECT
			si.name AS sales_invoice,
			si.customer AS student,
			c.customer_name AS student_name,
			si.company,
			si.posting_date,
			si.due_date,
			si.grand_total,
			si.outstanding_amount,
			c.custom_email AS email_id
		FROM `tabSales Invoice` si
		INNER JOIN `tabCustomer` c ON c.name = si.customer
		WHERE {" AND ".join(conditions)}
		ORDER BY si.posting_date ASC, si.name ASC
		""",
		values,
		as_dict=True,
	)

	rows = prepare_invoice_rows(rows)
	rows = apply_invoice_filters(rows, filters)

	if include_payment_request_status:
		rows = attach_latest_payment_request_status(rows)

	return rows


def build_bulk_result(total_requested):
	return {
		"total_requested": total_requested,
		"created": [],
		"skipped": [],
		"failed": [],
		"created_count": 0,
		"skipped_count": 0,
		"failed_count": 0,
	}


def append_bulk_result(result, bucket, payload):
	result[bucket].append(payload)
	result[f"{bucket}_count"] = len(result[bucket])


def build_payment_request_email(invoice, payment_request):
	grand_total = fmt_money(
		invoice.grand_total,
		currency=frappe.get_cached_value("Company", invoice.company, "default_currency"),
	)
	doc_context = frappe._dict(
		{
			"contact_person": getattr(payment_request, "contact_person", None) or invoice.student_name,
			"doctype": "Sales Invoice",
			"name": invoice.sales_invoice,
			"grand_total": grand_total,
		}
	)

	return frappe.render_template(
		PAYMENT_REQUEST_EMAIL_TEMPLATE,
		{
			"doc": doc_context,
			"payment_url": STUDENT_FEES_REDIRECT_URL,
			"payment_request": payment_request,
			"invoice": invoice,
		},
	)


def send_custom_payment_request_email(invoice, payment_request):
	message = build_payment_request_email(invoice, payment_request)

	frappe.sendmail(
		recipients=[invoice.email_id],
		subject=_("Payment Request for {0}").format(invoice.sales_invoice),
		message=message,
		reference_doctype="Payment Request",
		reference_name=payment_request.name,
		now=True,
	)


@frappe.whitelist()
def bulk_create_and_send(invoice_names):
	invoice_names = normalize_invoice_names(invoice_names)

	if not invoice_names:
		frappe.throw(_("Please select at least one invoice."))

	result = build_bulk_result(len(invoice_names))
	eligible_invoices = get_student_invoice_rows(
		invoice_names=invoice_names,
		include_payment_request_status=False,
	)
	eligible_by_name = {row.sales_invoice: row for row in eligible_invoices}
	existing_request_map = get_payment_request_map(invoice_names, include_cancelled=False)

	for invoice_name in invoice_names:
		invoice = eligible_by_name.get(invoice_name)

		if not invoice:
			append_bulk_result(
				result,
				"skipped",
				{
					"invoice_name": invoice_name,
					"reason": _("Invoice is not an eligible outstanding student invoice."),
				},
			)
			continue

		existing_request = existing_request_map.get(invoice_name)
		if existing_request:
			append_bulk_result(
				result,
				"skipped",
				{
					"invoice_name": invoice_name,
					"payment_request": existing_request.name,
					"status": existing_request.status,
					"reason": _("A non-cancelled Payment Request already exists for this invoice."),
				},
			)
			continue

		if not invoice.email_id:
			append_bulk_result(
				result,
				"failed",
				{
					"invoice_name": invoice_name,
					"reason": _("Student email is required before sending a Payment Request."),
				},
			)
			continue

		try:
			payment_request = make_payment_request(
				dt="Sales Invoice",
				dn=invoice.sales_invoice,
				recipient_id=invoice.email_id,
				party_type="Customer",
				party=invoice.student,
				party_name=invoice.student_name,
				company=invoice.company,
				submit_doc=1,
				mute_email=1,
				return_doc=1,
			)
			send_custom_payment_request_email(invoice, payment_request)

			append_bulk_result(
				result,
				"created",
				{
					"invoice_name": invoice_name,
					"payment_request": payment_request.name,
					"email_to": invoice.email_id,
				},
			)
		except Exception as exc:
			frappe.log_error(
				frappe.get_traceback(),
				f"Bulk Payment Request failed for Sales Invoice {invoice_name}",
			)
			append_bulk_result(
				result,
				"failed",
				{
					"invoice_name": invoice_name,
					"reason": str(exc).strip() or _("Payment Request creation failed."),
				},
			)

	return result
