"""TỰ CHỌN MÀU CHỮ theo THƯƠNG HIỆU + SẢN PHẨM + VIDEO (20/11/2026 — người dùng: "skill tự nhận diện màu sản phẩm, video,
thương hiệu để chọn màu cho phù hợp").

Nguồn màu (trọng số):
  - logo thương hiệu (PNG, nếu hồ sơ có)                    x3
  - màu bao bì ghi trong hồ sơ ("mau_san_pham")            x2
  - cảnh trám / cận sản phẩm (các clip khác A-roll trong raw/) x2  — lấy vùng giữa khung, nơi sản phẩm hay nằm
  - khung hình người nói (A-roll)                           -> là NỀN: màu nào phủ nhiều trên nền thì bị trừ điểm
                                                               (chữ trùng màu nền sẽ chìm)
Chỉ tính điểm ảnh có sắc rõ (bão hoà >= 0,35, không quá tối) — bỏ trắng / đen / xám / da người.
Chọn sắc độ điểm cao nhất -> đẩy về màu tươi đọc rõ trên video (S ~0,8, V ~0,9) -> mau_chinh; cùng sắc đậm -> mau_dam;
vừa -> mau_vien. Không có màu nào rõ -> màu tương phản với nền (vàng nếu nền lạnh, xanh dương nếu nền ấm).

Kết quả lưu projects/<du-an>/mau.json (lần sau dùng lại, xoá file để dò lại) + mau.jpg (bảng màu đã dò để xem).

Dùng (tự động trong thuong_hieu.tai_thuong_hieu):
  - hồ sơ thương hiệu KHÔNG ghi "mau_chinh"                -> tự chọn
  - hồ sơ ghi "mau_tu_dong": true, hoặc cau-hinh "mau": "tu_dong" -> tự chọn (bỏ qua màu hồ sơ, nhưng màu hồ sơ / logo
    vẫn là 1 nguồn trọng số cao)
  - cau-hinh "mau": "#RRGGBB" -> dùng đúng màu đó ; "mau": "thuong_hieu" -> giữ màu hồ sơ
Chạy tay: mau_tu_dong.py <thư mục dự án>  (in kết quả, ghi mau.json + mau.jpg)
"""
import colorsys, json, subprocess, sys
from pathlib import Path

BIN = 36                     # số ô sắc độ (10 độ / ô)
import numpy as _np
HIST_SV = _np.zeros((BIN, 2))   # tổng (bão hoà, độ sáng) có trọng số của lần _hist gần nhất


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c * 255))) for c in rgb)


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _khung(video, n=5, crop=None):
    """Trích n khung nhỏ (PIL Image) rải đều trong clip."""
    from PIL import Image
    import io
    try:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                                   capture_output=True, text=True).stdout.strip() or 0)
    except Exception:
        dur = 0
    out = []
    for i in range(n):
        t = dur * (i + 0.5) / n if dur else i
        vf = "scale=180:320" if not crop else f"crop=iw*{crop}:ih*{crop},scale=160:160"
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-vf", vf,
                            "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
        if r.stdout:
            try:
                out.append(Image.open(io.BytesIO(r.stdout)).convert("RGB"))
            except Exception:
                pass
    return out


def _hist(imgs, alpha=None):
    """Biểu đồ sắc độ (BIN ô) có trọng số bão hoà, chỉ điểm ảnh có màu rõ; trả (hist, tỉ lệ điểm ảnh có màu)."""
    import numpy as np
    h = np.zeros(BIN)
    sv = np.zeros((BIN, 2))
    tong = co = 0
    for im in imgs:
        a = np.asarray(im.convert("RGBA") if alpha else im.convert("RGB"), dtype=np.float32) / 255
        if alpha:
            m = a[..., 3] > 0.5
            a = a[..., :3][m]
        else:
            a = a.reshape(-1, 3)
        if not len(a):
            continue
        mx, mn = a.max(1), a.min(1)
        s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        r, g, b = a[:, 0], a[:, 1], a[:, 2]
        d = np.maximum(mx - mn, 1e-6)
        hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
        # bỏ trắng/đen/xám và màu da (sắc 0.02–0.11, bão hoà vừa, sáng) — da người không phải màu thương hiệu
        da = (hue > 0.0) & (hue < 0.11) & (s < 0.65) & (mx > 0.35)
        ok = (s >= 0.35) & (mx >= 0.25) & ~da
        tong += len(a); co += int(ok.sum())
        ix = (hue[ok] * BIN).astype(int) % BIN
        np.add.at(h, ix, s[ok])
        np.add.at(sv, ix, np.stack([s[ok] * s[ok], mx[ok] * s[ok]], 1))
    if h.sum():
        sv = sv / h.sum()
        h = h / h.sum()
    HIST_SV[:] = sv
    return h, (co / tong if tong else 0)


def _lam_muot(h):
    import numpy as np
    return (np.roll(h, 1) + 2 * h + np.roll(h, -1)) / 4


def chon(project_dir, th, ghi=True):
    """Trả {"mau_chinh", "mau_dam", "mau_vien", "nguon", ...}."""
    import numpy as np
    P = Path(project_dir)
    luu = P / "mau.json"
    if luu.exists():
        try:
            return json.loads(luu.read_text(encoding="utf-8"))
        except Exception:
            pass
    cfg = {}
    try:
        cfg = json.loads((P / "cau-hinh.json").read_text(encoding="utf-8"))
    except Exception:
        pass
    raw = P / "raw"
    aroll = raw / cfg.get("aroll", "") if cfg.get("aroll") else None
    tong = np.zeros(BIN)
    sv_tong = np.zeros((BIN, 2))
    nguon = []
    # 1) logo
    lg = th.get("logo")
    if lg and Path(lg).exists():
        from PIL import Image
        hl, _ = _hist([Image.open(lg)], alpha=True)
        if hl.sum():
            tong += 3 * hl; sv_tong += 3 * HIST_SV; nguon.append("logo")
    # 2) màu hồ sơ (màu thương hiệu ghi tay + màu bao bì)
    for k, w in (("_mau_ho_so", 3), ("mau_san_pham", 2)):
        v = th.get(k) or []
        for c in (v if isinstance(v, list) else [v]):
            if isinstance(c, str) and c.startswith("#") and len(c) >= 7:
                hh, s, vv = colorsys.rgb_to_hsv(*_rgb(c))
                if s >= 0.3:
                    tong[int(hh * BIN) % BIN] += w * 0.5; nguon.append(f"{k} {c}")
    # 3) cảnh trám / cận sản phẩm: vùng giữa khung
    # ưu tiên đúng các clip cảnh trám đang dùng trong cau-hinh; không có thì mọi clip khác A-roll (bỏ ảnh minh hoạ "_anh")
    clips = [raw / b["file"] for b in cfg.get("broll", []) if b.get("file") and (raw / b["file"]).exists()]
    if not clips and raw.exists():
        clips = [f for f in sorted(raw.glob("*.mp4")) if (not aroll or f.name != aroll.name) and "_anh" not in f.stem]
    clips = list(dict.fromkeys(clips))[:12]
    if clips:
        imgs = [im for f in clips for im in _khung(f, 2, crop=0.6)]
        hp, ty = _hist(imgs)
        if hp.sum():
            tong += 2 * hp; sv_tong += 2 * HIST_SV; nguon.append(f"cảnh sản phẩm ({len(clips)} clip, {ty:.0%} điểm ảnh có màu)")
    # 4) nền A-roll
    hn = np.zeros(BIN); ty_nen = 0
    if aroll and aroll.exists():
        hn, ty_nen = _hist(_khung(aroll, 5))
    hn_m = _lam_muot(_lam_muot(_lam_muot(hn))) * 2.5 * min(1.0, ty_nen * 6)      # nền ít màu (tường trắng) -> trừ ít
    diem = _lam_muot(tong / max(tong.sum(), 1e-6)) - 1.0 * hn_m        # trùng màu nền -> chữ chìm -> trừ điểm
    if tong.sum() and diem.max() > 0.03:
        b = int(diem.argmax())
        hue = (b + 0.5) / BIN
        ly_do = "màu nổi bật nhất của " + " + ".join(x.split(" (")[0] for x in nguon)
    else:
        # không có màu rõ -> tương phản với nền
        am = hn[: BIN // 6].sum() + hn[-BIN // 12:].sum()           # đỏ-cam-vàng
        hue = 0.6 if am > 0.5 else 0.135
        ly_do = "không thấy màu thương hiệu / sản phẩm rõ -> màu tương phản nền"
    # GIỮ TÍNH CÁCH màu gốc (hồng pastel vẫn là hồng, không thành đỏ chói) nhưng đủ đậm / sáng để đọc trên video
    s0 = v0 = None
    if tong.sum() and diem.max() > 0.03:
        lan = [(b - 1) % BIN, b, (b + 1) % BIN]
        w = sum(tong[i] for i in lan)
        if w > 0:
            s0 = sum(sv_tong[i][0] for i in lan) / w      # bão hoà trung bình của màu gốc
            v0 = sum(sv_tong[i][1] for i in lan) / w      # độ sáng trung bình
    vang = 0.10 <= hue <= 0.20
    s, v = (0.78, 1.0) if vang else (0.80, 0.92)
    if s0 is not None:                                    # theo màu gốc, kẹp vào vùng đọc rõ
        s = min(0.85, max(0.45, s0 * 1.15))
        v = min(1.0, max(0.80 if not vang else 0.92, v0 * 1.1))
    chinh = _hex(colorsys.hsv_to_rgb(hue, s, v))
    dam = _hex(colorsys.hsv_to_rgb(hue, 0.85, 0.42))
    vien = _hex(colorsys.hsv_to_rgb(hue, 0.75, 0.68))
    kq = {"mau_chinh": chinh, "mau_dam": dam, "mau_vien": vien, "sac_do": round(hue * 360), "ly_do": ly_do,
          "nguon": nguon, "nen_co_mau": round(ty_nen, 3),
          "_huong_dan": "Màu chữ tự chọn (mau_tu_dong.py). Xoá file này để dò lại; ép màu: \"mau\": \"#RRGGBB\" trong cau-hinh.json."}
    if ghi:
        luu.write_text(json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
        try:
            _bang(P / "mau.jpg", tong, hn, kq)
        except Exception:
            pass
    return kq


def _bang(out, tong, hn, kq):
    """Ảnh xem nhanh: dải sắc độ nguồn (trên) / nền (dưới) + ô màu đã chọn."""
    from PIL import Image, ImageDraw
    W, H = 720, 220
    im = Image.new("RGB", (W, H), (30, 30, 30)); d = ImageDraw.Draw(im)
    bw = 480 / BIN
    for i in range(BIN):
        c = tuple(round(x * 255) for x in colorsys.hsv_to_rgb((i + 0.5) / BIN, 0.8, 0.9))
        for arr, y0 in ((tong, 10), (hn, 115)):
            hh = int(90 * (arr[i] / max(arr.max(), 1e-6)))
            d.rectangle([10 + i * bw, y0 + 90 - hh, 10 + (i + 1) * bw - 1, y0 + 90], fill=c)
    for j, k in enumerate(("mau_chinh", "mau_dam", "mau_vien")):
        d.rectangle([510, 10 + j * 68, 710, 70 + j * 68], fill=kq[k])
        d.text((516, 14 + j * 68), f"{k} {kq[k]}", fill=(255, 255, 255) if k != "mau_chinh" else (0, 0, 0))
    d.text((12, 102), "nguon: logo / san pham", fill=(200, 200, 200)); d.text((12, 207), "nen video", fill=(200, 200, 200))
    im.save(out, quality=88)


def ap(project_dir, th, the_ho_so):
    """Gọi từ thuong_hieu: quyết định có tự chọn màu không, rồi ghi đè mau_chinh/mau_dam/mau_vien trong th."""
    try:
        cfg = json.loads((Path(project_dir) / "cau-hinh.json").read_text(encoding="utf-8"))
    except Exception:
        return th
    m = cfg.get("mau")
    if isinstance(m, str) and m.startswith("#"):
        hh, s, v = colorsys.rgb_to_hsv(*_rgb(m))
        th.update(mau_chinh=m, mau_dam=_hex(colorsys.hsv_to_rgb(hh, 0.85, 0.42)), mau_vien=_hex(colorsys.hsv_to_rgb(hh, 0.75, 0.68)))
        return th
    if m == "thuong_hieu":
        return th
    tu_dong = m == "tu_dong" or the_ho_so.get("mau_tu_dong") or "mau_chinh" not in the_ho_so
    if not tu_dong:
        return th
    if "mau_chinh" in the_ho_so:
        th["_mau_ho_so"] = the_ho_so["mau_chinh"]
    try:
        kq = chon(project_dir, th)
    except Exception as e:
        print(f"! Không tự chọn được màu ({e}) -> giữ màu hồ sơ")
        return th
    th.update(mau_chinh=kq["mau_chinh"], mau_dam=kq["mau_dam"], mau_vien=kq["mau_vien"])
    print(f"Màu chữ tự chọn: {kq['mau_chinh']} — {kq['ly_do']} (xem {Path(project_dir) / 'mau.jpg'})")
    return th


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.path.insert(0, str(Path(__file__).parent))
    import thuong_hieu as T
    P = Path(sys.argv[1])
    th = T.tai_thuong_hieu(P)
    (P / "mau.json").unlink(missing_ok=True)
    the = T._doc(T.SKILL / "thuong-hieu" / f"{json.loads((P / 'cau-hinh.json').read_text(encoding='utf-8')).get('thuong_hieu', '')}.json")
    th["_mau_ho_so"] = the.get("mau_chinh")
    print(json.dumps(chon(P, th), ensure_ascii=False, indent=1))
