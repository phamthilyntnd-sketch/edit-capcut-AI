---
name: edit-capcut-ai
description: Dựng video bán hàng / review / KOC dọc 9:16 từ footage thô (1 clip người nói + vài clip cảnh trám sản phẩm) thành PROJECT CAPCUT SỬA ĐƯỢC + MP4 xem thử, theo hồ sơ thương hiệu (màu, logo, nút kêu gọi, nhãn pháp lý, từ cấm). Tự cắt vấp, chọn đoạn cảnh trám đẹp, chữ nhấn là chữ CapCut thật né người & sản phẩm, chuyển cảnh + hiệu ứng + tiếng nhấn có sẵn, lọc tạp âm, -14 LUFS, kiểm luật quảng cáo, cập nhật TẠI CHỖ project đang góp ý. Dùng khi nói "dựng video này trong CapCut", "edit video bán hàng", "làm video KOC/review cho <thương hiệu>", "sửa lại project <tên>", hoặc /edit-capcut-ai.
---

# Edit video bán hàng thành project CapCut (edit-capcut-ai)

Đầu vào: 1 thư mục footage (1 clip người nói = A-roll, vài clip cận sản phẩm/minh hoạ = cảnh trám), kịch bản/brief (nếu có).
Đầu ra: project CapCut (chữ, chuyển cảnh, hiệu ứng, tiếng nhấn sửa được) + `<MÃ>_thumbnail.png` (+ `<MÃ>_FINAL.mp4` xem thử chỉ khi được yêu cầu).

Cách làm việc với người dùng: **hỏi hết 1 lần ngay đầu, sau đó làm tới xong không hỏi nữa.** Trả lời tiếng Việt, ngắn, không thuật ngữ.

## Câu hỏi đầu (1 lần duy nhất) và lệnh hàng loạt
Đọc yêu cầu → đối chiếu bảng dưới → gom MỌI mục còn thiếu vào **1 lượt hỏi** (AskUserQuestion / 1 tin nhắn). Mục có mặc
định thì KHÔNG hỏi, tự dùng mặc định và ghi vào báo cáo cuối. Sau lượt hỏi đó: **làm tới xong, không hỏi lại** — chỗ không
chắc thì tự quyết theo quy tắc của skill và liệt kê ở báo cáo cuối ("chỗ đã tự quyết"). Ngoại lệ duy nhất: CapCut đang mở
khi tới bước ghi project → nhờ đóng (không tự tắt).

| # | Thông tin | Bắt buộc? | Mặc định nếu không nói |
|---|---|---|---|
| 1 | Thư mục footage (mỗi video 1 thư mục) | bắt buộc | — |
| 2 | Thương hiệu (mã hồ sơ `thuong-hieu/<ma>.json`) | bắt buộc | chưa có hồ sơ → hỏi theo mẫu hồ sơ ở dưới |
| 3 | Người nói NAM hay NỮ (`nguoi_noi`; nam = không mịn da) | bắt buộc | — |
| 4 | Mã video / tên project | không | tên thư mục footage |
| 5 | Chữ thumbnail (dòng 1 dải màu / dòng 2 chữ to) | không | tự rút từ câu hook đầu hoặc brief, ≤ 14 ký tự/dòng |
| 6 | Kịch bản / brief | không | brief trong hồ sơ thương hiệu; không có thì theo lời nói |
| 7 | Clip người nói | không | clip dài nhất |
| 8 | Câu kêu gọi (nút giỏ hàng hiện từ đâu) | không | câu có "giỏ hàng / mua ngay / link" cuối video |
| 9 | MP4 xem thử | không | KHÔNG (nhân sự tự xuất trong CapCut) |
| 10 | Ghi chú riêng (clip không dùng, chữ bắt buộc…) | không | không có |

**Lệnh hàng loạt** (nhân sự dán mẫu "DỰNG HÀNG LOẠT" trong sổ tay — danh sách nhiều video, mỗi dòng: thư mục | mã |
nam/nữ | thumbnail | ghi chú): kiểm đủ mục bắt buộc cho TẤT CẢ video ngay đầu, hỏi 1 lần nếu thiếu, nhờ đóng CapCut 1 lần,
rồi dựng LẦN LƯỢT từng video (mỗi video 1 dự án `projects/<ma>`, `--moi` lần đầu), không dừng giữa chừng; video nào lỗi thì
ghi lại và làm tiếp video sau. Cuối cùng báo 1 bảng: video · project CapCut · ảnh thumbnail · chỗ đã tự quyết · lỗi (nếu có).
Chạy các bước nặng (chuẩn bị footage, dựng) dưới nền; kiểm ổ đĩa ≥ 2 GB × số video trước khi bắt đầu.

**Hồ sơ thương hiệu chưa có** → nhân sự dán mẫu "HỒ SƠ THƯƠNG HIỆU" (mã · tên IN HOA · sản phẩm + đơn vị công bố · ngành ·
màu chính/màu đậm · logo · nút kêu gọi · màu bao bì · tên riêng hay nghe sai · từ cấm · số liệu được phép + nguồn · brief ·
hoạt chất in nghiêng) → tạo `thuong-hieu/<ma>.json` từ `_mau.json` rồi làm tiếp, không hỏi thêm.

## Chung
- `SK` = thư mục skill này. `PY` = Python có faster-whisper, numpy, pillow, onnxruntime (`SK/.venv/Scripts/python.exe` nếu cài theo README). Luôn chạy `PY -I`.
- Cài máy mới: bấm đúp `SK/cai-dat/CAI-DAT.cmd` (tự cài + tải mọi thứ theo `cai-dat/lien-ket.json`). Kiểm: `PY -I SK/scripts/kiem_may.py` phải in SẴN SÀNG. Tiếng nhấn: `PY -I SK/scripts/tao_sfx.py` (tự tổng hợp, không bản quyền).
- Mỗi video = 1 thư mục dự án `<nơi làm việc>/projects/<du-an>/` (raw/, transcript.json, cau-hinh.json, du-an.json…).

## Hồ sơ thương hiệu (`SK/thuong-hieu/<ma>.json`) — làm 1 lần cho mỗi khách
Chép `_mau.json` → `<ma>.json`, điền: `mau_chinh` / `mau_dam` / `mau_vien` (màu chữ, viền thumbnail), `logo` (đường dẫn PNG; hoặc ghi `"logo"` trong cau-hinh.json của dự án), `cta` ("GIỎ HÀNG"…), `nhan_qc.tag` + `nhan_qc.phaply` (tên sản phẩm + đơn vị công bố — luật quảng cáo), `tu_cam` (từ cấm của brief + luật), `mau_san_pham` (MÀU BAO BÌ để máy dò sản phẩm, vd xanh lá nhãn chai), `tu_vung` (tên riêng cho Whisper nghe đúng), `nganh` + `nganh_tra_loi` + `facts` (số liệu được phép lên video kèm nguồn), `brief` (file text brief). Ví dụ đầy đủ: `thuong-hieu/santav.json`. Dự án chọn bằng `"thuong_hieu": "<ma>"` trong cau-hinh.json.
**Không đưa brief/logo/footage của khách vào repo skill** — để trên máy, trỏ đường dẫn.

## Style cố định (đã có trong `scripts/dung.py`)
- **KHÔNG chạy phụ đề suốt video** — chỉ **chữ nhấn nhá** (`nhan`) đúng lúc nói. `"phu_de": true` mới bật phụ đề.
- **CHỈ 2 KIỂU CHỮ** (nhiều kiểu thì rối): `chinh` = chữ MÀU CHÍNH IN HOA, viền trắng + bóng (câu nhấn, câu hỏi, câu chốt) · `nen` = chữ trắng trên nền màu chính bo góc (tên sản phẩm, lợi ích, liệt kê). Không emoji, không tô màu từ khoá, không đổi font. Font Be Vietnam Pro (kèm trong `fonts/`, OFL).
- **CHỮ LÀ CHỮ CAPCUT THẬT** (sửa được): chữ nhấn, thumbnail, nút kêu gọi, nhãn QC, dòng pháp lý; chỉ logo là ảnh. Máy CapCut vẽ chữ lỗi ("Input text") thì đặt `"chu_capcut": false` trong `SK/may.json` → chữ thành ảnh PNG.
- Thumbnail ở khung đầu (`thumb`, `thumb_dur` 2s, `thumb_size`): dòng 1 = chữ trắng trên dải màu thương hiệu bo góc, các dòng sau = chữ TO màu thương hiệu ExtraBold viền trắng dày + bóng (2 chữ CapCut thật: track Thumbnail + Thumbnail 2). Mỗi dòng ≤ ~14 ký tự; câu dài thì `thumb_size` 48–56. Không chạy MP4 vẫn có ảnh `out_thumb` (khung đầu + logo + chữ). Logo góc trái trên, nhãn "Hợp tác quảng cáo" góc phải trên.
- Track CapCut: Hinh chinh (A-roll tắt tiếng xen cảnh trám) · Giong (giọng đã lọc tạp âm) · Logo · Thumbnail · Nhan nha 1..n · Gio hang · Nhan quang cao · Dong phap ly · SFX (+ SFX 2… khi chồng) · (Nhac nen nếu bật).

## Quy tắc bắt buộc (rút ra từ góp ý thật của người dùng — làm đúng từng điểm)
1. **Chữ TUYỆT ĐỐI không che sản phẩm và nhân vật.** Bố cục tự động (`bo_cuc.py`): bản nháp không chữ → u2net tách người → vùng mặt/người; màu bao bì → vùng sản phẩm; trọng số cấm 40/20/30. Chữ không còn chỗ trống thì BỎ (in "Bỏ chữ nhấn vì không còn chỗ trống"), không ép. Cảnh cận sản phẩm: KHÔNG đặt chữ. Nút kêu gọi + dòng pháp lý cũng đi qua bố cục.
2. **Vị trí: luôn CĂN GIỮA ngang, dọc chỉ ở 2 dải cố định** (`chu.ROWS`: dải trên y 260/340/430 — trên đầu người, dưới logo; dải dưới 1120/1240). Thử cỡ 100/85/72/62%. `vi_tri: tren|duoi` ép dải. **Luôn XEM `bang-bo-cuc.jpg`** (đỏ = mặt, vàng = sản phẩm, `c=` điểm đè).
3. **Chữ ĐỒNG BỘ GIỌNG:** mốc chữ = lúc tiếng nói bắt đầu THẬT (đo độ lớn tiếng quanh mốc Whisper, `onset()`), hiện sớm `chu_som` 0,08s; hiệu ứng vào CapCut 0,25s. Không đẩy chữ lùi quá 0,25s (lệch giọng) — chữ quá ngắn thì bỏ. `khi` phải là đúng cụm lời đầu tiên của ý đó (không phải từ giữa câu).
3b. **Nhịp "chữ trước – cảnh sản phẩm sau":** cảnh cận sản phẩm chiếm cả khung → mỗi ý chính: chữ hiện trên hình NGƯỜI NÓI ~1,5–2s (`"den"` = giây cảnh trám bắt đầu) RỒI cảnh trám vào. Câu mà hình đã tự nói rõ thì không cần chữ. Mọi chữ tự tắt khi chữ sau hiện; mỗi chữ ≥ 1,2s; không đặt chữ khi thumbnail còn hiện.
4. **Cảnh trám = ĐOẠN QUAY ĐẸP trong cả clip, khớp lời, đủ dài:** `"from": "auto"` → `tram.py` chấm 4 khung/giây: nét (≥ 200), đủ sáng (0,18–0,92, đẹp ~0,55), có người/sản phẩm, máy ổn định; chọn đoạn liền mạch điểm cao nhất, không trùng đoạn đã dùng. `"tim_trong": [a,b]` khoanh vùng nội dung khớp lời (xem bảng ảnh mỗi 2s của clip), `"tranh"` loại vùng xấu (chai nghiêng/lộn ngược, mờ, bẩn, móp), `"san_pham": true` = cận sản phẩm. Mỗi đoạn ≥ 3s (`tram_min`), bỏ 0,5s đầu/cuối mỗi clip (lúc bấm quay hay rung), ưu tiên đoạn máy ổn định; khe người nói < 1s giữa 2 cảnh trám tự lấp. **XEM `bang-tram.jpg` TỪNG DÒNG** (đầu | giữa | cuối + LỜI ĐANG NÓI lúc đó): chai ĐỨNG THẲNG, nét, sạch, và hình phải KHỚP lời bên cạnh — dòng nào không khớp/không đẹp thì sửa `tim_trong`/`tranh` rồi dựng lại (góp ý 16/11: "cảnh trám lấy chưa đẹp, chưa chuẩn, hơi ngắn").
5. **Cắt vấp KỸ, không cắt cụt chữ:** giữ LẦN NÓI CUỐI. `dung.py` TỰ bám điểm cắt vào ranh giới từ: đầu đoạn lùi về đầu thật của từ, cuối đoạn kéo tới khi đuôi từ tắt hẳn (âm cuối nhẹ "hiệu", "quả" — lỗi "rất hiệ/u/ quả"), không lấn vào từ đã bỏ; mỗi vết cắt giọng có làm mờ 15–20 ms (cả CapCut). Không chia 2 `keeps` giữa 1 câu. Sau khi dựng nghe lại MP4 (word timestamps) → không còn LẶP / ĐỆM (ừ, à, ờ) / từ kéo DÀI.
6. **Không có đoạn chớp:** đoạn người nói < 0,6s kẹp giữa/ngay trước cảnh trám tự được lấp. In track chính (spec.json) kiểm lại.
7. **Chuyển cảnh CapCut ĐA DẠNG theo ngữ cảnh** (`CHUYEN` trong dung.py): người nói → trám (pull-in / slide / wipe / inhale) · → cận sản phẩm (light-sweep-ii / white-flash / twinkle-zoom) · trám → trám khác cảnh (slide / wipe-up / mix / flash) · trám → người nói (pull-out / dissolve / blur / camera-glow). Không lặp kiểu liền nhau, 2 phía ≥ 1,2s, cách nhau ≥ 2,5s, tối đa 10. **Hiệu ứng cảnh** `hieu_ung_capcut` 3–4/video (mini-zoom mở đầu & câu chốt, white-flash khi gọi tên sản phẩm, gleam ở câu cảm xúc cuối). **Hiệu ứng chữ** vào/ra CapCut cho mọi chữ (pop-up/slide-up, fade-out).
8. **Tiếng nhấn NHIỀU, NGHE RÕ, KHỚP HÌNH** (-6…-12 dB so với file, dưới giọng -14 LUFS): tiếng theo kiểu chuyển cảnh (whoosh/swipe/shutter/sparkle/whip), mọi chữ có tiếng ĐÚNG LÚC CHỮ BẬT LÊN và hợp kiểu hiện (`chu.SFX_CHU`: pop-up → pop/bubble, trượt lên → whip; câu hỏi notify), tiếng của chữ luôn thắng tiếng chuyển cảnh khi trùng giờ, chữ bị bỏ thì không còn tiếng, riser 1s trước khi gọi tên sản phẩm, sparkle tên sản phẩm, chime câu chốt, ding + cash ở nút kêu gọi. `"sfx_db": ±3` chỉnh chung.
9. **Lọc tạp âm giọng** (cắt ù < 80 Hz, khử nhiễu nền afftdn, bỏ rít > 14 kHz) cho cả MP4 và CapCut. `"loc_tap_am"` 0–3. Cảnh trám luôn tắt tiếng.
10. **Nhạc nền: KHÔNG tự chèn** — người dùng chọn nhạc có quyền thương mại trong thư viện CapCut (TikTok yêu cầu với video quảng cáo).
11. **Nguyên tắc TikTok:** chữ trong vùng an toàn (y 220–1520, không sát mép phải); hook 3s đầu; nhãn "Hợp tác quảng cáo"; không từ cấm/claim y tế; số liệu chỉ từ `facts`; 9:16 1080×1920; -14 LUFS.
12. **Sửa TẠI CHỖ project đang góp ý, không tạo v2/v3:** `--capcut` mặc định cập nhật project ghi trong `du-an.json` (`cap_nhat.py`: dựng vào `<tên>__moi`, chuyển bản cũ — không xoá — sang `projects/<du-an>/_draft-cu/`, giữ draft_id, sửa danh sách CapCut). Chỉ giữ 1 bản sao lưu gần nhất. `--moi` = tạo project mới (lần đầu). CapCut phải ĐÓNG HẲN (kể cả khay) — nhờ người dùng, không tự tắt. Ổ đĩa phải còn ≥ 2 GB; thiếu thì báo, không tự xoá project khác.

## Quy trình
1. **Footage + kịch bản:** tìm thư mục footage (trống thì tìm .MOV mới ở Downloads/Desktop rồi chép — không di chuyển). Brief: `PY -I SK/scripts/chuan_bi.py brief "<mã>" --th <ma>`.
2. **Chuẩn bị:** `PY -I SK/scripts/chuan_bi.py footage "<thư mục>" <du-an> --th <ma> [--aroll IMG_x]` (chạy nền) → raw/ 1080×1920 30fps, transcript.json (in số đoạn), khoảng lặng, bảng ảnh `xem/`. XEM bảng ảnh từng clip; ghi chú giây nào đẹp/khớp lời.
3. **Cắt vấp:** `PY -I SK/scripts/cat_vap.py projects/<du-an> [--tu <giây bắt đầu nói>]` → liệt kê nói lại / bắt đầu lại câu / nói lại cả đoạn (giữ lần cuối) / tiếng đệm / câu lẻ ngoài kịch bản / lời chen giữa các lần nói lại / Whisper bịa ("subscribe…") / từ kéo dài, và ĐỀ XUẤT `keeps`. Đối chiếu kịch bản, đọc lại từng chỗ rồi chốt `keeps` (chạy được trên mọi máy, không cần bo-skill-video). Có bo-skill-video thì thêm `plan_cuts.py` + `do_am.py` để soát.
4. **Viết `cau-hinh.json`** (mẫu: `SK/vi-du/cau-hinh-mau.json`): `thuong_hieu`, `draft`, `aroll`, `out_mp4`, `out_thumb`, `keeps`, `skip_segments`, `fix` (sửa chữ Whisper nghe sai), `thumb`, `broll` (auto + tim_trong/tranh/san_pham), `nhan` (`{"khi": "<cụm lời như transcript thô>", "sau": <giây>, "kieu": "chinh|nen", "chu": [...], "den": ..., "vi_tri": ...}` — rút ý, ≤ 18 ký tự/dòng, 1 chữ / ~3–4s), `hieu_ung_capcut`, `cta_src`.
5. **Dựng — MẶC ĐỊNH CHỈ LÀM PROJECT CAPCUT** (nhân sự tự xuất trong CapCut, góp ý 16/11): (CapCut đóng hẳn) `PY -I SK/scripts/dung.py projects/<du-an>` (= `--pngs --capcut`; lần đầu thêm `--moi`) → lint phải "no issues", có ảnh thumbnail `out_thumb`. XEM `bang-tram.jpg` (từng dòng: đẹp + khớp lời), `bang-bo-cuc.jpg`, ảnh thumbnail. Sửa cấu hình → chạy lại (cập nhật tại chỗ).
6. **MP4 xem thử + kiểm bản ra (chỉ khi được yêu cầu, hoặc `"xuat_mp4": true`):** `... dung.py projects/<du-an> --pngs --mp4 --qa` (chạy nền) → trích khung ở từng chữ + thumbnail + CTA; đọc `kiem-tra.md`.
7. **Báo kết quả:** tên project, ảnh thumbnail (+ MP4 nếu có), chỗ đoán (nghe không rõ), việc người dùng tự làm (chọn nhạc thương mại trong CapCut, xuất bản cuối từ CapCut).

## Phụ thuộc
Bắt buộc: Python + `requirements.txt`, ffmpeg, Node.js + `capcut-cli` (npm), Chrome/Edge, CapCut desktop.
Tuỳ chọn (tự bỏ qua nếu thiếu): mô hình `u2net_human_seg.onnx` (né người), bộ dùng chung bo-skill-video (chỉnh màu `grade_video`, `plan_cuts`, `do_am`, `kiem_ban_ra`, `an_toan`, `nganh`). Không dùng Remotion (cần giấy phép công ty cho video khách) và không chép mã skill khác.
