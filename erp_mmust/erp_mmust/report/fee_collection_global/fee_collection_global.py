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

    # 1. Get all descendant accounts (including parent)
    descendants = frappe.db.get_descendants("Account", parent_account)
    descendants.append(parent_account)

    # 2. Filter these descendants by name/number
    account_filter_values = {"accounts": tuple(descendants)}
    account_conditions = ["name IN %(accounts)s"]
    if filters.get("account_name"):
        account_conditions.append("account_name LIKE %(account_name)s")
        account_filter_values["account_name"] = f"%{filters.get('account_name')}%"
    if filters.get("account_number"):
        account_conditions.append("name LIKE %(account_number)s")
        account_filter_values["account_number"] = f"%{filters.get('account_number')}%"

    accounts_to_process = frappe.db.sql(f"""
        SELECT name, account_name
        FROM `tabAccount`
        WHERE {" AND ".join(account_conditions)}
    """, account_filter_values, as_dict=True)

    # 3. Get balances for these accounts for the date range
    data = []
    date_filters = ""
    date_values = {}
    if filters.get("from_date"):
        date_filters += " AND posting_date >= %(from_date)s"
        date_values["from_date"] = filters.get("from_date")
    if filters.get("to_date"):
        date_filters += " AND posting_date <= %(to_date)s"
        date_values["to_date"] = filters.get("to_date")

    for acc in accounts_to_process:
        balance_values = {"account": acc.name}
        balance_values.update(date_values)
        
        balance = frappe.db.sql(f"""
            SELECT SUM(credit) - SUM(debit)
            FROM `tabGL Entry`
            WHERE account = %(account)s {date_filters}
        """, balance_values, as_list=True)
        
        balance = balance[0][0] if balance and balance[0][0] is not None else 0
        
        if balance != 0:
            data.append({
                "account_number": acc.name,
                "account_name": acc.account_name,
                "amount": balance
            })
            
    return data
