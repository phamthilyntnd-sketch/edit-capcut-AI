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
PX_PER_SIZE = 4.0          # px trên khung 1080x1920 / cỡ chữ CapCut (ước lượng; CapCut máy này chưa vẽ chữ để căn)
FONT_DIR = th.FONTS
FONT_SRC = FONT_DIR / "be-vietnam-pro-600.ttf"
FONT_NAME = "BeVietnamPro-SemiBold.ttf"
# độ đậm theo kiểu: chữ nhấn chính đậm hơn cho dễ đọc trên điện thoại
FONT_W = {"chinh": 800, "nen": 700, "co_dinh": 600}
FONT_TEN = {600: "Be Vietnam Pro SemiBold", 700: "Be Vietnam Pro Bold", 800: "Be Vietnam Pro ExtraBold"}
# hiệu ứng chữ CÓ SẴN của CapCut (capcut enums --text-intros / --text-outros): (vào, giây, ra, giây)
ANIM_CAPCUT = {"chinh": ("pop-up", 0.35, "fade-out", 0.25), "nen": ("slide-up", 0.35, "fade-out", 0.25)}

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
    if k == "chinh":   # viền trắng dày 20 (thang CapCut 0–100 -> 0.04) + bóng, đúng brief
        style = {"alignment": 1, "borderColor": "#FFFFFF", "borderWidth": 0.06, "borderAlpha": 1.0,
                 "shadow": True, "shadowColor": "#000000", "shadowAlpha": 0.45, "shadowDistance": 5,
                 "shadowAngle": -45, "shadowSmoothing": 0.45}
    else:              # nền xanh bo góc
        style = {"alignment": 1, "bgColor": GREEN, "bgAlpha": 1.0, "bgStyle": 1, "bgRoundRadius": 0.35,
                 "bgWidth": 0.14, "bgHeight": 0.14, "bgHOffset": 0.0, "bgVOffset": 0.0,
                 "shadow": True, "shadowColor": "#000000", "shadowAlpha": 0.3, "shadowDistance": 4,
                 "shadowAngle": -45, "shadowSmoothing": 0.5}
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
            fpath, ften = by_text.get(txt, (font_path, "Be Vietnam Pro SemiBold"))
            fp = Path(fpath).as_posix()
            t.update(font_path=fp, font_resource_id="", font_source_platform=0, font_title=ften,
                     font_name=ften, font_id="", initial_scale=1.0, line_max_width=0.92)
            c = json.loads(t["content"])
            for s in c.get("styles", []):
                s["font"] = {"path": fp, "id": ""}
                s["bold"] = False
                s["useLetterColor"] = True
            t["content"] = json.dumps(c, ensure_ascii=False)
            n += 1
        f.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    return n
