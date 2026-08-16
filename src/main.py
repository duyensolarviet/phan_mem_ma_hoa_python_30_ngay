"""
Entrypoint: src/main.py
Mục đích: PYTHON ULTIMATE PROTECTOR & NATIVE .EXE BUILDER
Tập trung 100% vào:
- Mã hóa Python Đỉnh Cao (AES-256 In-Memory Decryption + Obfuscation + Anti-Debug Daemon).
- Đóng gói toàn bộ Thư Mục Dự Án thành file .EXE độc lập duy nhất.
- Tự động gom 100% dependencies (selenium, undetected_chromedriver, customtkinter, google, groq...).
- Tự động chuyển đổi logo PNG/JPG sang ICO chuẩn Windows.
- Khóa bản quyền HWID 2.0 RSA-PSS & Hạn dùng thử linh hoạt (Phút/Giờ/Ngày) & Zalo CSKH.
"""

import sys
import os
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Thiết lập UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from builder.pack_engine import prepare_protected_script, build_executable

CONFIG_FILE = os.path.join(BASE_DIR, "builder_config.json")

def find_candidate_py_files(folder: str) -> list[str]:
    """Tìm tất cả các file .py trong thư mục dự án để làm entrypoint."""
    if not folder or not os.path.exists(folder):
        return []
    py_files = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith(('.', '__', 'build', 'dist'))]
        for f in files:
            if f.endswith('.py') and not f.startswith(('_temp_wrapped', '.')):
                rel_p = os.path.relpath(os.path.join(root, f), folder)
                py_files.append(rel_p)
    # Ưu tiên các file chính
    priority = ["src/main.py", "src\\main.py", "main.py", "app.py", "src/app.py", "gui.py", "run.py"]
    py_files.sort(key=lambda x: (0 if x in priority else 1, x))
    return py_files


class UltimateBuilderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🛡️ PYTHON ULTIMATE PROTECTOR & .EXE BUILDER")
        self.root.geometry("820x760")
        self.root.minsize(780, 680)
        self.root.eval('tk::PlaceWindow . center')

        self.bg_dark = "#11111b"
        self.card_bg = "#181825"
        self.card_inner = "#1e1e2e"
        self.accent = "#89b4fa"
        self.text_color = "#cdd6f4"
        self.text_dim = "#a6adc8"
        self.btn_green = "#a6e3a1"
        self.btn_purple = "#cba6f7"
        self.btn_yellow = "#f9e2af"

        self.root.configure(bg=self.bg_dark)
        self.saved_cfg = self._load_config()
        self.public_key_path = os.path.join(BASE_DIR, "keys", "public_key.pem")
        self.is_building = False

        self._setup_ui()

    def _load_config(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                import json
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_config(self):
        import json
        cfg = {
            "last_project_dir": self.ent_project_dir.get().strip(),
            "last_output_dir": self.ent_output_dir.get().strip(),
            "last_app_name": self.ent_app_name.get().strip(),
            "last_icon": self.ent_ico.get().strip(),
            "zalo_support": self.ent_zalo.get().strip(),
            "enable_license": self.var_enable_license.get(),
            "enable_trial": self.var_auto_trial.get(),
            "trial_val": self.spn_trial.get().strip(),
            "trial_unit": self.cbo_trial_unit.get().strip(),
            "hide_console": self.var_hide_console.get(),
            "anti_debug": self.var_anti_debug.get()
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _setup_ui(self):
        # 1. Header
        header = tk.Frame(self.root, bg=self.card_bg, pady=12, highlightbackground="#313244", highlightthickness=1)
        header.pack(fill="x")

        lbl_title = tk.Label(header, text="🛡️ PYTHON ULTIMATE PROTECTOR & .EXE BUILDER", font=("Segoe UI", 16, "bold"), fg=self.accent, bg=self.card_bg)
        lbl_title.pack()

        lbl_sub = tk.Label(header, text="Mã Hóa AES-256 In-Memory • Khóa Bản Quyền HWID 2.0 • Dùng Thử (Phút/Giờ/Ngày) • Đóng Gói .EXE Siêu Tốc", font=("Segoe UI", 9), fg=self.text_dim, bg=self.card_bg)
        lbl_sub.pack(pady=(2, 0))

        # Main Body
        body = tk.Frame(self.root, bg=self.bg_dark, padx=16, pady=8)
        body.pack(fill="both", expand=True)

        # KHUNG 1: THƯ MỤC DỰ ÁN & THƯ MỤC XUẤT
        box_src = tk.LabelFrame(body, text=" 1. 📂 CẤU HÌNH DỰ ÁN & ĐẦU RA .EXE ", font=("Segoe UI", 9, "bold"), fg=self.accent, bg=self.card_inner, padx=12, pady=8, relief="groove")
        box_src.pack(fill="x", pady=(0, 6))

        # Dòng 1: Thư mục dự án
        row_proj = tk.Frame(box_src, bg=self.card_inner)
        row_proj.pack(fill="x", pady=(0, 4))
        tk.Label(row_proj, text="Thư mục Dự Án:", font=("Segoe UI", 9, "bold"), fg=self.btn_yellow, bg=self.card_inner, width=17, anchor="w").pack(side="left")
        
        self.ent_project_dir = tk.Entry(row_proj, font=("Segoe UI", 10), bg="#11111b", fg=self.text_color, insertbackground=self.text_color, relief="flat", highlightbackground="#45475a", highlightthickness=1)
        self.ent_project_dir.insert(0, self.saved_cfg.get("last_project_dir", r"E:\tesdangbaitatca"))
        self.ent_project_dir.pack(side="left", fill="x", expand=True, ipady=2)
        
        tk.Button(row_proj, text="📂 Chọn Thư Mục", font=("Segoe UI", 9, "bold"), bg=self.accent, fg="#11111b", activebackground="#b4befe", relief="flat", padx=8, command=self._browse_project_dir, cursor="hand2").pack(side="left", padx=(6, 2))
        tk.Button(row_proj, text="📄 File Lẻ", font=("Segoe UI", 9), bg="#313244", fg=self.text_color, activebackground="#45475a", relief="flat", padx=6, command=self._browse_single_file, cursor="hand2").pack(side="left")

        # Dòng 2: File Khởi Động
        row_entry = tk.Frame(box_src, bg=self.card_inner)
        row_entry.pack(fill="x", pady=(0, 4))
        tk.Label(row_entry, text="File Khởi Động:", font=("Segoe UI", 9), fg=self.text_dim, bg=self.card_inner, width=17, anchor="w").pack(side="left")
        
        self.cbo_entrypoint = ttk.Combobox(row_entry, font=("Segoe UI", 10), state="normal")
        self.cbo_entrypoint.pack(side="left", fill="x", expand=True)
        tk.Label(row_entry, text="⚡ (Tự động nhận diện file chính)", font=("Segoe UI", 8, "italic"), fg=self.btn_green, bg=self.card_inner).pack(side="left", padx=(6, 0))

        # Dòng 3: Thư mục Xuất
        row_out = tk.Frame(box_src, bg=self.card_inner)
        row_out.pack(fill="x", pady=(0, 4))
        tk.Label(row_out, text="Thư mục Xuất .EXE:", font=("Segoe UI", 9, "bold"), fg=self.btn_green, bg=self.card_inner, width=17, anchor="w").pack(side="left")
        
        self.ent_output_dir = tk.Entry(row_out, font=("Segoe UI", 10), bg="#11111b", fg=self.btn_green, insertbackground=self.text_color, relief="flat", highlightbackground="#45475a", highlightthickness=1)
        self.ent_output_dir.insert(0, self.saved_cfg.get("last_output_dir", r"E:\thutestallinomahoa"))
        self.ent_output_dir.pack(side="left", fill="x", expand=True, ipady=2)
        
        tk.Button(row_out, text="📁 Nơi Xuất", font=("Segoe UI", 9, "bold"), bg=self.btn_green, fg="#11111b", activebackground="#94e2d5", relief="flat", padx=8, command=self._browse_output_dir, cursor="hand2").pack(side="left", padx=(6, 2))
        tk.Button(row_out, text="📂 Mở Thư Mục", font=("Segoe UI", 9), bg="#313244", fg=self.text_color, activebackground="#45475a", relief="flat", padx=6, command=self._open_output_dir, cursor="hand2").pack(side="left")

        # Dòng 4: Tên file & Logo
        row_ico = tk.Frame(box_src, bg=self.card_inner)
        row_ico.pack(fill="x")
        tk.Label(row_ico, text="Tên File .EXE:", font=("Segoe UI", 9, "bold"), fg=self.btn_yellow, bg=self.card_inner, width=17, anchor="w").pack(side="left")
        
        self.ent_app_name = tk.Entry(row_ico, font=("Segoe UI", 10, "bold"), bg="#11111b", fg=self.btn_yellow, insertbackground=self.text_color, relief="flat", highlightbackground="#45475a", highlightthickness=1, width=18)
        self.ent_app_name.insert(0, self.saved_cfg.get("last_app_name", "AutoDangBaiAllInOne"))
        self.ent_app_name.pack(side="left", padx=(0, 10), ipady=2)

        tk.Label(row_ico, text="Logo (.png/.jpg/.ico):", font=("Segoe UI", 9), fg=self.text_dim, bg=self.card_inner).pack(side="left")
        self.ent_ico = tk.Entry(row_ico, font=("Segoe UI", 9), bg="#11111b", fg=self.text_color, insertbackground=self.text_color, relief="flat", highlightbackground="#45475a", highlightthickness=1)
        self.ent_ico.insert(0, self.saved_cfg.get("last_icon", ""))
        self.ent_ico.pack(side="left", fill="x", expand=True, padx=(5, 5), ipady=2)
        tk.Button(row_ico, text="🎨 Chọn Logo", font=("Segoe UI", 9, "bold"), bg=self.btn_purple, fg="#11111b", activebackground="#d6bbfb", relief="flat", padx=6, command=self._browse_ico, cursor="hand2").pack(side="left")

        # KHUNG 2: BẢO MẬT ĐỈNH CAO & BẢN QUYỀN
        box_sec = tk.LabelFrame(body, text=" 2. 🛡️ CẤU HÌNH MÃ HÓA ĐỈNH CAO & BẢN QUYỀN ", font=("Segoe UI", 9, "bold"), fg=self.btn_green, bg=self.card_inner, padx=12, pady=8, relief="groove")
        box_sec.pack(fill="x", pady=(0, 6))

        row_sec_opts = tk.Frame(box_sec, bg=self.card_inner)
        row_sec_opts.pack(fill="x", pady=(0, 4))

        self.var_enable_license = tk.BooleanVar(value=self.saved_cfg.get("enable_license", True))
        tk.Checkbutton(row_sec_opts, text="Khóa Bản Quyền HWID 2.0 (RSA-PSS)", variable=self.var_enable_license, font=("Segoe UI", 9, "bold"), fg=self.accent, bg=self.card_inner, selectcolor="#11111b", activebackground=self.card_inner).pack(side="left")

        self.var_anti_debug = tk.BooleanVar(value=self.saved_cfg.get("anti_debug", True))
        tk.Checkbutton(row_sec_opts, text="Bật Anti-Debug / Anti-Dump Daemon", variable=self.var_anti_debug, font=("Segoe UI", 9), fg=self.text_color, bg=self.card_inner, selectcolor="#11111b", activebackground=self.card_inner).pack(side="left", padx=(15, 0))

        self.var_hide_console = tk.BooleanVar(value=self.saved_cfg.get("hide_console", True))
        tk.Checkbutton(row_sec_opts, text="Ẩn Console đen (Khuyên dùng)", variable=self.var_hide_console, font=("Segoe UI", 9, "bold"), fg=self.btn_green, bg=self.card_inner, selectcolor="#11111b", activebackground=self.card_inner).pack(side="left", padx=(15, 0))

        # Dòng Dùng thử & CSKH
        row_trial = tk.Frame(box_sec, bg=self.card_inner)
        row_trial.pack(fill="x", pady=(2, 0))

        self.var_auto_trial = tk.BooleanVar(value=self.saved_cfg.get("enable_trial", True))
        tk.Checkbutton(row_trial, text="Cho phép Dùng thử", variable=self.var_auto_trial, font=("Segoe UI", 9, "bold"), fg=self.btn_green, bg=self.card_inner, selectcolor="#11111b", activebackground=self.card_inner).pack(side="left")

        tk.Label(row_trial, text="Thời hạn thử:", font=("Segoe UI", 9), fg=self.text_color, bg=self.card_inner).pack(side="left", padx=(10, 3))
        self.spn_trial = tk.Spinbox(row_trial, from_=1, to=999, font=("Segoe UI", 10), bg="#11111b", fg=self.btn_green, insertbackground=self.text_color, relief="flat", highlightbackground="#45475a", highlightthickness=1, width=4)
        self.spn_trial.delete(0, tk.END)
        self.spn_trial.insert(0, str(self.saved_cfg.get("trial_val", "20")))
        self.spn_trial.pack(side="left")

        self.cbo_trial_unit = ttk.Combobox(row_trial, values=["Phút", "Giờ", "Ngày"], state="readonly", font=("Segoe UI", 9), width=6)
        self.cbo_trial_unit.set(self.saved_cfg.get("trial_unit", "Phút"))
        self.cbo_trial_unit.pack(side="left", padx=(4, 15))

        tk.Label(row_trial, text="💬 Zalo CSKH:", font=("Segoe UI", 9, "bold"), fg=self.accent, bg=self.card_inner).pack(side="left")
        self.ent_zalo = tk.Entry(row_trial, font=("Segoe UI", 9), bg="#11111b", fg=self.accent, insertbackground=self.text_color, relief="flat", highlightbackground="#45475a", highlightthickness=1)
        self.ent_zalo.insert(0, self.saved_cfg.get("zalo_support", "https://zalo.me/g/mmgznzbleun8cirr19ld"))
        self.ent_zalo.pack(side="left", fill="x", expand=True, padx=(4, 0), ipady=2)

        # NÚT ĐÓNG GÓI LỚN
        self.btn_build = tk.Button(
            body,
            text="🚀 BẮT ĐẦU MÃ HÓA & ĐÓNG GÓI RA FILE .EXE ĐỘC LẬP",
            font=("Segoe UI", 12, "bold"),
            bg=self.btn_green,
            fg="#11111b",
            activebackground="#94e2d5",
            relief="flat",
            pady=10,
            cursor="hand2",
            command=self._start_build
        )
        self.btn_build.pack(fill="x", pady=(4, 6))

        # KHUNG 3: TERMINAL LOGS
        box_log = tk.LabelFrame(body, text=" 📋 NHẬT KÝ BIÊN DỊCH THỜI GIAN THỰC ", font=("Segoe UI", 9, "bold"), fg=self.text_dim, bg=self.card_inner, padx=8, pady=4, relief="groove")
        box_log.pack(fill="both", expand=True)

        self.txt_log = tk.Text(box_log, font=("Consolas", 9), bg="#11111b", fg="#a6adc8", insertbackground=self.text_color, relief="flat", wrap="word")
        self.txt_log.pack(side="left", fill="both", expand=True)

        scroll = tk.Scrollbar(box_log, command=self.txt_log.yview)
        scroll.pack(side="right", fill="y")
        self.txt_log.config(yscrollcommand=scroll.set)

        # Cập nhật danh sách candidate ban đầu
        self._update_candidate_files()

    def _log(self, text: str):
        self.txt_log.insert(tk.END, text + "\n")
        self.txt_log.see(tk.END)

    def _browse_project_dir(self):
        folder = filedialog.askdirectory(title="Chọn Thư Mục Dự Án Python")
        if folder:
            self.ent_project_dir.delete(0, tk.END)
            self.ent_project_dir.insert(0, folder)
            self._update_candidate_files()

    def _browse_single_file(self):
        f = filedialog.askopenfilename(title="Chọn File Python (.py)", filetypes=[("Python Files", "*.py")])
        if f:
            folder = os.path.dirname(f)
            self.ent_project_dir.delete(0, tk.END)
            self.ent_project_dir.insert(0, folder)
            self._update_candidate_files(selected_file=os.path.basename(f))

    def _browse_output_dir(self):
        folder = filedialog.askdirectory(title="Chọn Thư Mục Xuất File .EXE")
        if folder:
            self.ent_output_dir.delete(0, tk.END)
            self.ent_output_dir.insert(0, folder)

    def _open_output_dir(self):
        out_dir = self.ent_output_dir.get().strip()
        if out_dir and os.path.exists(out_dir):
            if sys.platform == "win32":
                os.startfile(out_dir)
            else:
                subprocess.Popen(["xdg-open", out_dir])
        else:
            messagebox.showinfo("Thông báo", "Thư mục xuất chưa tồn tại!")

    def _browse_ico(self):
        f = filedialog.askopenfilename(title="Chọn Logo (.png, .jpg, .ico)", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.ico;*.bmp;*.webp")])
        if f:
            self.ent_ico.delete(0, tk.END)
            self.ent_ico.insert(0, f)

    def _update_candidate_files(self, selected_file: str = None):
        folder = self.ent_project_dir.get().strip()
        candidates = find_candidate_py_files(folder)
        self.cbo_entrypoint['values'] = candidates
        if candidates:
            if selected_file and selected_file in candidates:
                self.cbo_entrypoint.set(selected_file)
            else:
                self.cbo_entrypoint.set(candidates[0])
            base_app = os.path.splitext(os.path.basename(candidates[0]))[0]
            if base_app and not self.ent_app_name.get().strip():
                self.ent_app_name.delete(0, tk.END)
                self.ent_app_name.insert(0, base_app)

    def _start_build(self):
        if self.is_building:
            return

        proj_dir = self.ent_project_dir.get().strip()
        if not proj_dir or not os.path.exists(proj_dir):
            messagebox.showerror("Lỗi", "Vui lòng chọn Thư Mục Dự Án Python hợp lệ!")
            return

        entry_rel = self.cbo_entrypoint.get().strip()
        if not entry_rel:
            messagebox.showerror("Lỗi", "Vui lòng chọn File Khởi Động!")
            return

        full_src = os.path.join(proj_dir, entry_rel) if not os.path.isabs(entry_rel) else entry_rel
        if not os.path.exists(full_src):
            messagebox.showerror("Lỗi", f"Không tìm thấy file nguồn:\n{full_src}")
            return

        out_dir = self.ent_output_dir.get().strip() or os.path.join(BASE_DIR, "dist")
        app_name = self.ent_app_name.get().strip() or "App"
        ico_path = self.ent_ico.get().strip() or None

        self._save_config()

        # Tính toán ngày thử (hỗ trợ phút, giờ, ngày)
        try:
            trial_raw = float(self.spn_trial.get().strip()) if self.var_auto_trial.get() else 0.0
            unit = self.cbo_trial_unit.get().strip()
            if unit == "Phút":
                trial_days = trial_raw / 1440.0
            elif unit == "Giờ":
                trial_days = trial_raw / 24.0
            else:
                trial_days = trial_raw
        except ValueError:
            trial_days = 0.0

        if not self.var_enable_license.get():
            trial_days = 0.0

        support_cfg = {
            "zalo_support": self.ent_zalo.get().strip(),
            "enable_auto_trial": self.var_auto_trial.get() and trial_days > 0,
            "trial_days": trial_days
        }

        self.is_building = True
        self.btn_build.config(state="disabled", text="⏳ ĐANG MÃ HÓA & BIÊN DỊCH .EXE...")
        self.txt_log.delete("1.0", tk.END)

        def worker():
            self._log("=" * 60)
            self._log(f"[*] Bắt đầu quy trình bảo mật và đóng gói: {app_name}")
            self._log(f"[*] Thư mục dự án: {proj_dir}")
            self._log(f"[*] File khởi chạy: {full_src}")
            self._log(f"[*] Thư mục xuất .EXE: {out_dir}")
            self._log("=" * 60)

            temp_script = os.path.join(proj_dir, f"_temp_wrapped_{app_name}.py")
            try:
                self._log("[*] Bước 1: Tiêm mã hóa AES-256 In-Memory, Anti-Debug, HWID Guard & Trial...")
                prepare_protected_script(
                    source_file=full_src,
                    output_temp_file=temp_script,
                    app_name=app_name,
                    public_key_path=self.public_key_path,
                    trial_days=trial_days,
                    enable_license=self.var_enable_license.get(),
                    security_level="ultimate",
                    enable_anti_debug=self.var_anti_debug.get(),
                    support_config=support_cfg,
                    project_dir=proj_dir
                )
                self._log("[✓] Đã tiêm mã hóa In-Memory hoàn tất!")

                self._log("[*] Bước 2: Kích hoạt Engine PyInstaller gom trọn gói thư viện...")
                success = build_executable(
                    target_script=temp_script,
                    output_dir=out_dir,
                    app_name=app_name,
                    engine="auto",
                    project_dir=proj_dir,
                    icon_path=ico_path,
                    hide_console=self.var_hide_console.get(),
                    security_level="ultimate",
                    log_callback=self._log
                )
            except Exception as e:
                self._log(f"\n[!] LỖI ĐÓNG GÓI: {e}")
                success = False
            finally:
                if os.path.exists(temp_script):
                    try:
                        os.remove(temp_script)
                    except Exception:
                        pass
                self.is_building = False
                self.root.after(0, lambda: self.btn_build.config(state="normal", text="🚀 BẮT ĐẦU MÃ HÓA & ĐÓNG GÓI RA FILE .EXE ĐỘC LẬP"))

            if success:
                self.root.after(0, lambda: messagebox.showinfo("Thành Công", f"🎉 Đã mã hóa và đóng gói thành công file:\n{os.path.join(out_dir, f'{app_name}.exe')}"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Thất Bại", "Quá trình đóng gói gặp lỗi! Vui lòng kiểm tra tab nhật ký log."))

        threading.Thread(target=worker, daemon=True).start()


def main():
    root = tk.Tk()
    app = UltimateBuilderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
