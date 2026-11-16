"""Chọn ĐOẠN HAY trong mỗi clip cảnh trám (người dùng: "cảnh trám cần chọn đoạn hay trong cả đoạn", "có đoạn chưa có
nội dung gì").

Mỗi clip được chấm điểm 4 khung/giây (180x320, chạy trên máy):
  - nét      : phương sai Laplacian (mờ / rung -> thấp)
  - nội dung : tỉ lệ khung có NGƯỜI (u2net) hoặc SẢN PHẨM (mảng màu bao bì theo hồ sơ thương hiệu)
  - chuyển động: chênh lệch giữa 2 khung — đứng im trống trơn hoặc lia/rung mạnh đều bị trừ
Khung "hỏng" (mờ, gần như không có người/sản phẩm, lia máy mạnh) không được nằm trong đoạn chọn.
Cache: raw/_tram/<clip>.npz.  Bảng xem: projects/<du-an>/bang-tram.jpg (đầu | giữa | cuối mỗi đoạn đã chọn).
"""
import hashlib, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

FPS_T = 4
GW, GH = 180, 320


def _frames(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={FPS_T},scale={GW}:{GH}:flags=area",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, GH, GW, 3)


def analyze(path, cache_dir):
    """-> dict(t, sharp, content, motion, frames) cho cả clip (cache theo kích thước + thời gian sửa file)."""
    path = Path(path)
    st = path.stat()
    key = hashlib.md5(f"{path.name}{st.st_size}{st.st_mtime_ns}".encode()).hexdigest()[:10]
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    cache = Path(cache_dir) / f"{path.stem}_{key}.npz"
    if cache.exists():
        d = np.load(cache)
        return {k: d[k] for k in d.files}
    import bo_cuc as bc
    fr = _frames(path)
    person = bc.person_masks(fr, Path(cache_dir) / f"{path.stem}_{key}_nguoi.npz")
    prod = np.array([bc.product_mask(f) for f in fr])
    g = fr.astype(np.float32).mean(-1)
    lap = (4 * g[:, 1:-1, 1:-1] - g[:, :-2, 1:-1] - g[:, 2:, 1:-1] - g[:, 1:-1, :-2] - g[:, 1:-1, 2:])
    sharp = lap.reshape(len(g), -1).var(1)
    content = np.clip(person.reshape(len(g), -1).mean(1) + 1.5 * prod.reshape(len(g), -1).mean(1), 0, 1)
    motion = np.r_[0, np.abs(np.diff(g, axis=0)).reshape(len(g) - 1, -1).mean(1)]
    out = {"t": np.arange(len(g)) / FPS_T, "sharp": sharp, "content": content, "motion": motion,
           "thumbs": fr[:, ::2, ::2]}
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, **out)
    return out


def frame_score(a):
    """Chỉ lấy CẢNH QUAY ĐẸP (người dùng 14/11): nét, đủ sáng (không tối / cháy), có người hoặc sản phẩm, máy ổn định."""
    s = np.clip(a["sharp"] / 600, 0, 1)                      # 600+ = nét rõ
    c = np.clip(a["content"] / 0.25, 0, 1)                   # >= 25% khung là người/sản phẩm = đủ nội dung
    m = a["motion"]
    mo = np.where(m < 1.0, 0.5, np.where(m > 15, 0.0, 1.0))  # đứng im trơ / lia, rung mạnh bị trừ
    br = a["thumbs"].astype(np.float32).mean(axis=(1, 2, 3)) / 255 if "thumbs" in a else np.full(len(s), 0.5)
    ex = np.clip(1 - np.abs(br - 0.55) / 0.35, 0, 1)        # sáng vừa ~0.55 là đẹp nhất
    # góp ý 16/11 "cảnh trám lấy chưa đẹp": ngưỡng nét chặt hơn (250)
    bad = (a["sharp"] < 250) | (a["content"] < 0.05) | (m > 22) | (br < 0.18) | (br > 0.92)
    return 0.35 * s + 0.35 * c + 0.15 * mo + 0.15 * ex, bad


BIEN = 0.5   # bỏ 0,5s đầu/cuối mỗi clip: lúc bấm quay / dừng máy hay rung, chưa vào cảnh


def pick(a, dur, used=(), within=None, avoid=()):
    """Đoạn dài `dur` giây có điểm TB cao nhất, không chứa khung hỏng, không trùng đoạn đã dùng / vùng tránh,
    tránh 0,5s đầu/cuối clip, và ƯU TIÊN ĐOẠN ỔN ĐỊNH (chuyển động đều, không giật cục giữa chừng)."""
    sc, bad = frame_score(a)
    n, w = len(sc), max(1, int(round(dur * FPS_T)))
    b = int(BIEN * FPS_T)
    lo, hi = (b, n - w - b) if n - w - 2 * b >= 0 else (0, n - w)
    if within:
        lo, hi = max(lo, int(within[0] * FPS_T)), min(hi, int(within[1] * FPS_T) - w)
    mo = np.asarray(a["motion"], np.float32)
    best = None
    for i in range(lo, hi + 1):
        t0, t1 = i / FPS_T, (i + w) / FPS_T
        if any(t0 < b_ and t1 > a_ for a_, b_ in list(used) + list(avoid)):
            continue
        nb = bad[i:i + w].sum()
        giat = float(np.std(mo[i:i + w])) / 10.0           # chuyển động lúc nhanh lúc chậm = máy giật / đổi cảnh
        v = sc[i:i + w].mean() - 0.5 * nb / w - 0.1 * min(giat, 1.0)
        if best is None or v > best[0]:
            best = (v, t0)
    if best is None:
        return None, 0.0
    return round(best[1], 2), round(float(best[0]), 3)


def _font(px):
    from PIL import ImageFont
    try:
        import thuong_hieu as th
        return ImageFont.truetype(str(th.FONTS / "be-vietnam-pro-600.ttf"), px)
    except Exception:
        return ImageFont.load_default()


def sheet(choices, out_png):
    """choices: [(nhãn, analyze-dict, from, dur[, lời đang nói])] -> ảnh đầu|giữa|cuối mỗi đoạn + LỜI ĐANG NÓI lúc đó,
    để soát cảnh trám có KHỚP LỜI không (góp ý 16/11 "cảnh trám lấy chưa chuẩn")."""
    import textwrap
    rows, LW = [], 330
    f1, f2 = _font(13), _font(14)
    for ch in choices:
        lab, a, f0, d = ch[:4]
        loi = ch[4] if len(ch) > 4 else ""
        th = a["thumbs"]
        idx = [min(len(th) - 1, int((f0 + x) * FPS_T)) for x in (0.1, d / 2, max(0.1, d - 0.2))]
        row = Image.new("RGB", (3 * 90 + LW, 160), (25, 25, 25))
        for k, i in enumerate(idx):
            row.paste(Image.fromarray(th[i]), (LW + k * 90, 0))
        dr = ImageDraw.Draw(row)
        dr.text((6, 4), lab, fill=(255, 230, 0), font=f1)
        if loi:
            dr.multiline_text((6, 26), "\n".join(textwrap.wrap("“" + loi + "”", 40)[:7]), fill=(235, 235, 235),
                              font=f2, spacing=3)
        rows.append(row)
    if not rows:
        return
    im = Image.new("RGB", (rows[0].width, 160 * len(rows)))
    for k, r in enumerate(rows):
        im.paste(r, (0, 160 * k))
    im.save(out_png, quality=85)
