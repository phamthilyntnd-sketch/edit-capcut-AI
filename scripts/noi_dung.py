"""NHẬN DIỆN NỘI DUNG VIDEO (20/11/2026) — đọc lời nói (transcript.json, chỉ phần giữ lại) và gắn LOẠI cho từng câu
(mở đầu, câu hỏi, vấn đề, chi tiết sản phẩm, thông số, lợi ích, so sánh, danh sách, hướng dẫn, giá, ưu đãi, dịch vụ,
cảm nhận, thương hiệu, kêu gọi), rồi GỢI Ý hiệu ứng hợp với từng loại câu:
  · kiểu chữ (vai -> kiểu TikTok TTxx theo ngành, cong_thuc.bo_tiktok) · có nên đặt chữ không
  · cảnh trám nên dùng (cận sản phẩm / minh hoạ vấn đề / đang dùng / bối cảnh dịch vụ / cửa hàng)
  · tiếng nhấn · vị trí chữ (câu chi tiết sản phẩm: chữ trên đầu, không che sản phẩm)
  · có nên nhờ Mike làm điểm nhấn không và kiểu nào (không khung mặt, không phủ kín khi nói chi tiết sản phẩm)
Là luật dựng của skill này (không lấy từ Mike). dung.py / cong_thuc.py dùng kết quả để gắn vai cho chữ nhấn.

Chạy:  PY -I SK/scripts/noi_dung.py projects/<du-an>   -> projects/<du-an>/noi-dung.md (+ noi-dung.json)
"""
import json, re, sys, unicodedata
from pathlib import Path

LOAI = {  # thứ tự = độ ưu tiên khi 1 câu khớp nhiều loại
    "cta": ("Kêu gọi", r"ghé (ngay|qua|thăm)|ghé cửa hàng|nhấn (ngay )?vào|dò hàng|rõ hàng|mua ngay|đặt (hàng|ngay|lịch)|inbox|nhắn tin|link|giỏ hàng|địa chỉ|liên hệ|hotline|bấm vào"),
    "gia": ("Giá", r"\d[\d.,]*\s?(k|nghìn|ngàn|đ|đồng|triệu|tr|tỷ)\b|giá (chỉ|có|rẻ|tốt)|bao nhiêu tiền"),
    "uu_dai": ("Ưu đãi", r"tặng|giảm|sale|ưu đãi|freeship|miễn phí|quà|khuyến mãi|voucher|mua \d+ tặng"),
    "cau_hoi": ("Câu hỏi", r"\?|(có|đã) (bị|biết|thấy|từng)|tại sao|vì sao|làm sao|có phải|bạn có|hay không|không nè|đúng không"),
    "so_sanh": ("So sánh / trước–sau", r"thay vì|so với|đổi sang|không còn|chuyển sang|trước đây|khác hẳn|hơn hẳn|thay cho"),
    "thuong_hieu": ("Thương hiệu / slogan", r"tinh tế|trong từng|đồng hành|cam kết|uy tín|chính hãng|thương hiệu"),
    "dich_vu": ("Dịch vụ", r"tư vấn|nhân viên|chuyên viên|chăm sóc khách|phục vụ|bảo hành|đổi trả|giao hàng"),
    "chi_tiet": ("Chi tiết sản phẩm", r"chất liệu|thiết kế|đường nét|thành phần|công nghệ|chiết xuất|kết cấu|dung tích|kích thước|"
                 r"titanium|high grade|tròng|khung|gọng|lớp phủ|bề mặt|đường may|vải|da thật|nguyên liệu|hương|mùi"),
    "thong_so": ("Thông số", r"\b\d+[.,]?\d*\s?(ml|g|kg|mah|w|inch|cm|mm|gb|tb|m2|lít|viên|giờ|phút|%|x)\b"),
    "van_de": ("Vấn đề", r"đau|mỏi|khó chịu|lo lắng|\bsợ\b|ngại|\bbị\b|hư|hỏng|tốn|vướng|ngứa|nóng|bí|hằn|mệt|chói|khô|nứt|xệ|mụn"),
    "danh_sach": ("Danh sách", r"thứ nhất|thứ hai|thứ ba|đầu tiên là|tiếp theo|cuối cùng|thứ \d|top \d|\d (lưu ý|cách|bước|món)"),
    "huong_dan": ("Hướng dẫn", r"cách (dùng|làm|chọn)|bước|chỉ cần|hướng dẫn|sau đó|thoa|bôi|lắc đều|pha"),
    "loi_ich": ("Lợi ích", r"giúp|nhẹ|êm|mềm|bền|tiện|đẹp|sạch|thoáng|hiệu quả|tiết kiệm|nhanh|dịu|mát|thoải mái|an toàn|"
                r"tôn dáng|lịch sự|sang|xinh|đàn hồi|dẻo|chắc"),
    "cam_nhan": ("Cảm nhận", r"mình thấy|mình thích|ưng|\bmê\b|cảm giác|thử rồi|dùng rồi|xài|thích lắm|quá trời"),
}
# GỢI Ý theo loại câu (luật dựng của skill)
GOI_Y = {
    "mo_dau":     dict(vai="hook", tram="giữ người nói (hook trong 3s đầu)", sfx="hoi", chu=True, mike="chữ to trên / sau đầu (không khung mặt)"),
    "cau_hoi":    dict(vai="hook", tram="giữ người nói", sfx="hoi", chu=True, mike="chữ to trên / sau đầu"),
    "van_de":     dict(vai="hook", tram="minh hoạ vấn đề (người đang gặp vấn đề)", sfx="chu", chu=True, mike=""),
    "so_sanh":    dict(vai="y", tram="trước / sau, đổi sang sản phẩm", sfx="chuyen", chu=True, mike="cảnh cũ → mới (chỉ khi KHÔNG đang cầm sản phẩm)"),
    "chi_tiet":   dict(vai="ten_sp", tram="CẬN SẢN PHẨM (san_pham: true)", sfx="san_pham", chu=True, vi_tri="tren",
                       mike="KHÔNG phủ kín — để cảnh trám cận sản phẩm; nếu cần chỉ chữ trên đầu"),
    "thong_so":   dict(vai="tu_khoa", tram="cận sản phẩm / con số", sfx="chu", chu=True, vi_tri="tren", mike=""),
    "loi_ich":    dict(vai="y", tram="đang dùng sản phẩm", sfx="chu", chu=True, mike="1 từ khoá to sau đầu"),
    "danh_sach":  dict(vai="danh_sach", tram="lần lượt từng món / bước", sfx="chu", chu=True, mike=""),
    "huong_dan":  dict(vai="danh_sach", tram="thao tác từng bước (cận tay)", sfx="chu", chu=True, vi_tri="tren", mike=""),
    "gia":        dict(vai="gia", tram="giữ người nói / sản phẩm", sfx="gia", chu=True, mike=""),
    "uu_dai":     dict(vai="uu_dai", tram="quà tặng / sản phẩm", sfx="gia", chu=True, mike=""),
    "dich_vu":    dict(vai="y", tram="bối cảnh dịch vụ (nhân viên, cửa hàng)", sfx="chu", chu=True, mike=""),
    "cam_nhan":   dict(vai="mo_ta", tram="đang dùng / cận mặt", sfx="", chu=False, mike=""),
    "thuong_hieu": dict(vai="ten_sp", tram="logo / cửa hàng", sfx="san_pham", chu=True, mike="biển LED tên thương hiệu sau đầu"),
    "cta":        dict(vai="cta", tram="cửa hàng / giỏ hàng", sfx="cta", chu=True, mike=""),
    "ke":         dict(vai="mo_ta", tram="", sfx="", chu=False, mike=""),
}


def _n(s):
    return unicodedata.normalize("NFC", s or "").lower()


def cau(P, cfg):
    """Câu nói trong các đoạn giữ (keeps) theo giây nguồn: [{a, b, text}] — tách theo dấu câu + khoảng lặng."""
    tr = json.loads((Path(P) / "transcript.json").read_text(encoding="utf-8"))
    keeps = cfg.get("keeps") or [[0, 1e9]]
    giu = lambda t: any(a - 0.05 <= t <= b + 0.05 for a, b in keeps)
    out, cur = [], []
    for sg in tr:
        ws = sg.get("words") or [{"w": sg["text"], "s": sg["start"], "e": sg["end"]}]
        for i, w in enumerate(ws):
            t = (w.get("w") or w.get("word") or w.get("text") or "").strip()
            s, e = w.get("s", w.get("start")), w.get("e", w.get("end"))
            if not t or not giu(s):
                if cur:
                    out.append(cur); cur = []
                continue
            if cur and s - cur[-1][2] > 0.6:
                out.append(cur); cur = []
            cur.append((t, s, e))
            if re.search(r"[.?!]$", t) or (t.endswith(",") and cur[-1][2] - cur[0][1] > 2.5):
                out.append(cur); cur = []
        if cur:
            out.append(cur); cur = []
    return [{"a": c[0][1], "b": c[-1][2], "text": " ".join(x[0] for x in c)} for c in out if c]


def _khop(rx, t):
    """khớp NGUYÊN TỪ (tiếng Việt: 'êm' không khớp 'đêm', 'hư' không khớp 'như / hướng'); dấu '?' xét riêng."""
    if rx.startswith(r"\?|") and "?" in t:
        return True
    return re.search(r"(?<!\w)(?:" + rx + r")(?!\w)", t) is not None


def loai_cau(text, TH, dau=False):
    t = _n(text)
    ten = [_n(x) for x in (TH.get("ten"), TH.get("san_pham"), TH.get("ten_sp")) if x]
    t2 = re.sub(r"không (có )?(sợ|lo|ngại)?( ?bị)?|lỡ tay|vô tình", "", t)   # "không sợ bị..." / "lỡ tay làm rơi" (vẫn bền) không phải vấn đề
    hit = [k for k, (_, rx) in LOAI.items() if _khop(rx, t2 if k == "van_de" else t)]
    # tên thương hiệu (cả khi Whisper nghe thiếu chữ đầu: EYEMEDI -> IMEDI) + câu khẩu hiệu
    ten_ok = any(x and (x in t or (len(x) >= 6 and x[-5:] in t)) for x in ten)
    if ten_ok and re.search(r"trong (từng|mỗi)|tinh tế|đồng hành|cam kết|nâng tầm|vì bạn|cho bạn", t) and "cta" not in hit:
        return "thuong_hieu", hit
    if dau and ("cau_hoi" in hit or "van_de" in hit or not hit):
        return "mo_dau", hit
    if any(x and x in t for x in ten) and not hit:
        return "thuong_hieu", hit
    return (hit[0] if hit else "ke"), hit


def phan_tich(P, cfg, TH, ghi=True):
    P = Path(P)
    ds = cau(P, cfg)
    ng = cfg.get("nganh") or TH.get("nganh") or ""
    try:
        import cong_thuc
        bo = cong_thuc.bo_tiktok(cong_thuc.BIDANH.get(ng, ng))
    except Exception:
        bo = {}
    out = []
    for i, c in enumerate(ds):
        lo, hit = loai_cau(c["text"], TH, dau=(i == 0 or (i == 1 and ds[0]["b"] - ds[0]["a"] < 1.5)))
        g = dict(GOI_Y[lo])
        g["kieu_chu"] = (bo.get(g["vai"]) or [""])[0]
        out.append(dict(c, loai=lo, khop=hit, **g))
    # gợi ý Mike: tối đa 3 câu đắt giá, ưu tiên mở đầu > thương hiệu > lợi ích; không chọn câu chi tiết sản phẩm
    uu = {"mo_dau": 0, "cau_hoi": 0, "thuong_hieu": 1, "loi_ich": 2}
    mike, da = [], set()
    for x in sorted([x for x in out if x["loai"] in uu and x["b"] - x["a"] >= 1.5], key=lambda x: (uu[x["loai"]], x["a"])):
        k = "mo_dau" if x["loai"] == "cau_hoi" else x["loai"]
        if k in da and k != "loi_ich":
            continue
        da.add(k); mike.append(x)
        if len(mike) == 3:
            break
    for x in mike:
        x["chon_mike"] = True
    if ghi:
        (P / "noi-dung.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        md = ["# Nhận diện nội dung video", "", f"Ngành: {ng or '?'} · {len(out)} câu", "",
              "| giây | loại | lời | chữ (vai → kiểu) | cảnh trám nên dùng | tiếng | Mike |", "|---|---|---|---|---|---|---|"]
        for x in out:
            ten_loai = LOAI.get(x["loai"], ("Mở đầu" if x["loai"] == "mo_dau" else "Câu nối",))[0]
            chu = (f"{x['vai']} → {x['kieu_chu']}" + (" · TRÊN ĐẦU" if x.get("vi_tri") == "tren" else "")) if x["chu"] else "không đặt chữ"
            md.append(f"| {x['a']:.1f}–{x['b']:.1f} | {ten_loai} | {x['text'][:70]} | {chu} | {x['tram']} | {x['sfx']} | "
                      f"{('**chọn** · ' if x.get('chon_mike') else '') + x['mike']} |")
        if mike:
            md += ["", "**Điểm nhấn Mike gợi ý** (`dung.py projects/<du-an> --mike-edl \"" +
                   ",".join(f"{x['a'] - 0.1:.1f}-{x['b'] + 0.15:.1f}" for x in sorted(mike, key=lambda x: x['a'])) + "\"`): "
                   + "; ".join(f"{x['a']:.1f}s {x['loai']}" for x in mike)]
        md += ["", "Luật: câu CHI TIẾT SẢN PHẨM / THÔNG SỐ / HƯỚNG DẪN → chữ trên đầu, cảnh trám cận sản phẩm, KHÔNG cảnh phủ kín;"
               " câu nối / cảm nhận ngắn → không đặt chữ; mỗi ý có cảnh quay tương ứng → 1 cảnh trám."]
        (P / "noi-dung.md").write_text("\n".join(md), encoding="utf-8")
    return out


def vai_tai(nd, t):
    """câu chứa giây nguồn t (ưu tiên câu chứa hẳn t, rồi câu gần nhất trong 0,3s); None nếu không có."""
    for x in nd or []:
        if x["a"] <= t <= x["b"]:
            return x
    gan = [x for x in nd or [] if x["a"] - 0.3 <= t <= x["b"] + 0.3]
    return min(gan, key=lambda x: min(abs(t - x["a"]), abs(t - x["b"]))) if gan else None


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.path.insert(0, str(Path(__file__).parent))
    import thuong_hieu as th
    P = Path(sys.argv[1])
    cfg = json.loads((P / "cau-hinh.json").read_text(encoding="utf-8"))
    TH = th.tai_thuong_hieu(P)
    kq = phan_tich(P, cfg, TH)
    from collections import Counter
    print(f"{len(kq)} câu:", dict(Counter(x["loai"] for x in kq)), "->", P / "noi-dung.md")
