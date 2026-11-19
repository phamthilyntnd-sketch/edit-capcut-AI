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

## BỘ KIỂU CHỮ + KHO MẪU CHỮ TIKTOK (19/11/2026)
- **Kho mẫu thật** `kho/mau-chu-tiktok.json`: **1.035 mẫu chữ** lọc từ ~1.950 ảnh bìa video TikTok Việt Nam (16 ngành, 5 loại
  video; 18–20/11/2026 — thêm 829 mẫu từ 23 hashtag ngành hàng), chia **23 nhóm kiểu chữ** (thêm 22 trang trí + sticker lấp lánh,
  24 neon phát sáng, 25 phụ đề tô màu từ khoá), mỗi nhóm có mô tả + **cách dựng lại trong CapCut**. Chỉ lưu nhóm / ngành / loại video, KHÔNG lưu ảnh
  của người khác (trang xem ảnh `KHO-MAU-CHU-TIKTOK.html` chỉ ở máy người dùng, không đưa vào repo).
- Tra cứu: `PY -I SK/scripts/mau_chu.py goi-y <ngành>` (vd `my-pham`, `"Ẩm thực"`) → nhóm hay dùng ở ngành + bộ nên dùng ·
  `mau_chu.py nhom <số>` → công thức 1 nhóm · `mau_chu.py bo` → các bộ skill dựng tự động.
- **Bộ kiểu chữ** (`chu.BO_CHU`) — vẫn CHỈ 2 KIỂU / video (`chinh` + `nen`), bộ chỉ đổi DÁNG; đều là chữ CapCut thật, font
  Be Vietnam Pro kèm skill (đủ dấu):
  `thuong_hieu` (mặc định — màu thương hiệu viền trắng + nhãn nền màu) · `tiktok` (phụ đề trắng bóng mờ + hộp trắng chữ đen) ·
  `hop_trang` (hộp trắng chữ đen + hộp vàng) · `vien_den` (in hoa trắng viền đen kiểu ảnh bìa + nhãn màu) · `ban_hang_nong`
  (vàng viền đen + nhãn đỏ — đồ ăn, khuyến mãi) · `toi_gian` (trắng không viền, sang — trang sức, spa, thời trang).
- Chọn: `"bo_chu": "<tên>"` trong cau-hinh.json (1 video) hoặc hồ sơ thương hiệu (mọi video); `"bo_chu": "tu_dong"` = chọn theo
  ngành (`"nganh"` của cau-hinh / hồ sơ). Không ghi = `thuong_hieu` (giữ đúng brief cũ — SANTAV không đổi).
  Người dùng nói "chữ kiểu TikTok / hộp trắng / viền đen / sang / bán hàng…" → đặt bộ tương ứng, không hỏi lại.
- Nhóm cần font/khung ngoài Be Vietnam Pro (viết tay, chữ phồng dễ thương, chữ có chân, chữ hoạt hình, bảng chữ dày): skill
  KHÔNG tự dựng; ghi công thức của nhóm (từ `mau_chu.py nhom <số>`) vào báo cáo cuối để nhân sự làm tay trong CapCut. Font
  CapCut đã kiểm đủ dấu: CapCut Sans, Montserrat Bold, Anton, Coiny, Sigmar One, Amatic SC, Source Serif 4; font CapCut họ
  "ZY…", Corben, DynaPuff, Bounce House **thiếu dấu tiếng Việt — cấm dùng**.

## ĐA DẠNG TIẾNG NHẤN · CHUYỂN CẢNH · MẶT NẠ (20/11/2026)
- **Mức đa dạng** `"da_dang": "thap" | "thuong" | "cao"` (ngành đặt nền; yêu cầu "nhiều hiệu ứng", "sôi động", "đa dạng",
  "nhiều tiếng", "nhiều chuyển cảnh" → cao; "tối giản", "gọn" → thap). Cao = xoay vòng cả kho tiếng / chuyển cảnh của phong
  cách, +1 chuyển cảnh, +1 mặt nạ. Ghi lại những gì đã dùng: `projects/<du-an>/da-dang.json` (tiếng theo vai, chuyển cảnh, hoạt
  ảnh cảnh trám, mặt nạ) — đọc file này khi báo người dùng.
- **Tiếng nhấn theo VAI** (`scripts/kho_tieng.py`, bảng `kho/cong-thuc.json` "tieng"): chu · tram · chuyen · san_pham · gia
  (chữ có giá / % / giảm…) · cta · hoi · cao_trao · ket. Mỗi vai có danh sách theo phong cách, xoay vòng, không lặp liền nhau;
  tiếng của chữ luôn cùng HỌ với kiểu chữ hiện (pop → pop / pop-2 / bubble…). 26 tiếng tự tạo (`tao_sfx.py`, không bản quyền).
  **THƯA tiếng chuyển cảnh** (góp ý O-5 20/11 "âm thanh chuyển cảnh lặp nhiều quá"): vào cảnh trám KHÔNG có chuyển cảnh thì im;
  chỉ chỗ có chuyển cảnh thật mới có tiếng, tối đa ~1 tiếng / 9s (`"sfx_chuyen_cach"`; bật lại tiếng mọi lần vào cảnh trám:
  `"sfx_vao_tram": true`). Mỗi lần chọn lấy tiếng DÙNG ÍT NHẤT trong video — chỉ lặp khi đã dùng hết tiếng cùng loại.
- **Tiếng THƯ VIỆN CAPCUT** (có mã, CapCut tự tải trên máy khác): skill KHÔNG bịa cấu trúc — học từ draft thật. Người dùng thả
  20–30 tiếng từ CapCut (Âm thanh › Hiệu ứng âm thanh) vào 1 project (tên gợi ý "-KHO TIENG"), lưu, ĐÓNG CapCut, rồi chạy
  `PY -I SK/scripts/kho_tieng.py thu` → `kho/tieng-capcut.json` (mẫu material chép nguyên, vai đoán theo tên — sửa khoá "vai"
  nếu cần; xem: `kho_tieng.py xem`). Khi dựng, tiếng của vai có trong kho được thay bằng tiếng thư viện ở bước CapCut (MP4 xem
  thử vẫn dùng tiếng tự tạo). Kho trống / thiếu vai → tiếng tự tạo. Tắt: `"sfx_thu_vien": false`.
- **Chuyển cảnh theo PHONG CÁCH** (`kho/cong-thuc.json` "chuyen"): sang_trong (dissolve, pull-in, mix, black-fade, light-sweep…),
  nang_dong (pull-in, slide, woosh, horizontal-blur; cao: radial-blur, stretch, squeeze, split), cong_nghe (horizontal-lines,
  vertical-blur; cao: rgb-glitch, glitch, color-glitch), de_thuong (wave, dots; cao: cloud, like), co_dien (vintage-screening…).
  Mỗi dự án bắt đầu xoay ở 1 kiểu khác, không lặp 2 kiểu vừa dùng. Giữ luật: chỉ ở chỗ đổi bối cảnh, tối đa `chuyen_toi_da`
  (≤ 5), cách nhau ≥ `chuyen_cach`, không đặt khi 1 phía < 1,5s. Giữa 2 cảnh trám liền nhau = chuyển cảnh CapCut thật; vào /
  ra cảnh trám từ người nói (khác track) = HOẠT ẢNH vào / ra CapCut cùng cảm giác (pull → zoom-in, slide → slide-left, dissolve
  → fade-in…). Ép danh sách: `"chuyen_vao" / "chuyen_doi" / "chuyen_san_pham" / "chuyen_ra": [slug…]`.
- **Mặt nạ CapCut cho cảnh trám** (`scripts/mat_na.py`, ghi bằng `capcut mask`, mã từ `capcut enums --masks`): bo_goc (thẻ bo
  góc, người nói lộ viền) · tron (khung tròn, cận sản phẩm) · chia_doi (cảnh trám nửa khung, người nói nửa kia) · tim (dễ
  thương). THƯA: `mat_na_toi_da` (mặc định 1, giáo dục / tài chính 0, tối đa 2), ưu tiên cảnh `san_pham`, cảnh ≥ 2,5s, không ở
  1s đầu, không 2 cảnh mặt nạ liền nhau; cảnh có mặt nạ tự thêm hoạt ảnh vào (lộ dần). Tắt: `"mat_na": false`; chọn kiểu:
  `"mat_na_kieu": ["tron"]`; 1 cảnh: `broll[i]["mat_na"]: "tron" | false`. Yêu cầu "chia đôi màn hình", "khung tròn", "không
  mặt nạ" tự đổi. CHƯA làm mặt nạ có keyframe: cấu trúc chưa ai bắt được từ draft thật (capcut-cli #44) — ghi sai thì CapCut im
  lặng bỏ qua.

## CÔNG THỨC DỰNG THEO NGÀNH × LOẠI VIDEO × SẢN PHẨM × YÊU CẦU (19/11/2026)
- `kho/cong-thuc.json` + `scripts/cong_thuc.py`: `dung.py` TỰ ÁP ngay khi đọc cau-hinh — điền các thông số còn trống
  (phong cách hiệu ứng, bộ kiểu chữ, nhịp cắt / khoảng chừa giữa câu, số & độ dài cảnh trám, chuyển cảnh, hiệu ứng cảnh,
  phóng khung, mức tiếng nhấn). KHÔNG ghi đè khoá đã có trong cau-hinh.json. Ưu tiên: cau-hinh > `yeu_cau` > hồ sơ thương
  hiệu (khoá ghi rõ trong file) > loại video > ngành. Giới hạn an toàn: tiếng nhấn −6…+4 dB, chuyển cảnh ≤ 5, hiệu ứng ≤ 3, mặt nạ ≤ 2.
- **16 ngành** (`nganh`): my-pham, spa-tham-my, trang-suc, thoi-trang, am-thuc, do-uong, gia-dung, cong-nghe, me-va-be,
  thuc-pham-chuc-nang, du-lich, bat-dong-san, xe, giao-duc, tai-chinh, dich-vu (không ghi → theo hồ sơ, rồi tự đoán theo lời nói).
- **10 loại video** (`loai_video`): review, mo_hop, so_sanh, huong_dan, top_n, khuyen_mai, ke_chuyen, hoi_thoai, phan_hoi,
  dia_diem (không ghi → tự đoán; mặc định review). Mỗi loại có KHUNG (hook → … → kêu gọi).
- **Yêu cầu bằng lời** (`"yeu_cau": "<lời người dùng>"`): ghi NGUYÊN câu người dùng nói về cách dựng ("sôi động hơn", "sang",
  "ít chữ", "nhiều hiệu ứng", "nhịp nhanh", "nhiều cảnh trám", "chốt đơn", "kiểu chữ team", "hộp trắng"…) — công thức tự đổi
  đúng thông số. Danh sách: `PY -I SK/scripts/cong_thuc.py ds`; xem trước 1 dự án: `cong_thuc.py xem projects/<du-an>`.
- **AI ĐỌC `projects/<du-an>/cong-thuc.md` TRƯỚC KHI VIẾT `nhan`**: mật độ chữ gợi ý (chữ / phút), khung video theo loại, lưu ý
  ngành, **gợi ý chữ theo sản phẩm** (giá → số to, ưu đãi → nhãn, thông số → chữ to / danh sách, thành phần → danh sách — rút
  từ lời nói + kịch bản). Chạy `cong_thuc.py xem` sau khi có transcript để có file này trước khi viết chữ.
- **MẶC ĐỊNH `"bo_chu": "kho_team"`** (người dùng 19/11: "edit chưa ra được các text như trong kho"): mỗi chữ nhấn tự gắn
  kiểu kho team theo VAI (hook · ý chính · từ khoá / thông số · danh sách · mô tả · tên SP · giá · ưu đãi · CTA; kiểu theo
  ngành trong cong-thuc.json) và **đổi màu nhấn của kiểu sang màu thương hiệu** đang dựng (trắng / đen giữ nguyên). Chữ đã
  ghi `"kho"` thì giữ. Bộ chữ gợi ý theo ngành / loại video KHÔNG còn thay kho; chỉ đổi khi cau-hinh ghi `bo_chu` khác,
  yêu cầu bằng lời ("hộp trắng", "chốt đơn"…) hoặc hồ sơ khoá (`_ro`). **MP4 xem thử cũng vẽ đúng kiểu kho**
  (`chu.html_kho`: font, màu, viền, bóng, nền; hiệu ứng chữ 3D / neon / phụ đề giải trí và hoạt ảnh chỉ thấy trong CapCut).
  Chữ dài hơn mẫu tự co nhưng không dưới 72%. Font kho không có trên máy → luôn thay bằng font kèm skill đủ dấu (xoá mã font
  thư viện của máy làm kho — trước đây máy khác bị lỗi font). Xem 82 kiểu: trang demo `KHO-TEXT-TEAM-DEMO.html` hoặc dự án
  CapCut "-KHO TEXT".
- **Không lặp 1 kiểu** (người dùng 19/11: "nhiều kiểu đẹp mà toàn dùng 1 kiểu rất xấu"): mỗi video tự chọn 1 BỘ KIỂU kho
  (`cong_thuc.BO_KHO`: dam_vien_den · hai_mau_nau · do_trang · neon_nghieng (chỉ ẩm thực / đồ uống / du lịch); ít dùng:
  trang_vien_mau · pastel_vien_kem) — các kiểu cùng 1 dự án team (đồng bộ font / viền / bóng), đổi bộ giữa các video theo
  tên dự án; trong video xoay vòng kiểu của từng vai, 2 chữ liền nhau không cùng kiểu. Chọn bộ: `"bo_kho": "<tên>"`.
- Hồ sơ SANTAV nay cũng `bo_chu: kho_team` (kiểu kho, màu xanh SANTAV). Muốn kiểu cũ: `"bo_chu": "thuong_hieu"` trong cau-hinh.

## CHẾ ĐỘ MIKE — GỌI /edit-video-mike-2, KHÔNG CHÉP MIKE (20/11/2026)
Người dùng muốn dùng hệ sinh thái Mike mà vẫn chỉ gọi `/edit-capcut-ai` và sửa trong CapCut. **Giấy phép Mike: 1 người dùng,
cấm chia sẻ / đăng tải file Mike và cấm dùng mã / thiết kế Mike làm skill khác** → repo này KHÔNG chứa file, mã hay hiệu ứng
nào của Mike, không viết lại hiệu ứng Mike; chỉ GỌI Mike đã cài trên máy (`~/.claude/skills/edit-video-mike-2`, có
`LICENSE-INFO.txt`) và ĐỌC kết quả Mike xuất ra. Máy chưa có Mike → bỏ qua mọi bước Mike, dựng CapCut như thường, báo 1 dòng.
Bộ cài (bước 6b) hỏi file ZIP Mike của CHÍNH người dùng máy đó; mỗi người dùng cần bản quyền Mike riêng.
Chọn chế độ trong cau-hinh `"mike"` (hoặc theo lời người dùng; mặc định TẮT — Mike nặng máy, ~1–1,5 GB / video):
- **`"diem_nhan"` (khuyên dùng cho video chủ lực)**: dựng CapCut như thường, Mike chỉ làm 2–4 câu đắt giá (câu mở đầu với chữ
  sau đầu, 1–2 cảnh đồ hoạ, câu chốt). Quy trình:
  1. Sau `cat_sach --chot` + viết `nhan`: chọn câu (giây nguồn), `PY -I SK/scripts/dung.py projects/<du-an> --mike-edl
     "3.2-8.5,40-46"` → `projects/<du-an>/mike-edl.json` = đúng các đoạn giữ của video này trong những câu đó.
  2. Làm theo SKILL.md của Mike cho 1 dự án nhỏ `<projectsDir Mike>/<du-an>-diem-nhan`: `takes.py` với CHÍNH clip A-roll
     gốc (đổi `clip` trong mike-edl.json đúng mã clip takes.py đặt, thường `c1`), chép mike-edl.json thành `edl.json` (KHÔNG tự
     chọn lại đoạn — lệch là không ghép được), rồi các bước aroll → storyboard (chỉ các câu đó) → build → render → finish.
  3. cau-hinh `"mike_diem_nhan": ["<thư mục dự án Mike nhỏ>"]` → dựng lại: đoạn render Mike phủ đúng giây (lớp **"Mike"** trong
     CapCut, tắt tiếng; MP4 cũng phủ); chữ nhấn của skill trùng khung đó tự bỏ; đoạn nào không khớp vết cắt (> 0,15s) bị bỏ và in
     cảnh báo.
- **`"cat"` (mượn nhịp cắt)**: đã có dự án Mike của CÙNG clip A-roll → `"mike_cat": "<thư mục dự án Mike>"`: dùng edl.json của
  Mike làm `keeps` (lần nói sạch cuối, bỏ lặng > 0,45s, shot ≥ 1,5s). Không vẽ gì thêm, không nặng máy.
- **`"tron"` (Mike trọn video)**: dựng cả video bằng `/edit-video-mike-2` (đủ hiệu ứng, chữ sau đầu, editor Mike), rồi (CapCut đóng)
  `PY -I SK/scripts/mike_capcut.py "<dự án Mike>" [--chu-capcut]` → project CapCut `<tên>-capcut`: A-roll theo vết cắt Mike ·
  B-roll · "Hieu ung Mike" (đoạn đồ hoạ từ bản render, chỉ cắt / dời / xoá được) · phụ đề (ảnh đúng kiểu Mike, hoặc chữ CapCut
  Be Vietnam Pro với `--chu-capcut`) · nhạc nền · SFX. Không bao giờ ghi đè draft (tạo `-v2`, `-v3`…).
- **Luật dựng điểm nhấn Mike (góp ý người dùng 19/11 sau bản thử 1):** KHÔNG dùng khung vuông chụp vào mặt (`locked_on`);
  KHÔNG dùng cảnh phủ kín khung (canvas, old_to_new, two_cards…) ở câu nói về CHI TIẾT SẢN PHẨM — sản phẩm trên tay phải luôn
  thấy; chữ đặt TRÊN ĐẦU (`Reel(place='top')`) hoặc SAU ĐẦU ('back'), biển LED sau đầu cho tên thương hiệu. Dự án Mike nhỏ đặt
  trong `projects/<du-an>/mike-*` (không để ở thư mục dự án Mike chung); bản render tự chép vào `projects/<du-an>/mike/`.
  Câu mở đầu là điểm nhấn Mike → thumbnail chỉ còn ở khung đầu (ảnh bìa). Tạp âm nền: `"loc_tap_am": 2` cho MP4; trong CapCut
  bật "Giảm tiếng ồn" trên đoạn giọng (hoặc tạo project mẫu `-MAU` để skill tự bật).
- **Cảnh trám ƯU TIÊN hơn điểm nhấn Mike** (góp ý 19/11 "chưa lấy đủ cảnh trám phù hợp nội dung"): chỗ có cảnh trám khớp lời,
  đoạn Mike tự cắt ra cho cảnh trám hiện (Mike còn lại giữ đúng giây); chữ nhấn của skill chỉ bỏ ở phần Mike còn hiện. Vẫn phải
  xếp ĐỦ cảnh trám theo lời (mỗi ý có cảnh quay tương ứng → 1 cảnh; nâng `tram_toi_da` khi clip quay nhiều ý).
- Đã thử 20/11 (EYEMEDI Kb4): `mike_capcut.py --check` OK (A-roll 10 · B-roll 9 · hiệu ứng 8 · phụ đề 48); `mike_diem_nhan` với
  dự án Mike cũ của Kb4: 9/10 đoạn khớp vết cắt, 1 đoạn lệch 0,2s bị bỏ đúng như thiết kế.

## 25 KIỂU CHỮ TIKTOK DỰNG ĐƯỢC + CHỌN FONT THEO TÌNH HUỐNG (20/11/2026)
Người dùng: "sưu tầm nhiều kiểu đẹp mà lúc edit không dùng" + "có phân được khi nào dùng font nào không". `kho/kieu-tiktok.json`
= 25 kiểu chữ CapCut THẬT (mã `TT01`…`TT27`) dựng từ 23 nhóm kho 1.035 mẫu TikTok; `kho_text.py` sinh vật liệu chữ CapCut
(font, màu, viền, bóng, nền, giãn chữ, chữ 2 tầng, hoạt ảnh mượn từ kho team), `chu.html_kho` vẽ đúng kiểu cho MP4 xem thử.
- **MẶC ĐỊNH `bo_kho: "tiktok"`**: mỗi chữ nhấn gắn kiểu theo VAI (`cong_thuc.VAI_NHOM`: hook · ý chính · từ khoá · giá · ưu đãi ·
  tên SP · CTA · danh sách · mô tả); trong mỗi vai, nhóm nào **ngành đó dùng nhiều nhất trong kho mẫu thật** được chọn trước
  (`cong_thuc.bo_tiktok(ngành)`), mỗi vai 1 kiểu (ý chính 2 kiểu xoay vòng) → video gọn ~3–4 họ font. Các bộ kho team cũ vẫn chọn
  được bằng `"bo_kho": "dam_vien_den"|...`; ép từng chữ: `"kho": "TT09"`.
- **Font theo tình huống** (font kèm skill trong `fonts/`, OFL, đã kiểm đủ dấu tiếng Việt — máy khác cập nhật là có):
  Anton = giá / số to, câu hook in hoa viền đen · Playfair Display = sang trọng (mỹ phẩm cao cấp, trang sức, spa, BĐS hạng sang,
  nhà hàng) · Dancing Script = viết tay mềm (son phấn, cafe, quà, thời trang nữ) · Lobster = chữ "Review" ảnh bìa ·
  Coiny / Baloo 2 = dễ thương (mẹ bé, trà sữa, đồ ăn vặt, nail) · Sigmar One = trẻ em · Chakra Petch = công nghệ / xe / game ·
  Paytone One = neon / khai trương · Amatic SC = handmade, vintage · Montserrat Bold = tối giản giãn chữ, tiêu đề 2 tầng ·
  Be Vietnam Pro 600–900 = phụ đề, nhãn, hộp chữ, câu hỏi, bán hàng nóng. Viết tay / chữ có chân giữ chữ thường, còn lại in hoa.
- Màu nhấn của kiểu đổi sang màu chữ video (`kho_doi_mau`, kể cả viền / quầng neon); `TT17` bán hàng nóng giữ vàng viền đen.
- Bảng so 25 kiểu với mẫu thật: chạy lại `KIEU-CHU-TIKTOK-DUNG-*.jpg` (máy người dùng).

## MÀU CHỮ TỰ CHỌN THEO THƯƠNG HIỆU · SẢN PHẨM · VIDEO (20/11/2026)
Người dùng: "skill tự nhận diện màu sản phẩm, video, thương hiệu để chọn màu cho phù hợp". `scripts/mau_tu_dong.py`
(tự gọi khi nạp hồ sơ): gom màu có sắc rõ từ **logo** (x3), **màu bao bì** `mau_san_pham` + màu hồ sơ (x2–3), **cảnh trám /
cận sản phẩm** đang dùng trong `broll` (vùng giữa khung, x2); bỏ trắng / đen / xám / da người. **Nền video** (A-roll) là
đối trọng: sắc độ nào phủ nhiều trên nền bị trừ mạnh (chữ trùng nền sẽ chìm). Chọn sắc điểm cao nhất, GIỮ tính cách màu gốc
(hồng pastel vẫn hồng) nhưng kẹp độ đậm / sáng để đọc rõ → `mau_chinh`, `mau_dam`, `mau_vien`. Không có màu sản phẩm /
thương hiệu rõ (vd gọng kính trong) → màu TƯƠNG PHẢN nền (nền ấm → xanh dương, nền lạnh → vàng).
- Khi nào tự chọn: hồ sơ thương hiệu KHÔNG ghi `mau_chinh`; hoặc hồ sơ `"mau_tu_dong": true`; hoặc cau-hinh `"mau": "tu_dong"`.
  Hồ sơ đã ghi màu (vd SANTAV #6CBE45) → giữ đúng màu brief. Ép tay: cau-hinh `"mau": "#RRGGBB"`; giữ màu hồ sơ: `"mau": "thuong_hieu"`.
- Kết quả: `projects/<du-an>/mau.json` (lý do + nguồn; xoá để dò lại) + `mau.jpg` (dải sắc độ nguồn / nền + ô màu). XEM `mau.jpg`
  khi báo kết quả. Chữ kho team đổi màu nhấn sang màu này (`kho_doi_mau`).
- Thử 20/11: EYEMEDI Kb4 (gọng trong, kệ gỗ ấm) → xanh dương #2F7AEB; Kb5 (hộp kính hồng) → hồng #CC5B65.

## KHO CHỮ CAPCUT CỦA TEAM — 82 kiểu thật (19/11/2026)
- `kho/kho-text.md`: 82 kiểu chữ lấy từ 21 dự án team đã edit trong CapCut (job 11B14 → 11B18, có cả chỉnh tay), 6 nhóm:
  **H** Hook / tiêu đề mở đầu · **K** Từ khoá TO · **T** Ý chính / tính năng · **M** Mô tả / phụ đề · **N** Nhãn có nền / CTA ·
  **D** Chữ đặc biệt (ART vàng 3D, neon, bong bóng). Mỗi kiểu là chữ CapCut thật: font, màu, viền, bóng, hiệu ứng chữ, hoạt ảnh.
  CHỈ ĐỌC phần danh mục + "Quy tắc chọn chữ" ở đầu file (phần `<!--KHO ...-->` cuối file là dữ liệu cho công cụ).
- Tra nhanh: `PY -I SK/scripts/kho_text.py ds [H|K|T|M|N|D]` · `kho_text.py xem <mã>` · `kho_text.py cau <từ khoá>`.
- DÙNG: trong `nhan` của cau-hinh.json thêm `"kho": "<mã>"` (vd `{"khi": "...", "kieu": "chinh", "chu": [...], "kho": "H02"}`)
  → `dung.py` nhân bản ĐÚNG kiểu đó cho chữ (giữ nội dung, thời gian, vị trí do bố cục chọn; tự thu nhỏ khi chữ dài hơn mẫu;
  dùng hoạt ảnh của kiểu, không gắn hoạt ảnh xoay vòng). Chữ không ghi `kho` vẫn theo bộ kiểu chữ `bo_chu` như cũ.
- Chọn theo quy tắc của kho: 1 Hook (H) phủ câu mở đầu → 3–5 Ý chính (T) / Từ khoá (K) dồn vào 2/3 đầu → Nhãn/CTA (N);
  cả video giữ 1 họ font + 1 màu thương hiệu; nhóm D chỉ cho tên quán / khẩu hiệu, 1–2 lần / video. Màu của kiểu là màu
  thương hiệu của dự án gốc — chọn kiểu có màu hợp thương hiệu đang dựng (hoặc chỉ dùng kiểu trắng / đen).
- Font: font cài riêng trên máy người làm kho được thay bằng font kèm skill (đủ dấu tiếng Việt): Montserrat* → Montserrat
  Bold · Be Vietnam Pro / Lexend Deca / Phudu / Helvetica / SVN-Gilroy / UTM Flavour → Be Vietnam Pro cùng độ đậm (Black →
  900). Font / hiệu ứng / hoạt ảnh có mã thư viện CapCut thì CapCut tự tải trên máy khác.
- Bản MP4 xem thử vẫn vẽ chữ theo `bo_chu` (không có kiểu kho) — kiểu kho chỉ hiện đúng trong project CapCut.
- **Câu chữ mẫu** (gộp chung trong `kho/kho-text.md`, mục `## CÂU CHỮ MẪU` cuối file): 1.691 câu chữ trên màn hình của 81 dự
  án (hook, tên SP, CTA theo từng clip). Không đọc cả mục — tra `PY -I SK/scripts/kho_text.py cau <từ khoá>` (ngành / sản phẩm /
  "giỏ hàng"…) để viết chữ nhấn cùng giọng team. Nội dung của khách: chỉ học cách viết, KHÔNG chép nguyên văn cho thương hiệu khác.

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
- **Nhịp thoại**: không cắt cụt — chừa ~0,2s giữa các câu / đoạn, cuối mỗi video dư ~0,4s (0,3–0,5s). Điểm cắt BÁM TIẾNG NÓI THẬT
  (đo độ lớn tiếng, ngưỡng riêng từng clip) chứ không bám mốc giây trong cấu hình; mọi quãng im >= 0,35s bên trong cũng rút còn
  ~0,2s (góp ý 17/11 "còn đoạn trống") — không cắt vào chữ bình thường (phụ âm đầu nhẹ "gh/th" vẫn giữ).
- **Ít hiệu ứng (góp ý 17/11 "quá nhiều chuyển cảnh -> rối")**: cảnh trám vào/ra bằng CẮT THẲNG (hoạt ảnh tắt mặc định,
  `"hoat_anh_tram": true` để bật); chuyển cảnh tối đa 2 / video, cách nhau >= 8s; hiệu ứng cảnh tối đa 2 / video.
- **Chữ trong vùng an toàn**: cỡ chữ CapCut nhỏ hơn ~23% bản cũ (`chu.PX_PER_SIZE` 5.2) và tự xuống dòng trong 78% chiều ngang
  (`chu.LINE_MAX`) -> không tràn mép, né cột nút TikTok bên phải.
- **Chữ + tiếng đa dạng**: mỗi chữ 1 kiểu hiện CapCut xoay vòng (`chu.ANIM_POOL`: pop-up, bounce-in, zoom-in, spring, flip-up,
  mini-zoom · slide-up, wipe-right, grow, slide-left, showing-up), tiếng nhấn đi theo đúng kiểu hiện.
- Quy trình: `chia` → mỗi mã: `chuan_bi.py footage` + `cat_sach.py` (kịch bản → `kich-ban.txt`) + viết cau-hinh (`"ma": "<mã>"`) + `dung.py projects/<mã>
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
| 11 | Ngành / loại video / yêu cầu cách dựng ("sôi động", "sang", "ít chữ"…) | không | ngành theo hồ sơ, loại video tự đoán; ghi lời người dùng vào `yeu_cau` (xem CÔNG THỨC DỰNG) |

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
- **CHỈ 2 KIỂU CHỮ** (nhiều kiểu thì rối): `chinh` = chữ MÀU CHÍNH IN HOA, viền trắng + bóng (câu nhấn, câu hỏi, câu chốt) · `nen` = chữ trắng trên nền màu chính bo góc (tên sản phẩm, lợi ích, liệt kê). Dáng của 2 kiểu đổi theo **bộ kiểu chữ** (`bo_chu`, xem mục BỘ KIỂU CHỮ ở trên). Không emoji, không tô màu từ khoá, không đổi font. Font Be Vietnam Pro (kèm trong `fonts/`, OFL).
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
7. **Chuyển cảnh CapCut ĐA DẠNG theo ngữ cảnh + phong cách** (`bo_chuyen` trong dung.py, danh sách ở `kho/cong-thuc.json` "chuyen" — xem mục ĐA DẠNG): người nói → trám · → cận sản phẩm (ánh sáng, không chớp trắng) · trám → trám khác cảnh · trám → người nói. Không lặp kiểu vừa dùng, 2 phía ≥ 1,5s, cách nhau ≥ `chuyen_cach`, tối đa `chuyen_toi_da`. **Hiệu ứng cảnh** `hieu_ung_capcut` ≤ `hieu_ung_toi_da` (không chớp / lắc, không ngay mở đầu). **Hiệu ứng chữ** vào/ra CapCut cho mọi chữ (pop-up/slide-up, fade-out).
8. **Tiếng nhấn NHIỀU, NGHE RÕ, KHỚP HÌNH, ĐA DẠNG** (-6…-12 dB so với file, dưới giọng -14 LUFS): mỗi điểm nhấn 1 tiếng theo VAI (kho_tieng.py) — chữ có tiếng ĐÚNG LÚC CHỮ BẬT LÊN, cùng họ với kiểu hiện; vào cảnh trám, chuyển cảnh, tên sản phẩm (lấp lánh), giá / ưu đãi (coin), câu hỏi, cao trào 1s trước tên sản phẩm, câu chốt, nút kêu gọi; tiếng của chữ luôn thắng tiếng chuyển cảnh khi trùng giờ; chữ bị bỏ thì không còn tiếng; xoay vòng không lặp liền nhau; tiếng thư viện CapCut thay vào khi kho có. `"sfx_db": ±3` chỉnh chung.
9. **KHÔNG lọc âm, KHÔNG chỉnh màu (V2):** giọng giữ GỐC — không khử nhiễu / cắt tần số (làm méo giọng), không nén; chỉ tăng/giảm âm lượng tới gần -14 LUFS nhưng KHÔNG để đỉnh vượt -1 dB (giọng có đỉnh cao thì giữ nhỏ hơn và tiếng nhấn tự hạ theo). Hình giữ GỐC — không chỉnh màu, không mịn da / làm đẹp (khoá `grade` cũ bị bỏ qua); người dựng chỉnh màu và "Giảm tiếng ồn" trực tiếp trong CapCut nếu cần. Chỉ bật lọc âm khi người dùng yêu cầu rõ (`"loc_tap_am": 1–3`). Cảnh trám luôn tắt tiếng.
10. **Nhạc nền: KHÔNG tự chèn** — người dùng chọn nhạc có quyền thương mại trong thư viện CapCut (TikTok yêu cầu với video quảng cáo).
11. **Nguyên tắc TikTok:** chữ trong vùng an toàn (y 220–1520, không sát mép phải); hook 3s đầu; nhãn "Hợp tác quảng cáo"; không từ cấm/claim y tế; số liệu chỉ từ `facts`; 9:16 1080×1920; -14 LUFS.
12. **Sửa TẠI CHỖ project đang góp ý, không tạo v2/v3:** `--capcut` mặc định cập nhật project ghi trong `du-an.json` (`cap_nhat.py`: dựng vào `<tên>__moi`, chuyển bản cũ — không xoá — sang `projects/<du-an>/_draft-cu/`, giữ draft_id, sửa danh sách CapCut). Chỉ giữ 1 bản sao lưu gần nhất. `--moi` = tạo project mới (lần đầu). CapCut phải ĐÓNG HẲN (kể cả khay) — nhờ người dùng, không tự tắt. Ổ đĩa phải còn ≥ 2 GB; thiếu thì báo, không tự xoá project khác.

## Quy trình
1. **Footage + kịch bản:** tìm thư mục footage (trống thì tìm .MOV mới ở Downloads/Desktop rồi chép — không di chuyển). Brief: `PY -I SK/scripts/chuan_bi.py brief "<mã>" --th <ma>`.
2. **Chuẩn bị:** `PY -I SK/scripts/chuan_bi.py footage "<thư mục>" <du-an> --th <ma> [--aroll IMG_x]` (chạy nền) → raw/ 1080×1920 30fps, transcript.json (in số đoạn), khoảng lặng, bảng ảnh `xem/`. XEM bảng ảnh từng clip; ghi chú giây nào đẹp/khớp lời.
3. **Cắt vấp — CẮT SẠCH (19/11/2026, thay bước cat_vap):**
   a. Ghi **lời thoại kịch bản** vào `projects/<du-an>/kich-ban.txt` (mỗi câu 1 dòng, lấy từ brief — cột lời thoại; hoặc
      `"kich_ban"` trong cau-hinh). Không có kịch bản vẫn chạy được, chỉ thiếu phần khớp kịch bản.
   b. `PY -I SK/scripts/cat_sach.py projects/<du-an> [--tu <giây>] [--hoi-thoai]` → (1) nghe lại riêng các câu có từ dài bất
      thường (Whisper nuốt chỗ vấp) và siết mốc từng từ theo tiếng thật; (2) mọi luật của `cat_vap.py`; (3) **khớp kịch bản**:
      mỗi câu kịch bản giữ LẦN NÓI ĐẦY ĐỦ CUỐI CÙNG, bỏ các lần khác (kể cả nói lại bằng câu chữ khác) + lời ngoài lề ngắn,
      kéo lại chữ đầu câu bị gán lệch; (4) **dò bằng tiếng thật**: vùng có tiếng mà không thành chữ, 1 từ bị lắp ("sả… sản"),
      từ kéo dài / ậm ừ ("em… ờờ") → cắt cứng (`cat_tieng`). Ra `cat/bang-cat.md` + `cat/de-xuat.json`.
   c. **AI ĐỌC `cat/bang-cat.md`** như người dựng: câu kịch bản THIẾU, câu bỏ dở, lời ngoài lề có đáng giữ (dòng ⚠xem),
      chỗ cắt làm mất nghĩa → sửa `don_vi[].giu` (`giu` / `bo` / `mot_phan`) trong `cat/de-xuat.json`.
   d. (tuỳ chọn, khi người dùng muốn tự nghe) `cat_sach.py projects/<du-an> --duyet` → `cat/duyet.html`: từng chỗ cắt có nút
      nghe TRƯỚC / SAU, bấm Cắt / Giữ lại, tải `duyet.json` vào thư mục `cat/` (hoặc dán kết quả cho AI).
   e. `cat_sach.py projects/<du-an> --chot` → ghi `keeps` + `cat_tieng` vào cau-hinh.json (sao lưu `cau-hinh.truoc-cat.json`).
   f. `cat_sach.py projects/<du-an> --kiem` → dựng tiếng bản đã cắt (đúng điểm cắt thật của dung.py), NGHE LẠI, tự bỏ chỗ
      còn lặp / tiếng đệm, báo khoảng lặng > 0,45s → `cat/kiem.md` (≈30s / video 1 phút).
   Đo 19/11 so với bản cắt tay đã duyệt: O-5 đúng 86% → **100%** (đủ 99%), T-5 98% → **99%** (đủ 100%), C-6 hội thoại giữ 100%.
   `dung.py`: khoảng chừa ở vết cắt tự theo nhịp người nói (0,14–0,24s), cắt cứng `cat_tieng`, mỗi đoạn thoại trên track
   chính CapCut được làm mờ tiếng vào 15 ms / ra 20 ms (không nghe "tách").
   Cách cũ (chỉ dò theo chữ): `PY -I SK/scripts/cat_vap.py projects/<du-an> [--tu <giây bắt đầu nói>]` → liệt kê nói lại / bắt đầu lại câu / nói lại cả đoạn (giữ lần cuối) / tiếng đệm / câu lẻ ngoài kịch bản / lời chen giữa các lần nói lại / Whisper bịa ("subscribe…") / từ kéo dài, và ĐỀ XUẤT `keeps`. Đối chiếu kịch bản, đọc lại từng chỗ rồi chốt `keeps` (chạy được trên mọi máy, không cần bo-skill-video). Có bo-skill-video thì thêm `plan_cuts.py` + `do_am.py` để soát.
   - **Video HỘI THOẠI (2 người nói qua lại):** `cat_vap.py ... --hoi-thoai` (hoặc `"hoi_thoai": true` trong cấu hình) — tắt dò bắt đầu lại câu / tiếng đệm (người kia đáp "ừ", "dạ" là lời thật), chỉ bỏ câu lặp gần y hệt.
   - Phiên âm tự chạy nhiều lượt (giữ nguyên tiếng vấp → thêm lọc lặng → thường) và chọn lượt phủ đủ cả clip; vẫn thấy hở thì `chuan_bi.py nghe-lai <du-an>`.
4. **Viết `cau-hinh.json`** (mẫu: `SK/vi-du/cau-hinh-mau.json`): `thuong_hieu`, `draft`, `aroll`, `out_mp4`, `out_thumb`, `keeps`, `skip_segments`, `fix` (sửa chữ Whisper nghe sai), `thumb`, `broll` (auto + tim_trong/tranh/san_pham), `nhan` (`{"khi": "<cụm lời như transcript thô>", "sau": <giây>, "kieu": "chinh|nen", "chu": [...], "den": ..., "vi_tri": ...}` — rút ý, ≤ 18 ký tự/dòng, 1 chữ / ~3–4s), `hieu_ung_capcut`, `cta_src`.
5. **Dựng — MẶC ĐỊNH CHỈ LÀM PROJECT CAPCUT** (nhân sự tự xuất trong CapCut, góp ý 16/11): (CapCut đóng hẳn) `PY -I SK/scripts/dung.py projects/<du-an>` (= `--pngs --capcut`; lần đầu thêm `--moi`) → lint phải "no issues", có ảnh thumbnail `out_thumb`. XEM `bang-tram.jpg` (từng dòng: đẹp + khớp lời), `bang-bo-cuc.jpg`, ảnh thumbnail. Bố cục dò mặt của MỌI người trong khung (cảnh 2 người); giữa khung bị đè thì chữ tự lệch trái/phải vào chỗ trống. Chữ nhấn rơi vào cảnh cận sản phẩm bị bỏ → lùi đầu cảnh trám (`broll.src`) ra sau câu đó và đặt `den` cho chữ, để chữ hiện lúc người đang nói (≥ 1,8s). Sửa cấu hình → chạy lại (cập nhật tại chỗ).
6. **MP4 xem thử + kiểm bản ra (chỉ khi được yêu cầu, hoặc `"xuat_mp4": true`):** `... dung.py projects/<du-an> --pngs --mp4 --qa` (chạy nền) → trích khung ở từng chữ + thumbnail + CTA; đọc `kiem-tra.md`.
7. **Báo kết quả:** tên project, ảnh thumbnail (+ MP4 nếu có), chỗ đoán (nghe không rõ), việc người dùng tự làm (chọn nhạc thương mại trong CapCut, xuất bản cuối từ CapCut).

## Phụ thuộc
Bắt buộc: Python + `requirements.txt`, ffmpeg, Node.js + `capcut-cli` (npm), Chrome/Edge, CapCut desktop.
Tuỳ chọn (tự bỏ qua nếu thiếu): mô hình `u2net_human_seg.onnx` (né người), bộ dùng chung bo-skill-video (`plan_cuts`, `do_am`, `kiem_ban_ra`, `an_toan`, `nganh`). Không dùng Remotion (cần giấy phép công ty cho video khách) và không chép mã skill khác.
