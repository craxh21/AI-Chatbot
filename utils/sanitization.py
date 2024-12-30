import re

def sanitize_input(user_input):
    # Remove special characters and excessive whitespace
    sanitized = re.sub(r'[^\w\s]', '', user_input).strip()
    return sanitized if len(sanitized) > 0 else None
