# Cài skill edit-capcut-AI trên MÁY MỚI — quy trình chuẩn

Làm theo đúng thứ tự. Mất khoảng **20–40 phút** (phần lớn là chờ tải ~2–3 GB). Chỉ làm 1 lần mỗi máy.

## 0. Máy cần có
- Windows 10/11, mạng ổn định, ổ C: còn **≥ 8 GB** trống.
- Tài khoản **Claude** của công ty (gói có Claude Code).
- Nếu repo đang **riêng tư**: tài khoản GitHub của nhân sự đã được quản lý mời và đã bấm **Accept invitation** trong email.

## 1. Cài (chọn 1 trong 2 cách)

**Cách A — 1 lệnh, không cần gửi file** (repo công khai):
bấm phím Windows, gõ `PowerShell`, mở lên, dán lệnh dưới rồi Enter:
```
powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/phamthilyntnd-sketch/edit-capcut-AI/main/cai-dat/tai-va-cai.ps1 | iex"
```

**Cách B — gửi file** (dùng được cả khi repo riêng tư):
quản lý gửi file `cai-dat/CAI-DAT.cmd` (Zalo / Drive) → nhân sự lưu ra Desktop → **bấm đúp**.
Windows hiện "Windows protected your PC" thì bấm **More info → Run anyway**.

Bộ cài tự làm hết, theo thứ tự:

| Bước | Việc | Ghi chú |
|---|---|---|
| 1 | Cài app **Claude**, Git, Python 3.12, Node.js, ffmpeg, Chrome nếu thiếu | qua winget; có thể hiện hộp hỏi quyền Admin → **Yes** |
| 1 | Kiểm **CapCut desktop** | chưa có → mở trang tải; cài, **mở CapCut 1 lần**, đóng, rồi chạy lại bộ cài |
| 2 | Tải skill về `%USERPROFILE%\.claude\skills\edit-capcut-ai` | repo riêng tư → hiện cửa sổ đăng nhập GitHub: đăng nhập tài khoản đã được mời |
| 3 | Tạo môi trường Python riêng `.venv`, cài thư viện | ~3–5 phút |
| 4 | Cài `capcut-cli` | |
| 5 | Tải mô hình tách người (u2net ~170 MB) + mô hình nghe tiếng Việt (Whisper ~1,6 GB) | lâu nhất |
| 6 | Tạo bộ tiếng nhấn, **kiểm máy** | phải ra **SẴN SÀNG** |
| 7 | Tạo lối tắt Desktop **"Cap nhat skill edit-capcut-AI"** | dùng để cập nhật về sau |

Cuối cùng in **XONG**. Nếu in "Còn thiếu mục bắt buộc" → làm theo gợi ý trên màn hình rồi chạy lại (chạy lại không mất gì, chỉ làm phần còn thiếu).

## 2. Mở Claude lần đầu
1. **Tắt hẳn** app Claude (chuột phải biểu tượng ở khay đồng hồ → Quit) rồi mở lại — để nhận skill mới.
2. Đăng nhập tài khoản Claude công ty → chuyển sang tab **Code**.
3. Chọn thư mục làm việc (ví dụ `Documents\Du-an-video`).
4. Gõ `/edit-capcut-ai` — thấy skill hiện ra là xong.

## 3. Chuẩn bị cho từng khách hàng (logo không nằm trên GitHub)
- Hồ sơ thương hiệu nằm trong `%USERPROFILE%\.claude\skills\edit-capcut-ai\thuong-hieu\`. Có sẵn `santav.json`; khách mới: nói với Claude *"tạo hồ sơ thương hiệu cho <tên khách>"* (hoặc chép `_mau.json`).
- **Logo, brief, footage** của khách: để trên máy (Drive nội bộ / ổ D:), KHÔNG đưa lên GitHub. Khi dựng, nói cho Claude biết file logo ở đâu — Claude ghi đường dẫn vào cấu hình dự án.

## 4. Dùng thử
Trong tab Code, nói:
> Dựng video trong thư mục `D:\footage\kol-01` cho thương hiệu santav thành project CapCut

Claude hỏi những gì còn thiếu **1 lần**, rồi làm tới xong. Mở CapCut xem project `SANTAV <mã>`, góp ý bằng lời — Claude sửa thẳng vào project đó.
**Trước khi Claude ghi project, đóng hẳn CapCut.**

## 5. Cập nhật khi có bản mới
Bấm đúp lối tắt **"Cap nhat skill edit-capcut-AI"** trên Desktop (hoặc chạy lại lệnh/file ở bước 1). Chỉ tải phần thay đổi, giữ nguyên cấu hình máy và hồ sơ thương hiệu đã sửa.

## 6. Kiểm 1 máy đã cài đủ chưa (không cài gì)
```
powershell -ExecutionPolicy Bypass -File "%USERPROFILE%\.claude\skills\edit-capcut-ai\cai-dat\cai-dat.ps1" -KiemTra
```
- Báo "không tìm thấy file" → máy chưa cài → làm bước 1.
- Có dòng `[THIẾU]` → chạy lại bước 1.
- Ra **SẴN SÀNG** mà gõ `/edit-capcut-ai` vẫn không thấy → tắt hẳn Claude rồi mở lại.

## 7. Lỗi hay gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `winget` không có | Microsoft Store → cài **App Installer** → chạy lại |
| "Không tải được skill" | Kiểm mạng; repo riêng tư → nhân sự đã Accept lời mời chưa, đăng nhập đúng tài khoản GitHub chưa |
| Lệnh 1 dòng báo `[LOI] Khong tai duoc` | Repo đang riêng tư → dùng Cách B (file CAI-DAT.cmd) |
| Cài xong gõ `python`/`ffmpeg` không nhận | Đóng cửa sổ, chạy lại bộ cài (máy cần mở cửa sổ mới để nhận phần mềm vừa cài) |
| Thiếu "Thư mục project CapCut" | Mở CapCut 1 lần, tạo thử 1 project trống, đóng, chạy lại bộ cài |
| Ổ đĩa < 2 GB | Dọn ổ C: (mỗi project CapCut ~0,5–1 GB) |
| Chữ trong CapCut hiện "Input text" | Báo Claude: *"máy này CapCut lỗi chữ, dùng chữ dạng ảnh"* |

Còn lỗi khác: chụp màn hình cửa sổ cài gửi quản lý.
