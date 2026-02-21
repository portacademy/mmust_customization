def get_data(data=None):
    data = data or {}
    
    transactions = data.get("transactions", [])
    transactions.append({
        "label": "Sponsorship",
        "items": ["Sponsorship Allocation"]
    })
    data["transactions"] = transactions
    
    if "fieldname" not in data:
        data["fieldname"] = "donation"
        
    return data