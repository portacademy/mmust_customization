import frappe
from erp_mmust.services.accounting_service import get_company
import random


# def create_donor_gl_account(doc, method=None):
#     company = get_company()

#     parent_account = frappe.db.get_single_value("MMUST Donor Settings", "default_sponsor_parent_account")
#     if not parent_account:
#         frappe.throw(
#             "No Default Sponsor Parent Account set in <b>MMUST Donor Settings</b>. "
#             "Please set it before creating donors."
#         )

#     account = frappe.new_doc("Account")
#     account.account_name = f"{doc.donor_name} Sponsor"
#     account.account_number =  str(random.randint(10000000000, 99999999999))
#     account.parent_account = parent_account
#     account.company = company
#     account.is_group = 0
#     account.insert(ignore_permissions=True)

#     frappe.db.set_value("Donor", doc.name, "custom_sponsor_gl_account", account.name)

#     frappe.msgprint(
#         f"✅ Sponsor GL Account <b>{account.name}</b> created and linked to donor.",
#         indicator="green",
#         alert=True
#     )


import frappe
from erp_mmust.services.accounting_service import get_company


def create_donor_gl_account(doc, method=None):
    company = get_company()

    parent_account = frappe.db.get_single_value("MMUST Donor Settings", "default_sponsor_parent_account")
    if not parent_account:
        frappe.throw(
            "No Default Sponsor Parent Account set in <b>MMUST Donor Settings</b>. "
            "Please set it before creating donors."
        )

    # Get parent account number e.g. "17-00-000"
    parent_account_number = frappe.db.get_value("Account", parent_account, "account_number")
    if not parent_account_number:
        frappe.throw(
            f"Parent account <b>{parent_account}</b> has no account number set. "
            "Please set it before creating donors."
        )

    # Strip last segment: "17-00-000" → "17-00"
    parts = parent_account_number.split("-")
    prefix = "-".join(parts[:-1])  # "17-00"

    # Find all children matching "17-00-NNN" pattern (3 digit suffix only)
    existing_numbers = frappe.db.sql("""
        SELECT account_number
        FROM `tabAccount`
        WHERE parent_account = %s
        AND account_number IS NOT NULL
        AND account_number != ''
        AND account_number REGEXP %s
    """, (parent_account, f"^{prefix}-[0-9]{{3}}$"), as_list=True)

    # Find max suffix
    max_suffix = 0
    for row in existing_numbers:
        try:
            suffix = int(row[0].split("-")[-1])
            if suffix > max_suffix:
                max_suffix = suffix
        except (ValueError, IndexError):
            continue

    next_suffix = max_suffix + 1
    next_account_number = f"{prefix}-{str(next_suffix).zfill(3)}"

    account = frappe.new_doc("Account")
    account.account_name   = f"{doc.donor_name} Sponsor"
    account.account_number = next_account_number
    account.parent_account = parent_account
    account.company        = company
    account.is_group       = 0
    account.insert(ignore_permissions=True)

    frappe.db.set_value("Donor", doc.name, "custom_sponsor_gl_account", account.name)

    frappe.msgprint(
        f"✅ Sponsor GL Account <b>{account.name}</b> created and linked to donor.",
        indicator="green",
        alert=True
    )