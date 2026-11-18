"""CÔNG THỨC DỰNG (19/11/2026) — tự chỉnh cách dựng theo NGÀNH x LOẠI VIDEO x SẢN PHẨM x YÊU CẦU bằng lời.

Dữ liệu: kho/cong-thuc.json (16 ngành, 10 loại video, từ điển yêu cầu). dung.py gọi ap() ngay khi đọc cau-hinh.json.
Thứ tự ưu tiên: cau-hinh.json (khoá đã ghi) > "yeu_cau" > hồ sơ thương hiệu (khoá ghi trong file hồ sơ) > loại video > ngành.
Chỉ ĐIỀN khoá còn trống — không bao giờ ghi đè khoá người dùng / AI đã ghi trong cau-hinh.json.

Trong cau-hinh.json:
  "nganh": "am-thuc"                (không ghi -> theo hồ sơ thương hiệu, rồi tự đoán theo lời nói / kịch bản)
  "loai_video": "khuyen_mai"        (không ghi -> tự đoán; mặc định review)
  "yeu_cau": "sôi động hơn, ít chữ"  (lời thường của người dùng)
  "bo_chu": "kho_team"              -> chữ nhấn tự lấy kiểu trong kho chữ team theo VAI (hook, giá, tên SP, CTA…), đổi sang màu
                                       thương hiệu đang dựng
Ghi báo cáo: projects/<du-an>/cong-thuc.md (đã áp gì, vì sao; gợi ý chữ theo sản phẩm; khung video).

Chạy:  cong_thuc.py ds                  -> các ngành / loại video / từ khoá yêu cầu
       cong_thuc.py xem <du-an>         -> xem trước công thức sẽ áp cho dự án (không dựng)
"""
import json, re, sys, unicodedata
from pathlib import Path

SK = Path(__file__).resolve().parent.parent
CT = SK / "kho" / "cong-thuc.json"
NUM = {"chu_moi_phut", "chuyen_toi_da", "hieu_ung_toi_da", "punch", "sfx_db", "cho_giua_cau", "tram_min", "chuyen_cach", "tram_chia"}
NUM_THUC = {"punch", "sfx_db", "cho_giua_cau", "tram_min", "chuyen_cach", "tram_chia"}
KNOB = NUM | {"phong_cach", "bo_chu", "nhip", "hoat_anh_tram", "hoi_thoai"}
# giới hạn an toàn (cộng dồn ngành + loại + yêu cầu không vượt): tiếng nhấn nghe rõ mà không át giọng, ít hiệu ứng (góp ý 17/11)
GIOI_HAN = {"sfx_db": (-6, 4), "punch": (1.0, 1.12), "chuyen_toi_da": (0, 4), "hieu_ung_toi_da": (0, 3),
            "cho_giua_cau": (0.12, 0.26), "tram_chia": (5, 14), "tram_min": (2.5, 6), "chu_moi_phut": (5, 22)}
BIDANH = {"thuc-pham": "am-thuc", "do-an": "am-thuc", "spa": "spa-tham-my", "tpcn": "thuc-pham-chuc-nang",
          "o-to-xe-may": "xe", "noi-that": "bat-dong-san", "cafe": "do-uong", "cong-nghe-saas": "cong-nghe",
          "dien-tu": "cong-nghe", "thuong-mai": "gia-dung", "tiktok-shop": "gia-dung"}


def _kd(s):
    return unicodedata.normalize("NFC", (s or "").lower())


def _doc(p):
    try:
        return Path(p).read_text(encoding="utf-8")
    except Exception:
        return ""


def _van_ban(cfg, P):
    """Lời nói + kịch bản + chữ nhấn + yêu cầu -> chữ thường để đoán ngành / loại / sản phẩm."""
    t = []
    if P:
        try:
            t += [s.get("text", "") for s in json.loads(_doc(Path(P) / "transcript.json") or "[]")]
        except Exception:
            pass
        t.append(_doc(Path(P) / "kich-ban.txt"))
    kb = cfg.get("kich_ban")
    if kb:
        t.append(_doc(kb) if Path(str(kb)).exists() else str(kb))
    t += [" ".join(n.get("chu", [])) for n in cfg.get("nhan", [])]
    return _kd(" \n".join(t))


def _dem(text, tu):
    return sum(text.count(_kd(k)) for k in tu)


def _ap_gia_tri(cur, v):
    if isinstance(v, str) and v[:1] in "+-x" and re.match(r"^[+\-x]\d", v):
        try:
            x = float(v[1:])
        except ValueError:
            return v
        base = float(cur if isinstance(cur, (int, float)) else 0)
        return base * x if v[0] == "x" else base + (x if v[0] == "+" else -x)
    return v


def thong_tin_san_pham(text):
    """Phần 3: giá, ưu đãi, thông số, thành phần trong lời nói / kịch bản -> gợi ý kiểu chữ."""
    goi = []
    gia = sorted(set(re.findall(r"\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\s?(?:k|nghìn|ngàn|đ|đồng|triệu|tr|tỷ)\b", text)))[:5]
    if gia:
        goi.append(f"GIÁ {', '.join(gia)} -> chữ SỐ TO (vai 'gia'), đặt đúng lúc nói giá")
    uu = sorted(set(re.findall(r"(giảm \d+ ?%|giảm giá|sale \d+|freeship|tặng [^,.\n]{2,20}|mua \d+ tặng \d+|voucher)", text)))[:5]
    if uu:
        goi.append(f"ƯU ĐÃI {', '.join(uu)} -> nhãn đỏ / vàng (vai 'uu_dai')")
    ts = sorted(set(re.findall(r"\b\d+(?:[.,]\d+)?\s?(?:ml|g|kg|mah|w|inch|cm|mm|gb|tb|m2|lít|viên|ngày)\b", text)))[:6]
    if ts:
        goi.append(f"THÔNG SỐ {', '.join(ts)} -> chữ to / danh sách (vai 'tu_khoa' / 'danh_sach')")
    tp = re.findall(r"(?:chiết xuất|thành phần|chứa|có)\s([^,.\n]{3,40})", text)[:3]
    if tp:
        goi.append(f"THÀNH PHẦN «{' / '.join(x.strip() for x in tp)}» -> danh sách 2–3 dòng")
    return goi


def vai_chu(n, dau_tien, TH):
    """Vai của 1 chữ nhấn -> chọn kiểu trong kho chữ team."""
    t = _kd(" ".join(n.get("chu", [])))
    if re.search(r"giỏ hàng|mua ngay|đặt hàng|link|inbox|góc trái|bấm vào", t):
        return "cta"
    if re.search(r"\d{1,3}(?:[.,]\d{3})*\s?(?:k|nghìn|ngàn|đ|triệu|tr|tỷ)\b|\bgiá\b", t):
        return "gia"
    if re.search(r"giảm|sale|%|tặng|freeship|ưu đãi|voucher", t):
        return "uu_dai"
    if dau_tien:
        return "hook"
    ten = [_kd(x) for x in (TH.get("ten"), TH.get("san_pham"), TH.get("ten_sp")) if x]
    if any(x and x in t for x in ten):
        return "ten_sp"
    if n.get("nhom") or len(n.get("chu", [])) >= 3:
        return "danh_sach"
    if re.search(r"\b\d+(?:[.,]\d+)?\s?(?:ml|g|kg|mah|w|inch|cm|mm|gb|tb|m2|lít|viên|giờ|phút)\b", t):
        return "tu_khoa"
    if len(t) <= 14:
        return "tu_khoa"
    if len(t) > 34:
        return "mo_ta"
    return "y"


def ap(cfg, TH, P=None, in_ra=True, ghi=True):
    ct = json.loads(CT.read_text(encoding="utf-8"))
    text = _van_ban(cfg, P)
    yc = _kd(cfg.get("yeu_cau", ""))
    bc = ["# Công thức dựng", ""]
    # ---- ngành
    ng = cfg.get("nganh") or TH.get("nganh") or ""
    ng = BIDANH.get(ng, ng)
    ng_ly_do = "cau-hinh / hồ sơ thương hiệu"
    if ng not in ct["nganh"]:
        diem = {k: _dem(text + " " + _kd(TH.get("ten", "")), v["tu_khoa"]) for k, v in ct["nganh"].items()}
        best = max(diem, key=diem.get)
        ng, ng_ly_do = (best, f"tự đoán theo lời nói ({diem[best]} từ khoá)") if diem[best] else ("", "không rõ")
    # ---- loại video
    lo = cfg.get("loai_video") or ""
    lo_ly_do = "cau-hinh"
    if lo not in ct["loai"]:
        if cfg.get("hoi_thoai"):
            lo, lo_ly_do = "hoi_thoai", "cau-hinh hoi_thoai"
        else:
            diem = {k: _dem(yc, v["tu_khoa"]) * 5 + _dem(text, v["tu_khoa"]) for k, v in ct["loai"].items()}
            best = max(diem, key=diem.get)
            lo, lo_ly_do = (best, "tự đoán theo yêu cầu / lời nói") if diem[best] >= 2 else ("review", "mặc định")
    # ---- gộp các lớp
    p, nguon = {}, {}

    def dat(k, v, src):
        if k == "nhip" and v in ct["nhip"]:
            p["nhip"] = v; nguon["nhip"] = src
            for k2, v2 in ct["nhip"][v].items():
                p[k2] = v2; nguon[k2] = f"{src} (nhịp {v})"
            return
        p[k] = _ap_gia_tri(p.get(k), v); nguon[k] = src

    if ng:
        for k in KNOB:
            if k in ct["nganh"][ng]:
                dat(k, ct["nganh"][ng][k], f"ngành {ct['nganh'][ng]['ten']}")
    for k, v in ct["loai"][lo]["dat"].items():
        dat(k, v, f"loại video {ct['loai'][lo]['ten']}")
    ro = set(TH.get("_ro", []))
    for k in KNOB:
        if k in ro and k in TH:
            dat(k, TH[k], "hồ sơ thương hiệu")
    trung = []
    for e in ct["yeu_cau"]:
        hit = [w for w in e["tu_khoa"] if _kd(w) in yc]
        if hit:
            trung.append(hit[0])
            for k, v in e["dat"].items():
                dat(k, v, f"yêu cầu «{hit[0]}»")
    # ---- điền vào cau-hinh (không ghi đè)
    da_ap = []
    for k, v in p.items():
        if k in ("nhip", "chu_moi_phut"):
            continue
        if k in GIOI_HAN and isinstance(v, (int, float)):
            v = min(max(v, GIOI_HAN[k][0]), GIOI_HAN[k][1])
        if isinstance(v, float) and k in NUM and k not in NUM_THUC:
            v = int(round(v))
        if isinstance(v, float):
            v = round(v, 3)
        if k in cfg:
            da_ap.append(f"- `{k}` = {cfg[k]!r} (giữ theo cau-hinh; công thức gợi ý {v!r} — {nguon[k]})")
            continue
        cfg[k] = v
        da_ap.append(f"- `{k}` = {v!r} — {nguon[k]}")
    # ---- bộ chữ kho team: gắn kiểu theo vai cho chữ nhấn chưa có "kho"
    gan = []
    if cfg.get("bo_chu") == "kho_team":
        vai_map = dict(ct["vai_kho_mac_dinh"])
        if ng:
            vai_map.update(ct["nganh"][ng].get("kho", {}))
        nh = sorted(enumerate(cfg.get("nhan", [])), key=lambda x: float(x[1].get("sau", 0)))
        for j, (i, n) in enumerate(nh):
            if n.get("kho"):
                continue
            v = vai_chu(n, j == 0, TH)
            n["kho"] = vai_map.get(v, vai_map["y"])
            gan.append(f"- «{' / '.join(n.get('chu', []))[:40]}» -> vai {v} -> {n['kho']}")
        cfg.setdefault("kho_doi_mau", True)
    # ---- báo cáo
    bc += [f"**Ngành:** {ct['nganh'][ng]['ten'] if ng else 'không rõ (dùng mặc định)'} — {ng_ly_do}",
           f"**Loại video:** {ct['loai'][lo]['ten']} — {lo_ly_do}",
           f"**Yêu cầu nhận ra:** {', '.join(trung) if trung else '(không có)'}", ""]
    bc += ["## Thông số đã áp", ""] + (da_ap or ["- (không đổi gì)"]) + [""]
    cpm = p.get("chu_moi_phut")
    if cpm:
        bc.append(f"**Mật độ chữ nhấn gợi ý:** ~{round(cpm)} chữ / phút video (AI viết `nhan` theo mật độ này)")
    if ng:
        bc.append(f"**Lưu ý ngành:** {ct['nganh'][ng]['goi_y']}")
    bc += ["", "## Khung video (" + ct["loai"][lo]["ten"] + ")", ""] + [f"{i + 1}. {x}" for i, x in enumerate(ct["loai"][lo]["khung"])]
    sp = thong_tin_san_pham(text)
    if sp:
        bc += ["", "## Gợi ý chữ theo sản phẩm (từ lời nói / kịch bản)", ""] + [f"- {x}" for x in sp]
    if gan:
        bc += ["", "## Kiểu chữ kho team đã gắn theo vai (đổi sang màu thương hiệu)", ""] + gan
    if P and ghi:
        (Path(P) / "cong-thuc.md").write_text("\n".join(bc), encoding="utf-8")
    if in_ra:
        print(f"Công thức: ngành {ct['nganh'][ng]['ten'] if ng else '?'} · {ct['loai'][lo]['ten']}"
              + (f" · yêu cầu: {', '.join(trung)}" if trung else "") + f" · {sum(1 for x in da_ap if 'giữ theo' not in x)} thông số"
              + (f" · {len(gan)} chữ theo kho team" if gan else "") + (f" -> {Path(P) / 'cong-thuc.md'}" if P else ""))
    return cfg, bc


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    a = sys.argv[1:]
    if a[:1] == ["ds"]:
        ct = json.loads(CT.read_text(encoding="utf-8"))
        print("NGÀNH:", ", ".join(f"{k} ({v['ten']})" for k, v in ct["nganh"].items()))
        print("LOẠI VIDEO:", ", ".join(f"{k} ({v['ten']})" for k, v in ct["loai"].items()))
        print("YÊU CẦU:", " · ".join(e["tu_khoa"][0] for e in ct["yeu_cau"]))
    elif a[:1] == ["xem"] and len(a) > 1:
        P = Path(a[1]).resolve()
        sys.path.insert(0, str(Path(__file__).parent))
        import thuong_hieu as th
        cfg = json.loads((P / "cau-hinh.json").read_text(encoding="utf-8"))
        _, bc = ap(cfg, th.tai_thuong_hieu(P), P, in_ra=False, ghi=False)
        print("\n".join(bc))
    else:
        print(__doc__)
