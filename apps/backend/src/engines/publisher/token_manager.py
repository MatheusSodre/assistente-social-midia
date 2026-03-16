import os
import base64
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

_KEY = os.getenv("ENCRYPTION_KEY", "")


def _get_fernet() -> Fernet:
    if not _KEY:
        # Gera chave determinística para desenvolvimento — em produção use uma chave fixa no .env
        key = base64.urlsafe_b64encode(b"assistente-social-midia-dev-key!!")
        return Fernet(key)
    return Fernet(_KEY.encode())


def encrypt_token(token: str) -> str:
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()
