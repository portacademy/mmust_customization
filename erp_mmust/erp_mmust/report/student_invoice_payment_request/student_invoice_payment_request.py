from frappe import _

from erp_mmust.services.payment_request_service import get_student_invoice_rows


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_student_invoice_rows(filters=filters)

	return columns, data, None, None, None


def get_columns():
	return [
		{"label": _("Marked"), "fieldname": "marked", "fieldtype": "Data", "width": 80},
		{
			"label": _("Sales Invoice"),
			"fieldname": "sales_invoice",
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 150,
		},
		{"label": _("Student"), "fieldname": "student", "fieldtype": "Link", "options": "Customer", "width": 140},
		{"label": _("Student Name"), "fieldname": "student_name", "fieldtype": "Data", "width": 200},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 105},
		{"label": _("Due Date"), "fieldname": "due_date", "fieldtype": "Date", "width": 105},
		{"label": _("Age (Days)"), "fieldname": "invoice_age_days", "fieldtype": "Int", "width": 90},
		{"label": _("Grand Total"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
		{"label": _("Paid Amount"), "fieldname": "paid_amount", "fieldtype": "Currency", "width": 120},
		{
			"label": _("Outstanding Amount"),
			"fieldname": "outstanding_amount",
			"fieldtype": "Currency",
			"width": 140,
		},
		{"label": _("Payment State"), "fieldname": "payment_state", "fieldtype": "Data", "width": 110},
		{"label": _("Email"), "fieldname": "email_id", "fieldtype": "Data", "width": 220},
		{
			"label": _("Payment Request Status"),
			"fieldname": "payment_request_status",
			"fieldtype": "Data",
			"width": 150,
		},
	]
