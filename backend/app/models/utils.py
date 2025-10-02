import uuid


def generate_uuid() -> str:
    """Generate a UUID string for database IDs."""
    return str(uuid.uuid4())
