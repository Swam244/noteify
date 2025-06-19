from app.config import settings
from cryptography.fernet import Fernet
import bcrypt

key = str(settings.TOKEN_KEY).encode('utf-8')

def generate_hash(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password.decode()

def verify_hash(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def generateFernetKey() -> bytes:
    return Fernet.generate_key()

def encryptToken(plaintext_token: str) -> str:
    f = Fernet(key)
    encrypted_data = f.encrypt(plaintext_token.encode('utf-8'))
    return encrypted_data.decode('utf-8')

def decryptToken(encrypted_string: str) -> str:
    f = Fernet(key)
    try:
        decrypted_data = f.decrypt(encrypted_string.encode('utf-8'))
        return decrypted_data.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}. Data might be tampered with or key is incorrect.")
