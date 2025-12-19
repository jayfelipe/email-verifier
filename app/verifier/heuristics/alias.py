#alias.py
def check_alias(local: str):
    if "+" in local:
        base, tag = local.split("+", 1)
        return {
            "has_alias": True,
            "tag": tag
        }
    return {
        "has_alias": False,
        "tag": None
    }
