# edit-capcut-AI

Skill cho **Claude Code**: biến footage thô (1 clip người nói + vài clip cảnh trám sản phẩm) thành **project CapCut sửa được** (+ ảnh thumbnail; MP4 xem thử khi cần) — đúng nhận diện thương hiệu, sẵn sàng đăng TikTok / Reels / Shorts.

Claude tự làm:
- cắt vấp, nói lại, tiếng ừ/ờ — giữ lần nói cuối, không cắt cụt chữ;
- chọn **đoạn quay đẹp nhất** trong mỗi clip cảnh trám (nét, đủ sáng, chai đứng thẳng, khớp lời);
- **chữ nhấn là chữ CapCut thật** (sửa được), chỉ 2 kiểu, căn giữa, **không che người và sản phẩm**;
- **chuyển cảnh, hiệu ứng cảnh, hiệu ứng chữ có sẵn của CapCut**, đa dạng theo ngữ cảnh;
- **tiếng nhấn** khớp hình (bộ tiếng tự tổng hợp, không bản quyền), **lọc tạp âm** giọng nói, chuẩn -14 LUFS;
- nhãn "Hợp tác quảng cáo", dòng pháp lý, kiểm từ cấm và luật quảng cáo;
- mỗi lần góp ý: **sửa thẳng vào project đang xem**, không tạo v2/v3 (bản trước được sao lưu).

Nhạc nền **không** tự chèn: bạn chọn nhạc có quyền thương mại trong thư viện CapCut (TikTok yêu cầu với video quảng cáo).

## Cài đặt (repo RIÊNG TƯ — chỉ người được mời mới dùng được)

**Hướng dẫn đầy đủ: [HUONG-DAN-CAI-DAT.md](HUONG-DAN-CAI-DAT.md)** (quản lý cấp quyền + nhân sự cài + xử lý lỗi) · **Cách edit: [HUONG-DAN-EDIT.md](HUONG-DAN-EDIT.md)**

Tóm tắt:
1. **Quản lý** mời tài khoản GitHub của nhân sự: Settings → Collaborators → *Add people*. Gửi nhân sự file `cai-dat/CAI-DAT.cmd`.
2. **Nhân sự** bấm *Accept invitation* trong email GitHub, rồi **bấm đúp `CAI-DAT.cmd`**, đăng nhập GitHub đúng tài khoản được mời (cửa sổ đăng nhập, hoặc mã ở github.com/login/device). Bộ cài tự làm hết (link tải trong `cai-dat/lien-ket.json`):
   - cài app Claude (có tab Code), Git, Python 3.12, Node.js, ffmpeg, Chrome nếu máy chưa có (qua winget);
   - tải skill về `%USERPROFILE%\.claude\skills\edit-capcut-ai`;
   - tạo môi trường Python riêng `.venv`, cài thư viện, cài `capcut-cli`;
   - tải sẵn mô hình tách người (u2net, ~170 MB) và mô hình nghe tiếng Việt (Whisper large-v3-turbo, ~1,6 GB);
   - tạo bộ tiếng nhấn, kiểm máy, tạo lối tắt Desktop "Cap nhat skill edit-capcut-AI" → in **XONG**.
3. **Tắt hẳn rồi mở lại Claude** → tab Code → gõ `/edit-capcut-ai`.
4. **Cập nhật**: bấm đúp lối tắt "Cap nhat skill edit-capcut-AI" trên Desktop.
5. **Gỡ quyền** người nghỉ: Settings → Collaborators → *Remove*.

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
| `scripts/cong_thuc.py` + `kho/cong-thuc.json` | Công thức dựng: 16 ngành × 10 loại video × yêu cầu bằng lời (sôi động, sang, ít chữ…) tự chỉnh nhịp, chữ, cảnh trám, hiệu ứng, tiếng; gợi ý chữ theo sản phẩm; báo cáo `cong-thuc.md` |
| `scripts/kho_text.py` + `kho/kho-text.md` | Kho 82 kiểu chữ CapCut thật của team (6 nhóm H/K/T/M/N/D); chữ nhấn ghi `"kho": "<mã>"` được nhân bản đúng kiểu. gộp chung 1.691 câu chữ mẫu (`kho_text.py cau <từ khoá>`) |
| `scripts/cat_sach.py` | CẮT SẠCH: khớp kịch bản (giữ lần nói đầy đủ cuối), dò vấp bằng tiếng thật, bảng đọc lại, trang duyệt nghe trước/sau, tự nghe lại bản cắt |
| `scripts/cat_vap.py` | Tìm chỗ nói vấp / nói lại / tiếng đệm từ phiên âm, đề xuất đoạn giữ (không cần bộ công cụ ngoài) |
| `scripts/chuan_bi.py` | Chuyển footage, phiên âm, bảng ảnh, tra brief |
| `scripts/tram.py` · `bo_cuc.py` · `chu.py` · `cap_nhat.py` | Chọn cảnh trám đẹp · bố cục chữ né người/sản phẩm · chữ CapCut thật · cập nhật tại chỗ |
| `scripts/tao_sfx.py` · `kiem_may.py` | Tạo bộ tiếng nhấn · kiểm máy |
| `cai-dat/` | Bộ cài tự động (`CAI-DAT.cmd`, `cai-dat.ps1`) + danh sách link tải (`lien-ket.json`) |
| `thuong-hieu/` | Hồ sơ thương hiệu (mẫu + ví dụ) |
| `fonts/` | Be Vietnam Pro (SIL Open Font License — xem `fonts/OFL.txt`) |
| `vi-du/cau-hinh-mau.json` | Cấu hình 1 video mẫu |

**Bảo mật:** không đưa footage, brief, logo của khách lên repo này — để trên máy và trỏ đường dẫn trong hồ sơ / cấu hình dự án.
