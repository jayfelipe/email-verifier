#role.py
ROLE_ACCOUNTS = {
    "admin", "info", "support", "sales",
    "contact", "help", "billing", "abuse",
    "postmaster", "webmaster"
}

def check_role_account(local: str):
    user = local.lower()
    if user in ROLE_ACCOUNTS:
        return {
            "is_role": True,
            "role_type": user
        }
    return {
        "is_role": False,
        "role_type": None
    }
