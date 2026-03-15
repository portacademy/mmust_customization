from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from erp_mmust.services.payment_request_service import (
	apply_invoice_filters,
	attach_latest_payment_request_status,
	bulk_create_and_send,
	classify_payment_state,
	prepare_invoice_rows,
)


class TestPaymentRequestService(FrappeTestCase):
	def test_classify_payment_state(self):
		self.assertEqual(classify_payment_state(1000, 1000), "Unpaid")
		self.assertEqual(classify_payment_state(1000, 400), "Partly Paid")

	def test_prepare_invoice_rows_and_filters(self):
		rows = [
			frappe._dict(
				{
					"sales_invoice": "SINV-001",
					"posting_date": "2026-03-10",
					"due_date": "2026-03-20",
					"grand_total": 1000,
					"outstanding_amount": 1000,
				}
			),
			frappe._dict(
				{
					"sales_invoice": "SINV-002",
					"posting_date": "2026-03-01",
					"due_date": "2026-03-15",
					"grand_total": 1000,
					"outstanding_amount": 250,
				}
			),
		]

		prepare_invoice_rows(rows, current_date="2026-03-15")
		filtered = apply_invoice_filters(
			rows,
			{
				"payment_state": "Partly Paid",
				"invoice_age_min_days": 10,
				"outstanding_amount_max": 300,
			},
		)

		self.assertEqual([row.sales_invoice for row in filtered], ["SINV-002"])
		self.assertEqual(rows[0].payment_state, "Unpaid")
		self.assertEqual(rows[1].invoice_age_days, 14)
		self.assertEqual(rows[1].paid_amount, 750)

	@patch("erp_mmust.services.payment_request_service.get_payment_request_map")
	def test_attach_latest_payment_request_status(self, mock_get_payment_request_map):
		mock_get_payment_request_map.return_value = {
			"SINV-001": frappe._dict({"name": "PR-001", "status": "Requested", "docstatus": 1}),
			"SINV-002": frappe._dict({"name": "PR-002", "status": "Requested", "docstatus": 2}),
		}
		rows = [
			frappe._dict({"sales_invoice": "SINV-001"}),
			frappe._dict({"sales_invoice": "SINV-002"}),
			frappe._dict({"sales_invoice": "SINV-003"}),
		]

		attach_latest_payment_request_status(rows)

		self.assertEqual(rows[0].payment_request_status, "Requested")
		self.assertEqual(rows[1].payment_request_status, "Cancelled")
		self.assertIsNone(rows[2].payment_request_status)

	@patch("erp_mmust.services.payment_request_service.frappe.log_error")
	@patch("erp_mmust.services.payment_request_service.resend_payment_email")
	@patch("erp_mmust.services.payment_request_service.make_payment_request")
	@patch("erp_mmust.services.payment_request_service.get_payment_request_map")
	@patch("erp_mmust.services.payment_request_service.get_student_invoice_rows")
	def test_bulk_create_and_send_mixed_outcomes(
		self,
		mock_get_student_invoice_rows,
		mock_get_payment_request_map,
		mock_make_payment_request,
		mock_resend_payment_email,
		mock_log_error,
	):
		mock_get_student_invoice_rows.return_value = [
			frappe._dict(
				{
					"sales_invoice": "SINV-001",
					"student": "CUST-001",
					"student_name": "Student One",
					"company": "MMUST",
					"email_id": "student1@example.com",
				}
			),
			frappe._dict(
				{
					"sales_invoice": "SINV-002",
					"student": "CUST-002",
					"student_name": "Student Two",
					"company": "MMUST",
					"email_id": "",
				}
			),
			frappe._dict(
				{
					"sales_invoice": "SINV-003",
					"student": "CUST-003",
					"student_name": "Student Three",
					"company": "MMUST",
					"email_id": "student3@example.com",
				}
			),
		]
		mock_get_payment_request_map.return_value = {
			"SINV-004": frappe._dict({"name": "PR-EXISTING", "status": "Requested", "docstatus": 1})
		}

		def make_payment_request_side_effect(**kwargs):
			if kwargs["dn"] == "SINV-003":
				raise RuntimeError("SMTP failure")

			return frappe._dict({"name": "PR-NEW-001"})

		mock_make_payment_request.side_effect = make_payment_request_side_effect

		result = bulk_create_and_send(["SINV-001", "SINV-002", "SINV-003", "SINV-004", "SINV-999"])

		self.assertEqual(result["created_count"], 1)
		self.assertEqual(result["skipped_count"], 2)
		self.assertEqual(result["failed_count"], 2)
		self.assertEqual(result["created"][0]["payment_request"], "PR-NEW-001")
		self.assertTrue(any(row["invoice_name"] == "SINV-999" for row in result["skipped"]))
		self.assertTrue(any(row["invoice_name"] == "SINV-004" for row in result["skipped"]))
		self.assertTrue(any(row["invoice_name"] == "SINV-002" for row in result["failed"]))
		self.assertTrue(any(row["invoice_name"] == "SINV-003" for row in result["failed"]))
		mock_resend_payment_email.assert_called_once_with("PR-NEW-001")
		mock_log_error.assert_called_once()
