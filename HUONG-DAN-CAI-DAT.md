# Hướng dẫn CÀI ĐẶT skill edit-capcut-AI (repo riêng tư)

Skill nằm trên GitHub ở chế độ **RIÊNG TƯ**: chỉ người được quản lý **mời vào repo** mới tải và dùng được.
Ai thôi việc / không cần nữa → quản lý gỡ quyền là máy đó không cập nhật được nữa.

Gồm 2 phần: **A. Quản lý** (cấp quyền) · **B. Nhân sự** (cài trên máy mình).

---

## A. PHẦN QUẢN LÝ — cấp quyền cho 1 người (2 phút)

1. Xin nhân sự **tên tài khoản GitHub** (username). Chưa có → nhân sự tạo miễn phí ở https://github.com/signup.
2. Mở https://github.com/phamthilyntnd-sketch/edit-capcut-AI/settings/access (đăng nhập tài khoản chủ repo).
   GitHub hỏi lại mật khẩu / mã xác thực → nhập.
3. Bấm **Add people** → gõ username hoặc email của nhân sự → chọn đúng người → **Add … to this repository**.
4. Gửi cho nhân sự **2 thứ** (Zalo / email / Drive nội bộ):
   - file **`cai-dat/CAI-DAT.cmd`** (trên máy quản lý: `Documents\Calude x Capcut\edit-capcut-AI\cai-dat\CAI-DAT.cmd`);
   - file hướng dẫn này (phần B) và `HUONG-DAN-EDIT.md`.

**Gỡ quyền:** cùng trang trên → dòng của người đó → **Remove**. Lời mời chưa được chấp nhận cũng huỷ ở đây.

> Lưu ý: repo cá nhân chỉ có 1 mức quyền "cộng tác viên" — người được mời tải được và cũng đẩy sửa đổi lên được. Chỉ mời người tin tưởng. Cần phân quyền chỉ-đọc thì chuyển repo sang một **Organization** của công ty (miễn phí) rồi đặt quyền **Read** cho nhân sự.

**Kiểm repo vẫn riêng tư:** https://github.com/phamthilyntnd-sketch/edit-capcut-AI/settings → mục **Danger Zone** phải ghi *"This repository is currently private"*.

---

## B. PHẦN NHÂN SỰ — cài trên máy mình (1 lần, 20–40 phút)

### B0. Chuẩn bị
- Windows 10/11, mạng ổn định, ổ C: trống **≥ 8 GB**.
- **Tài khoản GitHub** đã gửi cho quản lý.
- **Tài khoản Claude** công ty (gói có Claude Code).
- **CapCut desktop** (chưa có cũng được — bộ cài sẽ mở trang tải).

### B1. Chấp nhận lời mời GitHub
Mở email từ GitHub *"… invited you to collaborate on phamthilyntnd-sketch/edit-capcut-AI"* → **View invitation** → **Accept invitation**.
(Không thấy email: đăng nhập GitHub → https://github.com/notifications, hoặc mở thẳng https://github.com/phamthilyntnd-sketch/edit-capcut-AI/invitations.)
Lời mời hết hạn sau **7 ngày** — hết hạn thì nhờ quản lý mời lại.

### B2. Chạy bộ cài
1. Lưu file **`CAI-DAT.cmd`** ra Desktop → **bấm đúp**.
   Windows hiện *"Windows protected your PC"* → **More info → Run anyway**.
   Hộp hỏi quyền Admin (khi cài phần mềm) → **Yes**.
2. **Đăng nhập GitHub** (chỉ lần đầu) — 1 trong 2 kiểu sẽ hiện:
   - Cửa sổ *"Connect to GitHub"* → **Sign in with your browser** → đăng nhập **đúng tài khoản đã được mời** → **Authorize**.
   - Hoặc cửa sổ đen hiện **một MÃ 8 ký tự** (ví dụ `1718-76BB`) → mở https://github.com/login/device → nhập mã → **Continue** → **Authorize**, rồi quay lại cửa sổ đen. Mã hết hạn sau ~15 phút.
3. Chờ bộ cài tự làm hết:

| Bước | Bộ cài làm | Bạn cần làm |
|---|---|---|
| 1 | Cài app **Claude**, Git, Python, Node.js, ffmpeg, Chrome nếu thiếu | bấm **Yes** khi hỏi quyền |
| 1 | Kiểm CapCut | chưa có → trang tải mở ra: cài CapCut, **mở 1 lần, tạo 1 project trống, đóng**, rồi bấm đúp lại `CAI-DAT.cmd` |
| 2 | Tải skill về `%USERPROFILE%\.claude\skills\edit-capcut-ai` | — |
| 3–5 | Thư viện Python, capcut-cli, mô hình tách người + mô hình nghe tiếng Việt (~2 GB) | chờ (lâu nhất) |
| 6 | Tạo tiếng nhấn, **kiểm máy** | phải thấy **SẴN SÀNG** |
| 7 | Lối tắt Desktop **"Cap nhat skill edit-capcut-AI"** | — |

Cuối cùng hiện **XONG**. Nếu hiện *"Còn thiếu mục bắt buộc"* → làm theo gợi ý dòng `[THIẾU]` rồi bấm đúp lại `CAI-DAT.cmd` (chạy lại không mất gì).

### B3. Mở Claude lần đầu
1. **Tắt hẳn** app Claude (chuột phải biểu tượng Claude cạnh đồng hồ → **Quit**) rồi mở lại.
2. Đăng nhập tài khoản Claude công ty → chọn tab **Code**.
3. Chọn thư mục làm việc (nên tạo `Documents\Du-an-video`).
4. Gõ `/edit-capcut-ai` → thấy skill hiện ra là xong. Tiếp theo đọc **HUONG-DAN-EDIT.md**.

### B4. Cập nhật khi quản lý báo có bản mới
Bấm đúp lối tắt **"Cap nhat skill edit-capcut-AI"** trên Desktop → chờ **XONG** → tắt hẳn rồi mở lại Claude.
Chỉ tải phần thay đổi; cấu hình máy và hồ sơ thương hiệu bạn tạo được giữ nguyên.

### B5. Kiểm máy đã cài đủ chưa (không cài gì)
Mở PowerShell, dán:
```
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.claude\skills\edit-capcut-ai\cai-dat\cai-dat.ps1" -KiemTra
```
- "không tìm thấy file" → chưa cài → làm B2.
- Có `[THIẾU]` → bấm đúp lại `CAI-DAT.cmd`.
- **SẴN SÀNG** mà `/edit-capcut-ai` không hiện → tắt hẳn Claude rồi mở lại.

---

## C. Lỗi hay gặp

| Hiện tượng | Xử lý |
|---|---|
| `[LOI] Van khong tai duoc skill` / `Repository not found` / `403` | Chưa **Accept invitation**, hoặc đăng nhập **nhầm tài khoản GitHub**. Accept xong bấm đúp lại. Nhầm tài khoản: Control Panel → **Credential Manager** → Windows Credentials → xoá dòng `git:https://github.com` → chạy lại |
| Cửa sổ đăng nhập GitHub không hiện, bộ cài đứng im | Đóng cửa sổ, bấm đúp lại — bộ cài chuyển sang đăng nhập bằng MÃ (B2 bước 2) |
| `expired_token` | Mã đăng nhập quá hạn → bấm đúp lại để lấy mã mới, nhập ngay |
| `winget` không có | Microsoft Store → cài **App Installer** → chạy lại |
| Cài xong vẫn báo thiếu Python/ffmpeg | Đóng cửa sổ, bấm đúp lại (cửa sổ mới mới nhận phần mềm vừa cài) |
| Thiếu "Thư mục project CapCut" | Mở CapCut, tạo 1 project trống, đóng, chạy lại |
| Ổ đĩa < 2 GB | Dọn ổ C: (mỗi project CapCut ~0,5–1 GB) |
| Cập nhật báo lỗi `pull` | Bạn đã sửa một file có sẵn của skill. Báo quản lý, hoặc nhờ Claude: *"cập nhật skill edit-capcut-ai giúp tôi, giữ hồ sơ thương hiệu của tôi"* |

Lỗi khác: chụp màn hình cửa sổ cài gửi quản lý.
