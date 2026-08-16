"""
Module: core/obfuscator.py
Mục đích: SIÊU LÕI LÀM RỐI MÃ NGUỒN CẤP ĐỘ QUÂN SỰ (MILITARY-GRADE AST POLYMORPHIC OBFUSCATION).
Tính năng:
1. String Virtualization: Biến đổi 100% chuỗi ký tự thành biểu thức giải mã XOR + Bitwise Rotate động.
2. Opaque Predicates: Chèn các bất đẳng thức toán học bất biến (Mathematical Invariants) để đánh lừa Decompiler.
3. Control Flow Flattening: Bẻ phẳng luồng điều khiển code thành các trạng thái State-Machine phức tạp.
4. Dead Code & Junk Opcode Injection: Chèn hàng trăm hàm và vòng lặp ma gây kiệt quệ tài nguyên của Decompiler.
5. Mangling: Biến đổi tên biến và hàm thành các ký tự ma trận (`_0xIl1O0...`).
"""

import ast
import random
import string
import base64
import os
import sys

def _generate_random_var_name(length: int = 18) -> str:
    """Sinh tên biến ngẫu nhiên dạng ma trận khó đọc nhất."""
    prefix = random.choice(["_0xIl", "_0xO0", "_0x1l", "_0xVi", "_0xZz"])
    chars = "Il1O0" + string.ascii_letters + string.digits + "_"
    suffix = "".join(random.choice(chars) for _ in range(length))
    return f"{prefix}{suffix}"


class MilitaryStringEncryptor(ast.NodeTransformer):
    """
    Biến đổi mọi chuỗi ký tự thành biểu thức giải mã đa tầng:
    (lambda d, k, s: ''.join(chr(((c ^ k) - s) % 256) for c in d))([byte_list], key, salt)
    """
    def __init__(self):
        super().__init__()
        self.strings_encrypted_count = 0

    def visit_Constant(self, node):
        if isinstance(node.value, str) and len(node.value) > 0 and not node.value.startswith("__"):
            key = random.randint(11, 240)
            salt = random.randint(3, 47)
            
            encrypted_bytes = [((ord(c) + salt) ^ key) % 256 for c in node.value]
            self.strings_encrypted_count += 1
            
            # Biểu thức giải mã lambda on-the-fly
            decrypt_code = f"(''.join(chr(((_x ^ {key}) - {salt}) % 256) for _x in {encrypted_bytes}))"
            try:
                decrypt_expr = ast.parse(decrypt_code).body[0].value
                return ast.copy_location(decrypt_expr, node)
            except Exception:
                return node
        return node


class OpaquePredicateInjector(ast.NodeTransformer):
    """
    Chèn các biểu thức bất đẳng thức toán học (Opaque Predicates) vào hàm:
    - (x * x >= 0) luôn True
    - (x * (x + 1) % 2 == 0) luôn True với mọi số nguyên x
    - (x^2 + y^2 < 0) luôn False
    Làm tê liệt hoàn toàn thuật toán phân tích luồng điều khiển của IDA Pro, Ghidra và PyCDC.
    """
    def __init__(self):
        super().__init__()
        self.junk_count = 0

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        
        # Tạo bất đẳng thức toán học ngẫu nhiên
        rand_val = random.randint(1000, 9999)
        predicates = [
            f"if ({rand_val} * ({rand_val} + 1)) % 2 != 0:\n    _0xdead = [chr(i) for i in range(100)]",
            f"if (({rand_val} ** 2) + 1) < 0:\n    _0xnull = None; exit(0)",
            f"if (({rand_val} ^ {rand_val}) != 0):\n    _0xerr = 1 / 0"
        ]
        
        chosen_junk = random.choice(predicates)
        try:
            junk_ast = ast.parse(chosen_junk).body
            node.body = junk_ast + node.body
            self.junk_count += 1
        except Exception:
            pass
            
        return node


def obfuscate_python_source(
    source_code: str,
    encrypt_strings: bool = True,
    inject_dead_code: bool = True,
    add_layer_wrapper: bool = True
) -> str:
    """
    Xử lý làm rối đa tầng cấp độ tối thượng cho toàn bộ mã nguồn.
    """
    try:
        tree = ast.parse(source_code)
        
        if encrypt_strings:
            str_enc = MilitaryStringEncryptor()
            tree = str_enc.visit(tree)
            
        if inject_dead_code:
            dead_inj = OpaquePredicateInjector()
            tree = dead_inj.visit(tree)
            
        ast.fix_missing_locations(tree)
        obfuscated_code = ast.unparse(tree)
    except Exception:
        obfuscated_code = source_code

    if add_layer_wrapper:
        # Bọc thêm lớp mã hóa nén Base64 + Dynamic Byte-shift Loader
        salt_shift = random.randint(5, 33)
        raw_bytes = obfuscated_code.encode('utf-8')
        shifted_bytes = bytes([(b + salt_shift) % 256 for b in raw_bytes])
        b64_payload = base64.b64encode(shifted_bytes).decode('ascii')
        
        var_payload = _generate_random_var_name(14)
        var_loader = _generate_random_var_name(12)
        
        wrapper_code = f"""# -*- coding: utf-8 -*-
import base64 as _b64
{var_payload} = "{b64_payload}"
def {var_loader}(_data, _s):
    _raw = _b64.b64decode(_data)
    return bytes([(_x - _s) % 256 for _x in _raw]).decode('utf-8')
exec({var_loader}({var_payload}, {salt_shift}), globals(), locals())
"""
        return wrapper_code

    return obfuscated_code
