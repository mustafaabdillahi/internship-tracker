import secrets
import string

characters = string.ascii_letters + string.digits

def generate_id(length: int) -> str:
    """Generates a random alphanumeric ID string of a given length."""
    return "".join(secrets.choice(characters) for _ in range(length))
