import hashlib
import os
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


ENCRYPTION_KEY = hashlib.sha256(
    settings.storage_secret.encode()
).digest()


def encrypt_file(data: bytes) -> bytes:
    nonce = secrets.token_bytes(12)

    aes = AESGCM(ENCRYPTION_KEY)

    encrypted_data = aes.encrypt(
        nonce,
        data,
        None,
    )

    return nonce + encrypted_data


def decrypt_file(data: bytes) -> bytes:
    if len(data) < 13:
        raise ValueError("Invalid encrypted data")

    nonce = data[:12]
    encrypted_data = data[12:]

    aes = AESGCM(ENCRYPTION_KEY)

    return aes.decrypt(
        nonce,
        encrypted_data,
        None,
    )


def generate_file_id(filename: str) -> str:
    random_part = secrets.token_hex(16)

    value = f"{filename}:{random_part}".encode()

    return hashlib.sha256(value).hexdigest()