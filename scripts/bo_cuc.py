"""Bố cục chữ tự động cho dung.py: chữ không che MẶT, không che SẢN PHẨM.

Cách làm (chạy trên máy, không gửi gì ra ngoài):
  1. Dựng bản nháp KHÔNG CHỮ của video (A-roll đã cắt + phóng khung + cảnh trám), 180x320, 5 khung/giây.
  2. Mỗi khung: tách người bằng u2net_human_seg.onnx (có sẵn trong ~/.cache/hyperframes) -> vùng mặt
     (đỉnh đầu -> cổ, rộng theo đầu) + thân người; dò sản phẩm theo MÀU BAO BÌ trong hồ sơ thương hiệu ("mau_san_pham")
     rồi nới khung lên trên/ra hai bên để gồm cả thân chai trắng.
  3. Mỗi chữ (PNG 1080x1920 trong suốt): thử dời theo lưới dọc/ngang, tính phần chữ đè lên mặt / sản phẩm / người /
     logo / nút giỏ hàng / chữ khác đang hiện, trên MỌI khung trong lúc chữ hiện -> chọn chỗ ít đè nhất, gần vị trí gợi ý.
  4. Ghi ảnh chữ đã dời (MP4 và CapCut dùng chung ảnh này) + bang-bo-cuc.jpg để xem.
"""
import hashlib, json, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

W, H = 1080, 1920
GW, GH = 180, 320          # lưới phân tích (1/6)
S = W // GW
FPS_A = 5
import thuong_hieu as th
U2NET = Path(th.MAY.get("u2net", ""))


# ------------------------------------------------------------------ khung nháp
def clean_frames(filter_v, inputs, total, cache):
    """filter_v: chuỗi filter_complex ra nhãn [v] (1080x1920). Trả mảng (N, GH, GW, 3) uint8 ở 5 khung/giây."""
    key = hashlib.md5((filter_v + " ".join(inputs) + f"{total:.3f}").encode()).hexdigest()
    if cache.exists():
        d = np.load(cache)
        if str(d["k"]) == key:
            return d["f"]
    cmd = ["ffmpeg", "-v", "error", "-y"] + inputs + [
        "-filter_complex", filter_v + f";[v]fps={FPS_A},scale={GW}:{GH}:flags=area[o]",
        "-map", "[o]", "-t", f"{total:.3f}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode:
        raise SystemExit("Dựng bản nháp để dò bố cục lỗi: " + r.stderr.decode("utf-8", "replace")[-1500:])
    f = np.frombuffer(r.stdout, np.uint8).reshape(-1, GH, GW, 3)
    np.savez_compressed(cache, f=f, k=key)
    return f


# ------------------------------------------------------------------ dò người / mặt / sản phẩm
def _sess():
    import onnxruntime as ort
    if not U2NET.exists():
        return None
    return ort.InferenceSession(str(U2NET), providers=["CPUExecutionProvider"])


def person_masks(frames, cache):
    key = hashlib.md5(frames[::7].tobytes()).hexdigest()
    if cache.exists():
        d = np.load(cache)
        if str(d.get("k", "")) == key:
            return d["m"]
    sess = _sess()
    if sess is None:
        print("! Không có u2net_human_seg.onnx -> chỉ né sản phẩm, không né người")
        return np.zeros(frames.shape[:3], bool)
    name = sess.get_inputs()[0].name
    mean, std = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])
    out = []
    for fr in frames:
        im = np.asarray(Image.fromarray(fr).resize((320, 320), Image.BILINEAR), np.float32)
        im = im / max(im.max(), 1e-6)
        x = ((im - mean) / std).transpose(2, 0, 1)[None].astype(np.float32)
        p = sess.run(None, {name: x})[0][0, 0]
        p = (p - p.min()) / max(p.max() - p.min(), 1e-6)
        m = np.asarray(Image.fromarray((p * 255).astype(np.uint8)).resize((GW, GH), Image.BILINEAR)) > 110
        out.append(m)
    m = np.array(out)
    np.savez_compressed(cache, m=m, k=key)
    return m


def face_zone(person, so_nguoi=3):
    """Vùng mặt của MỌI người trong khung (góp ý 18/11: cảnh 2 người chỉ thấy 1 mặt -> chữ đè mặt người kia).
    Tìm mặt người cao nhất, xoá cột của người đó, tìm tiếp (tối đa so_nguoi); mặt sau phải nằm nửa trên khung."""
    z = np.zeros_like(person)
    p = person.copy()
    for k in range(so_nguoi):
        m, cot = _mot_mat(p)
        if m is None:
            break
        rows = np.where(m.any(1))[0]
        if k and (len(rows) == 0 or rows[0] > GH * 0.55):
            break
        z |= m
        p[:, cot[0]:cot[1]] = False
    return z


def _mot_mat(person):
    z, cot = _mot_mat_z(person)
    return (z if z.any() else None), cot


def _mot_mat_z(person):
    """Vùng mặt từ mặt nạ người: đỉnh đầu -> cổ (1.65 x bề rộng đầu), nới 30% hai bên. Trả mặt nạ GHxGW."""
    z = np.zeros_like(person)
    rows = np.where(person.sum(1) >= 4)[0]
    if len(rows) == 0:
        return z, (0, 0)
    top = rows[0]
    probe = min(GH - 1, top + 120 // S)
    xs = np.where(person[probe])[0]
    if len(xs) == 0:
        return z, (0, 0)
    # đầu = đoạn liền mạch quanh giữa các điểm người ở hàng dò
    mid = int(np.median(xs))
    x0 = x1 = mid
    while x0 > 0 and person[probe, x0 - 1]:
        x0 -= 1
    while x1 < GW - 1 and person[probe, x1 + 1]:
        x1 += 1
    hw = max(x1 - x0, 60 // S)
    hw = min(hw, 420 // S)
    bot = min(GH, int(top + 1.65 * hw))
    pad = int(0.3 * hw)
    c0, c1 = max(0, x0 - pad), min(GW, x1 + pad + 1)
    z[max(0, top - 2):bot, c0:c1] = True
    return z, (c0, c1)


def product_mask(fr):
    """Sản phẩm: mảng màu bao bì (hồ sơ thương hiệu "mau_san_pham", vd xanh lá nhãn chai/hộp) -> khung nới lên trên
    + hai bên (thân chai thường trắng)."""
    a = fr.astype(np.float32) / 255
    mx, mn = a.max(-1), a.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = _hue(a, mx, mn)
    green = np.zeros(mx.shape, bool)
    for h0 in MAU_HUE:
        d = np.abs(hue - h0)
        green |= (np.minimum(d, 360 - d) < 22) & (sat > 0.32) & (mx > 0.22)
    m = np.zeros_like(green)
    try:
        from scipy import ndimage  # có thì dùng
        lab, n = ndimage.label(ndimage.binary_closing(green, iterations=2))
        objs = ndimage.find_objects(lab)
    except ImportError:
        lab, objs = _label(green)
    for i, sl in enumerate(objs):
        if sl is None:
            continue
        ys, xs = sl
        h, w = ys.stop - ys.start, xs.stop - xs.start
        blob = lab[sl] == i + 1
        if h * w < 30 or blob.sum() < 18:
            continue
        # lá cây / vật cùng màu nhưng tối hoặc nhỏ -> không phải bao bì (bao bì in màu sáng, mảng lớn)
        if float(mx[sl][blob].mean()) < 0.5 or blob.sum() < 45:
            continue
        y0 = max(0, int(ys.start - 0.9 * h)); y1 = min(GH, int(ys.stop + 0.25 * h))
        x0 = max(0, int(xs.start - 0.35 * w)); x1 = min(GW, int(xs.stop + 0.35 * w))
        m[y0:y1, x0:x1] = True
    return m


def _hue(a, mx, mn):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h


def _hex_hue(c):
    c = c.lstrip("#")
    rgb = np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], np.float32).reshape(1, 1, 3) / 255
    return float(_hue(rgb, rgb.max(-1), rgb.min(-1))[0, 0])


MAU_HUE = [_hex_hue(c) for c in th.TH.get("mau_san_pham", ["#6CBE45"])]


def _label(mask):
    """Gán nhãn vùng liền (dự phòng khi không có scipy)."""
    lab = np.zeros(mask.shape, np.int32)
    objs, n = [], 0
    H_, W_ = mask.shape
    for y in range(H_):
        for x in range(W_):
            if mask[y, x] and not lab[y, x]:
                n += 1
                st = [(y, x)]
                lab[y, x] = n
                y0 = y1 = y; x0 = x1 = x
                while st:
                    cy, cx = st.pop()
                    y0, y1, x0, x1 = min(y0, cy), max(y1, cy), min(x0, cx), max(x1, cx)
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < H_ and 0 <= nx < W_ and mask[ny, nx] and not lab[ny, nx]:
                            lab[ny, nx] = n
                            st.append((ny, nx))
                objs.append((slice(y0, y1 + 1), slice(x0, x1 + 1)))
    return lab, objs


def scene_maps(frames, person):
    faces = np.array([face_zone(p) for p in person])
    prods = np.array([product_mask(f) for f in frames])
    return faces, prods


# ------------------------------------------------------------------ đặt chữ
def _alpha_grid(png):
    a = np.asarray(Image.open(png).getchannel("A"))
    g = a.reshape(GH, S, GW, S).max(axis=(1, 3)) > 40
    return a, g


W_NGUOI = 20   # trọng số thân người / tay (mặt luôn 40). Gói Basic hạ xuống: chữ được đè nhẹ lên tay đang thao tác


def place_all(items, frames, person, faces, prods, fixed, out_dir):
    """items: [{name, png, a, b, pref_y (px đỉnh chữ mong muốn) hoặc None}] -> dời ảnh, trả {name: (dx, dy, cost)}.
    fixed: [(a, b, mask GHxGW)] vùng cấm theo thời gian (logo, nút giỏ hàng, thumbnail, dòng pháp lý)."""
    res, placed, group_pos = {}, [], {}
    groups = {}
    for it in sorted(items, key=lambda x: x["a"]):
        if it.get("nhom") is not None:
            groups.setdefault(it["nhom"], []).append(it)
    for it in sorted(items, key=lambda x: x["a"]):
        a_full, g = _alpha_grid(it["png"])
        ys, xs = np.where(g)
        if len(ys) == 0:
            continue
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        gid = it.get("nhom")
        if gid is not None and gid in group_pos:          # dòng sau của danh sách: xếp ngay dưới dòng trước
            gy, gcx, gsc = group_pos[gid]
            hh, ww = int(round((y1 - y0) * gsc)), int(round((x1 - x0) * gsc))
            ny, nx = gy, int(round(gcx - ww / 2))
            if gsc == 1.0:
                _shift(it["png"], (nx - x0) * S, (ny - y0) * S)
            else:
                _move_scaled(it["png"], (x0 * S, y0 * S, x1 * S, y1 * S), gsc, nx * S, ny * S)
            m = np.zeros((GH, GW), bool); m[ny:ny + hh, nx:nx + ww] = True
            placed.append((it["a"], it["b"], m))
            group_pos[gid] = (ny + hh + max(1, round(3 * gsc)), gcx, gsc)
            res[it["name"]] = (int((nx - x0) * S), int((ny - y0) * S), 0.0, gsc)
            continue
        box = g[y0:y1, x0:x1]
        if gid is not None:                                # khối cả danh sách để tìm chỗ
            rows = [box]
            for o in groups[gid][1:]:
                _, go = _alpha_grid(o["png"])
                oy, ox = np.where(go)
                ob = go[oy.min():oy.max() + 1, ox.min():ox.max() + 1]
                rows.append(np.zeros((3, ob.shape[1]), bool)); rows.append(ob)
            wmax = max(r.shape[1] for r in rows)
            box = np.vstack([np.pad(r, ((0, 0), ((wmax - r.shape[1]) // 2, wmax - r.shape[1] - (wmax - r.shape[1]) // 2)))
                             for r in rows])
            x0 = x0 - (wmax - (x1 - x0)) // 2
            x1 = x0 + wmax
            it = dict(it, b=max(o["b"] for o in groups[gid]))
        bh, bw = box.shape
        # bỏ 0,2s hai đầu: khung nối với cảnh kế bên (làm tròn thời gian) không được tính là "đè"
        f0 = int((it["a"] + 0.2) * FPS_A)
        f1 = max(f0 + 1, int((it["b"] - 0.2) * FPS_A))
        f1 = min(f1, len(frames))
        F = faces[f0:f1].mean(0) if f1 > f0 else np.zeros((GH, GW))
        Pm = prods[f0:f1].mean(0) if f1 > f0 else np.zeros((GH, GW))
        Pe = person[f0:f1].mean(0) if f1 > f0 else np.zeros((GH, GW))
        cost_map = 40 * F + 30 * Pm + it.get("w_nguoi", W_NGUOI) * Pe   # mặt / sản phẩm / người: gần như cấm hẳn
        ban = np.zeros((GH, GW))
        for fa, fb, m in fixed + placed:
            if fa < it["b"] and fb > it["a"]:
                ban += m * 30
        cost_map = cost_map + ban
        # vùng an toàn: trên 200px (thanh trạng thái), dưới 1600px (chữ/nút của TikTok), mép 30px
        safe_top, safe_bot = 200 // S, 1520 // S        # vùng an toàn TikTok
        pref = it.get("pref_y")
        best = None
        # thử cỡ 100% / 85% / 70% (chữ nhỏ lại khi khung quá chật), mỗi bậc nhỏ hơn bị trừ điểm
        rows = it.get("rows")                              # chế độ hàng cố định: căn giữa, tâm chữ ở 1 trong các hàng
        for sc in ((1.0, 0.85, 0.72, 0.62) if gid is not None else ((1.0, 0.85, 0.72, 0.62) if rows else (1.0, 0.85, 0.7))):
            if sc == 1.0:
                bx = box
            else:
                bx = np.asarray(Image.fromarray(box.astype(np.uint8) * 255).resize(
                    (max(1, round(bw * sc)), max(1, round(bh * sc))), Image.NEAREST)) > 0
            sh, sw = bx.shape
            if rows:
                cand_y = [max(safe_top, min(safe_bot - sh, int(round(cy / S - sh / 2)))) for cy in rows]
                # căn giữa là chính; giữa bị đè người/mặt thì thử lệch trái / phải (vẫn trong vùng an toàn:
                # mép trái >= 60px, mép phải <= 960px né cột nút TikTok) — bị trừ điểm nên chỉ dùng khi cần
                lech = [x for x in (60 // S, (GW - sw) // 2, 960 // S - sw) if 60 // S <= x <= 960 // S - sw]
                cand_x = sorted(set([(GW - sw) // 2] + lech))
            else:
                cand_y = range(safe_top, safe_bot - sh + 1, 2)
                cand_x = range(30 // S, GW - 30 // S - sw + 1, 3)
            for ny in cand_y:
                for nx in cand_x:
                    c = float((cost_map[ny:ny + sh, nx:nx + sw] * bx).sum() / bx.sum())
                    c += 0.05 * abs(nx - (GW - sw) / 2) / GW          # hơi ưu tiên giữa
                    if rows and nx != (GW - sw) // 2:
                        c += 0.3                                     # hàng cố định: lệch chỉ khi giữa bị đè
                    c += 0.45 * (1 - sc)                             # ưu tiên giữ cỡ chữ
                    if pref is not None:
                        c += 0.25 * abs(ny * S - pref) / H             # gần vị trí gợi ý
                    if best is None or c < best[0]:
                        best = (c, ny, nx, sc, sh, sw)
        c, ny, nx, sc, bh, bw = best
        dy, dx = (ny - y0) * S, (nx - x0) * S
        if sc == 1.0:
            _shift(it["png"], dx, dy)
        else:
            _move_scaled(it["png"], (x0 * S, y0 * S, x1 * S, y1 * S), sc, nx * S, ny * S)
        m = np.zeros((GH, GW), bool)
        if gid is not None:
            fh = int(round((y1 - y0) * sc))                # chiều cao dòng đầu (khối đã chừa chỗ cho các dòng sau)
            group_pos[gid] = (ny + fh + max(1, round(3 * sc)), nx + bw / 2, sc)
            m[ny:ny + fh, nx:nx + bw] = True
            placed.append((it["a"], groups[gid][0]["b"], m))
        else:
            m[ny:ny + bh, nx:nx + bw] = True
            placed.append((it["a"], it["b"], m))
        res[it["name"]] = (int(dx), int(dy), round(float(c), 3), sc)
    _sheet(items, res, frames, faces, prods, out_dir)
    return res


def _move_scaled(png, bbox, sc, nx, ny):
    """Cắt chữ theo khung (chừa 24px cho bóng đổ), thu nhỏ theo sc, dán ở (nx, ny) = góc trên-trái khung mới."""
    im = Image.open(png).convert("RGBA")
    x0, y0, x1, y1 = bbox
    pad = 24
    cx0, cy0, cx1, cy1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    crop = im.crop((cx0, cy0, cx1, cy1))
    crop = crop.resize((max(1, round(crop.width * sc)), max(1, round(crop.height * sc))), Image.LANCZOS)
    can = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    can.paste(crop, (int(nx - (x0 - cx0) * sc), int(ny - (y0 - cy0) * sc)), crop)
    can.save(png)


def _shift(png, dx, dy):
    im = Image.open(png)
    can = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    can.paste(im, (int(dx), int(dy)), im)
    can.save(png)


def _sheet(items, res, frames, faces, prods, out_dir):
    """Bảng xem: mỗi chữ 1 ô = khung giữa thời gian hiện + vùng mặt (đỏ) + sản phẩm (vàng) + chữ."""
    tiles = []
    for it in sorted(items, key=lambda x: x["a"]):
        if it["name"] not in res:
            continue
        fi = min(len(frames) - 1, int((it["a"] + it["b"]) / 2 * FPS_A))
        bg = Image.fromarray(frames[fi]).resize((270, 480)).convert("RGBA")
        ov = np.zeros((GH, GW, 4), np.uint8)
        ov[faces[fi]] = (255, 0, 0, 70)
        ov[prods[fi]] = (255, 210, 0, 70)
        bg.alpha_composite(Image.fromarray(ov).resize((270, 480)))
        txt = Image.open(it["png"]).resize((270, 480))
        bg.alpha_composite(txt)
        d = ImageDraw.Draw(bg)
        d.rectangle([0, 0, 270, 16], fill=(0, 0, 0, 160))
        d.text((4, 2), f"{it['name']} {it['a']:.1f}s c={res[it['name']][2]}", fill=(255, 255, 0, 255))
        tiles.append(bg)
    if not tiles:
        return
    cols = 8
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 270, rows * 480), (20, 20, 20))
    for i, t in enumerate(tiles):
        sheet.paste(t.convert("RGB"), ((i % cols) * 270, (i // cols) * 480))
    sheet.save(out_dir / "bang-bo-cuc.jpg", quality=85)
