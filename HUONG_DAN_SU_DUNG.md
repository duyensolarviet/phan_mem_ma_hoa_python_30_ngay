# 🛡️ PYTHON ULTIMATE PROTECTOR & .EXE BUILDER

---

## 🌟 CÁC LỚP BẢO MẬT ĐỈNH CAO ĐƯỢC TỰ ĐỘNG TIÊM VÀO .EXE

1. **Mã Hóa AES-256 GCM In-Memory Decryption:**
   * Nén mã nguồn bằng `zlib` và mã hóa chuẩn quân sự **AES-256-GCM**.
   * Chỉ giải mã trực tiếp trên RAM. Không bao giờ trích xuất file `.py` hay `.pyc` ra ổ đĩa.
2. **Lõi Anti-Debug, Anti-Dump & Anti-VM:**
   * Tự động phát hiện và chặn các trình dịch ngược: `x64dbg`, `Cheat Engine`, `Process Hacker`, `IDA Pro`...
   * Kiểm tra thanh ghi phần cứng CPU (`DR0-DR7`) để chống Hardware Breakpoints.
   * Chống máy ảo / Sandbox (`VMware`, `VirtualBox`, `Sandboxie`).
3. **Khóa Bản Quyền HWID 2.0 & Chữ Ký Số RSA-PSS:**
   * Khóa mã máy theo phần cứng (`Motherboard UUID + CPU ID + Disk Serial + MachineGUID`).
   * Chữ ký số RSA-PSS tiêu chuẩn NIST (chống giả mạo / bẻ khóa key).
   * Chống tua lùi ngày giờ máy tính qua `TimeGuard` đa máy chủ Internet.
4. **Gom 100% Dependencies Đa Tầng:**
   * Tự động quét AST gom trọn vẹn toàn bộ thư viện bên thứ 3 (`selenium`, `undetected_chromedriver`, `customtkinter`, `google.generativeai`, `groq`, `PIL`, `requests`...).
   * Tự động chuyển đổi logo ảnh (`.png`, `.jpg`, `.jpeg`, `.webp`) sang định dạng `.ico` chuẩn Windows.
   * Ẩn console đen mặc định, chạy trực tiếp giao diện đồ họa GUI mượt mà.

---

## 📁 CẤU TRÚC DỰ ÁN TINH GỌN (CHUẨN 100%)

```text
e:\mahoapython\
│
├── core\                      # Lõi bảo mật & Mã hóa đỉnh cao
│   ├── anti_analysis.py       # Lõi Anti-Debug, Hardware Breakpoints, Anti-VM
│   ├── crypto_payload.py      # Lõi AES-256-GCM In-Memory Decryption Loader
│   ├── keygen_engine.py       # Lõi sinh mã Key RSA-PSS / RSA-2048
│   ├── license_engine.py      # Lõi HWID 2.0, TimeGuard, Hạn dùng thử & CSKH
│   └── obfuscator.py          # Lõi làm rối mã nguồn & String Virtualization
│
├── keys\                      # Nơi lưu cặp khóa RSA
│   ├── private_key.pem        # ⚠️ Khóa bí mật (Dùng tạo Key, KHÔNG gửi cho ai)
│   └── public_key.pem         # Khóa công khai (Tự động nhúng vào file .EXE)
│
├── builder\                   # Trình đóng gói nhị phân
│   └── pack_engine.py         # Lõi gom dependencies & đóng gói PyInstaller / C++
│
├── src\                       # Giao diện chính
│   └── main.py                # 🛡️ Studio Mã Hóa & Đóng Gói .EXE Siêu Tốc
│
├── CHAY_MAIN.bat              # Click đúp 1 chạm để mở phần mềm
└── HUONG_DAN_SU_DUNG.md       # Cẩm nang hướng dẫn
```

---

## 🚀 CÁCH KHỞI ĐỘNG VÀ SỬ DỤNG

Chỉ cần chạy lệnh duy nhất:
```bash
python src/main.py
```
*(Hoặc click đúp vào file `CHAY_MAIN.bat`)*
