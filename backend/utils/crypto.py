from cryptography.fernet import Fernet
import base64
import hashlib


class PasswordEncryption:
    """密码加密类，使用Fernet对称加密"""

    def __init__(self, key):
        # Ensure key is 32 bytes for Fernet
        key_bytes = key.encode() if isinstance(key, str) else key
        # Create a consistent 32-byte key using SHA256
        hashed = hashlib.sha256(key_bytes).digest()
        self.cipher = Fernet(base64.urlsafe_b64encode(hashed))

    def encrypt(self, password):
        """加密密码"""
        if isinstance(password, str):
            password = password.encode()
        encrypted = self.cipher.encrypt(password)
        return encrypted.decode()

    def decrypt(self, encrypted_password):
        """解密密码"""
        if isinstance(encrypted_password, str):
            encrypted_password = encrypted_password.encode()
        decrypted = self.cipher.decrypt(encrypted_password)
        return decrypted.decode()
