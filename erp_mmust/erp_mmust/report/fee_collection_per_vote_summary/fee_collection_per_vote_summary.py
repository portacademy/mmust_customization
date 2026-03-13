import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)
    
    return columns, data, None, None, None

def get_columns():
    return [
        {
            "label": _("Account Number"),
            "fieldname": "account_number",
            "fieldtype": "Link",
            "options": "Account",
            "width": 200
        },
        {
            "label": _("Account Name"),
            "fieldname": "account_name",
            "fieldtype": "Data",
            "width": 300
        },
        {
            "label": _("Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 150
        }
    ]

def get_data(filters):
    parent_account = filters.get("parent_account")
    if not parent_account:
        return []

    accounts = frappe.db.get_descendants("Account", parent_account)
    accounts.append(parent_account)
    
    conditions = []
    values = {}

    if filters.get("from_date"):
        conditions.append("gle.posting_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions.append("gle.posting_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    condition_str = " AND ".join(conditions) if conditions else "1=1"

    data = []
    for account_name in accounts:
        query = f"""
            SELECT
                SUM(gle.debit) - SUM(gle.credit)
            FROM `tabGL Entry` gle
            WHERE gle.account = %(account)s AND {condition_str}
        """
        
        balance_values = values.copy()
        balance_values["account"] = account_name
        
        balance = frappe.db.sql(query, balance_values, as_list=True)
        
        balance = balance[0][0] if balance and balance[0][0] is not None else 0
        
        if balance != 0:
            account_info = frappe.db.get_value("Account", account_name, ["name", "account_name"], as_dict=True)
            data.append({
                "account_number": account_info.name,
                "account_name": account_info.account_name,
                "amount": balance
            })

    return data
