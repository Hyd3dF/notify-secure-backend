from argon2 import PasswordHasher
from cryptography.fernet import Fernet
import os
import base64

# Initialize Argon2 Password Hasher
ph = PasswordHasher()

def hash_password(password):
    """Hash a password using Argon2."""
    return ph.hash(password)

def verify_password(hash, password):
    """Verify a password against an Argon2 hash."""
    try:
        return ph.verify(hash, password)
    except Exception:
        return False

def generate_encryption_key():
    """Generate a new Fernet key."""
    return Fernet.generate_key()

def encrypt_data(data, key):
    """Encrypt data (string) using the provided key."""
    f = Fernet(key)
    if isinstance(data, str):
        data = data.encode()
    return f.encrypt(data).decode()

def decrypt_data(token, key):
    """Decrypt data (token) using the provided key."""
    f = Fernet(key)
    if isinstance(token, str):
        token = token.encode()
    return f.decrypt(token).decode()
