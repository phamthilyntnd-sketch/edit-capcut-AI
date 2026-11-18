"""Chữ của video: CHỮ THẬT trong CapCut (sửa được), ảnh PNG chỉ để đo / xuất MP4 / dự phòng máy lỗi.

Chỉ 2 kiểu chữ nhấn trong 1 video (người dùng: nhiều kiểu quá thì rối):
  chinh : chữ MÀU CHÍNH thương hiệu, Be Vietnam Pro ExtraBold, IN HOA, viền trắng + bóng (đúng brief)  -> câu nhấn, câu chốt
  nen   : chữ trắng trên nền xanh bo góc                                                  -> tên sản phẩm, lợi ích, liệt kê
Luôn CĂN GIỮA ngang; dọc chỉ ở 2 dải cố định (trên đầu người / dưới ngực), bố cục tự chọn dải để né mặt và sản phẩm.

Chữ cố định khác (thumbnail, GIỎ HÀNG, nhãn QC, dòng pháp lý) cũng là chữ CapCut thật.
Máy CapCut vẽ chữ lỗi ("Input text"): đặt "chu_capcut": false trong may.json (máy đó) hoặc cau-hinh.json
-> dùng lại ảnh PNG như cũ.
"""
import json, os, shutil
from pathlib import Path

import thuong_hieu as th
GREEN, DARK = th.TH["mau_chinh"], th.TH["mau_dam"]
W, H = 1080, 1920
PX_PER_SIZE = 5.2          # px trên khung 1080x1920 / cỡ chữ CapCut. 4.0 cũ làm chữ CapCut TO hơn bản thiết kế -> tràn khung
                           # an toàn (góp ý 17/11). 5.2 = nhỏ hơn ~23%, kèm xuống dòng trong 78% chiều ngang (LINE_MAX)
LINE_MAX = 0.78            # CapCut tự xuống dòng khi chữ rộng quá 78% khung -> mép phải <= ~960px (né cột nút TikTok)
FONT_DIR = th.FONTS
FONT_SRC = FONT_DIR / "be-vietnam-pro-600.ttf"
FONT_NAME = "BeVietnamPro-SemiBold.ttf"
# độ đậm theo kiểu: chữ nhấn chính đậm hơn cho dễ đọc trên điện thoại
FONT_W = {"chinh": 800, "nen": 700, "co_dinh": 600}
FONT_TEN = {600: "Be Vietnam Pro SemiBold", 700: "Be Vietnam Pro Bold", 800: "Be Vietnam Pro ExtraBold"}
# hiệu ứng chữ CÓ SẴN của CapCut (capcut enums --text-intros / --text-outros): (vào, giây, ra, giây)
# vào nhanh 0,25s để chữ "chạm" đúng lúc nói (0,35s trông như chữ đến trễ — góp ý 16/11)
ANIM_CAPCUT = {"chinh": ("pop-up", 0.25, "fade-out", 0.2), "nen": ("slide-up", 0.25, "fade-out", 0.2)}
# tiếng đi kèm hiệu ứng chữ: (tên tiếng, lệch so với lúc chữ bắt đầu hiện). pop/bubble nổ ngay, whip vút theo chữ trượt lên
SFX_CHU = {"chinh": (("pop", "bubble"), 0.02), "nen": (("whip",), 0.0)}
# V3 (góp ý 18/11 "đa dạng sound effect và phù hợp với hoạt ảnh của text"): mỗi chữ 1 kiểu hiện khác nhau (xoay vòng),
# tiếng đi theo đúng kiểu hiện: (hiệu ứng vào CapCut, tiếng, lệch giây so với lúc chữ bắt đầu hiện)
ANIM_POOL = {
    "chinh": [("pop-up", "pop", 0.02), ("bounce-in", "bubble", 0.03), ("zoom-in", "whoosh", -0.06),
              ("spring", "bubble", 0.03), ("flip-up", "whip", 0.0), ("mini-zoom", "sparkle", -0.04)],
    "nen": [("slide-up", "whip", 0.0), ("wipe-right", "swipe", -0.02), ("grow", "pop", 0.02),
            ("slide-left", "swipe", -0.02), ("showing-up", "click", 0.05)],
}


def anim(n):
    """(hiệu ứng vào, tiếng, lệch) của chữ n: kiểu đã chọn từ kho CapCut (n["vao"]) hoặc xoay vòng ANIM_POOL."""
    if n.get("vao"):
        return n["vao"], n.get("sfx_vao", "pop"), n.get("lech", 0.02)
    pool = ANIM_POOL[kieu(n)]
    return pool[int(n.get("anim_idx", 0)) % len(pool)]

# kiểu cũ -> 2 kiểu mới
KIEU_MAP = {"chinh": "chinh", "nen": "nen",
            "hook": "chinh", "punch": "chinh", "quote": "chinh", "note": "chinh", "xanh": "chinh", "trang": "chinh",
            "lock": "chinh", "benefit": "nen", "list": "nen", "product": "nen", "pill": "nen", "the": "nen"}
STYLE = {
    "chinh": {"px": 86, "color": GREEN, "upper": True},
    "nen": {"px": 58, "color": "#FFFFFF", "upper": False},
}
# dải dọc (tâm chữ, px): trên = vùng trên đầu, dưới = vùng ngực/bụng (trên nút giỏ hàng)
# vùng an toàn TikTok: không lên trên 220px (thanh trạng thái), không xuống dưới ~1500px (chữ mô tả + nút của TikTok)
ROWS = {"tren": [260, 340, 430], "duoi": [1120, 1240]}

CSS = """
.t{position:absolute;left:40px;right:40px;top:0;text-align:center;white-space:nowrap;font-family:'Be Vietnam Pro';font-weight:600}
.t-chinh{font-size:86px;line-height:1.12;letter-spacing:.5px;font-weight:800}
.t-chinh .l{position:relative;display:block}
.t-chinh .bg{position:absolute;left:0;right:0;top:0;color:#fff;-webkit-text-stroke:24px #fff;
  filter:drop-shadow(4px 6px 6px rgba(0,0,0,.45))}
.t-chinh .fg{position:relative;color:GREEN}
.t-nen{font-size:58px;line-height:1.2;font-weight:700}
.t-nen .l{display:block;margin:0 auto 12px;width:max-content;background:GREEN;color:#fff;border-radius:22px;
  padding:8px 30px 12px;box-shadow:3px 5px 10px rgba(0,0,0,.28)}
.t i{font-style:italic;font-weight:700}
""".replace("GREEN", GREEN)


# ---------------------------------------------------------------- BỘ KIỂU CHỮ (19/11/2026)
# Rút từ kho 206 mẫu chữ TikTok thật (kho/mau-chu-tiktok.json, xem scripts/mau_chu.py). Vẫn CHỈ 2 KIỂU / video
# (chinh + nen) — bộ kiểu chỉ đổi DÁNG của 2 kiểu đó. Tất cả dựng bằng chữ CapCut thật + font Be Vietnam Pro kèm skill
# (đủ dấu tiếng Việt, không phụ thuộc font trên máy). Chọn: "bo_chu" trong cau-hinh.json / hồ sơ thương hiệu,
# hoặc "bo_chu": "tu_dong" -> theo ngành (mau_chu.bo_cho_nganh).
#   vien = (màu viền, độ dày CapCut 0–1) · nen = (màu nền chữ, độ đục) · bong = độ đậm bóng (0 = tắt)
BO_CHU = {
    "thuong_hieu": {"ten": "Màu thương hiệu (mặc định)", "nhom": [8, 10],
                    "chinh": dict(px=86, color="BRAND", upper=True, w=800, vien=("#FFFFFF", 0.06), nen=None, bong=0.45),
                    "nen": dict(px=58, color="#FFFFFF", upper=False, w=700, vien=None, nen=("BRAND", 1.0), bong=0.3)},
    "tiktok": {"ten": "Phụ đề trắng kiểu TikTok + hộp trắng", "nhom": [1, 2, 3, 15],
               "chinh": dict(px=76, color="#FFFFFF", upper=False, w=700, vien=None, nen=None, bong=0.65),
               "nen": dict(px=60, color="#111111", upper=False, w=700, vien=None, nen=("#FFFFFF", 1.0), bong=0.2)},
    "hop_trang": {"ten": "Hộp trắng chữ đen + hộp vàng", "nhom": [2, 14, 18],
                  "chinh": dict(px=70, color="#111111", upper=False, w=800, vien=None, nen=("#FFFFFF", 1.0), bong=0.25),
                  "nen": dict(px=60, color="#111111", upper=False, w=700, vien=None, nen=("#FFE14D", 1.0), bong=0.2)},
    "vien_den": {"ten": "In hoa trắng viền đen (kiểu ảnh bìa)", "nhom": [7, 9, 11, 13, 16, 21],
                 "chinh": dict(px=92, color="#FFFFFF", upper=True, w=800, vien=("#111111", 0.08), nen=None, bong=0.4),
                 "nen": dict(px=60, color="#FFFFFF", upper=False, w=700, vien=None, nen=("BRAND", 1.0), bong=0.3)},
    "ban_hang_nong": {"ten": "Vàng viền đen + nhãn đỏ (bán hàng, đồ ăn)", "nhom": [17, 9],
                      "chinh": dict(px=92, color="#FFD60A", upper=True, w=800, vien=("#111111", 0.08), nen=None, bong=0.4),
                      "nen": dict(px=62, color="#FFFFFF", upper=True, w=800, vien=None, nen=("#E53935", 1.0), bong=0.3)},
    "toi_gian": {"ten": "Tối giản sang (trắng, không viền)", "nhom": [12, 4, 5, 6],
                 "chinh": dict(px=72, color="#FFFFFF", upper=True, w=700, vien=None, nen=None, bong=0.55),
                 "nen": dict(px=52, color="#FFFFFF", upper=False, w=600, vien=None, nen=None, bong=0.6)},
}
BO = "thuong_hieu"


def _mau(c):
    return GREEN if c == "BRAND" else c


def _css_bo(b):
    c, e = b["chinh"], b["nen"]
    out = [".t{position:absolute;left:40px;right:40px;top:0;text-align:center;white-space:nowrap;font-family:'Be Vietnam Pro';font-weight:600}",
           f".t-chinh{{font-size:{c['px']}px;line-height:1.14;letter-spacing:.5px;font-weight:{c['w']}}}",
           ".t-chinh .l{position:relative;display:block}",
           f".t-chinh .fg{{position:relative;color:{_mau(c['color'])}}}"]
    if c["vien"]:
        out.append(f".t-chinh .bg{{position:absolute;left:0;right:0;top:0;color:{_mau(c['vien'][0])};"
                   f"-webkit-text-stroke:{round(c['vien'][1] * 400)}px {_mau(c['vien'][0])};"
                   f"filter:drop-shadow(4px 6px 6px rgba(0,0,0,{c['bong']}))}}")
    else:
        out.append(".t-chinh .bg{display:none}")
        if c["bong"] and not c["nen"]:
            out.append(f".t-chinh .fg{{text-shadow:2px 4px 10px rgba(0,0,0,{c['bong']})}}")
    if c["nen"]:
        out.append(f".t-chinh .l{{width:max-content;margin:0 auto 12px;background:{_mau(c['nen'][0])};border-radius:20px;"
                   f"padding:6px 28px 12px;box-shadow:3px 5px 10px rgba(0,0,0,{c['bong']})}}")
    out.append(f".t-nen{{font-size:{e['px']}px;line-height:1.2;font-weight:{e['w']}}}")
    if e["nen"]:
        out.append(f".t-nen .l{{display:block;margin:0 auto 12px;width:max-content;background:{_mau(e['nen'][0])};"
                   f"color:{_mau(e['color'])};border-radius:22px;padding:8px 30px 12px;box-shadow:3px 5px 10px rgba(0,0,0,{e['bong']})}}")
    else:
        out.append(f".t-nen .l{{display:block;color:{_mau(e['color'])};text-shadow:2px 4px 10px rgba(0,0,0,{e['bong']})}}")
    out.append(".t i{font-style:italic;font-weight:700}")
    return "\n".join(out)


def _capcut_style(s):
    st = {"alignment": 1}
    if s["vien"]:
        st.update(borderColor=_mau(s["vien"][0]), borderWidth=s["vien"][1], borderAlpha=1.0)
    if s["nen"]:
        st.update(bgColor=_mau(s["nen"][0]), bgAlpha=s["nen"][1], bgStyle=1, bgRoundRadius=0.35,
                  bgWidth=0.14, bgHeight=0.14, bgHOffset=0.0, bgVOffset=0.0)
    if s["bong"]:
        st.update(shadow=True, shadowColor="#000000", shadowAlpha=s["bong"], shadowDistance=5 if s["vien"] else 4,
                  shadowAngle=-45, shadowSmoothing=0.45 if s["vien"] else 0.5)
    return st


def dat_bo(ten):
    """Chọn bộ kiểu chữ cho video (đổi STYLE / CSS / độ đậm của 2 kiểu chinh + nen). Trả tên bộ đã dùng."""
    global BO, CSS
    if ten not in BO_CHU:
        print(f"! Không có bộ kiểu chữ '{ten}' -> dùng 'thuong_hieu'. Có: {', '.join(BO_CHU)}")
        ten = "thuong_hieu"
    BO = ten
    b = BO_CHU[ten]
    for k in ("chinh", "nen"):
        STYLE[k] = {"px": b[k]["px"], "color": _mau(b[k]["color"]), "upper": b[k]["upper"]}
        FONT_W[k] = b[k]["w"]
    CSS = _css_bo(b)
    return ten


def kieu(n):
    return KIEU_MAP.get(n.get("kieu", "chinh"), "chinh")


def lines(n):
    st = STYLE[kieu(n)]
    out = []
    for c in n["chu"]:
        c = c.replace("*", "")
        out.append(c.upper() if st["upper"] else c)
    return out


def html(n):
    """PNG đo + xuất MP4: chữ ở đỉnh khung (top 40), căn giữa; bố cục dời xuống dải đã chọn."""
    k = kieu(n)
    ls = lines(n)
    if k == "chinh":
        body = "".join(f'<span class="l"><span class="bg">{l}</span><span class="fg">{l}</span></span>' for l in ls)
    else:
        body = "".join(f'<span class="l">{l}</span>' for l in ls)
    return f'<div class="t t-{k}" style="top:40px">{body}</div>'


def capcut_text(n, cx, cy, scale=1.0):
    """1 mục chữ CapCut thật + kiểu dáng (text-style)."""
    k = kieu(n)
    st = STYLE[k]
    item = {"text": "\n".join(lines(n)), "fontSize": round(st["px"] * scale / PX_PER_SIZE, 1), "color": st["color"],
            "x": round((cx - W / 2) / (W / 2), 4), "y": round(1 - 2 * cy / H, 4)}
    # dáng theo bộ kiểu chữ đang chọn (mặc định "thuong_hieu" = chinh viền trắng + bóng, nen nền màu thương hiệu)
    style = _capcut_style(BO_CHU[BO][k])
    return item, style


def fixed_text(text, px, color, cx, cy, bg=None, border=None, shadow=True):
    item = {"text": text, "fontSize": round(px / PX_PER_SIZE, 1), "color": color,
            "x": round((cx - W / 2) / (W / 2), 4), "y": round(1 - 2 * cy / H, 4)}
    style = {"alignment": 1}
    if bg:
        style.update({"bgColor": bg[0], "bgAlpha": bg[1], "bgStyle": 1, "bgRoundRadius": 0.45,
                      "bgWidth": 0.14, "bgHeight": 0.14, "bgHOffset": 0.0, "bgVOffset": 0.0})
    if border:
        style.update({"borderColor": border, "borderWidth": 0.04, "borderAlpha": 1.0})
    if shadow:
        style.update({"shadow": True, "shadowColor": "#000000", "shadowAlpha": 0.4, "shadowDistance": 4,
                      "shadowAngle": -45, "shadowSmoothing": 0.5})
    return item, style


def project_font(P, w=600):
    """Chép font Be Vietnam Pro (độ đậm w) vào dự án (draft trỏ tới đây, không phụ thuộc thư mục người dùng khác)."""
    src = FONT_DIR / f"be-vietnam-pro-{w}.ttf"
    dst = Path(P) / "font" / f"BeVietnamPro-{w}.ttf"
    if not dst.exists():
        if not src.exists():
            return None
        dst.parent.mkdir(exist_ok=True)
        shutil.copy2(src, dst)
    return dst


def patch_fonts(draft_dir, font_path, by_text=None):
    """Gắn font Be Vietnam Pro cho mọi chữ (mặc định font_path; by_text: {nội dung chữ: (đường dẫn, tên)})."""
    by_text = by_text or {}
    n = 0
    for f in Path(draft_dir).rglob("*"):
        if f.name not in ("draft_content.json", "template-2.tmp", "draft_info.json") or ".capcut-cli-history" in f.parts:
            continue
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        texts = j.get("materials", {}).get("texts", [])
        if not texts:
            continue
        for t in texts:
            try:
                txt = json.loads(t["content"]).get("text", "")
            except Exception:
                txt = ""
            if txt in by_text and by_text[txt] is None:
                continue                  # chữ theo kho chữ team: giữ font kho đã gắn
            fpath, ften = by_text.get(txt, (font_path, "Be Vietnam Pro SemiBold"))
            fp = Path(fpath).as_posix()
            t.update(font_path=fp, font_resource_id="", font_source_platform=0, font_title=ften,
                     font_name=ften, font_id="", initial_scale=1.0, line_max_width=LINE_MAX)
            c = json.loads(t["content"])
            for s in c.get("styles", []):
                s["font"] = {"path": fp, "id": ""}
                s["bold"] = False
                s["useLetterColor"] = True
            t["content"] = json.dumps(c, ensure_ascii=False)
            n += 1
        f.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    return n
