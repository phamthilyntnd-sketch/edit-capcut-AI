---
name: edit-capcut-ai
description: Dựng video bán hàng / review / KOC dọc 9:16 từ footage thô (1 clip người nói + vài clip cảnh trám sản phẩm) thành PROJECT CAPCUT SỬA ĐƯỢC + MP4 xem thử, theo hồ sơ thương hiệu (màu, logo, nút kêu gọi, nhãn pháp lý, từ cấm). Tự cắt vấp, chọn đoạn cảnh trám đẹp, chữ nhấn là chữ CapCut thật né người & sản phẩm, chuyển cảnh + hiệu ứng + tiếng nhấn có sẵn, giữ nguyên giọng và màu gốc (V2), kiểm luật quảng cáo, cập nhật TẠI CHỖ project đang góp ý. Dùng khi nói "dựng video này trong CapCut", "edit video bán hàng", "làm video KOC/review cho <thương hiệu>", "sửa lại project <tên>", hoặc /edit-capcut-ai.
---

# Edit video bán hàng thành project CapCut (edit-capcut-ai) — PHIÊN BẢN V2

> **V2 (17/11/2026)** — theo góp ý dựng thật: **KHÔNG chỉnh màu / làm đẹp** (chỉnh màu làm trong CapCut) · **KHÔNG lọc âm** (giữ giọng gốc, chỉ chỉnh to/nhỏ không vượt đỉnh) · **cảnh trám ÍT mà CHẤT** (≥ 4s, có nội dung, ~1 cảnh / 9s, bỏ cảnh điểm thấp) · **xếp cảnh theo kịch bản / nội dung** (khớp lời, theo thứ tự quay).

Đầu vào: 1 thư mục footage (1 clip người nói = A-roll, vài clip cận sản phẩm/minh hoạ = cảnh trám), kịch bản/brief (nếu có).
Đầu ra: project CapCut (chữ, chuyển cảnh, hiệu ứng, tiếng nhấn sửa được) + `<MÃ>_thumbnail.png` (+ `<MÃ>_FINAL.mp4` xem thử chỉ khi được yêu cầu).

Cách làm việc với người dùng: **hỏi hết 1 lần ngay đầu, sau đó làm tới xong không hỏi nữa.** Trả lời tiếng Việt, ngắn, không thuật ngữ.

## BƯỚC 0 — LUÔN DÙNG BẢN MỚI NHẤT
Trước khi làm bất cứ việc gì: `git -C SK pull --ff-only -q` (im lặng; lỗi mạng thì bỏ qua và làm tiếp). Nhờ vậy máy nào dùng
skill cũng tự nhận bản sửa mới nhất trên GitHub. (Bộ cài cũng đặt lịch tự cập nhật khi mở máy + mỗi 2 giờ.)

## V4 — DÙNG KHO HIỆU ỨNG CÓ SẴN CỦA CAPCUT (17/11/2026)
- `kho/capcut.json` (tạo bằng `scripts/kho_capcut.py tao`, đi kèm skill): ~830 mục có sẵn của CapCut — 111 chuyển cảnh,
  311 hiệu ứng cảnh, 59 hiệu ứng nhân vật, 76 kiểu chữ vào, 68 kiểu chữ ra, 51 kiểu chữ lặp, 42 + 22 + 93 hoạt ảnh video
  vào / ra / kết hợp — đã bỏ mục không hợp video bán hàng (ma quái, buồn, biến dạng mặt…), gắn PHONG CÁCH + VAI TRÒ + tiếng.
- PHONG CÁCH theo hồ sơ thương hiệu `"phong_cach"`: `nang_dong` (bán hàng, review) · `sang_trong` (mỹ phẩm, cao cấp — santav)
  · `de_thuong` (mẹ & bé, quà) · `cong_nghe` (điện tử, app) · `co_dien` (retro). Ghi đè từng video bằng cau-hinh.
- Tự áp (mỗi dự án chọn ổn định, không lặp kiểu): mỗi chữ 1 kiểu VÀO + 1 kiểu RA khác nhau; mỗi cảnh trám 1 hoạt ảnh video
  vào / ra (thay cho chuyển cảnh trên lớp phủ); hiệu ứng cảnh tự chọn khi cấu hình không ghi `hieu_ung_capcut`: 1 mở đầu
  + tối đa 3 lần nhấn (tên sản phẩm, câu chốt). Tiếng nhấn theo đúng loại hoạt ảnh (zoom → whoosh, trượt → swipe, lật/xoay →
  whip, nảy → bubble, lấp lánh → sparkle, gõ chữ → tick, nhiễu → shutter…), không để 2 tiếng giống nhau liền nhau.
- **MƯỢT & GỌN (mặc định, góp ý 17/11)**: chỉ chọn trong danh sách đã duyệt `kho_capcut.MUOT` — chữ hiện bật / nảy / trượt /
  mờ dần (KHÔNG xoay, lật, lắc, nhiễu); cảnh trám hiện NHẸ (mờ dần, phóng nhẹ, trượt lên/ngang); KHÔNG hiệu ứng ngay mở đầu
  video; không hiệu ứng chớp / lắc / nhấp nháy (cả khi cấu hình cũ có ghi); hiệu ứng nhấn chỉ loại ánh sáng nhẹ (mini zoom,
  gleam, leak, halo); tiếng nhấn nhẹ, hợp kiểu hiện. Mở toàn bộ kho: `"kho_muot": false`.
- Máy có CapCut Pro (`may.json` `"capcut_pro": true`, mặc định) được dùng cả hiệu ứng Pro; máy miễn phí đặt `false`.
- Tắt kho cho 1 video: `"kho_capcut": false`. Gói Basic vẫn giữ đúng 3 chữ + 3 tiếng, không cảnh trám / hiệu ứng cảnh.

## QUY CHUẨN DỰ ÁN V3 (18/11/2026 — áp dụng mặc định)
- **1 dự án = 1 project CapCut**, tên = `-` + tên folder dự án (vd folder `11B17.2 -STV T11_400K` → project `-11B17.2 -STV T11_400K`).
  Mọi video của dự án nối tiếp trên cùng timeline, **ngăn cách bằng điểm đánh dấu** (tên = mã video); nhân sự tự xuất từng
  đoạn theo điểm đánh dấu.
- Clip để chung trong folder dự án, **đặt tên theo mã ở đầu tên file** (vd `O5_thoai.mov`, `O5_tram1.mov`, `O5 kịch bản.txt`)
  → `ghep_du_an.py chia "<folder>"` nhóm theo mã vào `_lam/footage/<mã>/` (liên kết cứng). Clip thoại = clip dài nhất của mã
  (hoặc tên có "thoai"/"noi" → `--aroll`). Ảnh minh hoạ (jpg/png) trong nhóm = cảnh trám ảnh.
- **Phân lớp**: timeline CHÍNH = video thoại đã cắt vấp hoàn chỉnh (không sót vấp, không lặp nội dung), **GIỮ âm thanh trong
  video** (không tách giọng) · cảnh trám = **lớp phủ** "Canh tram" phía trên, tắt tiếng, khớp lời + kịch bản · chữ, tiếng nhấn ở trên.
- **Âm thanh**: KHÔNG lọc bằng ffmpeg; bật bằng chức năng CapCut **Chuẩn hoá âm lượng + Cải thiện giọng nói + Giảm tiếng ồn**
  cho mọi đoạn thoại (`cap_nhat_am.py` chép cấu trúc từ project MẪU `-MAU` người dùng tạo trên máy — thiếu mẫu thì báo để
  nhân sự bấm tay). **Chỉnh màu + làm đẹp: nhân sự tự chỉnh trong CapCut** (AI không đụng).
- **Nhịp thoại**: không cắt cụt — chừa ~0,2s giữa các câu / đoạn (0,1s mỗi bên chỗ cắt), cuối mỗi video dư ~0,4s (0,3–0,5s).
- **Chữ + tiếng đa dạng**: mỗi chữ 1 kiểu hiện CapCut xoay vòng (`chu.ANIM_POOL`: pop-up, bounce-in, zoom-in, spring, flip-up,
  mini-zoom · slide-up, wipe-right, grow, slide-left, showing-up), tiếng nhấn đi theo đúng kiểu hiện.
- Quy trình: `chia` → mỗi mã: `chuan_bi.py footage` + `cat_vap.py` + viết cau-hinh (`"ma": "<mã>"`) + `dung.py projects/<mã>
  --pngs --capcut --chi-spec` → `ghep_du_an.py ghep "<folder>" <mã1> <mã2> …` (CapCut đóng hẳn; mặc định cập nhật tại chỗ).
- Hỏi hết thắc mắc 1 lần ngay đầu; quyền đã cấp thì tự làm; xong / rõ yêu cầu nào thì phản hồi rõ ngay.

## Câu hỏi đầu (1 lần duy nhất) và lệnh hàng loạt
Đọc yêu cầu → đối chiếu bảng dưới → gom MỌI mục còn thiếu vào **1 lượt hỏi** (AskUserQuestion / 1 tin nhắn). Mục có mặc
định thì KHÔNG hỏi, tự dùng mặc định và ghi vào báo cáo cuối. Sau lượt hỏi đó: **làm tới xong, không hỏi lại** — chỗ không
chắc thì tự quyết theo quy tắc của skill và liệt kê ở báo cáo cuối ("chỗ đã tự quyết"). Ngoại lệ duy nhất: CapCut đang mở
khi tới bước ghi project → nhờ đóng (không tự tắt).

| # | Thông tin | Bắt buộc? | Mặc định nếu không nói |
|---|---|---|---|
| 1 | Thư mục footage (mỗi video 1 thư mục) | bắt buộc | — |
| 2 | Thương hiệu (mã hồ sơ `thuong-hieu/<ma>.json`) | bắt buộc | chưa có hồ sơ → hỏi theo mẫu hồ sơ ở dưới |
| 3 | Kịch bản / thứ tự cảnh (để xếp cảnh trám đúng lời) | không | brief của hồ sơ, không có thì theo lời nói |
| 4 | Mã video / tên project | không | tên thư mục footage |
| 5 | Chữ thumbnail (dòng 1 dải màu / dòng 2 chữ to) | không | tự rút từ câu hook đầu hoặc brief, ≤ 14 ký tự/dòng |
| 6 | Kịch bản / brief | không | brief trong hồ sơ thương hiệu; không có thì theo lời nói |
| 7 | Clip người nói | không | clip dài nhất |
| 8 | Câu kêu gọi (nút giỏ hàng hiện từ đâu) | không | câu có "giỏ hàng / mua ngay / link" cuối video |
| 9 | MP4 xem thử | không | KHÔNG (nhân sự tự xuất trong CapCut) |
| 10 | Ghi chú riêng (clip không dùng, chữ bắt buộc…) | không | không có |

**Đọc file đi kèm trước khi hỏi:** thư mục footage có file tên chứa "kịch bản"/"kich-ban" (lời thoại) hoặc "ghi chú"/
"ghi-chu" (thumbnail, chữ bắt buộc, clip không dùng, thứ tự cảnh) → đọc và áp dụng, không hỏi lại những gì đã ghi (tên có dấu
hay không dấu đều nhận). Thư mục thương hiệu (vd `D:\Khách hàng\<TÊN>\`): "01 - Nhận diện thương hiệu" (Logo, Màu thương
hiệu), "02 - Brief và kịch bản" (Brief, Từ cấm riêng, Số liệu được phép) → dùng khi tạo hồ sơ; "03 - Mẫu tham khảo" chỉ để
tham khảo.

**Lệnh hàng loạt** (nhân sự dán mẫu "DỰNG HÀNG LOẠT" trong sổ tay — danh sách nhiều video, mỗi dòng: thư mục | mã |
thumbnail | ghi chú): kiểm đủ mục bắt buộc cho TẤT CẢ video ngay đầu, hỏi 1 lần nếu thiếu, nhờ đóng CapCut 1 lần,
rồi dựng LẦN LƯỢT từng video (mỗi video 1 dự án `projects/<ma>`, `--moi` lần đầu), không dừng giữa chừng; video nào lỗi thì
ghi lại và làm tiếp video sau. Cuối cùng báo 1 bảng: video · project CapCut · ảnh thumbnail · chỗ đã tự quyết · lỗi (nếu có).
Chạy các bước nặng (chuẩn bị footage, dựng) dưới nền; kiểm ổ đĩa ≥ 2 GB × số video trước khi bắt đầu.

**Gói dựng theo bảng giá TechPro 2026** (`"goi"` trong cau-hinh.json):
- `"basic"` (oneshot – 1 bối cảnh, 1 shot; hậu kỳ "3 text + 3 sound đầu video"): KHÔNG cảnh trám, KHÔNG hiệu ứng cảnh /
  chuyển cảnh; đúng **3 chữ = thumbnail (dải trên) + 2 chữ nhấn trong ~15–20s đầu**, mỗi chữ 1 tiếng (thumbnail whoosh, chữ
  pop/whip); không ding/cash. Không nút giỏ hàng nếu `"cta": false`. Vẫn cắt vấp, giữ nhãn "Hợp tác quảng cáo" + dòng
  pháp lý (bắt buộc, không tính vào 3 chữ). Nhiều cảnh cận tay thao tác → chữ được đè nhẹ lên tay/thân (`trong_so_nguoi`
  0,4, ngưỡng bỏ chữ 2,0) nhưng KHÔNG đè mặt.
- Gói khác (Standard / Delux / Premium…) = mặc định đầy đủ (cảnh trám, 7–20 chữ + tiếng theo kịch bản).
Khách chưa có logo → `"logo": ""` và `"logo_chu": ""` trong hồ sơ: không đặt logo.

**Nhiều thương hiệu trong 1 lệnh** (mẫu "DỰNG NHIỀU THƯƠNG HIỆU": mỗi dòng thêm cột thương hiệu): mỗi video dùng hồ sơ
của đúng thương hiệu dòng đó (`"thuong_hieu"` trong cau-hinh.json của từng dự án — dung.py nạp hồ sơ theo từng dự án). Kiểm
ngay đầu: thương hiệu nào chưa có hồ sơ → hỏi gộp 1 lần theo mẫu hồ sơ (có thể nhiều khối hồ sơ trong 1 tin nhắn).

**Từ cấm KHÔNG cần nhân sự điền**: `thuong-hieu/tu-cam-co-ban.json` = từ cấm cơ bản theo luật quảng cáo ("chung") + theo
ngành ("nganh": my-pham, thuc-pham-chuc-nang, me-va-be, thuc-pham, gia-dung) + câu bắt buộc của ngành; `thuong_hieu.py` tự
gộp với `tu_cam` RIÊNG của khách (chỉ ghi khi brief có thêm). `dung.py` quét chữ trên màn hình + lời nói giữ lại, in
"!! TỪ CẤM…": chữ trên màn hình có từ cấm → BẮT BUỘC sửa chữ; lời nói có từ cấm → cắt câu đó (nếu không làm gãy ý) hoặc
ghi vào báo cáo cuối. Sửa / thêm từ cấm cơ bản: chỉ sửa file json này.

**Hồ sơ thương hiệu chưa có** → nhân sự dán mẫu "HỒ SƠ THƯƠNG HIỆU" (mã · tên IN HOA · sản phẩm + đơn vị công bố · ngành ·
màu chính/màu đậm · logo · nút kêu gọi · màu bao bì · tên riêng hay nghe sai · (từ cấm RIÊNG nếu brief có) · số liệu được phép + nguồn · brief ·
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
- Track CapCut: Hinh chinh (A-roll tắt tiếng xen cảnh trám) · Giong (giọng GỐC, không lọc) · Logo · Thumbnail · Nhan nha 1..n · Gio hang · Nhan quang cao · Dong phap ly · SFX (+ SFX 2… khi chồng) · (Nhac nen nếu bật).

## Quy tắc bắt buộc (rút ra từ góp ý thật của người dùng — làm đúng từng điểm)
1. **Chữ TUYỆT ĐỐI không che sản phẩm và nhân vật.** Bố cục tự động (`bo_cuc.py`): bản nháp không chữ → u2net tách người → vùng mặt/người; màu bao bì → vùng sản phẩm; trọng số cấm 40/20/30. Chữ không còn chỗ trống thì BỎ (in "Bỏ chữ nhấn vì không còn chỗ trống"), không ép. Cảnh cận sản phẩm: KHÔNG đặt chữ. Nút kêu gọi + dòng pháp lý cũng đi qua bố cục.
2. **Vị trí: luôn CĂN GIỮA ngang, dọc chỉ ở 2 dải cố định** (`chu.ROWS`: dải trên y 260/340/430 — trên đầu người, dưới logo; dải dưới 1120/1240). Thử cỡ 100/85/72/62%. `vi_tri: tren|duoi` ép dải. **Luôn XEM `bang-bo-cuc.jpg`** (đỏ = mặt, vàng = sản phẩm, `c=` điểm đè).
3. **Chữ ĐỒNG BỘ GIỌNG:** mốc chữ = lúc tiếng nói bắt đầu THẬT (đo độ lớn tiếng quanh mốc Whisper, `onset()`), hiện sớm `chu_som` 0,08s; hiệu ứng vào CapCut 0,25s. Không đẩy chữ lùi quá 0,25s (lệch giọng) — chữ quá ngắn thì bỏ. `khi` phải là đúng cụm lời đầu tiên của ý đó (không phải từ giữa câu).
3b. **Nhịp "chữ trước – cảnh sản phẩm sau":** cảnh cận sản phẩm chiếm cả khung → mỗi ý chính: chữ hiện trên hình NGƯỜI NÓI ~1,5–2s (`"den"` = giây cảnh trám bắt đầu) RỒI cảnh trám vào. Câu mà hình đã tự nói rõ thì không cần chữ. Mọi chữ tự tắt khi chữ sau hiện; mỗi chữ ≥ 1,2s; không đặt chữ khi thumbnail còn hiện.
4. **Cảnh trám ÍT mà CHẤT, XẾP THEO KỊCH BẢN (V2):** mỗi cảnh ≥ 4s (`tram_min`), có nội dung rõ (điểm `tram.py` < 0,4 → BỎ, giữ hình người nói — `tram_diem_min`), tối đa ~1 cảnh / 9s video (`tram_toi_da`, giữ cảnh điểm cao + dài nhất). Không rải nhiều cảnh ngắn vô nghĩa. **Mỗi cảnh trám phải minh hoạ ĐÚNG câu đang nói / đúng đoạn kịch bản**: xem bảng ảnh mỗi 2s của clip, ghi `"tim_trong": [a,b]` cho TỪNG cảnh (thiếu là dung.py cảnh báo); không có `tim_trong` thì lần dùng sau của cùng clip lấy đoạn SAU lần trước (theo thứ tự quay = thứ tự kịch bản). `"tranh"` loại vùng xấu (chai nghiêng/lộn ngược, mờ, bẩn, móp), `"san_pham": true` = cận sản phẩm. Bỏ 0,5s đầu/cuối clip, ưu tiên máy ổn định; khe người nói < 1s giữa 2 cảnh trám tự lấp. **XEM `bang-tram.jpg` TỪNG DÒNG** (đầu | giữa | cuối + LỜI ĐANG NÓI): hình phải khớp lời và theo đúng trình tự kịch bản — sai thì sửa `tim_trong` rồi dựng lại.
5. **Cắt vấp: NÓI SAI RỒI NÓI LẠI → BỎ TRỌN ĐOẠN NÓI SAI** (góp ý 18/11: "nói sai và nói lại đoạn nào thì cắt bỏ cả đoạn nói sai, chỉ lấy từ đoạn nói đúng"): bỏ từ ĐẦU câu/cụm bị nói hỏng tới ngay trước chỗ bắt đầu nói lại, giữ LẦN NÓI ĐÚNG CUỐI; KHÔNG ghép nửa câu sai với nửa câu đúng, KHÔNG cắt lắt nhắt giữa câu (tiếng đệm lướt nhanh giữa câu giữ lại; mảnh lời < 0,8s kẹp giữa 2 chỗ cắt thì bỏ; chỉ cắt khoảng lặng >= 0,6s). **Phiên âm NGUYÊN VĂN** (`chuan_bi.py` dùng câu mồi kiểu nói vấp + không nối ngữ cảnh, để Whisper KHÔNG "dọn sạch" chữ nói lặp / nói dở — trước đây vì Whisper dọn sạch nên sót đoạn nói hỏng, vd "Hệt như một chiếc giường" + "Hệt như một chiếc giường di động mini"; dự án cũ: `chuan_bi.py nghe-lai <du-an>`). `cat_vap.py` tự tìm (chỉ tính là nói lại khi có ngập ngừng trước lần nói lại, bỏ qua lặp từ phổ biến) — vẫn ĐỌC LẠI từng chỗ. `dung.py` đặt mọi điểm cắt ở chỗ im giữa 2 từ, cuối đoạn kéo tới khi đuôi từ tắt hẳn nhưng KHÔNG BAO GIỜ lấn vào từ đầu tiên của đoạn đã bỏ (lỗi cũ: dính "Vừa…" của lần nói hỏng); mỗi vết cắt giọng làm mờ 15–20 ms. Không chia 2 `keeps` giữa 1 câu. **AI phải ĐỌC LẠI từng câu của bản nguyên văn**: câu bỏ dở không lặp lại chữ nào (vd "Đấy em này nhớ…" rồi im) cũng là đoạn hỏng → bỏ.
6. **Không có đoạn chớp:** đoạn người nói < 0,6s kẹp giữa/ngay trước cảnh trám tự được lấp. In track chính (spec.json) kiểm lại.
7. **Chuyển cảnh CapCut ĐA DẠNG theo ngữ cảnh** (`CHUYEN` trong dung.py): người nói → trám (pull-in / slide / wipe / inhale) · → cận sản phẩm (light-sweep-ii / white-flash / twinkle-zoom) · trám → trám khác cảnh (slide / wipe-up / mix / flash) · trám → người nói (pull-out / dissolve / blur / camera-glow). Không lặp kiểu liền nhau, 2 phía ≥ 1,2s, cách nhau ≥ 2,5s, tối đa 10. **Hiệu ứng cảnh** `hieu_ung_capcut` 3–4/video (mini-zoom mở đầu & câu chốt, white-flash khi gọi tên sản phẩm, gleam ở câu cảm xúc cuối). **Hiệu ứng chữ** vào/ra CapCut cho mọi chữ (pop-up/slide-up, fade-out).
8. **Tiếng nhấn NHIỀU, NGHE RÕ, KHỚP HÌNH** (-6…-12 dB so với file, dưới giọng -14 LUFS): tiếng theo kiểu chuyển cảnh (whoosh/swipe/shutter/sparkle/whip), mọi chữ có tiếng ĐÚNG LÚC CHỮ BẬT LÊN và hợp kiểu hiện (`chu.SFX_CHU`: pop-up → pop/bubble, trượt lên → whip; câu hỏi notify), tiếng của chữ luôn thắng tiếng chuyển cảnh khi trùng giờ, chữ bị bỏ thì không còn tiếng, riser 1s trước khi gọi tên sản phẩm, sparkle tên sản phẩm, chime câu chốt, ding + cash ở nút kêu gọi. `"sfx_db": ±3` chỉnh chung.
9. **KHÔNG lọc âm, KHÔNG chỉnh màu (V2):** giọng giữ GỐC — không khử nhiễu / cắt tần số (làm méo giọng), không nén; chỉ tăng/giảm âm lượng tới gần -14 LUFS nhưng KHÔNG để đỉnh vượt -1 dB (giọng có đỉnh cao thì giữ nhỏ hơn và tiếng nhấn tự hạ theo). Hình giữ GỐC — không chỉnh màu, không mịn da / làm đẹp (khoá `grade` cũ bị bỏ qua); người dựng chỉnh màu và "Giảm tiếng ồn" trực tiếp trong CapCut nếu cần. Chỉ bật lọc âm khi người dùng yêu cầu rõ (`"loc_tap_am": 1–3`). Cảnh trám luôn tắt tiếng.
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
Tuỳ chọn (tự bỏ qua nếu thiếu): mô hình `u2net_human_seg.onnx` (né người), bộ dùng chung bo-skill-video (`plan_cuts`, `do_am`, `kiem_ban_ra`, `an_toan`, `nganh`). Không dùng Remotion (cần giấy phép công ty cho video khách) và không chép mã skill khác.
