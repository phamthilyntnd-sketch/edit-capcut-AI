# edit-capcut-AI

Skill cho **Claude Code**: biến footage thô (1 clip người nói + vài clip cảnh trám sản phẩm) thành **project CapCut sửa được** và file MP4 xem thử — đúng nhận diện thương hiệu, sẵn sàng đăng TikTok / Reels / Shorts.

Claude tự làm:
- cắt vấp, nói lại, tiếng ừ/ờ — giữ lần nói cuối, không cắt cụt chữ;
- chọn **đoạn quay đẹp nhất** trong mỗi clip cảnh trám (nét, đủ sáng, chai đứng thẳng, khớp lời);
- **chữ nhấn là chữ CapCut thật** (sửa được), chỉ 2 kiểu, căn giữa, **không che người và sản phẩm**;
- **chuyển cảnh, hiệu ứng cảnh, hiệu ứng chữ có sẵn của CapCut**, đa dạng theo ngữ cảnh;
- **tiếng nhấn** khớp hình (bộ tiếng tự tổng hợp, không bản quyền), **lọc tạp âm** giọng nói, chuẩn -14 LUFS;
- nhãn "Hợp tác quảng cáo", dòng pháp lý, kiểm từ cấm và luật quảng cáo;
- mỗi lần góp ý: **sửa thẳng vào project đang xem**, không tạo v2/v3 (bản trước được sao lưu).

Nhạc nền **không** tự chèn: bạn chọn nhạc có quyền thương mại trong thư viện CapCut (TikTok yêu cầu với video quảng cáo).

## Cài đặt cho máy nhân sự (Windows) — 1 file, tự động

> **Quy trình chuẩn cho máy mới, từng bước + xử lý lỗi: [HUONG-DAN-MAY-MOI.md](HUONG-DAN-MAY-MOI.md)**

Repo công khai → mở PowerShell, dán 1 lệnh là xong (không cần gửi file):
```
powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/phamthilyntnd-sketch/edit-capcut-AI/main/cai-dat/tai-va-cai.ps1 | iex"
```

Hoặc (dùng được cả khi repo riêng tư):
1. Repo riêng tư: người quản lý **mời tài khoản GitHub của nhân sự** (Settings → Collaborators).
2. Gửi cho nhân sự đúng **1 file `cai-dat/CAI-DAT.cmd`** (Zalo / email / Drive nội bộ).
3. Nhân sự **bấm đúp** file đó. Bộ cài tự làm hết (link tải nằm trong `cai-dat/lien-ket.json`, không ai phải tự đi tải):
   - cài app Claude (có tab Code), Git, Python 3.12, Node.js, ffmpeg, Chrome nếu máy chưa có (qua winget);
   - tải skill về `%USERPROFILE%\.claude\skills\edit-capcut-ai` (lần đầu hiện cửa sổ đăng nhập GitHub);
   - tạo môi trường Python riêng `.venv`, cài thư viện, cài `capcut-cli`;
   - tải sẵn mô hình tách người (u2net, ~170 MB) và mô hình nghe tiếng Việt (Whisper large-v3-turbo, ~1,6 GB);
   - tạo bộ tiếng nhấn, kiểm máy, tạo lối tắt Desktop "Cap nhat skill edit-capcut-AI" → in **XONG**;
   - **tắt hẳn rồi mở lại Claude** để nhận skill.
   CapCut desktop: nếu chưa có, bộ cài mở trang tải — cài xong mở CapCut 1 lần rồi bấm lại `CAI-DAT.cmd`.
4. **Cập nhật** khi skill có bản mới: bấm lại `CAI-DAT.cmd` (chỉ tải phần thay đổi, giữ cấu hình máy).
5. Kiểm nhanh không cài gì: `powershell -ExecutionPolicy Bypass -File cai-dat\cai-dat.ps1 -KiemTra`

Máy đã có Git có thể cài bằng 1 lệnh thay cho bước 2–3:
```bash
git clone https://github.com/phamthilyntnd-sketch/edit-capcut-AI.git "%USERPROFILE%\.claude\skills\edit-capcut-ai" && powershell -ExecutionPolicy Bypass -File "%USERPROFILE%\.claude\skills\edit-capcut-ai\cai-dat\cai-dat.ps1"
```

## Dùng

1. Tạo hồ sơ thương hiệu: chép `thuong-hieu/_mau.json` thành `thuong-hieu/<ten-khach>.json`, điền màu, logo, nút kêu gọi, dòng pháp lý, từ cấm, màu bao bì sản phẩm (xem ví dụ `thuong-hieu/santav.json`).
2. Mở Claude Code ở thư mục làm việc của bạn và nói, ví dụ:
   > Dựng video trong thư mục `D:\footage\kol-01` cho thương hiệu `<ten-khach>` thành project CapCut
   (hoặc gõ `/edit-capcut-ai`). Claude hỏi những gì còn thiếu **một lần**, rồi làm tới xong.
3. Mở CapCut xem project, góp ý bằng lời ("chữ to hơn", "tiếng nhấn nhỏ quá", "cảnh trám đoạn 20s chưa đẹp"…) — Claude sửa thẳng vào project đó.
4. Chọn nhạc thương mại trong CapCut rồi xuất video.

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `SKILL.md` | Quy trình + quy tắc cho Claude |
| `scripts/dung.py` | Dựng: cắt, cảnh trám, chữ, hiệu ứng, tiếng, MP4, project CapCut, kiểm tra |
| `scripts/chuan_bi.py` | Chuyển footage, phiên âm, bảng ảnh, tra brief |
| `scripts/tram.py` · `bo_cuc.py` · `chu.py` · `cap_nhat.py` | Chọn cảnh trám đẹp · bố cục chữ né người/sản phẩm · chữ CapCut thật · cập nhật tại chỗ |
| `scripts/tao_sfx.py` · `kiem_may.py` | Tạo bộ tiếng nhấn · kiểm máy |
| `cai-dat/` | Bộ cài tự động (`CAI-DAT.cmd`, `cai-dat.ps1`) + danh sách link tải (`lien-ket.json`) |
| `thuong-hieu/` | Hồ sơ thương hiệu (mẫu + ví dụ) |
| `fonts/` | Be Vietnam Pro (SIL Open Font License — xem `fonts/OFL.txt`) |
| `vi-du/cau-hinh-mau.json` | Cấu hình 1 video mẫu |

**Bảo mật:** không đưa footage, brief, logo của khách lên repo này — để trên máy và trỏ đường dẫn trong hồ sơ / cấu hình dự án.
