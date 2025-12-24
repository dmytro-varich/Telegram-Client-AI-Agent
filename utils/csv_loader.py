import csv
from typing import List, Dict, Any


# ---------------------------------------------------------------------
# Load groups
# ---------------------------------------------------------------------
def load_groups(file_name: str = "groups.csv") -> List[Dict[str, Any]]:
    """
    Load group data from CSV.

    Returns:
        List of dicts with keys: id, username, title
    """
    groups = []

    with open(file_name, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            groups.append({
                "id": int(row["id"]),
                "username": row.get("username", ""),
                "title": row.get("title", ""),
            })
    return groups


# ---------------------------------------------------------------------
# Load users
# ---------------------------------------------------------------------
def load_users(file_name: str = "users.csv") -> List[Dict[str, Any]]:
    """
    Load user data from CSV.

    Returns:
        List of dicts with keys: id, username, first_name, last_name, phone
    """
    users = []

    with open(file_name, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append({
                "id": int(row["id"]),
                "username": row.get("username", ""),
                "first_name": row.get("first_name", ""),
                "last_name": row.get("last_name", ""),
                "phone": row.get("phone", ""),
            })
    return users
