"""KHO CHỮ CAPCUT CỦA TEAM (19/11/2026) — 82 kiểu chữ thật lấy từ các dự án team đã edit trong CapCut (job 11B14 → 11B18).

Dữ liệu: kho/kho-text.md (danh mục 6 nhóm H Hook · K Từ khoá TO · T Ý chính · M Mô tả/phụ đề · N Nhãn/CTA · D Chữ đặc biệt
ART/neon/3D + mỗi kiểu 1 dòng dữ liệu `<!--KHO {...}-->` đủ font, màu, viền, bóng, hiệu ứng chữ, hoạt ảnh của CapCut).
Cùng file (gộp 1 kho): mục `## CÂU CHỮ MẪU` cuối file — 1.691 câu chữ của 81 dự án, tra bằng `kho_text.py cau <từ khoá>`.

Dùng trong dựng (dung.py): chữ nhấn trong cau-hinh.json ghi thêm `"kho": "H01"` -> chữ CapCut được NHÂN BẢN ĐÚNG kiểu đó
(giữ nội dung, vị trí do bố cục chọn; tự thu nhỏ khi chữ dài hơn mẫu). Font cài riêng trên máy người làm kho được thay bằng
font kèm skill, đủ dấu tiếng Việt: Montserrat* -> Montserrat Bold; Be Vietnam Pro / Lexend Deca / Phudu / Helvetica / Inter /
SVN-Gilroy / UTM Flavour -> Be Vietnam Pro cùng độ đậm (Black -> 900). Font / hiệu ứng / hoạt ảnh có mã thư viện CapCut thì
CapCut tự tải.

Chạy:  kho_text.py ds [H|K|T|M|N|D]   -> danh mục (mã, mẫu chữ, font, màu, hoạt ảnh)
       kho_text.py xem <mã>          -> chi tiết 1 kiểu
       kho_text.py cau <từ khoá>     -> câu chữ mẫu (theo dự án / clip) có chứa từ khoá, vd "kính bơi", "giỏ hàng"
"""
import copy, json, os, re, shutil, sys, unicodedata, uuid
from pathlib import Path

SK = Path(__file__).resolve().parent.parent
KHO_MD = SK / "kho" / "kho-text.md"
FONTS = SK / "fonts"
NHOM = {"H": "Hook / tiêu đề mở đầu", "K": "Từ khoá TO", "T": "Ý chính / tính năng", "M": "Mô tả / phụ đề",
        "N": "Nhãn có nền / CTA", "D": "Chữ đặc biệt (ART / neon / 3D)"}
FPS = 30


def _rows():
    t = KHO_MD.read_text(encoding="utf-8")
    return {r["code"]: r for r in (json.loads(m) for m in re.findall(r"^<!--KHO (\{.*\})-->$", t, re.M))}


def _bang():
    """Dòng danh mục: mã -> (mẫu chữ, font, màu, hoạt ảnh)."""
    out = {}
    for ln in KHO_MD.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*\*\*([A-Z]\d\d)\*\*\s*\|(.*)", ln)
        if m:
            c = [x.strip() for x in m.group(2).split("|")]
            out[m.group(1)] = c
    return out


def font_thay(ten):
    """Tên file font gốc -> file font kèm skill (đủ dấu tiếng Việt)."""
    n = ten.lower()
    if "montserrat" in n:
        return "montserrat-bold.otf"
    if "black" in n or "heavy" in n:
        return "be-vietnam-pro-900.ttf"
    if "extrabold" in n:
        return "be-vietnam-pro-800.ttf"
    if "semibold" in n or "medium" in n:
        return "be-vietnam-pro-600.ttf"
    return "be-vietnam-pro-700.ttf"


def _font_du_an(P, ten):
    src = FONTS / ten
    dst = Path(P) / "font" / ten
    if not dst.exists() and src.exists():
        dst.parent.mkdir(exist_ok=True)
        shutil.copy2(src, dst)
    return dst.as_posix() if dst.exists() else src.as_posix()


def _rgb(h):
    if isinstance(h, list):
        return h
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] if len(h) >= 6 else [1, 1, 1]


def _nhan(c):
    """Màu NHẤN (có sắc, không phải trắng / đen / xám) -> được đổi sang màu thương hiệu."""
    r, g, b = c[:3]
    return max(r, g, b) - min(r, g, b) > 0.12


def _rong(t):
    return max((sum(1.12 if ch.isupper() else (0.45 if ch in " ·,." else 1.0) for ch in ln) for ln in t.split("\n")), default=1)


def _u16(t):
    return len(t.encode("utf-16-le")) // 2


def ap_kho(draft_dir, muc, P, mau=None):
    mau_th = mau
    """muc: [{"text", "start" (giây), "kho": mã}] — thay dáng các chữ đã có trong draft (tìm theo nội dung + lúc bắt đầu)
    bằng kiểu của kho; giữ nội dung, thời gian, vị trí. Trả số chữ đã áp."""
    rows = _rows()
    da = 0
    for f in Path(draft_dir).rglob("*"):
        if f.name not in ("draft_content.json", "template-2.tmp") or ".capcut-cli-history" in f.parts:
            continue
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        mats = j.setdefault("materials", {})
        texts = {m["id"]: m for m in mats.get("texts", [])}
        dem = 0
        for tr in j.get("tracks", []):
            if tr.get("type") != "text":
                continue
            for sg in tr.get("segments", []):
                m = texts.get(sg.get("material_id"))
                if not m:
                    continue
                txt = json.loads(m["content"]).get("text", "")
                st = sg["target_timerange"]["start"] / 1e6
                hit = next((x for x in muc if x["text"] == txt and abs(x["start"] - st) < 0.05 and x["kho"] in rows), None)
                if not hit:
                    continue
                row = rows[hit["kho"]]
                d = sg["target_timerange"]["duration"]
                # vật liệu chữ: lấy của kho, giữ id cũ (segment trỏ tới), nội dung mới, font thay bằng font kèm skill
                nm = copy.deepcopy(row["mat"])
                nm["id"] = m["id"]
                c = json.loads(nm["content"])
                old = c["styles"]
                text = unicodedata.normalize("NFC", txt)
                if len(old) > 1 and "\n" in text:     # chữ 2 màu: dòng 1 kiểu đầu, phần sau kiểu cuối
                    a = text.split("\n", 1)[0] + "\n"
                    s0, s1 = copy.deepcopy(old[0]), copy.deepcopy(old[-1])
                    s0["range"] = [0, _u16(a)]; s1["range"] = [_u16(a), _u16(text)]; c["styles"] = [s0, s1]
                else:
                    s0 = copy.deepcopy(old[0]); s0["range"] = [0, _u16(text)]; c["styles"] = [s0]
                # font của máy làm kho (kể cả font thư viện CapCut nằm trong cache máy đó) không có ở máy khác -> luôn thay bằng
                # font kèm skill đủ dấu tiếng Việt, xoá mã font thư viện để CapCut không tìm file cũ (lỗi font ở máy khác 19/11)
                co_ma_font = False
                if nm.get("font_path") and not os.path.exists(nm["font_path"]):
                    for k_ in ("font_resource_id", "font_id", "font_third_resource_id", "font_url"):
                        if k_ in nm:
                            nm[k_] = ""
                    nm["fonts"] = []
                for s_ in c["styles"]:
                    p = s_.get("font", {}).get("path", "")
                    if p and not os.path.exists(p) and not co_ma_font:
                        s_["font"] = {"path": _font_du_an(P, font_thay(os.path.basename(p))), "id": ""}
                if mau_th:                               # đổi màu nhấn (không phải trắng / đen) sang màu thương hiệu đang dựng
                    for s_ in c["styles"]:
                        for key in ("fill",):
                            sol = s_.get(key, {}).get("content", {}).get("solid", {})
                            if sol.get("color") and _nhan(sol["color"]):
                                sol["color"] = _rgb(mau_th)
                        for bg in ([s_["background"]] if isinstance(s_.get("background"), dict) else []):
                            sol = bg.get("content", {}).get("solid", {}) if isinstance(bg.get("content"), dict) else {}
                            if sol.get("color") and _nhan(sol["color"]):
                                sol["color"] = _rgb(mau_th)
                    if nm.get("text_color") and _nhan(_rgb(nm["text_color"])):
                        nm["text_color"] = mau_th.lower()
                    for key in ("background_color",):
                        if isinstance(nm.get(key), str) and nm[key].startswith("#") and _nhan(_rgb(nm[key])):
                            nm[key] = mau_th.lower()
                c["text"] = text
                nm["content"] = json.dumps(c, ensure_ascii=False)
                if nm.get("font_path") and not os.path.exists(nm["font_path"]) and not co_ma_font:
                    nm["font_path"] = _font_du_an(P, font_thay(os.path.basename(nm["font_path"])))
                for k in ("words", "current_words"):
                    nm[k] = {"start_time": [], "end_time": [], "text": []}
                for k, v in list(m.items()):          # giữ bề rộng dòng tối đa của skill (vùng an toàn)
                    if k == "line_max_width":
                        nm[k] = v
                mats["texts"] = [nm if x["id"] == m["id"] else x for x in mats["texts"]]
                texts[m["id"]] = nm
                # hiệu ứng chữ + hoạt ảnh của kho (bỏ hoạt ảnh skill đã gắn)
                refs = []
                for k, r in row["refs"]:
                    r = copy.deepcopy(r); r["id"] = str(uuid.uuid4()).upper()
                    if k == "material_animations":
                        for an in r.get("animations", []):
                            ad = min(an.get("duration", 500000), d if an.get("type") == "loop" else d // 2)
                            an["duration"] = ad; an["start"] = d - ad if an.get("type") == "out" else 0
                    mats.setdefault(k, []).append(r); refs.append(r["id"])
                giu = [r for r in sg.get("extra_material_refs", [])
                       if not any(r == x["id"] for k in ("material_animations", "effects") for x in mats.get(k, []))]
                sg["extra_material_refs"] = giu + refs
                # cỡ: theo mẫu của kho, thu nhỏ khi chữ dài hơn mẫu (giữ vị trí bố cục đã chọn)
                mau = json.loads(row["mat"]["content"]).get("text", "") or text
                sc = row["seg"]["clip"]["scale"]["x"] * min(1.0, max(0.72, _rong(mau) / max(_rong(text), 1)))   # không co quá 72% (chữ nhỏ quá khó đọc)
                sg["clip"]["scale"] = {"x": round(sc, 4), "y": round(sc, 4)}
                dem += 1
        f.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
        da = max(da, dem)
    return da


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    a = sys.argv[1:]
    bang = _bang()
    if a and a[0] == "cau":
        t = KHO_MD.read_text(encoding="utf-8")
        t = t[t.index("## CÂU CHỮ MẪU"):]
        q = " ".join(a[1:]).lower()
        du_an, n = "", 0
        for ln in t.splitlines():
            if ln.startswith("===") or not ln.strip():
                continue
            if not ln.startswith(("[", "---")):
                du_an = ln.strip()
            elif q in ln.lower() and n < 60:
                print(f"{du_an[:40]:<40} {ln.strip()[:110]}"); n += 1
        print(f"({n} câu{' — mới hiện 60 câu đầu' if n >= 60 else ''})")
        sys.exit()
    if not a or a[0] not in ("ds", "xem"):
        print(__doc__)
    elif a[0] == "ds":
        g = (a[1].upper() if len(a) > 1 else "")
        for ma, c in bang.items():
            if g and not ma.startswith(g):
                continue
            print(f"{ma}  {c[0][:60]:<60}  {c[1][:22]:<22} {c[2][:10]:<10} {c[5][:40]}")
    else:
        ma = a[1].upper() if len(a) > 1 else ""
        c = bang.get(ma)
        print(f"{ma} ({NHOM.get(ma[:1], '')}): " + (" | ".join(c) if c else "không có trong kho"))
