# Reference Link:
# https://stackoverflow.com/questions/9594125/salt-and-hash-a-password-in-python
from hashlib import sha256

def hash_new_password(password):
    """
    Hash the provided password and return the hashed password to store in the database.
    """
    password = password.encode()
    hash = sha256(password).hexdigest()
    return hash