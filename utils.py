import random
import string
from app.models import ShortURL

ALPHABET = string.ascii_letters + string.digits  # a-zA-Z0-9
CODE_LENGTH = 7

def generate_short_code():
    while True:
        code = "".join(random.choices(ALPHABET, k=CODE_LENGTH))
        if not ShortURL.query.filter_by(short_code=code).first():
            return code