"""
Module: builder/pack_engine.py
Mục đích: Lõi tự động tiêm bảo mật mã hóa đỉnh cao (In-Memory AES-256 + Anti-Debug + HWID 2.0 + Trial) 
và đóng gói Thư Mục Dự Án Python thành file .EXE độc lập.
Tính năng:
- Mã hóa AES-256 GCM + Obfuscation, giải mã trực tiếp trên RAM (Zero-Disk Footprint).
- Khóa bản quyền phần cứng HWID 2.0 & Chữ ký số RSA-PSS NIST.
- Hỗ trợ Dùng thử linh hoạt (Phút / Giờ / Ngày) & Chống tua ngược đồng hồ (TimeGuard).
- Tự động gom 100% mã nguồn (src, ui_actions...), dữ liệu (assets, json, txt) vào trong file .EXE qua --add-data.
- Tự động quét AST toàn bộ thư mục dự án để gom tất cả thư viện (selenium, customtkinter, requests, PIL, google, groq, undetected_chromedriver...) qua --collect-all và --hidden-import.
- Thiết lập sys.path thông minh và an toàn (chống xung đột module stdlib/thư viện như urllib3).
- Tự động giải phóng tiến trình cũ để chống lỗi WinError 32 / WinError 5 (Permission Denied).
- Tự động chuyển đổi ảnh PNG, JPG, JPEG, WEBP, BMP sang ICO chuẩn Windows đa kích thước.
"""

import sys
import os
import ast
import json
import shutil
import subprocess
import threading

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.obfuscator import obfuscate_python_source
from core.crypto_payload import encrypt_user_payload, build_in_memory_loader_template

def extract_project_imports(project_dir: str, entry_file: str = None) -> tuple[list[str], list[str]]:
    """
    Tự động phân tích AST toàn bộ mã nguồn trong thư mục để trích xuất:
    1. Danh sách top-level external packages (để dùng --collect-all)
    2. Danh sách tất cả dotted module paths (để dùng --hidden-import)
    """
    top_packages = set()
    dotted_imports = set()
    files_to_scan = []
    
    if project_dir and os.path.exists(project_dir):
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if not d.startswith(('.', '__', 'build', 'dist')) and d.lower() not in ('venv', '.venv', 'env', 'node_modules', '.git', '.idea', '.vscode')]
            for f in files:
                if f.endswith('.py') and not f.startswith('_temp_wrapped'):
                    files_to_scan.append(os.path.join(root, f))
    elif entry_file and os.path.exists(entry_file):
        files_to_scan.append(entry_file)
        
    for py_f in files_to_scan:
        try:
            with open(py_f, 'r', encoding='utf-8', errors='ignore') as f:
                tree = ast.parse(f.read(), filename=py_f)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dotted_imports.add(alias.name)
                        top_pkg = alias.name.split('.')[0]
                        if top_pkg:
                            top_packages.add(top_pkg)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dotted_imports.add(node.module)
                        top_pkg = node.module.split('.')[0]
                        if top_pkg:
                            top_packages.add(top_pkg)
        except Exception:
            pass
            
    # Lọc bỏ các thư mục / module nội bộ của project
    local_names = set()
    if project_dir and os.path.exists(project_dir):
        try:
            for item in os.listdir(project_dir):
                full_item = os.path.join(project_dir, item)
                if os.path.isdir(full_item):
                    local_names.add(item)
                    for root, dirs, files in os.walk(full_item):
                        for f in files:
                            if f.endswith('.py'):
                                local_names.add(os.path.splitext(f)[0])
                elif item.endswith('.py'):
                    local_names.add(os.path.splitext(item)[0])
        except Exception:
            pass

    # Lọc bỏ stdlib modules khỏi danh sách collect-all
    stdlib = getattr(sys, 'stdlib_module_names', set())
    
    final_top_pkgs = [pkg for pkg in top_packages if pkg and pkg not in local_names and pkg not in stdlib]
    final_dotted = [imp for imp in dotted_imports if imp and imp.split('.')[0] not in local_names]
    
    return sorted(final_top_pkgs), sorted(final_dotted)


def convert_to_ico(image_path: str, target_dir: str = None) -> str | None:
    """Tự động chuyển đổi bất kỳ định dạng ảnh nào (PNG, JPG, WEBP, BMP...) sang .ICO chuẩn đa kích thước."""
    if not image_path or not os.path.exists(image_path):
        return None
    if image_path.lower().endswith('.ico'):
        return image_path
    try:
        from PIL import Image
        img = Image.open(image_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        out_dir = target_dir or os.path.dirname(os.path.abspath(image_path))
        os.makedirs(out_dir, exist_ok=True)
        out_ico = os.path.join(out_dir, f"{base_name}_converted.ico")
        
        icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        img.save(out_ico, format='ICO', sizes=icon_sizes)
        return out_ico
    except Exception as e:
        print(f"[!] Lỗi chuyển đổi ảnh sang ICO: {e}")
        return None

WRAPPER_TEMPLATE = '''# -*- coding: utf-8 -*-
"""
ULTIMATE PROTECTED EXECUTABLE RUNNER
Generated by Python Anti-Crack Suite (Ultimate Beast Edition)
"""
import sys
import os
import json
import ctypes

# --- TỰ ĐỘNG THIẾT LẬP MÔI TRƯỜNG VÀ ĐƯỜNG DẪN IMPORT AN TOÀN CHO DỰ ÁN ---
if getattr(sys, 'frozen', False):
    _MEI_DIR = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    _EXE_DIR = os.path.dirname(sys.executable)
    _SEARCH_ROOTS = [_MEI_DIR, _EXE_DIR]
else:
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    _SEARCH_ROOTS = [_SCRIPT_DIR]

_SAFE_SUBDIRS = ["src", "ui_actions", "core", "utils", "modules", "components", "actions", "handlers"]
for _base in _SEARCH_ROOTS:
    if _base and os.path.exists(_base):
        if _base not in sys.path:
            sys.path.insert(0, _base)
        for _sub in _SAFE_SUBDIRS:
            _sub_path = os.path.join(_base, _sub)
            if os.path.isdir(_sub_path) and _sub_path not in sys.path:
                sys.path.insert(0, _sub_path)
            _src_sub = os.path.join(_base, "src", _sub)
            if os.path.isdir(_src_sub) and _src_sub not in sys.path:
                sys.path.insert(0, _src_sub)

# --- TỰ ĐỘNG BUNDLE TOÀN BỘ CÁC MODULE DEPENDENCY CỦA DỰ ÁN ---
{IMPORT_HINTS_CODE}

# --- 1. TIÊM MODULE CHỐNG DEBUG, HARDWARE BREAKPOINTS & VM/SANDBOX ---
{ANTI_DEBUG_CODE}

# --- 2. TIÊM LÕI BẢN QUYỀN HWID 2.0 & RSA-PSS ---
{LICENSE_ENGINE_CODE}

# --- 3. CẤU HÌNH KHÓA CÔNG KHAI & CSKH ---
EMBEDDED_PUBLIC_KEY_PEM = """{PUBLIC_KEY_PEM}"""
EMBEDDED_SUPPORT_CONFIG = json.loads(r"""{SUPPORT_CONFIG_JSON}""")

def _enforce_security():
    pass
    # 1. Kích hoạt chống debugger & phân tích tiến trình
    {START_WATCHER_CALL}
    
    # 2. Kiểm tra bản quyền & Hạn dùng thử (nếu được bật)
    {LICENSE_VERIFICATION_CALL}

# Thực thi kiểm tra an ninh trước khi giải mã payload
_enforce_security()

# --- 4. NỘI DUNG PAYLOAD MÃ HÓA AES-256 IN-MEMORY ---
{USER_PAYLOAD_EXECUTION}
'''

def prepare_protected_script(
    source_file: str,
    output_temp_file: str,
    app_name: str,
    public_key_path: str = None,
    trial_days: float = 0.0,
    enable_license: bool = True,
    security_level: str = "ultimate",
    enable_anti_debug: bool = True,
    support_config: dict = None,
    project_dir: str = None
) -> str:
    """Tạo file Python hoàn chỉnh đã tiêm đầy đủ các lớp bảo mật AES-256 In-Memory, HWID 2.0, Trial & Anti-Debug."""
    
    anti_debug_path = os.path.join(BASE_DIR, "core", "anti_analysis.py")
    if os.path.exists(anti_debug_path):
        with open(anti_debug_path, "r", encoding="utf-8") as f:
            anti_debug_code = f.read()
    else:
        anti_debug_code = "# Anti-debug module not found"

    license_engine_path = os.path.join(BASE_DIR, "core", "license_engine.py")
    if enable_license and os.path.exists(license_engine_path):
        with open(license_engine_path, "r", encoding="utf-8") as f:
            license_code = f.read()
    else:
        license_code = "# License engine disabled"

    public_key_pem = ""
    if public_key_path and os.path.exists(public_key_path):
        with open(public_key_path, "r", encoding="utf-8") as f:
            public_key_pem = f.read().strip()

    with open(source_file, "r", encoding="utf-8", errors="ignore") as f:
        user_code = f.read()

    if security_level == "ultimate":
        obfuscated_user_code = obfuscate_python_source(user_code, encrypt_strings=True, inject_dead_code=True, add_layer_wrapper=False)
        pkg_b64, salt_b64 = encrypt_user_payload(obfuscated_user_code, hwid_binding="")
        payload_exec_code = build_in_memory_loader_template(pkg_b64, salt_b64, hwid_binding="")
    elif security_level == "advanced":
        payload_exec_code = obfuscate_python_source(user_code, encrypt_strings=True, inject_dead_code=True, add_layer_wrapper=True)
    else:
        payload_exec_code = user_code

    watcher_call = "start_background_watcher(interval_sec=2.0)" if enable_anti_debug else "# Watcher disabled"
    if not enable_anti_debug:
        anti_debug_code = "# Anti-debug disabled"

    if enable_license and public_key_pem:
        license_verification_call = f'''guard = LicenseGuard(
        app_name="{app_name}",
        public_key_pem=EMBEDDED_PUBLIC_KEY_PEM,
        trial_days={trial_days},
        support_config=EMBEDDED_SUPPORT_CONFIG
    )
    guard.verify_and_protect()'''
    else:
        license_verification_call = "# License verification skipped"

    # Trích xuất toàn bộ dependencies của dự án để tạo import hints cho PyInstaller
    _, detected_dotted = extract_project_imports(project_dir, source_file)
    import_hints_lines = []
    for mod in detected_dotted:
        import_hints_lines.append(f"try:\n    import {mod}\nexcept Exception:\n    pass")
    import_hints_code = "\n".join(import_hints_lines) if import_hints_lines else "# No external imports detected"

    supp_json = json.dumps(support_config or {}, ensure_ascii=False)

    wrapped_content = WRAPPER_TEMPLATE.format(
        IMPORT_HINTS_CODE=import_hints_code,
        ANTI_DEBUG_CODE=anti_debug_code,
        LICENSE_ENGINE_CODE=license_code,
        PUBLIC_KEY_PEM=public_key_pem,
        SUPPORT_CONFIG_JSON=supp_json,
        START_WATCHER_CALL=watcher_call,
        LICENSE_VERIFICATION_CALL=license_verification_call,
        USER_PAYLOAD_EXECUTION=payload_exec_code
    )

    with open(output_temp_file, "w", encoding="utf-8") as f:
        f.write(wrapped_content)

    return output_temp_file


def _run_pyinstaller(target_script, output_dir, app_name, work_dir, project_dir, final_ico_path, hide_console, log):
    log("[*] Đang phân tích và đóng gói toàn bộ thư viện với Engine PyInstaller...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        f"--name={app_name}",
        f"--distpath={output_dir}",
        "--clean",
        "--noconfirm"
    ]
    
    sep = ";" if sys.platform == "win32" else ":"

    # Thêm các đường dẫn tìm kiếm mã nguồn
    if project_dir and os.path.exists(project_dir):
        cmd.append(f"--paths={project_dir}")
        src_sub = os.path.join(project_dir, "src")
        if os.path.exists(src_sub):
            cmd.append(f"--paths={src_sub}")
            for sub_r, sub_d, _ in os.walk(src_sub):
                cmd.append(f"--paths={sub_r}")

        # Tự động gom toàn bộ thư mục và tệp tin dự án vào file .EXE qua --add-data (bỏ qua môi trường ảo và tệp rác)
        ignored_names = {'venv', '.venv', 'env', 'node_modules', '.git', '__pycache__', 'build', 'dist', '.agents', '.idea', '.vscode'}
        for item in os.listdir(project_dir):
            if item.startswith(('_temp_wrapped', '.')) or item.endswith(('.spec', '.exe')) or item.lower() in ignored_names:
                continue
            full_item_path = os.path.join(project_dir, item)
            if os.path.isdir(full_item_path):
                cmd.append(f"--add-data={full_item_path}{sep}{item}")
            elif os.path.isfile(full_item_path):
                cmd.append(f"--add-data={full_item_path}{sep}.")
            
    # Tự động quét AST gom trọn gói tất cả các thư viện bên thứ ba
    top_pkgs, dotted_mods = extract_project_imports(project_dir, target_script)
    
    for mod in dotted_mods:
        cmd.append(f"--hidden-import={mod}")
        
    for pkg in top_pkgs:
        cmd.append(f"--collect-all={pkg}")

    if hide_console:
        cmd.append("--noconsole")
    if final_ico_path and os.path.exists(final_ico_path):
        cmd.append(f"--icon={final_ico_path}")
        
    cmd.append(target_script)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='ignore',
        cwd=work_dir,
        creationflags=0x08000000 if sys.platform == "win32" else 0
    )
    for line in iter(proc.stdout.readline, ''):
        if line:
            log(line.rstrip())
    proc.stdout.close()
    return proc.wait()


def build_executable(
    target_script: str,
    output_dir: str,
    app_name: str,
    engine: str = "auto",
    project_dir: str = None,
    icon_path: str = None,
    hide_console: bool = False,
    security_level: str = "ultimate",
    log_callback = None
) -> bool:
    """
    Biên dịch file Python thành file .exe độc lập và xuất trực tiếp vào thư mục chỉ định (output_dir).
    """
    # Chuẩn hóa tên ứng dụng
    app_name = app_name.strip()
    if app_name.lower().endswith('.exe'):
        app_name = app_name[:-4].strip()
    if not app_name:
        app_name = "App"

    os.makedirs(output_dir, exist_ok=True)
    
    def log(text):
        if log_callback:
            log_callback(text)
        else:
            try:
                print(text)
            except Exception:
                pass

    # Tự động đóng tiến trình cũ nếu đang mở để tránh lỗi WinError 32 / WinError 5
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/IM", f"{app_name}.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    # Tự động chuyển đổi ảnh PNG/JPG sang ICO nếu cần
    final_ico_path = None
    if icon_path and os.path.exists(icon_path):
        if icon_path.lower().endswith('.ico'):
            final_ico_path = icon_path
        else:
            log(f"[*] Đang tự động chuyển đổi ảnh [{os.path.basename(icon_path)}] sang định dạng .ICO chuẩn...")
            converted = convert_to_ico(icon_path, target_dir=output_dir)
            if converted and os.path.exists(converted):
                final_ico_path = converted
                log(f"[✓] Đã tạo file Icon thành công: {converted}")

    log(f"[*] Cấp độ bảo vệ: {security_level.upper()} (AES-256 In-Memory Decryption)")
    log(f"[*] Thư mục xuất file .EXE đích: {os.path.abspath(output_dir)}")
    
    work_dir = project_dir if (project_dir and os.path.exists(project_dir)) else os.path.dirname(os.path.abspath(target_script))

    # Xử lý Engine
    is_py314 = (sys.version_info.major == 3 and sys.version_info.minor >= 14)
    chosen_engine = engine.lower()

    success = False

    # Nếu người dùng chọn Nuitka (khi không phải Python 3.14)
    if chosen_engine == "nuitka" and not is_py314:
        log("[*] Đang chuẩn bị biên dịch với Engine: NUITKA Native C++...")
        cmd = [
            sys.executable, "-m", "nuitka",
            "--standalone",
            "--onefile",
            f"--output-dir={output_dir}",
            f"--output-filename={app_name}.exe",
            "--assume-yes-for-downloads",
            "--python-flag=no_docstrings,no_asserts"
        ]
        if security_level == "ultimate":
            cmd.append("--lto=yes")
        if hide_console:
            cmd.append("--windows-disable-console")
        if final_ico_path and os.path.exists(final_ico_path):
            cmd.append(f"--windows-icon-from-ico={final_ico_path}")
        cmd.append(target_script)

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore',
                cwd=work_dir,
                creationflags=0x08000000 if sys.platform == "win32" else 0
            )
            for line in iter(proc.stdout.readline, ''):
                if line:
                    log(line.rstrip())
            proc.stdout.close()
            ret = proc.wait()
            if ret == 0:
                success = True
        except Exception as e:
            log(f"[!] Nuitka gặp lỗi: {e}")

    # Nếu đang dùng Python 3.14 hoặc chế độ Auto -> Dùng PyInstaller siêu tốc gom trọn gói
    if not success:
        if is_py314:
            log("[*] Môi trường Python 3.14: Đang kích hoạt Engine PyInstaller gom đầy đủ tất cả thư viện...")
        else:
            log("[*] Đang tự động chuyển sang Engine PyInstaller...")
            
        ret = _run_pyinstaller(target_script, output_dir, app_name, work_dir, project_dir, final_ico_path, hide_console, log)
        if ret == 0:
            success = True

    if success:
        if project_dir and os.path.isdir(project_dir):
            log("[*] Đang sao chép các tệp tài nguyên phụ trợ sang thư mục xuất...")
            for root_p, dirs, files in os.walk(project_dir):
                dirs[:] = [d for d in dirs if not d.startswith(('.', '__', 'build', 'dist')) and d.lower() not in ('venv', '.venv', 'env', 'node_modules', '.git', '.idea', '.vscode')]
                rel_dir = os.path.relpath(root_p, project_dir)
                dest_sub = output_dir if rel_dir == "." else os.path.join(output_dir, rel_dir)
                for f_name in files:
                    if not f_name.endswith(('.py', '.pyc', '.pyo')) and not f_name.startswith('_temp_wrapped'):
                        src_f = os.path.join(root_p, f_name)
                        os.makedirs(dest_sub, exist_ok=True)
                        dst_f = os.path.join(dest_sub, f_name)
                        try:
                            shutil.copy2(src_f, dst_f)
                        except Exception:
                            pass

        log("\n" + "="*55)
        log(f"🎉 BIÊN DỊCH & ĐÓNG GÓI THÀNH CÔNG!")
        log(f"📁 File .EXE đã sẵn sàng tại: {os.path.abspath(output_dir)}")
        log("="*55)
        return True
    else:
        log("\n❌ Đóng gói thất bại.")
        return False
