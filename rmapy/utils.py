import uuid
import secrets


def generate_path() -> str:
    return secrets.token_hex(32)

def generate_doc_id() -> str:
    return str(uuid.uuid4())


