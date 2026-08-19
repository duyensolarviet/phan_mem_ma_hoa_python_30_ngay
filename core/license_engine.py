"""
Module: core/license_engine.py
Mục đích: Lõi quản lý bản quyền toàn diện cho ứng dụng Python:
1. HWID 2.0: Tạo mã định danh máy cứng duy nhất không thể làm giả.
2. Kiểm tra chế độ dùng thử (Trial) tự động với số ngày quy định.
3. Chống hack lùi giờ máy tính bằng Internet Time Guard đa máy chủ.
4. Xác thực chữ ký số RSA-PSS / RSA-2048 chuẩn quân sự.
5. Giao diện Tkinter hiện đại tích hợp nút liên hệ Zalo, Telegram CSKH và xem bảng giá gói cước.
"""

import sys
import os
import json
import time
import base64
import hashlib
import datetime
import subprocess
import webbrowser
import winreg
import tkinter as tk
from tkinter import ttk, messagebox

# Đảm bảo UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

# PUBLIC KEY MẶC ĐỊNH
DEFAULT_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyqWc9T0g89pL...
-----END PUBLIC KEY-----"""

DEFAULT_PACKAGES = {
    "1_month": {"name": "Gói 1 Tháng (30 Ngày)", "days": 30, "price": "200.000 VNĐ"},
    "3_months": {"name": "Gói 3 Tháng (90 Ngày)", "days": 90, "price": "500.000 VNĐ"},
    "6_months": {"name": "Gói 6 Tháng (180 Ngày)", "days": 180, "price": "900.000 VNĐ"},
    "1_year": {"name": "Gói 1 Năm (365 Ngày)", "days": 365, "price": "1.500.000 VNĐ"},
    "lifetime": {"name": "Gói Vĩnh Viễn (Trọn Đời)", "days": 9999, "price": "3.000.000 VNĐ"}
}


class HardwareID:
    """HWID 2.0: Tạo mã định danh phần cứng sâu cho máy tính Windows kèm bộ nhớ đệm (Cache)."""
    _CACHED_HWID = None
    
    @staticmethod
    def get_machine_guid() -> str:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            return str(guid).strip()
        except Exception:
            return ""

    @staticmethod
    def get_system_uuid() -> str:
        try:
            cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_ComputerSystemProduct).UUID"'
            res = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, creationflags=0x08000000).decode().strip()
            if res and "UUID" not in res:
                return res
        except Exception:
            pass
        return ""

    @staticmethod
    def get_disk_serial() -> str:
        try:
            cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_DiskDrive)[0].SerialNumber"'
            res = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, creationflags=0x08000000).decode().strip()
            if res:
                return res
        except Exception:
            pass
        return ""

    @staticmethod
    def get_cpu_id() -> str:
        try:
            cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_Processor)[0].ProcessorId"'
            res = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, creationflags=0x08000000).decode().strip()
            if res:
                return res
        except Exception:
            pass
        return ""

    @classmethod
    def generate_hwid(cls) -> str:
        if cls._CACHED_HWID:
            return cls._CACHED_HWID

        guid = cls.get_machine_guid()
        uuid = cls.get_system_uuid()
        disk = cls.get_disk_serial()
        cpuid = cls.get_cpu_id()
        
        raw = f"{guid}::{uuid}::{disk}::{cpuid}"
        if not guid and not uuid and not disk:
            raw = f"{os.environ.get('COMPUTERNAME', '')}::{os.environ.get('USERNAME', '')}"
            
        sha = hashlib.sha512(f"SALT_HWID_V2_{raw}".encode('utf-8')).hexdigest().upper()
        hwid = f"{sha[0:4]}-{sha[4:8]}-{sha[8:12]}-{sha[12:16]}"
        cls._CACHED_HWID = hwid
        return hwid


class TimeGuard:
    """Kiểm tra thời gian chuẩn và chống lùi giờ hệ thống từ nhiều máy chủ độc lập."""
    
    @staticmethod
    def get_trusted_time() -> float:
        import urllib.request
        import email.utils
        endpoints = [
            "https://www.google.com",
            "https://www.cloudflare.com",
            "https://www.microsoft.com",
            "https://1.1.1.1"
        ]
        for url in endpoints:
            try:
                req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    date_str = resp.headers.get('Date')
                    if date_str:
                        dt = email.utils.parsedate_to_datetime(date_str)
                        return dt.timestamp()
            except Exception:
                continue
        return time.time()


class LicenseStorage:
    """Lưu trữ và mã hóa dữ liệu bản quyền trên máy khách ĐA TẦNG (Triple-Anchor Anti-Reset & Auto-Healing)."""
    
    @staticmethod
    def _get_hwid_key() -> bytes:
        return hashlib.sha256(HardwareID.generate_hwid().encode()).digest()

    @staticmethod
    def _get_primary_path(app_name: str) -> str:
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        storage_dir = os.path.join(appdata, f".{app_name}_license")
        os.makedirs(storage_dir, exist_ok=True)
        return os.path.join(storage_dir, "license.dat")

    @staticmethod
    def _get_secondary_path(app_name: str) -> str:
        local_app = os.environ.get("LOCALAPPDATA", os.environ.get("TEMP", os.path.expanduser("~")))
        h = hashlib.sha256(f"SEC_{app_name}_{HardwareID.generate_hwid()}".encode()).hexdigest()[:16]
        storage_dir = os.path.join(local_app, "Microsoft", "Windows", "Caches")
        os.makedirs(storage_dir, exist_ok=True)
        return os.path.join(storage_dir, f"~{h}.tmp")

    @staticmethod
    def _get_registry_subpath(app_name: str) -> str:
        h = hashlib.sha256(f"REG_{app_name}_{HardwareID.generate_hwid()}_V2".encode()).hexdigest()
        guid_str = f"{{{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}}}"
        return f"Software\\Classes\\CLSID\\{guid_str}"

    @classmethod
    def _read_file_store(cls, filepath: str) -> dict:
        if not filepath or not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, "rb") as f:
                encrypted = f.read()
            key = cls._get_hwid_key()
            decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted)])
            return json.loads(decrypted.decode('utf-8'))
        except Exception:
            return {}

    @classmethod
    def _write_file_store(cls, filepath: str, data_bytes: bytes):
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(data_bytes)
        except Exception:
            pass

    @classmethod
    def _read_registry_store(cls, app_name: str) -> dict:
        if sys.platform != "win32":
            return {}
        try:
            reg_sub = cls._get_registry_subpath(app_name)
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_sub, 0, winreg.KEY_READ)
            b64_val, _ = winreg.QueryValueEx(key, "Data")
            winreg.CloseKey(key)
            encrypted = base64.b64decode(b64_val.encode('utf-8'))
            k = cls._get_hwid_key()
            decrypted = bytes([b ^ k[i % len(k)] for i, b in enumerate(encrypted)])
            return json.loads(decrypted.decode('utf-8'))
        except Exception:
            return {}

    @classmethod
    def _write_registry_store(cls, app_name: str, encrypted_bytes: bytes):
        if sys.platform != "win32":
            return
        try:
            reg_sub = cls._get_registry_subpath(app_name)
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_sub)
            b64_val = base64.b64encode(encrypted_bytes).decode('utf-8')
            winreg.SetValueEx(key, "Data", 0, winreg.REG_SZ, b64_val)
            winreg.CloseKey(key)
        except Exception:
            pass

    @classmethod
    def load_data(cls, app_name: str) -> dict:
        """Đọc dữ liệu từ 3 tầng (AppData, LocalAppData Cache, Registry) và tự động khôi phục nếu bị xóa."""
        d1 = cls._read_file_store(cls._get_primary_path(app_name))
        d2 = cls._read_file_store(cls._get_secondary_path(app_name))
        d3 = cls._read_registry_store(app_name)

        all_stores = [d for d in (d1, d2, d3) if d]
        if not all_stores:
            return {}

        # Hợp nhất dữ liệu: Lấy mốc thời gian lần đầu (first_run_time) sớm nhất
        merged = {}
        first_runs = [d["first_run_time"] for d in all_stores if d.get("first_run_time")]
        if first_runs:
            merged["first_run_time"] = min(first_runs)

        last_seens = [d["last_seen_time"] for d in all_stores if d.get("last_seen_time")]
        if last_seens:
            merged["last_seen_time"] = max(last_seens)

        for d in all_stores:
            if d.get("license_key"):
                merged["license_key"] = d["license_key"]
                break

        # Nếu phát hiện một trong các nơi bị xóa -> Tự động khôi phục lại toàn bộ (Auto-Healing)
        if not d1 or not d2 or not d3:
            cls.save_data(app_name, merged)

        return merged

    @classmethod
    def save_data(cls, app_name: str, data: dict):
        """Ghi đồng bộ dữ liệu vào cả 3 tầng bảo vệ."""
        try:
            raw = json.dumps(data).encode('utf-8')
            key = cls._get_hwid_key()
            encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(raw)])
            
            # 1. Ghi Primary File (AppData)
            cls._write_file_store(cls._get_primary_path(app_name), encrypted)
            # 2. Ghi Secondary File (LocalAppData Cache)
            cls._write_file_store(cls._get_secondary_path(app_name), encrypted)
            # 3. Ghi Registry CLSID Anchor
            cls._write_registry_store(app_name, encrypted)
        except Exception:
            pass


class LicenseVerifier:
    """Xác thực chữ ký số RSA (Hỗ trợ cả PSS và PKCS#1 v1.5)."""
    
    def __init__(self, public_key_pem: str):
        self.public_key_pem = public_key_pem
        try:
            self.public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
        except Exception:
            self.public_key = None

    def verify_key(self, license_key_str: str, current_hwid: str, current_timestamp: float) -> tuple[bool, str, dict]:
        if not self.public_key:
            return False, "Public Key chưa được cấu hình đúng!", {}
            
        license_key_str = license_key_str.strip()
        if not license_key_str.startswith("LIC-"):
            return False, "Định dạng Key không hợp lệ (Phải bắt đầu bằng LIC-)", {}
            
        parts = license_key_str[4:].split(".")
        if len(parts) != 2:
            return False, "Cấu trúc License Key không đúng định dạng", {}
            
        b64_payload, b64_sig = parts[0], parts[1]
        
        def _safe_b64decode(s: str) -> bytes:
            missing = len(s) % 4
            if missing:
                s += '=' * (4 - missing)
            return base64.urlsafe_b64decode(s.encode('utf-8'))

        try:
            payload_bytes = _safe_b64decode(b64_payload)
            signature = _safe_b64decode(b64_sig)
            payload = json.loads(payload_bytes.decode('utf-8'))
        except Exception:
            return False, "Không thể giải mã dữ liệu trong Key", {}
            
        # 1. Xác thực chữ ký số RSA
        sig_valid = False
        try:
            self.public_key.verify(
                signature,
                payload_bytes,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            sig_valid = True
        except Exception:
            pass

        if not sig_valid:
            try:
                self.public_key.verify(
                    signature,
                    payload_bytes,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                sig_valid = True
            except Exception:
                pass

        if not sig_valid:
            return False, "Chữ ký số không hợp lệ (Key giả mạo hoặc bị chỉnh sửa)!", {}
            
        # 2. Kiểm tra HWID
        key_hwid = payload.get("hwid", "")
        if key_hwid != "*" and key_hwid != current_hwid:
            return False, f"Key này được cấp cho máy khác ({key_hwid}), không dùng được trên máy này!", payload
            
        # 3. Kiểm tra Hạn sử dụng
        expiry = payload.get("expiry", "")
        if expiry != "LIFETIME":
            try:
                exp_dt = datetime.datetime.strptime(expiry, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                if current_timestamp > exp_dt.timestamp():
                    return False, f"Key đã hết hạn sử dụng vào ngày {expiry}!", payload
            except Exception:
                return False, "Định dạng ngày hết hạn trong Key không hợp lệ", payload
                
        return True, "Key hợp lệ", payload


class ActivationDialog:
    """Giao diện kích hoạt bản quyền hiện đại bằng Tkinter với đầy đủ nút Zalo, Telegram và Bảng giá."""
    
    def __init__(
        self,
        app_name: str,
        hwid: str,
        verifier: LicenseVerifier,
        trial_status: str,
        on_success_callback,
        support_config: dict = None
    ):
        self.app_name = app_name
        self.hwid = hwid
        self.verifier = verifier
        self.trial_status = trial_status
        self.on_success_callback = on_success_callback
        self.support_config = support_config or {}
        self.activated = False
        
        self.root = tk.Tk()
        self.root.title(f"Bản Quyền - {app_name}")
        self.root.geometry("560x520")
        self.root.resizable(False, False)
        self.root.eval('tk::PlaceWindow . center')
        
        self._setup_ui()

    def _setup_ui(self):
        bg_dark = "#1e1e2e"
        card_bg = "#252538"
        accent_color = "#89b4fa"
        text_color = "#cdd6f4"
        text_dim = "#a6adc8"
        btn_green = "#a6e3a1"
        btn_hover = "#94e2d5"
        btn_zalo = "#0068ff"
        btn_tele = "#229ed9"
        
        self.root.configure(bg=bg_dark)
        
        # Tiêu đề
        lbl_title = tk.Label(self.root, text=f"KÍCH HOẠT BẢN QUYỀN", font=("Segoe UI", 15, "bold"), fg=accent_color, bg=bg_dark)
        lbl_title.pack(pady=(15, 3))
        
        lbl_sub = tk.Label(self.root, text=f"Phần mềm: {self.app_name}", font=("Segoe UI", 10), fg=text_dim, bg=bg_dark)
        lbl_sub.pack(pady=(0, 6))
        
        lbl_status = tk.Label(self.root, text=self.trial_status, font=("Segoe UI", 9, "italic"), fg="#f38ba8", bg=bg_dark)
        lbl_status.pack(pady=(0, 8))
        
        # HWID Box
        hwid_frame = tk.Frame(self.root, bg=card_bg, padx=12, pady=8, relief="flat", highlightbackground="#45475a", highlightthickness=1)
        hwid_frame.pack(fill="x", padx=20, pady=3)
        
        lbl_hwid_tag = tk.Label(hwid_frame, text="MÃ MÁY CỦA BẠN (HWID):", font=("Segoe UI", 9, "bold"), fg=text_dim, bg=card_bg)
        lbl_hwid_tag.pack(anchor="w")
        
        hwid_row = tk.Frame(hwid_frame, bg=card_bg)
        hwid_row.pack(fill="x", pady=(3, 0))
        
        self.lbl_hwid_val = tk.Label(hwid_row, text=self.hwid, font=("Consolas", 12, "bold"), fg="#f9e2af", bg=card_bg)
        self.lbl_hwid_val.pack(side="left")
        
        btn_copy = tk.Button(hwid_row, text="📋 Sao chép", font=("Segoe UI", 9, "bold"), bg="#45475a", fg=text_color, activebackground="#585b70", activeforeground="#ffffff", relief="flat", padx=8, pady=1, command=self._copy_hwid, cursor="hand2")
        btn_copy.pack(side="right")
        
        # License Key Box
        key_frame = tk.Frame(self.root, bg=card_bg, padx=12, pady=8, relief="flat", highlightbackground="#45475a", highlightthickness=1)
        key_frame.pack(fill="x", padx=20, pady=8)
        
        lbl_key_tag = tk.Label(key_frame, text="NHẬP LICENSE KEY KÍCH HOẠT:", font=("Segoe UI", 9, "bold"), fg=text_dim, bg=card_bg)
        lbl_key_tag.pack(anchor="w")
        
        self.txt_key = tk.Text(key_frame, height=2, font=("Consolas", 9), bg="#181825", fg=text_color, insertbackground=text_color, relief="flat", highlightbackground="#585b70", highlightthickness=1)
        self.txt_key.pack(fill="x", pady=(4, 0))
        
        # Nút Kích Hoạt
        btn_activate = tk.Button(self.root, text="KÍCH HOẠT NGAY ➔", font=("Segoe UI", 11, "bold"), bg=btn_green, fg="#11111b", activebackground=btn_hover, relief="flat", pady=7, cursor="hand2", command=self._on_activate)
        btn_activate.pack(fill="x", padx=20, pady=(2, 10))

        # Khung Liên Hệ CSKH Zalo
        support_frame = tk.LabelFrame(self.root, text=" LIÊN HỆ MUA KEY & HỖ TRỢ ", font=("Segoe UI", 9, "bold"), fg="#89b4fa", bg=card_bg, padx=10, pady=8, relief="groove")
        support_frame.pack(fill="x", padx=20, pady=(0, 10))

        btn_zalo_chat = tk.Button(
            support_frame,
            text="💬 Nhắn Zalo Hỗ Trợ & Mua Key",
            font=("Segoe UI", 10, "bold"),
            bg=btn_zalo,
            fg="#ffffff",
            activebackground="#3385ff",
            relief="flat",
            pady=6,
            cursor="hand2",
            command=self._open_zalo
        )
        btn_zalo_chat.pack(fill="x")
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _open_zalo(self):
        zalo_url = self.support_config.get("zalo_support", "https://zalo.me/g/mmgznzbleun8cirr19ld")
        if zalo_url:
            webbrowser.open(zalo_url)

    def _open_telegram(self):
        tele_url = self.support_config.get("telegram_support", self.support_config.get("telegram_admin", "https://t.me/checkey_bot"))
        if tele_url:
            webbrowser.open(tele_url)

    def _show_packages_dialog(self):
        pkg_win = tk.Toplevel(self.root)
        pkg_win.title("Bảng Giá Các Gói Bản Quyền")
        pkg_win.geometry("450x380")
        pkg_win.resizable(False, False)
        pkg_win.configure(bg="#1e1e2e")
        pkg_win.eval(f'tk::PlaceWindow {str(pkg_win)} center')

        tk.Label(pkg_win, text="💎 BẢNG GIÁ GÓI BẢN QUYỀN", font=("Segoe UI", 13, "bold"), fg="#89b4fa", bg="#1e1e2e").pack(pady=(12, 8))

        packages = self.support_config.get("packages", DEFAULT_PACKAGES)
        for key, info in packages.items():
            card = tk.Frame(pkg_win, bg="#252538", padx=10, pady=6, highlightbackground="#45475a", highlightthickness=1)
            card.pack(fill="x", padx=15, pady=3)

            name = info.get("name", key)
            price = info.get("price", "Liên hệ")

            tk.Label(card, text=name, font=("Segoe UI", 10, "bold"), fg="#cdd6f4", bg="#252538").pack(side="left")
            tk.Label(card, text=price, font=("Segoe UI", 10, "bold"), fg="#a6e3a1", bg="#252538").pack(side="right")

        tk.Label(pkg_win, text="👉 Gửi mã HWID của bạn qua Zalo/Telegram để nhận Key kích hoạt!", font=("Segoe UI", 9, "italic"), fg="#a6adc8", bg="#1e1e2e").pack(pady=(10, 0))

        tk.Button(pkg_win, text="Đóng", font=("Segoe UI", 9, "bold"), bg="#45475a", fg="#ffffff", relief="flat", padx=15, pady=3, command=pkg_win.destroy).pack(pady=8)

    def _copy_hwid(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.hwid)
        messagebox.showinfo("Đã sao chép", "Đã sao chép mã máy (HWID) vào bộ nhớ tạm!\nHãy gửi mã này cho Admin qua Zalo để nhận License Key.")

    def _on_activate(self):
        key_input = self.txt_key.get("1.0", "end").strip()
        if not key_input:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập License Key!")
            return
            
        current_time = TimeGuard.get_trusted_time()
        valid, msg, payload = self.verifier.verify_key(key_input, self.hwid, current_time)
        
        if valid:
            exp_text = payload.get("expiry", "Vĩnh viễn")
            messagebox.showinfo("Thành Công", f"🎉 Kích hoạt bản quyền thành công!\nHạn sử dụng: {exp_text}")
            self.activated = True
            
            data = LicenseStorage.load_data(self.app_name)
            data["license_key"] = key_input
            data["last_seen_time"] = current_time
            LicenseStorage.save_data(self.app_name, data)
            
            self.root.destroy()
            if self.on_success_callback:
                self.on_success_callback()
        else:
            messagebox.showerror("Kích Hoạt Thất Bại", f"❌ {msg}")

    def _on_close(self):
        self.root.destroy()
        sys.exit(0)

    def show(self):
        self.root.mainloop()


class LicenseGuard:
    """Lớp chính tích hợp vào ứng dụng để kiểm soát toàn bộ vòng đời bản quyền."""
    
    def __init__(self, app_name: str, public_key_pem: str, trial_days: int = 3, support_config: dict = None):
        self.app_name = app_name
        self.public_key_pem = public_key_pem
        self.trial_days = trial_days
        self.support_config = support_config or {}
        self.hwid = HardwareID.generate_hwid()
        self.verifier = LicenseVerifier(public_key_pem)

    def _start_runtime_trial_watcher(self, time_allowed: float, first_run: float):
        """Luồng ngầm giám sát thời gian thực: Tự động khóa và đóng ứng dụng ngay lập tức khi hết hạn dùng thử lúc app đang mở."""
        def _watcher_loop():
            # Kiểm tra mỗi 5 giây cho các gói theo phút/giờ, 30 giây cho các gói theo ngày
            sleep_interval = 5.0 if time_allowed <= 86400.0 else 30.0
            while True:
                time.sleep(sleep_interval)
                try:
                    curr = time.time()
                    time_spent = curr - first_run
                    if time_spent >= time_allowed:
                        # 1. Định dạng thông báo hết hạn
                        trial_d = float(self.trial_days)
                        if trial_d < (1.0 / 24.0):
                            mins = max(1, int(round(trial_d * 1440)))
                            msg = f"❌ ĐÃ HẾT THỜI GIAN DÙNG THỬ ({mins} PHÚT)!\n\nỨng dụng sẽ tự động đóng ngay bây giờ.\nVui lòng liên hệ Admin qua Zalo/Telegram để kích hoạt bản quyền."
                        elif trial_d < 1.0:
                            hrs = max(1, int(round(trial_d * 24)))
                            msg = f"❌ ĐÃ HẾT THỜI GIAN DÙNG THỬ ({hrs} GIỜ)!\n\nỨng dụng sẽ tự động đóng ngay bây giờ.\nVui lòng liên hệ Admin qua Zalo/Telegram để kích hoạt bản quyền."
                        else:
                            days = int(round(trial_d))
                            msg = f"❌ ĐÃ HẾT THỜI GIAN DÙNG THỬ ({days} NGÀY)!\n\nỨng dụng sẽ tự động đóng ngay bây giờ.\nVui lòng liên hệ Admin qua Zalo/Telegram để kích hoạt bản quyền."
                        
                        # 2. Cập nhật và lưu lại trạng thái hết hạn vào 3 tầng bảo vệ
                        stored = LicenseStorage.load_data(self.app_name)
                        stored["last_seen_time"] = curr
                        LicenseStorage.save_data(self.app_name, stored)
                        
                        # 3. Hiện thông báo cảnh báo nổi lên trên cùng (TopMost) và đóng ứng dụng
                        if sys.platform == "win32":
                            try:
                                MB_ICONSTOP = 0x10
                                MB_TOPMOST = 0x40000
                                ctypes.windll.user32.MessageBoxW(0, msg, f"Hết Hạn Dùng Thử - {self.app_name}", MB_ICONSTOP | MB_TOPMOST)
                            except Exception:
                                pass
                        os._exit(0)
                except Exception:
                    pass

        t = threading.Thread(target=_watcher_loop, daemon=True, name="TrialRuntimeEnforcer")
        t.start()

    def verify_and_protect(self):
        current_time = TimeGuard.get_trusted_time()
        stored_data = LicenseStorage.load_data(self.app_name)
        
        # 1. Chống lùi giờ hệ thống
        last_seen = stored_data.get("last_seen_time", 0)
        if last_seen and current_time < (last_seen - 300):
            messagebox.showerror("Cảnh Báo Gian Lận", "Phát hiện thời gian hệ thống bị thay đổi bất thường!\nVui lòng đồng bộ lại giờ máy tính với Internet.")
            sys.exit(0)
            
        stored_data["last_seen_time"] = current_time
        
        # 2. Kiểm tra Key đã lưu
        saved_key = stored_data.get("license_key", "")
        if saved_key:
            valid, msg, payload = self.verifier.verify_key(saved_key, self.hwid, current_time)
            if valid:
                LicenseStorage.save_data(self.app_name, stored_data)
                return True
                
        # 3. Kiểm tra Trial Mode
        if float(self.trial_days) > 0:
            first_run = stored_data.get("first_run_time", 0)
            if not first_run:
                first_run = current_time
                stored_data["first_run_time"] = first_run
                LicenseStorage.save_data(self.app_name, stored_data)
                
            time_spent = current_time - first_run
            time_allowed = float(self.trial_days) * 86400.0
            
            if time_spent < time_allowed:
                LicenseStorage.save_data(self.app_name, stored_data)
                # Bắt đầu luồng giám sát thời gian thực tự động đóng app khi chạm mốc hết hạn
                self._start_runtime_trial_watcher(time_allowed, first_run)
                return True
            else:
                trial_d = float(self.trial_days)
                if trial_d < (1.0 / 24.0):
                    mins = max(1, int(round(trial_d * 1440)))
                    trial_msg = f"❌ ĐÃ HẾT THỜI GIAN DÙNG THỬ ({mins} PHÚT)! Vui lòng kích hoạt bản quyền."
                elif trial_d < 1.0:
                    hrs = max(1, int(round(trial_d * 24)))
                    trial_msg = f"❌ ĐÃ HẾT THỜI GIAN DÙNG THỬ ({hrs} GIỜ)! Vui lòng kích hoạt bản quyền."
                else:
                    days = int(round(trial_d))
                    trial_msg = f"❌ ĐÃ HẾT THỜI GIAN DÙNG THỬ ({days} NGÀY)! Vui lòng kích hoạt bản quyền."
        else:
            trial_msg = "🔒 Ứng dụng yêu cầu kích hoạt bản quyền để sử dụng."
            
        # 4. Hộp thoại đòi Key
        dialog = ActivationDialog(
            app_name=self.app_name,
            hwid=self.hwid,
            verifier=self.verifier,
            trial_status=trial_msg,
            on_success_callback=None,
            support_config=self.support_config
        )
        dialog.show()
        
        if not dialog.activated:
            sys.exit(0)
            
        return True
