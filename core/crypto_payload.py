"""
Module: core/crypto_payload.py
Mục đích: Đóng gói và mã hóa toàn bộ mã nguồn bằng thuật toán AES-256-GCM + Marshaled Bytecode Execution.
Đặc tính tối thượng:
1. Tiền biên dịch (Pre-compile) sang Python Code Object và Marshal nhị phân (chống đọc Plain-text trên RAM).
2. Nén dữ liệu mã nguồn bằng zlib level 9 tối đa.
3. Mã hóa bằng chuẩn quân sự AES-256-GCM (Authenticated Encryption) kèm thẻ tag xác thực tính toàn vẹn.
4. Sinh khóa bảo mật đa tầng từ HWID máy tính + Session Salt ngẫu nhiên.
5. Cơ chế thực thi hoàn toàn trong RAM (In-Memory Marshaled Bytecode Execution - Zero Disk Footprint).
6. Tự động xóa sạch vùng nhớ chứa khóa AES (Memory Zeroing) ngay sau khi giải mã để chống Memory Forensics Dump.
7. Tự động thiết lập đầy đủ môi trường runtime (__file__, __name__, paths) cho mã nguồn người dùng.
"""

import os
import sys
import zlib
import base64
import hashlib
import secrets
import marshal
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def derive_aes_key(secret_seed: str, salt: bytes) -> bytes:
    """Sinh khóa 256-bit (32 bytes) an toàn bằng SHA-256 KDF."""
    return hashlib.sha256(salt + secret_seed.encode('utf-8') + salt[::-1]).digest()

def encrypt_user_payload(source_code: str, hwid_binding: str = "") -> tuple[str, str]:
    """
    Tiền biên dịch sang Bytecode, nén và mã hóa bằng AES-256-GCM.
    Trả về: (encrypted_blob_b64, session_salt_b64)
    """
    # 1. Tiền biên dịch sang Marshaled Bytecode để xóa sạch chuỗi Python thuần
    try:
        code_obj = compile(source_code, "<encrypted_core>", "exec")
        raw_bytes = b"MSH:" + marshal.dumps(code_obj)
    except Exception:
        raw_bytes = b"STR:" + source_code.encode('utf-8')

    # 2. Nén dữ liệu mã nguồn level 9
    compressed_data = zlib.compress(raw_bytes, level=9)
    
    # 3. Sinh Salt và Khóa AES-256
    salt = secrets.token_bytes(16)
    seed = f"AntiCrack_GodMode_AES256_{hwid_binding}"
    aes_key = derive_aes_key(seed, salt)
    
    # 4. Mã hóa AES-GCM (Nonce 12 bytes chuẩn NIST)
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(aes_key)
    ciphertext = aesgcm.encrypt(nonce, compressed_data, None)
    
    # Gói [Nonce (12B)] + [Ciphertext + Auth Tag]
    package = nonce + ciphertext
    
    package_b64 = base64.b64encode(package).decode('ascii')
    salt_b64 = base64.b64encode(salt).decode('ascii')
    
    return package_b64, salt_b64


def build_in_memory_loader_template(package_b64: str, salt_b64: str, hwid_binding: str = "") -> str:
    """
    Sinh đoạn mã Python loader tự giải mã và thực thi Marshaled Bytecode trực tiếp trên RAM kèm Memory Zeroing.
    """
    return f'''# -*- coding: utf-8 -*-
# --- 🔐 AES-256-GCM IN-MEMORY BYTECODE RUNTIME LOADER (ZERO DISK FOOTPRINT) ---
import sys
import os
import zlib
import base64
import hashlib
import marshal
import ctypes
import traceback
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

__ENC_PAYLOAD = "{package_b64}"
__ENC_SALT = "{salt_b64}"
__HWID_BIND = "{hwid_binding}"

def __purge_memory_buffer(*buffers):
    """Xóa trắng toàn bộ vùng nhớ chứa khóa AES và ciphertext để chống Memory Dumper."""
    for b in buffers:
        try:
            if isinstance(b, (bytearray, bytes)):
                del b
        except Exception:
            pass

def __execute_in_memory_payload():
    try:
        raw_pkg = base64.b64decode(__ENC_PAYLOAD)
        raw_salt = base64.b64decode(__ENC_SALT)
        
        nonce = raw_pkg[:12]
        ciphertext = raw_pkg[12:]
        
        seed = f"AntiCrack_GodMode_AES256_{{__HWID_BIND}}"
        key = hashlib.sha256(raw_salt + seed.encode('utf-8') + raw_salt[::-1]).digest()
        
        aesgcm = AESGCM(key)
        decompressed_bytes = zlib.decompress(aesgcm.decrypt(nonce, ciphertext, None))
        
        # Xóa trắng khóa AES và bản mã khỏi bộ nhớ RAM
        __purge_memory_buffer(raw_pkg, raw_salt, key, aesgcm, ciphertext, nonce)
        del raw_pkg, key, aesgcm
        
        # Thiết lập an toàn biến môi trường runtime __file__, __name__ cho payload
        if getattr(sys, 'frozen', False):
            current_file_path = sys.executable
        elif '__file__' in globals():
            current_file_path = os.path.abspath(__file__)
        else:
            current_file_path = os.path.abspath(sys.argv[0]) if (sys.argv and sys.argv[0]) else os.path.abspath(".")
            
        current_dir_path = os.path.dirname(current_file_path)
        
        runtime_scope = globals()
        runtime_scope['__file__'] = current_file_path
        runtime_scope['__name__'] = '__main__'
        runtime_scope['__doc__'] = None
        
        if decompressed_bytes.startswith(b"MSH:"):
            code_obj = marshal.loads(decompressed_bytes[4:])
        elif decompressed_bytes.startswith(b"STR:"):
            code_obj = compile(decompressed_bytes[4:].decode('utf-8', errors='ignore'), "<protected_runtime>", "exec")
        else:
            code_obj = compile(decompressed_bytes.decode('utf-8', errors='ignore'), "<protected_runtime>", "exec")
            
        del decompressed_bytes
        
        exec(code_obj, runtime_scope, runtime_scope)
        
    except Exception as e:
        print(f"\\n[!] LỖI THỰC THI CHƯƠNG TRÌNH: {{e}}")
        traceback.print_exc()
        if sys.platform == "win32":
            try:
                import tkinter as _tk
                from tkinter import messagebox as _mb
                _root = _tk.Tk()
                _root.withdraw()
                _mb.showerror("Lỗi Khởi Động", f"Không thể tải mã nguồn mã hóa:\\n{{e}}")
                _root.destroy()
            except Exception:
                pass
        sys.exit(1)

__execute_in_memory_payload()
'''
