"""Encrypted escrow of school-issued student passwords, separate from login hashes."""
import base64
import hashlib
import json
from cryptography.fernet import Fernet,InvalidToken

def hash_fingerprint(password_hash):
    return hashlib.sha256(password_hash.encode()).hexdigest()

def cipher(secret):
    key=hashlib.sha256(b'school-issued-student-passwords-v1\x00'+secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))

def seal_password(secret,member_id,password,password_hash):
    payload=json.dumps({'memberId':member_id,'password':password,'hash':hash_fingerprint(password_hash)},ensure_ascii=False)
    return cipher(secret).encrypt(payload.encode()).decode()

def open_password(secret,member_id,encrypted,password_hash):
    try:
        data=json.loads(cipher(secret).decrypt(encrypted.encode()))
        if data.get('memberId')!=member_id or data.get('hash')!=hash_fingerprint(password_hash):return None
        return data['password'] if isinstance(data.get('password'),str) else None
    except (InvalidToken,ValueError,TypeError,KeyError,UnicodeError):
        return None
