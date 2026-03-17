import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    
    # Pass filters to get_summary for dynamic labeling
    summary = get_summary(data, filters)
    chart = get_chart(data)
    
    return columns, data, None, chart, summary

def get_columns():
    return [
        {"label": _("ID"), "fieldname": "name", "fieldtype": "Link", "options": "Student Refund", "width": 140},
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Request Type"), "fieldname": "request_type", "fieldtype": "Data", "width": 110},
        {"label": _("Action Type"), "fieldname": "action_type", "fieldtype": "Data", "width": 140},
        {"label": _("Funder"), "fieldname": "funder", "fieldtype": "Link", "options": "Donor", "width": 120},
        {"label": _("Academic Year"), "fieldname": "academic_year", "fieldtype": "Link", "options": "Academic Year", "width": 120},
        {"label": _("Status"), "fieldname": "workflow_state", "fieldtype": "Data", "width": 130},
        {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 120}
    ]

def get_data(filters):
    conditions = {}
    if filters.get("request_type"):
        conditions["request_type"] = filters.get("request_type")
    if filters.get("action_type"):
        conditions["action_type"] = filters.get("action_type")
    if filters.get("academic_year"):
        conditions["academic_year"] = filters.get("academic_year")
    if filters.get("workflow_state"):
        conditions["workflow_state"] = filters.get("workflow_state")
    if filters.get("from_date") and filters.get("to_date"):
        conditions["posting_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]

    return frappe.get_all(
        "Student Refund",
        fields=["name", "posting_date", "request_type", "action_type", "funder", "academic_year", "workflow_state", "total_amount"],
        filters=conditions,
        order_by="posting_date desc"
    )

def get_summary(data, filters):
    if not data:
        return []

    total_amount = sum(d.get("total_amount") or 0 for d in data)
    
    # Logic for the dynamic Status Card
    status_filter = filters.get("workflow_state")
    if status_filter:
        label = _("Total {0}").format(status_filter)
        val = len([d for d in data if d.get("workflow_state") == status_filter])
    else:
        label = _("Open Requests")
        # Define 'Open' as anything not in a terminal state
        terminal_states = ["Approved", "Completed", "Paid", "Rejected", "Cancelled"]
        val = len([d for d in data if d.get("workflow_state") not in terminal_states])

    return [
        {"value": len(data), "indicator": "Blue", "label": _("Total Requests"), "datatype": "Int"},
        {"value": total_amount, "indicator": "Green", "label": _("Total Amount"), "datatype": "Currency"},
        {"value": val, "indicator": "Orange", "label": label, "datatype": "Int"}
    ]

def get_chart(data):
    if not data:
        return None

    # Aggregate by Request Type
    type_counts = {}
    for d in data:
        t = d.get("request_type") or _("Other")
        type_counts[t] = type_counts.get(t, 0) + (d.get("total_amount") or 0)

    return {
        "data": {
            "labels": list(type_counts.keys()),
            "datasets": [{"name": _("Refund Amount"), "values": list(type_counts.values())}]
        },
        "type": "bar",
        "colors": ["#11a683"]
    }