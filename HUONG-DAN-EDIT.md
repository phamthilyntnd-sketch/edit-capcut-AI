# Hướng dẫn EDIT VIDEO với skill edit-capcut-AI

Bạn nói bằng lời thường, Claude tự dựng thành **project CapCut sửa được** + file MP4 xem thử.
Bạn chỉ cần: chuẩn bị footage → nói yêu cầu → xem → góp ý → chọn nhạc → xuất.

Chưa cài skill? Làm **HUONG-DAN-CAI-DAT.md** trước.

---

## 1. Chuẩn bị (mỗi video)

**Footage — 1 thư mục cho 1 video**, ví dụ `D:\footage\SANTAV-O5\`:
- **1 clip người nói** (A-roll): quay dọc, nói hết kịch bản. Nói vấp cứ nói lại — Claude giữ lần nói cuối.
- **Vài clip cảnh trám** (B-roll): cận sản phẩm (mặt trước, mặt sau/thành phần), thao tác dùng, bối cảnh (siêu thị, nhà…). Mỗi clip ≥ 5 giây, quay chậm, chai **đứng thẳng**, đủ sáng.
- Không cần đổi tên file, không cần cắt trước.

**Brief / kịch bản** (nếu có): file `.txt`/`.docx`/link Google Sheet. Có brief thì chữ thumbnail và chữ nhấn sát ý khách hơn.

**Logo khách**: file PNG nền trong. Để trên máy (Drive nội bộ / ổ D:). **Không** đưa logo, brief, footage của khách lên GitHub.

## 2. Hồ sơ thương hiệu (1 lần cho mỗi khách)
Đã có sẵn: **santav**. Khách mới — trong tab Code nói:
> Tạo hồ sơ thương hiệu cho khách **ABC**: màu chữ #E4572E, logo ở `D:\khach\ABC\logo.png`, nút kêu gọi "GIỎ HÀNG", sản phẩm "Kem chống nắng ABC – Công ty TNHH ABC", từ cấm theo brief `D:\khach\ABC\brief.docx`

Claude hỏi thêm những gì thiếu (màu bao bì sản phẩm, tên riêng hay bị nghe sai, ngành hàng, số liệu được phép nói) rồi lưu hồ sơ. Lần sau chỉ cần nói tên khách.

## 3. Dựng video
1. Mở app **Claude → tab Code**, chọn thư mục làm việc (ví dụ `Documents\Du-an-video`).
2. Nói, ví dụ:
   > Dựng video trong thư mục `D:\footage\SANTAV-O5` cho thương hiệu **santav** thành project CapCut. Mã video **MAN O-5**, kịch bản trong brief.

   hoặc gõ `/edit-capcut-ai` rồi trả lời câu hỏi.
3. Claude **hỏi hết 1 lần** những gì còn thiếu (thumbnail ghi gì, clip nào là người nói…) → rồi tự làm tới xong, không hỏi nữa. Mất khoảng 10–30 phút tuỳ độ dài, cứ để máy chạy.
4. Khi Claude nhắc **"đóng CapCut"**: tắt hẳn CapCut (cả biểu tượng cạnh đồng hồ) rồi trả lời *"Đã đóng CapCut"*. Claude không tự tắt CapCut của bạn.

Claude tự làm:
- cắt vấp, nói lại, ừ/ờ — không cắt cụt chữ;
- chọn **đoạn quay đẹp nhất** của mỗi cảnh trám, khớp với lời đang nói;
- **thumbnail** khung đầu (chữ IN HOA), logo, nhãn "Hợp tác quảng cáo", dòng pháp lý, nút kêu gọi;
- **chữ nhấn** là chữ CapCut thật (sửa được), chỉ 2 kiểu, căn giữa, **không che người và sản phẩm**;
- **chuyển cảnh, hiệu ứng cảnh, hiệu ứng chữ** có sẵn của CapCut; **tiếng nhấn** khớp hình;
- lọc tạp âm giọng, âm lượng chuẩn TikTok; kiểm từ cấm và luật quảng cáo.

## 4. Nhận kết quả
Claude báo:
- **Project CapCut** tên `<THƯƠNG HIỆU> <MÃ>` — mở CapCut là thấy trong danh sách project.
- **MP4 xem thử** + **ảnh thumbnail** trong thư mục footage (bản MP4 chỉ gần đúng; bản chuẩn là project CapCut).
- Những chỗ Claude **đoán** (nghe không rõ tên, số) → bạn kiểm lại.

⚠️ Project CapCut dùng video trong thư mục `projects\<tên dự án>\raw\` của thư mục làm việc → **không xoá / di chuyển** thư mục đó khi chưa xuất xong.

## 5. Góp ý — Claude sửa thẳng vào project đang xem
Nói tự nhiên, càng cụ thể càng tốt (có giây thì càng nhanh):
- *"Chữ ở giây 12 che mặt, dời xuống dưới"* · *"Chữ 'DỊU NHẸ' đổi thành 'SẠCH THOÁNG'"*
- *"Tiếng nhấn nhỏ quá"* · *"Bớt tiếng whoosh"* · *"Thêm tiếng ở chỗ gọi tên sản phẩm"*
- *"Cảnh trám ở giây 20 chai bị nghiêng, đổi đoạn khác"* · *"Cảnh trám quá nhanh"*
- *"Cắt bỏ câu 'cảm ơn mọi người'"* · *"Còn tiếng ờ ở giây 31"*
- *"Chuyển cảnh nhiều quá / đơn điệu quá"* · *"Thumbnail đổi thành: LO CHO CẢ NHÀ, ĐỪNG QUÊN LO MÌNH"*

Mỗi lần sửa, Claude **cập nhật đúng project đang xem** (không tạo v2, v3). Bản ngay trước được sao lưu — muốn quay lại thì nói *"quay lại bản trước"*.
Nhớ **đóng CapCut** khi Claude nhắc, mở lại sau khi Claude báo xong.

Sửa nhỏ (đổi 1 chữ, dời 1 chữ) có thể tự làm luôn trong CapCut — chữ là chữ thật. Nhưng **sau khi tự sửa trong CapCut thì đừng nhờ Claude sửa tiếp project đó** (Claude dựng lại sẽ ghi đè phần bạn tự sửa) — hoặc báo Claude những gì bạn đã sửa để Claude làm theo.

## 6. Hoàn thiện trong CapCut
1. **Nhạc nền**: Claude **không** chèn nhạc. Vào **Audio → Music** của CapCut, chọn bài có **quyền thương mại** (TikTok bắt buộc với video quảng cáo), để âm lượng nhỏ (~10–20%) dưới giọng.
2. Xem lại 1 lượt từ đầu đến cuối.
3. **Export**: 1080p, 30fps.

## 7. Trước khi đăng TikTok
- Bật nhãn **nội dung thương mại / hợp tác quảng cáo** khi đăng.
- Không thêm từ cấm, không hứa công dụng chữa bệnh, số liệu chỉ lấy từ brief.
- Không để watermark ứng dụng khác.

## 8. Mẹo
- Nhiều video cùng lúc: mỗi video 1 thư mục footage, nhờ Claude làm **lần lượt**, góp ý từng video.
- Video đầu tiên của khách mới: góp ý kỹ, rồi nói *"lưu các góp ý này vào hồ sơ thương hiệu ABC"* để video sau đúng ngay.
- Ổ C: phải còn ≥ 2 GB (mỗi project CapCut ~0,5–1 GB). Xuất xong, đăng xong thì có thể xoá project cũ trong CapCut.
- CapCut hiện chữ thành "Input text": nói *"máy này CapCut lỗi chữ, dùng chữ dạng ảnh"*.
- Kẹt ở đâu: chụp màn hình gửi quản lý, hoặc hỏi thẳng Claude *"vì sao…"*.
