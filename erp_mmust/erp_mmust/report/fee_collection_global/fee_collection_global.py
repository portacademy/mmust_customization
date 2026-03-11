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
    parent_account = filters.get("account")
    if not parent_account:
        return []

    accounts = frappe.db.get_descendants("Account", parent_account, ignore_permissions=True)
    accounts.append(parent_account)
    
    conditions = "1=1"
    if filters.get("from_date"):
        conditions += f" AND gle.posting_date >= '{filters['from_date']}'"
    if filters.get("to_date"):
        conditions += f" AND gle.posting_date <= '{filters['to_date']}'"
    if filters.get("account_name"):
        conditions += f" AND acc.account_name LIKE '%{filters['account_name']}%'"
    if filters.get("account_number"):
        conditions += f" AND acc.name LIKE '%{filters['account_number']}%'"

    data = []
    for account_name in accounts:
        balance = frappe.db.sql(f"""
            SELECT
                SUM(gle.debit) - SUM(gle.credit)
            FROM `tabGL Entry` gle
            JOIN `tabAccount` acc ON gle.account = acc.name
            WHERE gle.account = '{account_name}' AND {conditions}
        """, as_list=True)
        
        balance = balance[0][0] if balance and balance[0][0] is not None else 0
        
        if balance != 0:
            account_info = frappe.db.get_value("Account", account_name, ["name", "account_name"], as_dict=True)
            data.append({
                "account_number": account_info.name,
                "account_name": account_info.account_name,
                "amount": balance
            })

    return data
