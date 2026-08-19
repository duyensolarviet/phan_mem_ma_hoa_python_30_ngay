# 🛡️ PHẦN MỀM MÃ HÓA PYTHON & ĐÓNG GÓI .EXE BẢN QUYỀN (30 NGÀY / VĨNH VIỄN)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![AES-256-GCM](https://img.shields.io/badge/Encryption-AES--256--GCM-green.svg)]()
[![RSA-PSS](https://img.shields.io/badge/License-RSA--PSS%20NIST-purple.svg)]()
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()

> **Công cụ tối thượng giúp lập trình viên Python bảo vệ mã nguồn, chống dịch ngược / decompile, khóa bản quyền phần cứng (HWID 2.0), cấp key dùng thử tự động 30 ngày hoặc theo yêu cầu, và xuất file `.EXE` chạy độc lập 100%.**

---

## 🌟 CÁC TÍNH NĂNG BẢO MẬT ĐỈNH CAO

1. **Mã Hóa AES-256 GCM In-Memory Decryption (Zero-Disk Footprint):**
   - Nén mã nguồn bằng `zlib` và mã hóa chuẩn quân sự **AES-256-GCM**.
   - Toàn bộ quá trình giải mã và nạp code thực thi trực tiếp trên **RAM**. Tuyệt đối không trích xuất file `.py` hay `.pyc` tạm ra ổ đĩa.
2. **Làm Rối Mã Nguồn Đa Tầng (Polymorphic AST Obfuscation):**
   - Biến đổi 100% chuỗi ký tự thành biểu thức toán học giải mã XOR + Bitwise Rotate động.
   - Chèn các hàm ma, dead code và opaque predicates để đánh lừa mọi công cụ decompiler (`pycdc`, `uncompyle6`, `decompyle++`).
3. **Lõi Anti-Debug, Anti-Dump & Anti-VM:**
   - Tự động phát hiện và chặn các trình phân tích động: `x64dbg`, `Cheat Engine`, `Process Hacker`, `IDA Pro`, `Wireshark`...
   - Kiểm tra thanh ghi phần cứng CPU (`DR0-DR7`) để chống Hardware Breakpoints.
   - Tự động nhận diện và chặn môi trường máy ảo / Sandbox (`VMware`, `VirtualBox`, `Sandboxie`, `QEMU`).
4. **Khóa Bản Quyền HWID 2.0 & Chữ Ký Số RSA-PSS:**
   - Định danh máy tính chính xác dựa trên tổ hợp phần cứng: `Motherboard UUID + CPU ID + Disk Serial + MachineGUID`.
   - Cơ chế cấp phát License Key xác thực bằng chữ ký số RSA-PSS / RSA-2048 tiêu chuẩn NIST (không thể làm giả hay bẻ khóa).
   - **TimeGuard Chống Gian Lận Giờ:** So sánh thời gian thực với cụm máy chủ NTP / HTTP Internet đa tầng, chống người dùng tự lùi giờ hệ thống máy tính.
5. **Gom Trọn Vẹn 100% Dependencies Tự Động:**
   - Tự động quét AST gom toàn bộ thư viện bên thứ 3 (`customtkinter`, `selenium`, `undetected_chromedriver`, `google.generativeai`, `groq`, `PIL`, `requests`...).
   - Tự động chuyển đổi logo ảnh (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`) sang định dạng `.ico` chuẩn Windows.
   - Tùy chọn ẩn cửa sổ console đen, chỉ hiện giao diện GUI chuyên nghiệp.

---

## 📁 CẤU TRÚC DỰ ÁN

```text
phan_mem_ma_hoa_python_30_ngay/
│
├── core/                      # Lõi bảo mật & Mã hóa đỉnh cao
│   ├── anti_analysis.py       # Lõi Anti-Debug, Hardware Breakpoints, Anti-VM
│   ├── crypto_payload.py      # Lõi AES-256-GCM In-Memory Decryption Loader
│   ├── keygen_engine.py       # Lõi sinh mã Key RSA-PSS / RSA-2048
│   ├── license_engine.py      # Lõi HWID 2.0, TimeGuard, Hạn dùng thử & CSKH
│   └── obfuscator.py          # Lõi làm rối mã nguồn & String Virtualization
│
├── keys/                      # Nơi lưu cặp khóa RSA
│   ├── private_key.pem        # ⚠️ Khóa bí mật (Dùng tạo Key, KHÔNG gửi cho ai)
│   └── public_key.pem         # Khóa công khai (Tự động nhúng vào file .EXE)
│
├── builder/                   # Trình đóng gói nhị phân
│   └── pack_engine.py         # Lõi gom dependencies & đóng gói PyInstaller
│
├── src/                       # Giao diện chính
│   └── main.py                # Studio Mã Hóa & Đóng Gói .EXE Siêu Tốc
│
├── requirements.txt           # Danh sách thư viện cần thiết
├── install_requirements.bat   # Click 1 chạm để cài đặt thư viện tự động
├── CHAY_MAIN.bat              # Click đúp 1 chạm để mở phần mềm
└── README.md                  # Hướng dẫn chi tiết
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & SỬ DỤNG (100% HOẠT ĐỘNG)

### Bước 1: Tải mã nguồn về máy
Bạn có thể tải file `.ZIP` về giải nén hoặc clone qua git:
```bash
git clone https://github.com/duyensolarviet/phan_mem_ma_hoa_python_30_ngay.git
cd phan_mem_ma_hoa_python_30_ngay
```

### Bước 2: Cài đặt thư viện phụ thuộc
Chỉ cần **click đúp vào file `install_requirements.bat`**, hoặc chạy lệnh trong terminal:
```bash
pip install -r requirements.txt
```

### Bước 3: Khởi động phần mềm
- **Cách 1 (Nhanh nhất):** Click đúp vào file **`CHAY_MAIN.bat`**.
- **Cách 2:** Chạy lệnh terminal:
  ```bash
  python src/main.py
  ```

---

## 🛠️ HƯỚNG DẪN ĐÓNG GÓI TOOL PYTHON RA .EXE

1. Mở giao diện Studio.
2. Chọn thư mục dự án Python cần bảo vệ và chọn file chạy chính (ví dụ `main.py` hoặc `app.py`).
3. Chọn thư mục lưu file `.EXE` xuất ra và đặt tên phần mềm.
4. Cấu hình bảo mật:
   - **Khóa bản quyền (License Key):** Bật/Tắt theo nhu cầu.
   - **Chế độ dùng thử (Trial):** Cài đặt số ngày (ví dụ 30 ngày) hoặc số phút/giờ.
   - **Chống Debug & Dịch Ngược:** Bật bảo vệ toàn diện.
   - **Ẩn Console:** Bật để không hiện cửa sổ dòng lệnh đen khi chạy phần mềm.
5. Nhấn **"🛡️ BẮT ĐẦU ĐÓNG GÓI & MÃ HÓA .EXE"** và chờ hệ thống hoàn tất.

---

## 🔑 HƯỚNG DẪN TẠO KEY BẢN QUYỀN CHO KHÁCH HÀNG

1. Tại giao diện phần mềm, chuyển sang tab **"TẠO KEY BẢN QUYỀN (KEYGEN)"**.
2. Nhập mã **HWID** của khách hàng gửi cho bạn.
3. Chọn thời hạn bản quyền: 1 tháng (30 ngày), 3 tháng, 6 tháng, 1 năm hoặc vĩnh viễn.
4. Nhấn nút **"🔑 SINH KEY BẢN QUYỀN"** và sao chép mã Key gửi cho khách kích hoạt.

---

## 📝 BẢN QUYỀN & TÁC GIẢ
- **Phát triển bởi:** Duyen Solar Viet
- **Hỗ trợ kỹ thuật:** [Zalo Support](https://zalo.me/g/mmgznzbleun8cirr19ld)
