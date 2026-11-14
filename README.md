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

## Cài đặt (Windows)

1. Cần có: [Claude Code](https://claude.com/claude-code), **CapCut** desktop, **Google Chrome**, **Python 3.10+**, **Node.js**, **ffmpeg** (`winget install Gyan.FFmpeg`), **Git**.
2. Lấy skill về thư mục skill của Claude:
   ```bash
   git clone https://github.com/phamthilyntnd-sketch/edit-capcut-AI.git "%USERPROFILE%\.claude\skills\edit-capcut-ai"
   ```
3. Cài thư viện Python (trong thư mục skill):
   ```bash
   cd "%USERPROFILE%\.claude\skills\edit-capcut-ai"
   py -3 -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   npm i -g capcut-cli
   .venv\Scripts\python scripts\tao_sfx.py
   .venv\Scripts\python scripts\kiem_may.py
   ```
   Dòng cuối phải in **SẴN SÀNG**. Lần đầu dựng, Whisper sẽ tự tải mô hình nghe tiếng Việt (~1,5 GB).
4. (Tuỳ chọn) để chữ né được cả **người**: đặt file mô hình `u2net_human_seg.onnx` và ghi đường dẫn vào `may.json` (chép từ `may.json.mau`). Không có thì chữ vẫn né sản phẩm.

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
| `thuong-hieu/` | Hồ sơ thương hiệu (mẫu + ví dụ) |
| `fonts/` | Be Vietnam Pro (SIL Open Font License — xem `fonts/OFL.txt`) |
| `vi-du/cau-hinh-mau.json` | Cấu hình 1 video mẫu |

**Bảo mật:** không đưa footage, brief, logo của khách lên repo này — để trên máy và trỏ đường dẫn trong hồ sơ / cấu hình dự án.
