import frappe
from erp_mmust.services.accounting_service import get_company
import random


def create_donor_gl_account(doc, method=None):
    company = get_company()

    parent_account = frappe.db.get_single_value("MMUST Donor Settings", "default_sponsor_parent_account")
    if not parent_account:
        frappe.throw(
            "No Default Sponsor Parent Account set in <b>MMUST Donor Settings</b>. "
            "Please set it before creating donors."
        )

    account = frappe.new_doc("Account")
    account.account_name = f"{doc.donor_name} Sponsor"
    account.account_number =  str(random.randint(10000000000, 99999999999))
    account.parent_account = parent_account
    account.company = company
    account.is_group = 0
    account.insert(ignore_permissions=True)

    frappe.db.set_value("Donor", doc.name, "custom_sponsor_gl_account", account.name)

    frappe.msgprint(
        f"✅ Sponsor GL Account <b>{account.name}</b> created and linked to donor.",
        indicator="green",
        alert=True
    )