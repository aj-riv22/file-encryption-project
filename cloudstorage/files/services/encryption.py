from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
import os

class EncryptionService:
    def __init__(self):
        self.salt = os.urandom(16)

    def generate_key(self):
        """Generate a secure encryption key"""
        return base64.urlsafe_b64encode(os.urandom(32))

    def encrypt_file(self, file_data: bytes, key: bytes) -> tuple[bytes, bytes]:
        """
        Encrypt file data using AES-256-GCM
        Returns (encrypted_data, tag)
        """
        iv = os.urandom(12)
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
        )
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(file_data) + encryptor.finalize()
        return base64.b64encode(iv + ciphertext + encryptor.tag)

    def decrypt_file(self, encrypted_data: bytes, key: bytes) -> bytes:
        """Decrypt file data using AES-256-GCM"""
        data = base64.b64decode(encrypted_data)
        iv = data[:12]
        tag = data[-16:]
        ciphertext = data[12:-16]

        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, tag),
        )
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    @staticmethod
    def derive_key_from_password(password: str) -> bytes:
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key