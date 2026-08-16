"""
Module: core/keygen_engine.py
Mục đích: Lõi tạo License Key bằng RSA Private Key (Dành cho Admin).
Hỗ trợ cả RSA-PSS (Tiêu chuẩn NIST cao nhất) và RSA-PKCS1v15.
Được dùng chung bởi cả Tool Desktop Keygen và Telegram Bot.
"""

import sys
import os
import json
import time
import base64
import datetime

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

def load_private_key(private_key_source: str):
    """Nạp Private Key từ file đường dẫn hoặc từ chuỗi text."""
    if os.path.exists(private_key_source):
        with open(private_key_source, "rb") as f:
            pem_data = f.read()
    else:
        pem_data = private_key_source.encode('utf-8')
        
    return serialization.load_pem_private_key(pem_data, password=None)


def create_license_key(
    hwid: str,
    days: int | str,
    note: str = "Customer",
    private_key_path: str = "keys/private_key.pem",
    use_pss: bool = True
) -> str:
    """
    Sinh License Key định dạng: LIC-<Base64_Payload>.<Base64_Signature>
    
    Args:
        hwid: Mã máy HWID của khách (ví dụ: A1B2-C3D4-E5F6-7890 hoặc * cho tất cả máy)
        days: Số ngày cấp phép (ví dụ: 3, 30, 365) hoặc "LIFETIME"
        note: Ghi chú tên khách hàng
        private_key_path: Đường dẫn tới private_key.pem
        use_pss: Sử dụng chuẩn ký RSA-PSS (Probabilistic Signature Scheme)
    """
    private_key = load_private_key(private_key_path)
    
    # Tính ngày hết hạn
    if str(days).upper() in ["LIFETIME", "VINH VIEN", "-1"]:
        expiry_str = "LIFETIME"
    else:
        num_days = int(days)
        exp_date = datetime.date.today() + datetime.timedelta(days=num_days)
        expiry_str = exp_date.strftime("%Y-%m-%d")
        
    payload_dict = {
        "hwid": hwid.strip().upper(),
        "expiry": expiry_str,
        "type": "PRO",
        "scheme": "PSS" if use_pss else "PKCS1",
        "issued_at": int(time.time()),
        "note": str(note)
    }
    
    payload_json = json.dumps(payload_dict, separators=(',', ':')).encode('utf-8')
    
    if use_pss:
        pad_scheme = padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        )
    else:
        pad_scheme = padding.PKCS1v15()

    signature = private_key.sign(
        payload_json,
        pad_scheme,
        hashes.SHA256()
    )
    
    b64_payload = base64.urlsafe_b64encode(payload_json).decode('utf-8').rstrip('=')
    b64_signature = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    return f"LIC-{b64_payload}.{b64_signature}"


def parse_license_payload(license_key_str: str) -> dict | None:
    """Đọc thông tin trong License Key mà không cần Private Key."""
    try:
        license_key_str = license_key_str.strip()
        if not license_key_str.startswith("LIC-"):
            return None
        parts = license_key_str[4:].split(".")
        if len(parts) != 2:
            return None
            
        b64_payload = parts[0]
        missing_padding = len(b64_payload) % 4
        if missing_padding:
            b64_payload += '=' * (4 - missing_padding)
            
        payload_bytes = base64.urlsafe_b64decode(b64_payload.encode('utf-8'))
        return json.loads(payload_bytes.decode('utf-8'))
    except Exception:
        return None
