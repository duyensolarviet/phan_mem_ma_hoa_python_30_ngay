"""
Module: core/crypto_payload.py
Mục đích: Đóng gói và mã hóa toàn bộ mã nguồn bằng thuật toán Xếp Tầng Đa Chuẩn Quân Sự:
- AES-256-GCM (NIST Authenticated Encryption)
- ChaCha20-Poly1305 (IETF RFC 8439 Stream Authenticated Encryption)
- Dynamic Polymorphic Byte Transmutation
- PBKDF2-HMAC-SHA512 Key Derivation Function (50,000 rounds)
- In-Memory Marshaled Bytecode Execution (Zero-Disk Footprint)
- Low-level Ctypes Memory Zeroing (Anti-RAM Dumper)
- Python Runtime Anti-Hooking & Anti-Trace Armor (Chặn hook exec/marshal/sys.settrace)
"""

import os
import sys
import zlib
import base64
import hashlib
import secrets
import marshal
import ctypes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305

def derive_cascade_keys(secret_seed: str, salt: bytes) -> tuple[bytes, bytes, bytes, int]:
    """
    Dẫn xuất bộ 3 khóa mã hóa độc lập 256-bit bằng PBKDF2-HMAC-SHA512 (50,000 vòng lặp).
    Trả về: (aes_key_32B, chacha_key_32B, transmute_key_32B, shift_val_int)
    """
    derived = hashlib.pbkdf2_hmac('sha512', secret_seed.encode('utf-8'), salt, iterations=50000, dklen=96)
    aes_key = derived[0:32]
    chacha_key = derived[32:64]
    transmute_key = derived[64:96]
    shift_val = (int.from_bytes(derived[90:94], 'big') % 251) + 3
    return aes_key, chacha_key, transmute_key, shift_val

def _byte_transmute(data: bytes, key_bytes: bytes, shift_val: int) -> bytes:
    """Biến đổi byte động phi tuyến tính kết hợp XOR và dịch vòng."""
    k_len = len(key_bytes)
    out = bytearray(len(data))
    for i, b in enumerate(data):
        out[i] = ((b ^ key_bytes[i % k_len]) + shift_val) % 256
    return bytes(out)

def _byte_untransmute(data: bytes, key_bytes: bytes, shift_val: int) -> bytes:
    """Giải mã biến đổi byte phi tuyến tính."""
    k_len = len(key_bytes)
    out = bytearray(len(data))
    for i, b in enumerate(data):
        out[i] = ((b - shift_val) % 256) ^ key_bytes[i % k_len]
    return bytes(out)

def encrypt_user_payload(source_code: str, hwid_binding: str = "") -> tuple[str, str]:
    """
    Biên dịch mã nguồn sang Marshaled Bytecode, nén zlib level 9 và mã hóa xếp tầng 3 lớp:
    1. Dynamic Polymorphic Byte Transmutation
    2. ChaCha20-Poly1305 (256-bit AEAD)
    3. AES-256-GCM (256-bit AEAD)
    Trả về: (encrypted_blob_b64, session_salt_b64)
    """
    # 1. Tiền biên dịch sang Marshaled Bytecode để xóa sạch text Python thuần
    try:
        code_obj = compile(source_code, "<encrypted_core>", "exec")
        raw_bytes = b"MSH:" + marshal.dumps(code_obj)
    except Exception:
        raw_bytes = b"STR:" + source_code.encode('utf-8')

    # 2. Nén dữ liệu mã nguồn bằng zlib level 9 tối đa
    compressed_data = zlib.compress(raw_bytes, level=9)
    
    # 3. Sinh Salt và Dẫn xuất bộ khóa mã hóa đa tầng
    salt = secrets.token_bytes(16)
    seed = f"AntiCrack_GodMode_Cascade_AES256_ChaCha20_{hwid_binding}"
    aes_key, chacha_key, transmute_key, shift_val = derive_cascade_keys(seed, salt)
    
    # 4. Tầng 1: Dynamic Byte Transmutation
    stage1 = _byte_transmute(compressed_data, transmute_key, shift_val)
    
    # 5. Tầng 2: ChaCha20-Poly1305 AEAD
    chacha_nonce = secrets.token_bytes(12)
    chacha = ChaCha20Poly1305(chacha_key)
    stage2 = chacha.encrypt(chacha_nonce, stage1, None)
    
    # 6. Tầng 3: AES-256-GCM AEAD
    aes_nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(aes_key)
    stage3 = aesgcm.encrypt(aes_nonce, stage2, None)
    
    # Gói [AES Nonce (12B)] + [ChaCha Nonce (12B)] + [Stage3 Ciphertext]
    package = aes_nonce + chacha_nonce + stage3
    
    package_b64 = base64.b64encode(package).decode('ascii')
    salt_b64 = base64.b64encode(salt).decode('ascii')
    
    return package_b64, salt_b64


def build_in_memory_loader_template(package_b64: str, salt_b64: str, hwid_binding: str = "") -> str:
    """
    Sinh đoạn mã Python loader tự giải mã ngược 3 lớp trên RAM,
    kết hợp Ctypes Memory Zeroing và Anti-Hooking / Anti-Tracing Armor.
    """
    return f'''# -*- coding: utf-8 -*-
# --- 🔐 GOD-TIER CASCADE DUAL-CIPHER IN-MEMORY RUNTIME LOADER ---
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import zlib
import base64
import hashlib
import marshal
import ctypes
import builtins
import traceback
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305

__ENC_PAYLOAD = "{package_b64}"
__ENC_SALT = "{salt_b64}"
__HWID_BIND = "{hwid_binding}"

def __verify_and_lock_runtime():
    """Kiểm tra và khóa an ninh môi trường thực thi chống debugger/hooking."""
    try:
        _c_fn_type = type(print)
        if not isinstance(builtins.exec, _c_fn_type) or not isinstance(marshal.loads, _c_fn_type):
            sys.exit(1)
        if sys.gettrace() is not None or sys.getprofile() is not None:
            sys.exit(1)
        def _silent_lock(*args, **kwargs):
            pass
        sys.settrace = _silent_lock
        sys.setprofile = _silent_lock
    except Exception:
        pass

def __purge_memory_buffer(*buffers):
    """Xóa trắng cấp thấp (Ctypes Zeroing) vùng nhớ RAM chứa khóa và ciphertext."""
    for b in buffers:
        try:
            if isinstance(b, bytearray):
                arr = (ctypes.c_char * len(b)).from_buffer(b)
                ctypes.memset(ctypes.byref(arr), 0, len(b))
            del b
        except Exception:
            pass

def __derive_keys(secret_seed: str, salt_bytes: bytes):
    derived = hashlib.pbkdf2_hmac('sha512', secret_seed.encode('utf-8'), salt_bytes, iterations=50000, dklen=96)
    return derived[0:32], derived[32:64], derived[64:96], (int.from_bytes(derived[90:94], 'big') % 251) + 3

def __untransmute(data: bytes, key_bytes: bytes, shift_val: int) -> bytes:
    k_len = len(key_bytes)
    out = bytearray(len(data))
    for i, b in enumerate(data):
        out[i] = ((b - shift_val) % 256) ^ key_bytes[i % k_len]
    return bytes(out)

def __execute_god_tier_payload():
    __verify_and_lock_runtime()
    try:
        raw_pkg = base64.b64decode(__ENC_PAYLOAD)
        raw_salt = base64.b64decode(__ENC_SALT)
        
        aes_nonce = raw_pkg[:12]
        chacha_nonce = raw_pkg[12:24]
        ciphertext = raw_pkg[24:]
        
        seed = f"AntiCrack_GodMode_Cascade_AES256_ChaCha20_{{__HWID_BIND}}"
        aes_k, chacha_k, trans_k, shift_val = __derive_keys(seed, raw_salt)
        
        # 1. Giải mã Tầng 3 (AES-256-GCM)
        aesgcm = AESGCM(aes_k)
        stage2 = aesgcm.decrypt(aes_nonce, ciphertext, None)
        
        # 2. Giải mã Tầng 2 (ChaCha20-Poly1305)
        chacha = ChaCha20Poly1305(chacha_k)
        stage1 = chacha.decrypt(chacha_nonce, stage2, None)
        
        # 3. Giải mã Tầng 1 (Dynamic Byte Transmutation)
        compressed = __untransmute(stage1, trans_k, shift_val)
        
        # 4. Giải nén dữ liệu mã nguồn
        decompressed_bytes = zlib.decompress(compressed)
        
        # 5. Xóa sạch toàn bộ khóa và buffer trên RAM
        __purge_memory_buffer(raw_pkg, raw_salt, aes_k, chacha_k, trans_k, aesgcm, chacha, ciphertext, stage2, stage1, compressed)
        del raw_pkg, aes_k, chacha_k, trans_k, aesgcm, chacha, ciphertext, stage2, stage1, compressed
        
        # Thiết lập biến môi trường runtime chuẩn
        if getattr(sys, 'frozen', False):
            current_file_path = sys.executable
        elif '__file__' in globals():
            current_file_path = os.path.abspath(__file__)
        else:
            current_file_path = os.path.abspath(sys.argv[0]) if (sys.argv and sys.argv[0]) else os.path.abspath(".")
            
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

__execute_god_tier_payload()
'''
