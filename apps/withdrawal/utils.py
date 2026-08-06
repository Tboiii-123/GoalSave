import uuid


def generate_withdrawal_reference():
    return f"WDL_{uuid.uuid4().hex[:10].upper()}"