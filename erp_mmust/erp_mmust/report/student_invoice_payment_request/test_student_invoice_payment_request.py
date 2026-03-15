from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase

from erp_mmust.erp_mmust.report.student_invoice_payment_request.student_invoice_payment_request import execute


class TestStudentInvoicePaymentRequestReport(FrappeTestCase):
	@patch("erp_mmust.erp_mmust.report.student_invoice_payment_request.student_invoice_payment_request.get_student_invoice_rows")
	def test_execute_returns_report_data(self, mock_get_student_invoice_rows):
		mock_get_student_invoice_rows.return_value = [
			{
				"sales_invoice": "SINV-001",
				"student": "CUST-001",
				"student_name": "Student One",
				"payment_request_status": "Requested",
			}
		]

		columns, data, message, chart, summary = execute({"payment_state": "Unpaid"})

		self.assertTrue(any(column["fieldname"] == "sales_invoice" for column in columns))
		self.assertEqual(data[0]["sales_invoice"], "SINV-001")
		self.assertIsNone(message)
		self.assertIsNone(chart)
		self.assertIsNone(summary)
