# def get_data(data=None):
#     data = data or {}
    
#     transactions = data.get("transactions", [])
#     transactions.append({
#         "label": "Sponsorship",
#         "items": ["Sponsorship Allocation"]
#     })
#     data["transactions"] = transactions
    
#     if "fieldname" not in data:
#         data["fieldname"] = "donation"
        
#     return data


# def get_data(data=None):
#     data = data or {}
    
#     # Remove Payment Entry from existing transactions
#     transactions = data.get("transactions", [])
#     transactions = [
#         section for section in transactions
#         if "Payment Entry" not in section.get("items", [])
#     ]
    
#     # Add Sponsorship Allocation
#     transactions.append({
#         "label": "Sponsorship",
#         "items": ["Sponsorship Allocation"]
#     })
#     data["transactions"] = transactions

#     # Also remove from internal links if present
#     data["internal_links"] = {
#         k: v for k, v in data.get("internal_links", {}).items()
#         if k != "Payment Entry"
#     }

#     if "fieldname" not in data:
#         data["fieldname"] = "donation"
        
#     return data



def get_data(data=None):
    data = data or {}

    transactions = data.get("transactions", [])

    # Filter out Payment Entry and Journal Entry from all sections
    filtered = []
    for section in transactions:
        items = [
            item for item in section.get("items", [])
            if item not in ("Payment Entry", "Journal Entry")
        ]
        if items:  # only keep section if it still has items
            section["items"] = items
            filtered.append(section)

    # Add Sponsorship Allocation
    filtered.append({
        "label": "Sponsorship",
        "items": ["Sponsorship Allocation"]
    })
    data["transactions"] = filtered

    # Also remove from internal links if present
    data["internal_links"] = {
        k: v for k, v in data.get("internal_links", {}).items()
        if k not in ("Payment Entry", "Journal Entry")
    }

    if "fieldname" not in data:
        data["fieldname"] = "donation"

    return data