"""Dựng video bán hàng / review dọc 9:16 thành PROJECT CAPCUT sửa được + MP4 xem thử, theo HỒ SƠ THƯƠNG HIỆU.
Cắt vấp · cảnh trám chọn đoạn đẹp · chữ nhấn CapCut thật né người & sản phẩm · chuyển cảnh / hiệu ứng / tiếng nhấn
có sẵn · lọc tạp âm · kiểm bản ra + luật quảng cáo · cập nhật TẠI CHỖ project đang góp ý.

Chạy:  <python có faster-whisper> scripts/dung.py <thư mục dự án> [--pngs] [--mp4] [--capcut] [--qa] [--moi] [--xem-mau]
Không cờ nào = làm tất cả (trừ --moi / --xem-mau).
"""
import hashlib, json, math, os, re, subprocess, sys, shutil, time, wave
from pathlib import Path
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import thuong_hieu as th
import chu as tc
ROOT = th.SKILL
FONTS = th.FONTS
TH, MAY = th.TH, th.MAY
LOGO_FILE = Path(TH["logo"]) if TH.get("logo") else Path("__khong_co_logo__")
W, H, FPS = 1080, 1920, 30
# Bộ công cụ dùng chung (bo-skill-video): chỉnh màu/mịn da (edit-video-cao-cap), kiểm bản ra, an toàn nội dung, hồ sơ ngành,
# tiếng SFX tự tổng hợp (edit-video-sub-va-hieu-ung). Không dùng Remotion (cần giấy phép công ty cho video khách).
ENG = Path(MAY["eng"]) if MAY.get("eng") else Path("__khong_co_eng__")
ENG_PY = ENG / ".venv" / "Scripts" / "python.exe"
TECHPRO = Path(MAY.get("techpro", ""))
CAM = TH["tu_cam"]                       # từ cấm (hồ sơ thương hiệu + luật QC)
GREEN, DARK, VIEN = TH["mau_chinh"], TH["mau_dam"], TH["mau_vien"]


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def find_chrome():
    for base in (os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", ""), os.environ.get("LOCALAPPDATA", "")):
        for c in (os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                  os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe")):
            if base and os.path.isfile(c):
                return c
    raise SystemExit("Không tìm thấy Chrome/Edge")


def fr(t):  # làm tròn theo khung hình
    return round(t * FPS) / FPS


# ---------------------------------------------------------------- cắt
def silences(path):
    r = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vn", "-af", "silencedetect=n=-35dB:d=0.25", "-f", "null", "-"])
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return list(zip(st, en))


ENV_HOP = 0.01   # 10 ms


def envelope(path):
    """Độ lớn tiếng (dB) mỗi 10 ms của clip -> dùng để đặt điểm cắt / mốc chữ đúng lúc tiếng nói bắt đầu / tắt hẳn."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                       capture_output=True)
    x = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768
    n = len(x) // 160
    if n == 0:
        raise SystemExit(f"Không đọc được tiếng của {path} (thiếu file hoặc clip không có âm thanh)")
    db = 20 * np.log10(np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1)) + 1e-6)
    floor, speech = np.percentile(db, 10), np.percentile(db, 90)
    return {"db": db, "thr": floor + 0.25 * (speech - floor)}


def _i(env, t):
    return int(min(max(t / ENV_HOP, 0), len(env["db"]) - 1))


def onset(env, t):
    """Mốc tiếng nói bắt đầu thật quanh mốc Whisper t (lệch ±0,1–0,3s): chỗ âm lượng VỌT LÊN mạnh nhất trong
    [t-0,25; t+0,3] — để chữ hiện ĐÚNG lúc nói."""
    if env is None:
        return t
    db = env["db"]
    i0, i1 = _i(env, t - 0.25), _i(env, t + 0.3)
    if i1 - i0 < 5:
        return t
    best = max(range(i0, i1 - 3), key=lambda i: db[i + 3] - db[i])
    return (best + 1) * ENV_HOP if db[best + 3] - db[best] > 8 else t


def quiet_after(env, t, lim=0.35):
    """Điểm tiếng TẮT HẲN sau mốc t: đáy của cửa sổ [t, t+lim] + 6 dB; lấy điểm đầu tiên xuống tới mức đó (+0,04s).
    Bắt được cả âm cuối nhẹ ('hiệu', 'quả') mà ngưỡng cố định hay bỏ sót."""
    if env is None:
        return t + 0.15
    db = env["db"]
    i0, i1 = _i(env, t), _i(env, t + lim)
    m = db[i0:i1 + 1].min()
    for i in range(i0, i1 + 1):
        if db[i] <= m + 6:
            return i * ENV_HOP + 0.04
    return t + lim


def quiet_before(env, t, lim=0.3):
    """Điểm còn IM ngay trước khi tiếng nói bắt đầu quanh mốc t: đáy cửa sổ [t-lim, t+0,05] + 6 dB, lấy điểm im muộn nhất."""
    if env is None:
        return t - 0.1
    db = env["db"]
    i0, i1 = _i(env, t - lim), _i(env, t + 0.05)
    m = db[i0:i1 + 1].min()
    for i in range(i1, i0 - 1, -1):
        if db[i] <= m + 6:
            return i * ENV_HOP - 0.02
    return t - lim


def _co_tieng(env):
    """Ngưỡng 'có tiếng nói' riêng cho từng clip: nền ồn + 35% khoảng cách tới mức nói."""
    db = env["db"]
    f, sp = np.percentile(db, 10), np.percentile(db, 90)
    return f + 0.35 * (sp - f)


def build_pieces(keeps, sil, min_gap=0.35, pad=0.12, words=(), env=None, tho=None, duoi=0.4, dai_clip=None, cam=()):
    """Đoạn giữ -> các mảnh A-roll, BÁM TIẾNG NÓI THẬT (góp ý 17/11 "cắt giữa các đoạn vẫn còn đoạn trống"):
    - đầu mảnh = lúc tiếng nói thật bắt đầu - 0,1s ; cuối mảnh = lúc tiếng tắt thật + 0,1s  -> giữa 2 câu còn ~0,2s
    - mọi quãng im >= 0,35s bên trong đoạn giữ (đo bằng độ lớn tiếng, không chỉ dựa mốc Whisper) cũng rút còn ~0,2s
    - không bao giờ cắt giữa 1 từ được giữ, không lấn vào từ đã bỏ; cuối video dư ~0,4s."""
    ws = sorted(words, key=lambda w: w["s"])
    # NHỊP NGƯỜI NÓI (19/11): khoảng chừa ở vết cắt theo nhịp tự nhiên — trung vị khoảng nghỉ giữa 2 từ liền nhau
    # (0,04–0,35s) x1,2, kẹp 0,14–0,24s -> người nói nhanh chừa ít, nói chậm chừa nhiều hơn chút (mặc định cũ 0,2s)
    if tho is None:
        g = [b["s"] - a["e"] for a, b in zip(ws, ws[1:]) if 0.04 < b["s"] - a["e"] < 0.35]
        tho = min(0.12, max(0.07, 0.6 * float(np.median(g)))) if len(g) >= 8 else 0.10
    # CẮT CỨNG (cat_sach.py, cau-hinh "cat_tieng"): vùng có tiếng mà không thành chữ / lắp trong từ -> luôn cắt bỏ
    cam = sorted([float(a), float(b)] for a, b in (cam or []) if b > a)
    db = env["db"] if env is not None else None
    thr = _co_tieng(env) if env is not None else None
    pieces = []
    for s, e in keeps:
        s_, e_ = s, e
        kin = [w for w in ws if s <= (w["s"] + w["e"]) / 2 <= e]
        ngoai_sau = [w for w in ws if kin and w["s"] >= kin[-1]["e"] - 0.01 and not s_ <= (w["s"] + w["e"]) / 2 <= e_]
        ngoai_truoc = [w for w in ws if kin and w["e"] <= kin[0]["s"] + 0.01 and not s_ <= (w["s"] + w["e"]) / 2 <= e_]
        lo = ngoai_truoc[-1]["e"] + 0.02 if ngoai_truoc else max(0.0, s - 0.3)
        hi = ngoai_sau[0]["s"] - 0.02 if ngoai_sau else e + 0.4
        if db is not None and kin:
            a0, a1 = _i(env, max(lo, min(s, kin[0]["s"]) - 0.3)), _i(env, kin[0]["s"] + 0.5)
            on = next((i for i in range(a0, a1) if db[i] > thr and db[min(i + 4, len(db) - 1)] > thr), None)
            b0, b1 = _i(env, kin[-1]["s"]), _i(env, min(hi, max(e, kin[-1]["e"]) + 0.35))
            off = next((i for i in range(b1, b0, -1) if db[i] > thr), None)
            s = (on * ENV_HOP if on is not None else kin[0]["s"]) - tho
            e = ((off + 1) * ENV_HOP if off is not None else kin[-1]["e"]) + tho
        elif kin:
            s, e = kin[0]["s"] - tho, kin[-1]["e"] + tho
        s, e = max(s, lo), min(e, hi)
        if kin:   # không bao giờ cắt vào từ được giữ
            s, e = min(s, kin[0]["s"]), max(e, min(kin[-1]["e"], hi))
        # quãng im bên trong: từ envelope (>= min_gap dưới ngưỡng có tiếng) + khoảng lặng ffmpeg
        im = []
        if db is not None:
            i, i_end = _i(env, s + 0.05), _i(env, e - 0.05)
            while i < i_end:
                if db[i] <= thr:
                    j = i
                    while j < i_end and db[j] <= thr:
                        j += 1
                    if (j - i) * ENV_HOP >= min_gap:
                        im.append((i * ENV_HOP, j * ENV_HOP))
                    i = j
                else:
                    i += 1
        else:
            im = [(a, b) for a, b in sil if b - a >= min_gap and s < a and b < e]
        cung = [(a - tho, b + tho) for a, b in cam if a < e and b > s]
        im = sorted(im + cung)
        cur = s
        for a, b in im:
            cut_a, cut_b = a + tho, b - tho
            if cut_a < cur:              # chồng lên vùng cắt trước (vd vùng cắt cứng trùng quãng im)
                cur = max(cur, cut_b)
                continue
            if (a, b) in cung:
                if cut_a > cur:
                    pieces.append([cur, cut_a])
                cur = cut_b
                continue
            # mốc Whisper nói đang có 1 chữ bình thường ở đây (phụ âm đầu nhẹ như "gh", "th", âm cuối nhẹ) -> KHÔNG cắt.
            # Chỉ cắt trong "từ" dài bất thường (>= 0,8s: Whisper nuốt cả quãng im vào 1 từ).
            if any(w["e"] - w["s"] < 0.8 and (w["s"] - 0.02 < cut_a < w["e"] + 0.02 or w["s"] - 0.02 < cut_b < w["e"] + 0.02)
                   for w in kin):
                continue
            if cut_b - cut_a < 0.12:
                continue
            if cut_a > cur:
                pieces.append([cur, cut_a])
            cur = cut_b
        pieces.append([cur, e])
    pieces.sort()
    if pieces:   # cuối video để dư ~0,4s (0,3–0,5s) rồi mới hết, không tắt ngang
        sau = [w for w in ws if w["s"] >= pieces[-1][1] - 0.01]
        gioi_han = [pieces[-1][1] + duoi]
        if dai_clip:
            gioi_han.append(dai_clip - 0.05)
        if sau:
            gioi_han.append(sau[0]["s"] - 0.02)
        pieces[-1][1] = max(pieces[-1][1], min(gioi_han))
    # KHÔNG LẮT NHẮT: mẩu < 0,45s mà không có đầu chữ nào bên trong (chỉ là tiếng thở / tiếng kéo dài) -> bỏ
    pieces = [pc for pc in pieces if pc[1] - pc[0] >= 0.45
              or any(pc[0] - 0.02 <= w["s"] <= pc[1] - 0.05 and w["e"] - w["s"] < 0.8 for w in ws)]
    for x, y in zip(pieces, pieces[1:]):   # 2 đoạn giữ nới ra chạm nhau -> không phát lặp 1 khúc tiếng
        if y[0] < x[1]:
            y[0] = x[1]
    out, t = [], 0.0
    for s, e in pieces:
        s, e = fr(s), fr(e)
        if e - s < 2 / FPS:
            continue
        out.append({"s": s, "e": e, "o": round(t, 6)})
        t = fr(t + (e - s))
    return out, t



def mo_tieng_vet_cat(draft_dir, vao_us=15000, ra_us=20000):
    """Làm mờ tiếng vào/ra rất ngắn cho mọi đoạn trên track VIDEO CHÍNH (thoại giữ tiếng trong video) — ghi thẳng vật liệu
    "audio_fade" của CapCut (capcut audio-fade chỉ nhận track âm thanh). Trả số đoạn đã gắn."""
    import uuid
    n = 0
    for f in Path(draft_dir).rglob("*"):
        if f.name not in ("draft_content.json", "template-2.tmp") or ".capcut-cli-history" in f.parts:
            continue
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        vt = [t for t in j.get("tracks", []) if t.get("type") == "video"]
        if not vt:
            continue
        fades = j.setdefault("materials", {}).setdefault("audio_fades", [])
        co = {x["id"] for x in fades}
        dem = 0
        for sg in vt[0].get("segments", []):
            refs = sg.setdefault("extra_material_refs", [])
            if any(r in co for r in refs):
                continue
            fid = str(uuid.uuid4()).upper()
            fades.append({"id": fid, "fade_in_duration": vao_us, "fade_out_duration": ra_us, "fade_type": 0, "type": "audio_fade"})
            refs.append(fid)
            dem += 1
        f.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
        n = max(n, dem)
    return n


def mike_diem_nhan(cfg, m, fr, P=None):
    """ĐIỂM NHẤN MIKE (20/11/2026): cau-hinh "mike_diem_nhan": ["<thư mục dự án Mike nhỏ>", ...] — mỗi dự án Mike dựng
    vài câu đắt giá (chữ sau đầu, cảnh đồ hoạ...) bằng /edit-video-mike-2 với edl = đúng các đoạn giữ của câu đó trong
    video này. Bản render của Mike phủ lên đúng giây tương ứng (lớp "Mike" trong CapCut, tắt tiếng — giọng vẫn là của
    timeline chính); chữ nhấn của skill trùng khung giờ đó tự bỏ (Mike đã có chữ riêng). Không chép mã Mike: chỉ đọc
    segments.json + bản render Mike xuất ra."""
    out = []
    for i, d in enumerate(cfg.get("mike_diem_nhan") or []):
        D = Path(d)
        segf = D / "segments.json"
        rs = sorted([r for r in (D / "renders").glob("*.mp4") if not re.search(r"-(phone|raw)\.mp4$", r.name)],
                    key=lambda r: r.stat().st_mtime) if (D / "renders").exists() else []
        if not segf.exists() or not rs:
            print(f"! Điểm nhấn Mike {D.name}: chưa có segments.json / bản render -> bỏ qua")
            continue
        src_r = rs[-1]
        if P is not None:   # chép bản render vào dự án: project CapCut không phụ thuộc thư mục Mike (mất / dọn vẫn mở được)
            dst = Path(P) / "mike" / f"{D.name}.mp4"
            dst.parent.mkdir(exist_ok=True)
            if not dst.exists() or dst.stat().st_mtime < src_r.stat().st_mtime:
                shutil.copy2(src_r, dst)
            src_r = dst
        fps = 30   # mốc khung trong segments.json của Mike tính theo 30 khung/giây
        try:
            fps = json.loads((D / "work" / "editor-map.json").read_text(encoding="utf-8")).get("fps", 30)
        except Exception:
            pass
        for j, sg in enumerate(json.loads(segf.read_text(encoding="utf-8"))):
            a_src = sg.get("src_in", sg["in"]); b_src = sg.get("src_out", sg["out"])
            dur = sg["frames"] / fps
            t0 = m(a_src, "start"); t1 = m(b_src, "end")
            if abs((t1 - t0) - dur) > 0.15:
                print(f"! Điểm nhấn Mike {D.name}/{sg.get('id')}: đoạn {a_src:.2f}-{b_src:.2f}s không khớp vết cắt của video "
                      f"({t1 - t0:.2f}s vs {dur:.2f}s) -> bỏ; dựng Mike với edl = đúng các đoạn giữ (keeps)")
                continue
            out.append({"path": str(src_r), "start": fr(t0), "duration": fr(dur), "from": round(sg["frame"] / fps, 4),
                        "ref": f"mike{i}_{j}", "mike": True})
    if out:
        print(f"Điểm nhấn Mike: {len(out)} đoạn, {sum(x['duration'] for x in out):.1f}s")
    return out


def mapper(pieces):
    def m(t, side="start"):
        for p in pieces:
            if p["s"] <= t <= p["e"]:
                return p["o"] + (t - p["s"])
        if side == "start":
            for p in pieces:
                if p["s"] > t:
                    return p["o"]
            return pieces[-1]["o"] + pieces[-1]["e"] - pieces[-1]["s"]
        prev = None
        for p in pieces:
            if p["s"] > t:
                break
            prev = p
        return (prev["o"] + prev["e"] - prev["s"]) if prev else 0.0
    return m


# ---------------------------------------------------------------- phụ đề
def apply_fix(text, fix):
    for k, v in fix.items():
        text = text.replace(k, v)
    text = text.strip()
    return text[0].upper() + text[1:] if text else text


KEEP = {tuple(x.split()) for x in ["chiết xuất", "thoải mái", "những gì", "có thể", "vùng kín", "thành phần",
    "dung tích", "khỏe mạnh", "sản phẩm", "hướng dẫn", "sử dụng", "mang lại", "giỏ hàng", "người mua", "công dụng",
    "công bố", "chúng ta", "lựa chọn", "chăm sóc", "bản thân", "thông tin", "nhu cầu", "mangino women", "tìm hiểu",
    "trình bày", "rõ ràng", "đánh giá", "thiên nhiên", "thực vật", "quyết định", "thảo dược", "tự nhiên", "bao bì",
    "lô hội", "bạc hà", "lá xoài", "màn hình", "góc trái", "nhẹ nhàng", "tươi mát", "sạch thoáng", "hàng ngày", "tham khảo", "điểm cộng", "hằng ngày", "món quà", "thiết thực"]}


def make_cues(segs, cfg, pieces, m, maxc=40):
    cues = []
    for i, sg in enumerate(segs):
        if i in cfg.get("skip_segments", []):
            continue
        ws = sg["words"]
        inside = sum(any(p["s"] - 0.05 <= (w["s"] + w["e"]) / 2 <= p["e"] + 0.05 for p in pieces) for w in ws)
        if inside < min(3, max(1, 0.5 * len(ws))):   # câu chỉ chạm mép điểm cắt thì không phải lời có trong video
            continue
        text = apply_fix(sg["text"], cfg["fix"])
        words = text.split()
        if len(words) == len(ws):
            times = [w["s"] for w in ws]
        else:
            s0, s1 = ws[0]["s"], ws[-1]["e"]
            tot = sum(len(w) + 1 for w in words)
            acc, times = 0, []
            for w in words:
                times.append(s0 + (s1 - s0) * acc / tot)
                acc += len(w) + 1
        end = ws[-1]["e"]
        total_len = len(" ".join(words))
        nch = max(1, math.ceil(total_len / maxc))
        chunks, cur, acc = [], [], 0
        for j, w in enumerate(words):
            cur.append(j)
            acc += len(w) + 1
            nxt = words[j + 1].lower().strip(',.?!"') if j + 1 < len(words) else ""
            if (w.lower().strip(',.?!"'), nxt) in KEEP:
                continue
            if len(chunks) < nch - 1 and acc >= total_len * (len(chunks) + 1) / nch - 2:
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        for ci, ch in enumerate(chunks):
            a = times[ch[0]]
            b = times[chunks[ci + 1][0]] if ci + 1 < len(chunks) else end
            oa, ob = m(a, "start"), m(b + 0.1, "end")
            if ob - oa > 0.2:
                cues.append({"text": " ".join(words[k] for k in ch), "a": oa, "b": ob})
    cues.sort(key=lambda c: c["a"])
    for k in range(len(cues) - 1):
        if cues[k + 1]["a"] - cues[k]["b"] < 0.35:
            cues[k]["b"] = cues[k + 1]["a"]
        cues[k]["b"] = min(cues[k]["b"], cues[k + 1]["a"])
    return [dict(c, a=fr(c["a"]), b=fr(c["b"])) for c in cues if fr(c["b"]) - fr(c["a"]) >= 0.2]


# ---------------------------------------------------------------- ảnh chữ (Chrome)
CSS = f"""
html,body{{margin:0;padding:0;width:{W}px;height:{H}px;background:transparent;overflow:hidden;
  font-family:'Be Vietnam Pro',sans-serif;font-weight:600}}
.sub{{position:absolute;left:70px;right:70px;bottom:250px;text-align:center;font-size:60px;line-height:1.22;letter-spacing:1px;
  color:{GREEN}}}
.sub i{{font-style:italic;font-weight:700}}
.call{{position:absolute;left:50px;right:50px;top:360px;text-align:center;font-size:76px;line-height:1.2;
  color:{GREEN}}}
.bg{{color:#fff;-webkit-text-stroke:15px #fff;filter:drop-shadow(4px 4px 4px rgba(0,0,0,.32))}}
.call.bg{{-webkit-text-stroke:17px #fff}}
.pill{{position:absolute;left:80px;right:80px;top:1170px;min-height:190px;box-sizing:border-box;
  background:#fff;border:6px solid {VIEN};border-radius:200px;display:flex;align-items:center;justify-content:center;
  padding:24px 40px;text-align:center;font-size:64px;line-height:1.2;color:{GREEN};white-space:nowrap}}
.thumb .tb-band{{display:inline-block;background:{GREEN};color:#fff;font-weight:800;border-radius:26px;
  padding:10px 36px 16px;margin-bottom:16px;box-shadow:4px 6px 12px rgba(0,0,0,.35);line-height:1.15}}
.thumb .tb-big{{font-weight:800;line-height:1.06;color:{GREEN};letter-spacing:.5px}}
.thumb .tb-big .l{{position:relative;display:block}}
.thumb .tb-big .bg{{position:absolute;left:0;right:0;top:0;color:#fff;-webkit-text-stroke:28px #fff;
  filter:drop-shadow(5px 8px 8px rgba(0,0,0,.45))}}
.thumb .tb-big .fg{{position:relative}}
.cta{{position:absolute;left:46px;top:1440px;display:flex;align-items:center;gap:14px;background:{GREEN};
  color:#fff;font-size:46px;font-weight:700;padding:16px 34px 16px 22px;border-radius:60px;border:5px solid #fff;
  filter:drop-shadow(3px 3px 4px rgba(0,0,0,.3))}}
.cta .ar{{font-size:58px;line-height:1}}
.nh{{position:absolute;left:46px;right:46px;text-align:center;line-height:1.14}}
.nh i{{font-style:italic}}
.k-xanh{{font-size:92px;font-weight:800;color:{GREEN}}}
.k-xanh.bg{{color:#fff;-webkit-text-stroke:20px #fff;filter:drop-shadow(4px 5px 5px rgba(0,0,0,.35))}}
.k-trang{{font-size:86px;font-weight:800;color:#fff}}
.k-trang.bg{{color:{GREEN};-webkit-text-stroke:18px {GREEN};filter:drop-shadow(4px 5px 5px rgba(0,0,0,.35))}}
.box{{display:inline-block;border-radius:70px;padding:14px 46px 18px}}
.k-pill .box{{background:#fff;border:6px solid {VIEN};color:{GREEN};font-size:66px;font-weight:700;
  box-shadow:4px 6px 10px rgba(0,0,0,.28)}}
.k-the .box{{background:{GREEN};border:6px solid #fff;color:#fff;font-size:64px;font-weight:800;border-radius:22px;
  transform:rotate(-2.5deg);box-shadow:4px 6px 10px rgba(0,0,0,.3)}}
.k-list .box{{background:#fff;border:5px solid {VIEN};color:{DARK};font-size:54px;font-weight:700;border-radius:20px;
  padding:10px 34px 12px;box-shadow:3px 5px 8px rgba(0,0,0,.25)}}
.k-list .dot{{color:{GREEN};margin-right:14px}}
.k-lock .nho{{display:inline-block;background:{GREEN};color:#fff;font-size:44px;font-weight:700;border-radius:40px;
  padding:6px 30px 9px;margin-bottom:10px;box-shadow:3px 4px 8px rgba(0,0,0,.25)}}
.k-lock .to{{position:relative;font-size:96px;font-weight:800;line-height:1.08}}
.k-lock .to .bg,.k-lock .to .fg{{display:block}}
.k-lock .to .bg{{position:absolute;left:0;right:0;top:0;color:#fff;-webkit-text-stroke:20px #fff;
  filter:drop-shadow(4px 5px 5px rgba(0,0,0,.35))}}
.k-lock .to .fg{{position:relative;color:{GREEN}}}
.nhan{{position:absolute;right:46px;top:150px;font-size:26px;font-weight:600;color:#fff;background:rgba(0,0,0,.38);
  padding:6px 16px;border-radius:30px;letter-spacing:.5px}}
.phaply{{position:absolute;left:40px;right:40px;top:1352px;text-align:center;font-size:27px;line-height:1.3;color:#fff;
  font-weight:600;text-shadow:0 0 6px rgba(0,0,0,.85),0 2px 3px rgba(0,0,0,.7)}}
.logo{{position:absolute;left:52px;top:128px;width:180px;text-align:center}}
.logo .ov{{width:180px;height:112px;border-radius:50%;background:{GREEN};transform:rotate(-12deg);
  display:flex;align-items:center;justify-content:center}}
.logo .stv{{font-family:'Arial Black',Arial,sans-serif;font-style:italic;font-weight:900;font-size:62px;color:#fff;
  transform:rotate(12deg) skewX(-12deg);letter-spacing:-2px}}
.logo .nm{{font-family:Arial,sans-serif;font-weight:700;font-size:25px;color:{GREEN};margin-top:4px;letter-spacing:1px}}
"""


CSS2 = """
.nh .em{font-family:'Segoe UI Emoji','Noto Color Emoji',sans-serif;font-style:normal}
.k-hook .hand{display:inline-block;font-family:'Patrick Hand',cursive;font-size:60px;color:#fff;line-height:1.05;
  margin-bottom:10px;background:DARKC;padding:4px 30px 8px;border-radius:40px;transform:rotate(-2deg);
  box-shadow:3px 5px 10px rgba(0,0,0,.3)}
.big{position:relative;font-weight:900;line-height:1.06;letter-spacing:-1px}
.big .bg,.big .fg{display:block}
.big .bg{position:absolute;left:0;right:0;top:0}
.big .fg{position:relative}
.k-hook .big{font-size:104px}
.k-hook .bg{color:#fff;-webkit-text-stroke:22px #fff;filter:drop-shadow(4px 6px 6px rgba(0,0,0,.35))}
.k-hook .fg{color:GREEN}
.k-hook .bg .hl{color:DARKC;-webkit-text-stroke-color:DARKC}
.k-hook .fg .hl{color:#FFD23F}
.k-punch .big{font-size:132px}
.k-punch .bg{color:DARKC;-webkit-text-stroke:24px DARKC;filter:drop-shadow(5px 7px 7px rgba(0,0,0,.45))}
.k-punch .fg{color:#fff}
.k-punch .fg .hl{color:#FFD23F}
.k-quote{font-family:'Playfair Display',serif;font-style:italic;font-weight:900}
.k-quote .big{font-size:84px;letter-spacing:0}
.k-quote .bg{color:GREEN;-webkit-text-stroke:16px GREEN;filter:drop-shadow(3px 5px 6px rgba(0,0,0,.4))}
.k-quote .fg{color:#fff}
.k-quote .fg .hl{color:#FFE680}
.k-quote .mark{display:block;font-size:150px;line-height:.55;color:#fff;height:62px;
  text-shadow:0 0 0 GREEN,3px 3px 0 GREEN,-3px -3px 0 GREEN,3px -3px 0 GREEN,-3px 3px 0 GREEN}
.k-note .card{display:inline-block;position:relative;background:#FFFDF2;color:#24501A;font-family:'Patrick Hand',cursive;
  font-size:70px;line-height:1.08;padding:22px 44px 26px;border-radius:10px;transform:rotate(-3deg);
  box-shadow:5px 8px 14px rgba(0,0,0,.33)}
.k-note .card:before{content:"";position:absolute;left:50%;top:-18px;width:150px;height:38px;margin-left:-75px;
  background:rgba(108,190,69,.85);transform:rotate(2deg)}
.k-note .hl{color:#fff;background:GREEN;padding:0 10px;border-radius:8px}
.k-benefit .card,.k-list .card,.k-product .card{display:inline-flex;align-items:center;gap:20px;text-align:left}
.k-benefit .card{background:GREEN;border:6px solid #fff;border-radius:34px;padding:14px 40px 16px 16px;
  color:#fff;font-size:60px;font-weight:800;box-shadow:4px 7px 12px rgba(0,0,0,.32)}
.k-benefit .ic,.k-list .ic{display:inline-flex;align-items:center;justify-content:center;width:96px;height:96px;
  border-radius:50%;background:#fff;font-size:58px;flex:none}
.k-benefit .hl{color:#FFE680}
.k-list .card{background:#fff;border:5px solid GREEN;border-radius:26px;padding:8px 36px 8px 10px;
  color:#24501A;font-size:56px;font-weight:700;box-shadow:3px 6px 10px rgba(0,0,0,.28)}
.k-list .ic{background:#EAF6E2;width:82px;height:82px;font-size:50px}
.k-list .hl{color:GREEN}
.k-product .card{flex-direction:column;align-items:center;gap:0;text-align:center;background:#fff;border:7px solid GREEN;
  border-radius:36px;padding:16px 50px 20px;box-shadow:5px 8px 14px rgba(0,0,0,.3)}
.k-product .sm{font-size:40px;font-weight:700;color:DARKC;letter-spacing:4px}
.k-product .lg{font-size:90px;font-weight:900;color:GREEN;line-height:1.02;letter-spacing:-1px}
.nh{white-space:nowrap}
.nh .big .fg,.nh .big .bg{width:max-content;margin:0 auto}
""".replace("GREEN", GREEN).replace("DARKC", DARK)
CSS_GOC = CSS + CSS2
CSS = CSS_GOC + tc.CSS

# chuyển động theo kiểu: (phóng [(giây, tỉ lệ)], hiện [(giây, độ đục)]) — phóng quanh tâm khung, giống nhau ở MP4 và CapCut
ANIM = {"pop": ([(0, 0.86), (0.12, 1.05), (0.22, 1.0)], [(0, 0.0), (0.12, 1.0)]),
        "slam": ([(0, 1.32), (0.13, 0.96), (0.22, 1.0)], [(0, 0.0), (0.07, 1.0)]),
        "fade": ([(0, 0.96), (0.32, 1.0)], [(0, 0.0), (0.3, 1.0)]),
        "soft": ([(0, 0.92), (0.16, 1.02), (0.26, 1.0)], [(0, 0.0), (0.14, 1.0)])}
KIEU_ANIM = {"hook": "pop", "quote": "fade", "punch": "slam", "note": "soft", "benefit": "pop", "list": "soft",
             "product": "pop"}


def _hl(t):
    """*từ* -> tô nổi; :emoji: giữ nguyên; bọc emoji bằng span để dùng font màu."""
    t = re.sub(r"\*([^*]+)\*", r'<span class="hl">\1</span>', t)
    return re.sub(r"([\U0001F300-\U0001FAFF\u2600-\u27BF\u2728\u2764]\ufe0f?)", r'<span class="em">\1</span>', t)


def keep_nbsp(text):
    """Cụm trong KEEP không bị trình duyệt ngắt dòng giữa chừng."""
    w = text.split(" ")
    out = w[0]
    for a, b in zip(w, w[1:]):
        key = (re.sub(r"<[^>]+>", "", a).lower().strip(',.?!"'), re.sub(r"<[^>]+>", "", b).lower().strip(',.?!"'))
        out += ("&nbsp;" if key in KEEP else " ") + b
    return out


VI_TRI = {"tren": 330, "giua": 1110, "duoi": 1330}


def _norm(w):
    return re.sub(r"[^\w%]", "", w.lower())


def find_phrase(segs, phrase, after=0.0):
    """Mốc (nguồn) của cụm lời trong transcript thô: (giây bắt đầu từ đầu, giây kết thúc đoạn chứa nó)."""
    want = [_norm(x) for x in phrase.split() if _norm(x)]
    words = [(w, sg) for sg in segs for w in sg["words"] if w["s"] >= after - 0.05]
    toks = [_norm(w["w"]) for w, _ in words]
    for i in range(len(toks) - len(want) + 1):
        if toks[i:i + len(want)] == want:
            return words[i][0]["s"], words[i + len(want) - 1][1]["end"], words[i + len(want) - 1][0]["e"]
    raise SystemExit(f"Không thấy cụm lời '{phrase}' (sau {after}s) trong transcript.json")


def nhan_html(n):
    """1 chữ nhấn -> HTML khung 1080x1920 (vị trí cố định, để CapCut và MP4 giống nhau)."""
    k, chu = n.get("kieu", "xanh"), [_hl(c) for c in n["chu"]]
    top = n.get("vi_tri", "duoi")
    top = VI_TRI.get(top, top) if isinstance(top, str) else int(top)
    st = f'style="top:{top}px"'
    ic = f'<span class="ic"><span class="em">{n["icon"]}</span></span>' if n.get("icon") else ""
    if k == "hook":
        big = "<br>".join(chu[1:])
        return (f'<div class="nh k-hook" {st}><div class="hand">{chu[0]}</div>'
                f'<div class="big"><span class="bg">{big}</span><span class="fg">{big}</span></div></div>')
    if k in ("punch", "quote"):
        big = "<br>".join(chu)
        mk = '<span class="mark">“</span>' if k == "quote" else ""
        return (f'<div class="nh k-{k}" {st}>{mk}<div class="big"><span class="bg">{big}</span>'
                f'<span class="fg">{big}</span></div></div>')
    if k == "note":
        return f'<div class="nh k-note" {st}><span class="card">' + "<br>".join(chu) + "</span></div>"
    if k in ("benefit", "list") and (n.get("icon") or k == "benefit"):
        return f'<div class="nh k-{k}" {st}><span class="card">{ic}<span>' + "<br>".join(chu) + "</span></span></div>"
    if k == "product":
        em = f' <span class="em">{n["icon"]}</span>' if n.get("icon") else ""
        return (f'<div class="nh k-product" {st}><span class="card"><span class="sm">{chu[0]}</span>'
                f'<span class="lg">{"<br>".join(chu[1:])}{em}</span></span></div>')
    if k in ("xanh", "trang"):
        inner = "<br>".join(chu)
        return (f'<div class="nh k-{k} bg" {st}>{inner}</div>'
                f'<div class="nh k-{k}" {st}>{inner}</div>')
    if k in ("pill", "the"):
        return f'<div class="nh k-{k}" {st}><span class="box">' + "<br>".join(chu) + "</span></div>"
    if k == "list":
        return f'<div class="nh k-list" {st}><span class="box"><span class="dot">✔</span>{chu[0]}</span></div>'
    if k == "lock":  # dòng nhỏ trên nền xanh + dòng to
        big = "<br>".join(chu[1:])
        return (f'<div class="nh k-lock" {st}><div><span class="nho">{chu[0]}</span></div>'
                f'<div class="to"><span class="bg">{big}</span><span class="fg">{big}</span></div></div>')
    raise SystemExit(f"Kiểu chữ nhấn không có: {k}")


def thumb_px(cfg):
    """Cỡ chữ thumbnail: dòng to ~100px (thumb_size cũ 64 = mặc định; câu dài đặt thumb_size nhỏ hơn), dải nền = 0,6 lần."""
    big = 100 * float(cfg.get("thumb_size") or 64) / 64
    return round(big * 0.6), round(big)


def thumb_parts(cfg):
    ls = [l for l in cfg["thumb"] if l.strip()]
    return (ls[0], ls[1:]) if len(ls) >= 2 else (None, ls)


def thumb_html(cfg, part="all"):
    """THUMBNAIL MỚI (góp ý 16/11 "ảnh thumbnail chưa đẹp"): dòng 1 = chữ trắng trên dải màu thương hiệu bo góc,
    các dòng sau = chữ TO màu thương hiệu, ExtraBold, viền trắng dày + bóng đổ. 1 dòng -> chỉ kiểu chữ to."""
    band, big = thumb_parts(cfg)
    pb, pg = thumb_px(cfg)
    h = ""
    if band and part in ("all", "band"):
        h += f'<div class="tb-band" style="font-size:{pb}px">{band}</div>'
    if big and part in ("all", "big"):
        h += f'<div class="tb-big" style="font-size:{pg}px">' + "".join(
            f'<span class="l"><span class="bg">{l}</span><span class="fg">{l}</span></span>' for l in big) + "</div>"
    return f'<div class="t thumb" style="top:1170px">{h}</div>'


def stroked(cls, inner):
    return f'<div class="{cls} bg">{inner}</div><div class="{cls}">{inner}</div>'


def html_page(body):
    return (f'<!doctype html><html><head><meta charset="utf-8"><base href="{FONTS.as_uri()}/">'
            f'<link rel="stylesheet" href="fonts.css"><style>{tc.sang_vien(CSS)}</style></head><body>{body}'
            f'<div style="font-family:\'Be Vietnam Pro\';font-weight:700;position:absolute;opacity:0">ạ<i>ạ</i></div>'
            # chữ nhấn không rớt dòng: dòng nào quá rộng thì co cỡ chữ cả khối
            '<script>document.fonts.ready.then(()=>{document.querySelectorAll(".nh,.t").forEach(el=>{'
            'const k=el.querySelector(".big,.card,.hand")?el:el;'
            'const wide=()=>Math.max(...[...el.querySelectorAll(".big .fg,.card,.hand,.l .fg,.t-nen .l,.tb-band")].map(c=>Math.max(c.scrollWidth,c.getBoundingClientRect().width)),0);'
            'let z=1;for(let i=0;i<30&&wide()*z>990;i++){z*=0.95;}'
            'if(z<1){el.style.zoom=z;el.style.top=(parseFloat(el.style.top||0)/z)+"px";}})})</script></body></html>')


def render_pngs(jobs, out_dir):
    chrome = find_chrome()
    prof = out_dir / "_chrome-profile"
    for name, body in jobs:
        png = out_dir / f"{name}.png"
        hp = out_dir / f"_{name}.html"
        hp.write_text(html_page(body), encoding="utf-8")
        run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
             f"--user-data-dir={prof}", "--allow-file-access-from-files", "--force-device-scale-factor=1",
             "--default-background-color=00000000", f"--window-size={W},{H}", "--virtual-time-budget=4000",
             f"--screenshot={png}", hp.as_uri()], timeout=120)
        hp.unlink(missing_ok=True)
        if not png.exists():
            raise SystemExit(f"Vẽ ảnh lỗi: {name}")
    shutil.rmtree(prof, ignore_errors=True)


def logo_png(out_dir):
    dst = out_dir / "logo.png"
    if not LOGO_FILE.exists() and not TH.get("logo_chu"):   # khách chưa có logo -> không đặt logo
        dst.unlink(missing_ok=True)
        return "không có logo"
    if LOGO_FILE.exists():
        lg = Image.open(LOGO_FILE).convert("RGBA")
        a = np.asarray(lg).copy()
        if a[..., 3].min() == 255:  # nền trắng -> trong suốt
            white = (a[..., 0] > 235) & (a[..., 1] > 235) & (a[..., 2] > 235)
            # chỉ xoá trắng nối với viền ngoài (giữ chữ STV trắng trong hình oval)
            from PIL import ImageDraw
            mask = Image.fromarray((white * 255).astype("uint8"))
            ImageDraw.floodfill(mask, (0, 0), 128)
            ImageDraw.floodfill(mask, (mask.width - 1, mask.height - 1), 128)
            outside = np.asarray(mask) == 128
            a[outside, 3] = 0
            lg = Image.fromarray(a)
        lg = lg.crop(lg.getbbox())
        w = 190
        lg = lg.resize((w, round(lg.height * w / lg.width)), Image.LANCZOS)
        can = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        can.paste(lg, (50, 125), lg)
        can.save(dst)
        return "file"
    render_pngs([("logo", f'<div class="logo"><div class="ov"><span class="stv">{TH["logo_chu"][:3]}</span></div>'
                          f'<div class="nm">{TH["logo_chu"]}</div></div>')], out_dir)
    return "ve-lai"


# ---------------------------------------------------------------- nhạc nền
def make_music(path, dur, sr=48000):
    bpm = 84
    beat = 60 / bpm
    n = int((dur + 1) * sr)
    t = np.arange(n) / sr
    out = np.zeros((n, 2))
    prog = [[60, 64, 67, 71], [57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 67]]
    f = lambda m: 440 * 2 ** ((m - 69) / 12)
    bar = 4 * beat
    k = 0
    while k * bar * 2 < dur + 1:
        ch = prog[k % 4]
        a0 = int(k * bar * 2 * sr)
        L = int(bar * 2 * sr)
        tt = np.arange(L) / sr
        env = np.minimum(1, tt / 0.8) * np.minimum(1, (bar * 2 - tt) / 0.8)
        seg = np.zeros(L)
        for mnote in ch:
            for det in (-0.08, 0.08):
                seg += np.sin(2 * np.pi * f(mnote) * (1 + det / 100) * tt) * 0.05
            seg += np.sin(2 * np.pi * f(mnote - 12) * tt) * 0.03
        seg *= env
        e = min(n, a0 + L)
        out[a0:e, 0] += seg[: e - a0]
        out[a0:e, 1] += seg[: e - a0]
        # arpeggio nhẹ
        notes = ch + [ch[2] + 12, ch[1] + 12, ch[3], ch[2]]
        for s in range(16):
            st = a0 + int(s * beat / 2 * sr)
            if st >= n:
                break
            Ln = int(1.2 * sr)
            tn = np.arange(Ln) / sr
            mm = notes[s % len(notes)] + 12
            pl = (np.sin(2 * np.pi * f(mm) * tn) + 0.3 * np.sin(4 * np.pi * f(mm) * tn)) * np.exp(-tn * 4.5) * 0.06
            e2 = min(n, st + Ln)
            pan = 0.35 if s % 2 else -0.35
            out[st:e2, 0] += pl[: e2 - st] * (1 - pan)
            out[st:e2, 1] += pl[: e2 - st] * (1 + pan)
        k += 1
    d = int(0.18 * sr)  # vang nhẹ
    out[d:, 0] += out[:-d, 1] * 0.25
    out[d:, 1] += out[:-d, 0] * 0.25
    out = out[: int(dur * sr)]
    fade = int(2.0 * sr)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    out[: int(0.6 * sr)] *= np.linspace(0, 1, int(0.6 * sr))[:, None]
    out /= np.abs(out).max() + 1e-9
    out *= 10 ** (-3 / 20)
    pcm = (out * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


def loudness(path):
    r = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vn", "-af", "ebur128", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else -20.0


# ---------------------------------------------------------------- chỉnh màu (edit-video-cao-cap)
def _grade_args(g):
    a = []
    if g.get("kieu"):
        a += ["--kieu", g["kieu"]]
    if g.get("auto"):
        a.append("--auto")
    for k in ("net", "sat", "warm", "contrast", "denoise"):
        if g.get(k) is not None:
            a += [f"--{k}", str(g[k])]
    return a


def grade_clip(src, g, skin):
    """grade_video.py của bộ dùng chung -> raw/_mau/<ten>_<khoa>.mp4 (giữ nguyên tiếng và mốc thời gian)."""
    if not ENG_PY.exists():
        if not getattr(grade_clip, "_bao", False):
            print("! Không có bộ dùng chung bo-skill-video (may.json: eng) -> bỏ qua chỉnh màu")
            grade_clip._bao = True
        return src
    key = hashlib.md5(json.dumps([g, skin], sort_keys=True).encode()).hexdigest()[:6]
    dst = src.parent / "_mau" / f"{src.stem}_{key}.mp4"
    if dst.exists():
        return dst
    dst.parent.mkdir(exist_ok=True)
    r = run([str(ENG_PY), "-X", "utf8", str(ENG / "scripts/grade_video.py"), str(src), str(dst), "--skin", str(skin)]
            + _grade_args(g))
    if r.returncode or not dst.exists():
        print("! Chỉnh màu lỗi, dùng clip gốc:", (r.stderr or r.stdout)[-400:])
        return src
    print(f"Chỉnh màu: {src.name} -> {dst.name}")
    return dst


def grade_preview(src, g, t, out_dir):
    r = run([str(ENG_PY), "-X", "utf8", str(ENG / "scripts/grade_video.py"), str(src), str(out_dir / "_xem.mp4"),
             "--skin", str(g.get("skin", 1)), "--preview", f"{t:.2f}"] + _grade_args(g))
    print(r.stdout.strip()[-800:] or r.stderr[-800:])


# ---------------------------------------------------------------- SFX (edit-video-sub-va-hieu-ung)
SFX_DIR = Path(MAY["sfx"])
SFX_KIEU = {"xanh": ("pop", -16), "trang": ("pop", -16), "pill": ("pop", -17), "list": ("click", -14),
            "the": ("swipe", -18), "lock": ("swipe", -18), "hook": ("swipe", -17), "quote": ("whip", -21),
            "punch": ("impact", -21), "note": ("tick", -15), "benefit": ("pop", -16), "product": ("sparkle", -17)}


VAI_PRIO = {"tram": 1, "chuyen": 1, "cao_trao": 1, "chu": 2, "hoi": 2, "san_pham": 3, "gia": 3, "cta": 3, "ket": 3}
GIA_RE = re.compile(r"\d{1,3}(?:[.,]\d{3})*\s?(?:k|nghìn|ngàn|đ|đồng|triệu|tr|tỷ)\b|%|giảm|sale|freeship|voucher|ưu đãi",
                    re.I)


def sfx_file(n):
    """File tiếng tự tạo: kho tiếng của máy (may.json "sfx") trước, thiếu thì sfx/ của skill."""
    f = SFX_DIR / f"{n}.wav"
    return f if f.exists() else ROOT / "sfx" / f"{n}.wav"


def sfx_events(cfg, broll, calls, cta_a, total, nhans=(), trans=None, chon=None):
    """Mỗi điểm nhấn 1 tiếng theo VAI (chữ / cảnh trám / chuyển cảnh / sản phẩm / giá / CTA / câu hỏi / cao trào / kết),
    cách nhau >= 0.35s (trùng thì giữ vai ưu tiên hơn). Tiếng chọn bằng kho_tieng.BoChon: xoay vòng theo phong cách,
    không lặp liền nhau. Trả [(giây, tên tiếng tự tạo, dB, vai)] — tiếng thư viện CapCut (nếu có) thay ở bước CapCut."""
    if cfg.get("sfx") is False or not (SFX_DIR.exists() or (ROOT / "sfx").exists()):
        return []
    # NHIỀU + NGHE RÕ (người dùng 14/11): mọi chữ nhấn có tiếng, mỗi lần vào cảnh trám có tiếng, chuyển cảnh có tiếng.
    # Mức (dB so với file gốc ~ -3 dBFS) đặt để nghe rõ trên nền giọng -14 LUFS nhưng không át lời.
    L = float(cfg.get("sfx_db", 0))   # chỉnh chung: +3 = to hơn, -3 = nhỏ hơn
    trans = trans or {}
    ev = []   # (t, vai, gợi ý tiếng, dB, của chữ?)
    for i, b in enumerate(sorted(broll, key=lambda x: x["start"])):
        if (b["ref"], "vao") in trans:
            ev.append((b["start"], "chuyen", tieng_chuyen(trans[(b["ref"], "vao")]), -9 + L, False))
        elif b["start"] > 0.3:
            ev.append((b["start"], "tram", b.get("sfx_vao"), -11 + L, False))
        if (b["ref"], "ra") in trans:
            ev.append((b["start"] + b["duration"], "chuyen", tieng_chuyen(trans[(b["ref"], "ra")]), -10 + L, False))
    for n in nhans:   # tiếng dồn lên ngay trước khi gọi tên sản phẩm -> tạo cao trào
        if n.get("san_pham") and n["a"] > 1.5:
            ev.append((n["a"] - 1.0, "cao_trao", None, -14 + L, False))
    basic = str(cfg.get("goi", "")).lower() == "basic"
    if basic:   # GÓI BASIC: "3 text + 3 sound đầu video" -> tiếng chỉ đi kèm thumbnail + các chữ nhấn
        ev = [(0.05, "chuyen", "whoosh", -9 + L, True)]
    elif cfg.get("cta_src") and cfg.get("cta", True) is not False:
        ev += [(cta_a, "cta", "ding", -7 + L, True), (cta_a + 0.45, "gia", "cash", -12 + L, False)]
    cuoi = [] if basic else [n for n in nhans if tc.kieu(n) == "chinh"][-1:]   # câu chốt cảm xúc cuối
    # TIẾNG KHỚP HIỆU ỨNG CHỮ (góp ý 16/11): đặt đúng lúc chữ bật lên, loại tiếng hợp kiểu hiện; luôn thắng tiếng chuyển cảnh
    for n in nhans:
        _, ten1, lech = tc.anim(n)
        t = n["a"] + lech
        chu_ = " ".join(n["chu"])
        if n.get("sfx"):
            ev.append((t, "chu", "=" + n["sfx"], -8 + L, True))
        elif n in cuoi:
            ev.append((t, "ket", None, -8 + L, True))
        elif n.get("san_pham"):
            ev.append((t, "san_pham", None, -7 + L, True))
        elif GIA_RE.search(chu_):
            ev.append((t, "gia", None, -8 + L, True))
        elif any(c.rstrip().endswith("?") for c in n["chu"]):
            ev.append((t, "hoi", None, -9 + L, True))
        else:
            ev.append((t, "chu", ten1, (-7 if tc.kieu(n) == "chinh" else -9) + L, True))
    keep = []
    for x in sorted(ev, key=lambda e: e[0]):
        if keep and x[0] - keep[-1][0] < 0.35:
            if (x[4], VAI_PRIO[x[1]]) > (keep[-1][4], VAI_PRIO[keep[-1][1]]):   # tiếng của chữ thắng tiếng chuyển cảnh
                keep[-1] = x
            continue
        keep.append(x)
    # THƯA TIẾNG CHUYỂN CẢNH (góp ý O-5 20/11: "âm thanh chuyển cảnh lặp đi lặp lại nhiều quá"): KHÔNG gắn tiếng cho mọi lần
    # vào / ra cảnh trám — chỉ chỗ có chuyển cảnh thật (đổi bối cảnh rõ), tối đa ~1 tiếng / "sfx_chuyen_cach" giây (mặc định 9).
    # Vào cảnh trám không có chuyển cảnh: im (bật lại: "sfx_vao_tram": true).
    cach_ = float(cfg.get("sfx_chuyen_cach", 9.0))
    moc, keep2 = -99.0, []
    for x in keep:
        if x[1] in ("tram", "chuyen"):
            if (x[1] == "tram" and not cfg.get("sfx_vao_tram", False)) or x[0] - moc < cach_:
                continue
            moc = x[0]
        keep2.append(x)
    keep = keep2
    if chon is None:
        import kho_tieng
        chon = kho_tieng.BoChon(cfg.get("phong_cach") or "nang_dong", sfx_dir=SFX_DIR, thu_vien=False,
                                da_dang=cfg.get("da_dang", "thuong"))
    out = []
    for t, vai, goi_y, db, _ in keep:
        if t >= total - 0.3:
            continue
        if goi_y and goi_y.startswith("="):            # tiếng người dùng ghi riêng cho 1 chữ: giữ đúng, không thay
            out.append((fr(t), goi_y[1:], db, "co_dinh"))
            continue
        out.append((fr(t), chon.tu_tao_cho(vai, goi_y), db, vai))
    return out


# Chuyển cảnh CÓ SẴN của CapCut, chia theo ngữ cảnh (slug đều có trong `capcut enums --transitions`).
# Mặc định cũ (khi kho/cong-thuc.json không có mục "chuyen" cho phong cách đang dùng):
CHUYEN = {
    "vao": ["pull-in", "slide", "wipe-left", "inhale", "wipe-right"],          # người nói -> cảnh trám
    "san_pham": ["light-sweep-ii", "camera-glow", "dissolve"],                 # -> cảnh cận sản phẩm (không chớp trắng)
    "doi": ["slide", "wipe-up", "mix", "dissolve"],                             # cảnh trám -> cảnh trám khác
    "ra": ["pull-out", "dissolve", "blur", "camera-glow"],                      # cảnh trám -> người nói
}
# tiếng gợi ý đi kèm kiểu chuyển cảnh (kho_tieng xoay vòng trong cùng họ)
TIENG_CHUYEN = {"pull-in": "whoosh", "pull-out": "whoosh", "dissolve": "whoosh", "blur": "whoosh",
                "slide": "swipe", "wipe-left": "swipe", "wipe-right": "swipe", "wipe-up": "swipe",
                "inhale": "whip", "mix": "whip", "white-flash": "shutter", "flash": "shutter",
                "camera-glow": "sparkle", "light-sweep-ii": "sparkle", "twinkle-zoom": "sparkle"}
_TIENG_CHUYEN_RE = [(r"glitch|blocks|lines|slice|recorder|screening", "shutter"), (r"twinkle|light|glow|beam|highlight|like",
                     "sparkle"), (r"slide|wipe|split|wave|dots|page", "swipe"), (r"stretch|squeeze|inhale|radial", "whip")]
# người nói -> cảnh trám nằm ở 2 track khác nhau (CapCut chỉ đặt chuyển cảnh giữa 2 đoạn CÙNG track) -> vào / ra cảnh trám
# dùng HOẠT ẢNH VÀO / RA của CapCut có cảm giác giống kiểu chuyển cảnh đã chọn
_ANIM_VAO = [(r"pull|zoom|inhale|stretch|squeeze|radial|twinkle", "zoom-in"), (r"slide|wipe|woosh|split|lines|wave|dots",
              "slide-left"), (r"glitch|blocks", "mini-zoom"), (r".", "fade-in")]
_ANIM_RA = [(r"pull|zoom|radial", "zoom-out"), (r"slide|wipe", "slide-down"), (r".", "fade-out")]


def tieng_chuyen(slug):
    if slug in TIENG_CHUYEN:
        return TIENG_CHUYEN[slug]
    return next((n for r, n in _TIENG_CHUYEN_RE if re.search(r, slug)), "whoosh")


def anim_cho_chuyen(slug, k):
    return next(n for r, n in (_ANIM_VAO if k == "vao" else _ANIM_RA) if re.search(r, slug))


def bo_chuyen(cfg):
    """Danh sách kiểu theo PHONG CÁCH (kho/cong-thuc.json "chuyen"); da_dang "cao" -> thêm nhóm "cao" (whip, glitch, zoom…)."""
    pc = cfg.get("phong_cach") or TH.get("phong_cach") or "nang_dong"
    try:
        ct = json.loads((ROOT / "kho" / "cong-thuc.json").read_text(encoding="utf-8")).get("chuyen", {})
    except Exception:
        ct = {}
    g = ct.get(pc) or {}
    out = {}
    for nhom, mac_dinh in CHUYEN.items():
        ds = list(g.get(nhom) or mac_dinh)
        if cfg.get("da_dang") == "cao":
            ds += [x for x in g.get("cao", {}).get(nhom, []) if x not in ds]
        out[nhom] = cfg.get("chuyen_" + nhom) or ds
    return out


def chon_chuyen_canh(cfg, broll, total, hat=""):
    """Chuyển cảnh ĐA DẠNG ở chỗ ĐỔI BỐI CẢNH: vào/ra cảnh trám và giữa 2 cảnh trám khác cảnh quay — mỗi chỗ 1 kiểu hợp
    ngữ cảnh + phong cách ngành, xoay vòng (bắt đầu lệch theo dự án), không lặp kiểu liền nhau. Không đặt khi 1 phía
    < 1,5s, cách nhau >= chuyen_cach, tối đa chuyen_toi_da.
    Cảnh trám có "san_pham": true trong cấu hình (cận sản phẩm) -> kiểu ánh sáng (vệt sáng / lấp lánh).
    Trả {(ref cảnh trám, 'vao'|'ra'): slug}."""
    if cfg.get("chuyen_canh") is False:
        return {}
    toi_da, cach = int(cfg.get("chuyen_toi_da", 2)), float(cfg.get("chuyen_cach", 8.0))
    bo = bo_chuyen(cfg)
    sp_refs = {f"b{i}" for i, x in enumerate(cfg.get("broll", [])) if x.get("san_pham")}
    bs = sorted(broll, key=lambda b: b["start"])
    ev = []   # (thời điểm, ref, vao|ra, nhóm kiểu, độ dài 2 phía)
    for i, b in enumerate(bs):
        prev = bs[i - 1] if i and abs(bs[i - 1]["start"] + bs[i - 1]["duration"] - b["start"]) < 0.05 else None
        nhom = "san_pham" if b["ref"] in sp_refs else "vao"
        if prev is None:   # vào từ người nói
            ev.append((b["start"], b["ref"], "vao", nhom, min(b["duration"], 99.0 if b["start"] > 1.5 else b["start"])))
        elif (os.path.basename(prev["path"]) != os.path.basename(b["path"])
              or abs((prev["from"] + prev["duration"]) - b["from"]) > 3.0):   # khác clip / khác cảnh quay
            ev.append((b["start"], b["ref"], "vao", "san_pham" if nhom == "san_pham" else "doi",
                       min(b["duration"], prev["duration"])))
        nxt = bs[i + 1] if i + 1 < len(bs) and abs(b["start"] + b["duration"] - bs[i + 1]["start"]) < 0.05 else None
        end = b["start"] + b["duration"]
        if nxt is None and end < total - 1.5:   # ra lại người nói
            ev.append((end, b["ref"], "ra", "ra", min(b["duration"], total - end)))
    lech = int(hashlib.md5(hat.encode()).hexdigest(), 16) % 7 if hat else 0   # mỗi dự án bắt đầu ở 1 kiểu khác
    chosen, last, dem = {}, -99.0, {}
    for t, ref, k, nhom, d in sorted(ev):
        if d < 1.5 or t - last < cach or len(chosen) >= toi_da or t < 0.5:
            continue
        pool = bo[nhom]
        i0 = dem.get(nhom, 0) + lech
        slug = pool[i0 % len(pool)]
        if slug in list(chosen.values())[-2:] and len(pool) > 1:      # không lặp kiểu vừa dùng
            slug = next((pool[(i0 + j) % len(pool)] for j in range(1, len(pool))
                         if pool[(i0 + j) % len(pool)] not in list(chosen.values())[-2:]), slug)
        dem[nhom] = dem.get(nhom, 0) + 1
        chosen[(ref, k)] = slug
        last = t
    return chosen


def clip_dur(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 1e9


def wav_dur(path):
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


# ---------------------------------------------------------------- kiểm tra (techpro-video-master + bộ dùng chung)
def _tok(t):
    return re.findall(r"\w+(?:[,.]\d+)?", re.sub(r"<[^>]+>", "", t).lower())


def nghe_lai(mp4, want_text, cam):
    """Như kiem_loi.py của techpro (Claude không nghe được): Whisper trên máy nghe lại MP4, so với phụ đề, quét từ cấm.
    Whisper có thể nghe nhầm: chỗ khác là chỗ cần nghe lại, không phải bằng chứng lỗi."""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return ["## Nghe lại lời: BỎ QUA (thiếu faster-whisper)", ""]
    import difflib
    model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    import chuan_bi as cb
    segs, _ = model.transcribe(cb.doc_am(mp4), language="vi", vad_filter=True,
                               initial_prompt=TH.get("tu_vung", "") + ".")
    heard = " ".join(s.text for s in segs)
    a, b = _tok(want_text), _tok(heard)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    diffs = [(" ".join(a[i1:i2]), " ".join(b[j1:j2])) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
    big = [d for d in diffs if max(len(d[0].split()), len(d[1].split())) >= 3]
    hits = [c.strip() for c in cam.split(",") if c.strip() and re.search(rf"(?<!\w){re.escape(c.strip().lower())}(?!\w)",
                                                                           (heard + " " + want_text).lower())]
    ok = sm.ratio() >= 0.85 and not big and not hits
    mark = "ĐẠT" if ok else "XEM LẠI"
    lines = [f"## Nghe lại lời + từ cấm: {mark}", "",
             f"- Khớp phụ đề: {sm.ratio() * 100:.0f}% ({len(diffs)} chỗ khác nhỏ, {len(big)} chỗ khác ≥ 3 từ)",
             f"- Từ cấm: {', '.join(hits) if hits else 'không có'}"]
    lines += [f"  - phụ đề \"{x}\" / nghe \"{y}\"" for x, y in big[:15]]
    lines += ["", "<details><summary>Lời nghe được</summary>", "", heard.strip(), "", "</details>", ""]
    print(f"\n== Nghe lại lời + từ cấm: {mark}\n" + "\n".join(lines[2:4] + lines[4:4 + min(15, len(big))]))
    return lines


def qa(P, cfg, cues, calls):
    out = cfg["out_mp4"]
    txt = P / "_loi.txt"
    txt.write_text(" ".join(re.sub(r"<[^>]+>", "", c["text"]) for c in cues), encoding="utf-8")
    screen = P / "_chu-man-hinh.txt"
    screen.write_text("\n".join(cfg["thumb"] + [re.sub(r"<[^>]+>", "", l) for c in calls for l in c["lines"]]
                                + [re.sub(r"<[^>]+>", "", l) for n in cfg.get("nhan", []) for l in n["chu"]]),
                      encoding="utf-8")
    nqc = cfg.get("nhan_qc", {})
    if nqc is not False:
        with open(screen, "a", encoding="utf-8") as fh:
            fh.write("\n" + (nqc or {}).get("tag", "Hợp tác quảng cáo") + "\n"
                     + (nqc or {}).get("phaply", TH["nhan_qc"]["phaply"]))
    rep = ["# Kiểm tra " + cfg["draft"], ""]

    def step(title, cmd):
        r = run(cmd)
        body = (r.stdout + ("\n" + r.stderr if r.returncode and r.stderr else "")).strip()
        mark = "ĐẠT" if r.returncode == 0 else "XEM LẠI"
        print(f"\n== {title}: {mark}\n{body[-1500:]}")
        rep.extend([f"## {title}: {mark}", "", "```", body[-4000:], "```", ""])

    if not ENG_PY.exists():
        print("! Không có bộ dùng chung bo-skill-video (may.json: eng) -> chỉ kiểm được bằng mắt")
        return
    py = [str(ENG_PY), "-X", "utf8"]
    step("Bản ra (khung, âm lượng, đoạn đen)", py + [str(ENG / "scripts/kiem_ban_ra.py"), out])
    rep.extend(nghe_lai(out, txt.read_text(encoding="utf-8"), cfg.get("cam", CAM)))
    step("An toàn nội dung", py + [str(ENG / "scripts/an_toan.py"), "--van", str(txt), str(screen)])
    if not (P / "nganh.json").exists():
        run(py + [str(ENG / "scripts/nganh.py"), str(P), "--ap", cfg.get("nganh", TH.get("nganh", "my-pham"))])
    nj = json.loads((P / "nganh.json").read_text(encoding="utf-8"))
    md = TH.get("nganh_tra_loi", {})
    for sec in ("co", "gia_tri"):
        for k, v in md.get(sec, {}).items():
            if nj.setdefault(sec, {}).get(k) in (None, ""):
                nj[sec][k] = v
    (P / "nganh.json").write_text(json.dumps(nj, ensure_ascii=False, indent=2), encoding="utf-8")
    if not (P / "facts.json").exists() and TH.get("facts"):
        (P / "facts.json").write_text(json.dumps(TH["facts"], ensure_ascii=False, indent=2), encoding="utf-8")
    step("Luật quảng cáo ngành", py + [str(ENG / "scripts/nganh.py"), str(P), "--kiem", "--van", f"{txt},{screen}"])
    (P / "kiem-tra.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"\nBáo cáo: {P / 'kiem-tra.md'}")


def base_video(aroll_v, pieces, broll, punch, with_audio=True, trans=None):
    """inputs + filter cho hình nền (A-roll cắt + phóng khung + cảnh trám). Nhãn ra: [base] (+ [voice])."""
    inputs = ["-i", str(aroll_v)]
    for b in broll:
        inputs += ["-ss", f"{b['from']:.3f}", "-t", f"{b['duration'] + 0.2:.3f}", "-i", b["path"]]
    n = len(pieces)
    f = [f"[0:v]split={n}" + "".join(f"[v{i}]" for i in range(n))]
    if with_audio:
        f.append(f"[0:a]asplit={n}" + "".join(f"[a{i}]" for i in range(n)))
    for i, p in enumerate(pieces):
        zoom = (f",scale=trunc(iw*{punch}/2)*2:trunc(ih*{punch}/2)*2,crop={W}:{H}" if i % 2 and punch > 1.001 else "")
        f.append(f"[v{i}]trim={p['s']}:{p['e']},setpts=PTS-STARTPTS{zoom},setsar=1[vt{i}]")
        if with_audio:
            f.append(f"[a{i}]atrim={p['s']}:{p['e']},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,"
                     f"afade=t=out:st={p['e'] - p['s'] - 0.02:.3f}:d=0.02[at{i}]")
    if with_audio:
        f.append("".join(f"[vt{i}][at{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[b0][voice]")
    else:
        f.append("".join(f"[vt{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[b0]")
    last = "b0"
    for j, b in enumerate(broll):
        fd = min(0.3, b["duration"] / 4)
        fx = ""
        if trans and (b["ref"], "vao") in trans:
            fx += f",fade=in:st=0:d={fd}:alpha=1"
        if trans and (b["ref"], "ra") in trans:
            fx += f",fade=out:st={b['duration'] - fd:.3f}:d={fd}:alpha=1"
        f.append(f"[{1 + j}:v]fps={FPS},format=yuva420p{fx},setpts=PTS-STARTPTS+{b['start']}/TB[br{j}]")
        f.append(f"[{last}][br{j}]overlay=eof_action=pass:enable='between(t,{b['start']},{b['start'] + b['duration'] - 0.001})'[x{j}]")
        last = f"x{j}"
    f.append(f"[{last}]null[base]")
    return inputs, f


def LOC_TAP_AM(cfg):
    """V2 (góp ý 17/11): KHÔNG tự lọc âm — khử nhiễu / cắt tần số làm MÉO GIỌNG. Giữ nguyên giọng gốc; muốn giảm ồn thì
    dùng "Giảm tiếng ồn" của CapCut trên đoạn giọng. Chỉ bật lại khi người dùng yêu cầu rõ: "loc_tap_am": 1–3."""
    k = int(cfg.get("loc_tap_am", 0))
    if k <= 0:
        return ""
    nr = {1: 8, 2: 12, 3: 18}.get(k, 12)
    return f"highpass=f=80,lowpass=f=14000,afftdn=nr={nr}:nf=-40:tn=1,"


def _scale_expr(kf):
    """[(t, v)...] -> biểu thức ffmpeg tuyến tính từng đoạn theo t."""
    e = str(kf[-1][1])
    for (t0, v0), (t1, v1) in reversed(list(zip(kf, kf[1:]))):
        e = f"if(lt(t,{t1}),{v0}+({v1 - v0})*(t-{t0})/{t1 - t0},{e})"
    return e


# ---------------------------------------------------------------- main
def main():
    P = Path(sys.argv[1]).resolve()
    cfg = json.loads((P / "cau-hinh.json").read_text(encoding="utf-8"))
    # BỘ KIỂU CHỮ (kho mẫu chữ TikTok, 19/11/2026): "bo_chu" trong cau-hinh.json / hồ sơ thương hiệu;
    # "tu_dong" = chọn theo ngành (scripts/mau_chu.py). Mặc định "thuong_hieu" (giữ đúng style brief cũ).
    global CSS
    # CÔNG THỨC DỰNG (kho/cong-thuc.json): ngành x loại video x yêu cầu -> điền các thông số còn trống (không ghi đè)
    import cong_thuc
    cfg, _ = cong_thuc.ap(cfg, TH, P)
    # MƯỢN NHỊP CẮT CỦA MIKE (20/11/2026): "mike_cat": "<thư mục dự án Mike của CÙNG clip A-roll>" -> dùng các đoạn giữ Mike
    # đã chọn (edl.json: lần nói sạch cuối, bỏ khoảng lặng > 0,45s, mỗi shot >= 1,5s) thay cho keeps. Chỉ đọc edl.json.
    if cfg.get("mike_cat"):
        edl_f = Path(cfg["mike_cat"]) / "edl.json"
        if edl_f.exists():
            edl = json.loads(edl_f.read_text(encoding="utf-8"))
            clip0 = edl[0].get("clip") if edl else None
            cfg["keeps"] = [[e["in"], e["out"]] for e in edl if e.get("clip") == clip0]
            cfg["cat_tieng"] = []
            print(f"Nhịp cắt theo Mike: {len(cfg['keeps'])} đoạn giữ từ {edl_f}")
        else:
            print(f"! mike_cat: không thấy {edl_f} -> giữ keeps của cấu hình")
    bo_chu = cfg.get("bo_chu") or TH.get("bo_chu") or "thuong_hieu"
    if bo_chu == "kho_team":          # chữ theo kho team (đã gắn "kho" theo vai, MP4 xem thử vẽ theo kho); chữ khác theo kiểu thương hiệu
        bo_chu = "thuong_hieu"
    if bo_chu == "tu_dong":
        import mau_chu
        bo_chu = mau_chu.bo_cho_nganh(cfg.get("nganh") or TH.get("nganh"))
    bo_chu = tc.dat_bo(bo_chu)
    CSS = CSS_GOC + tc.CSS
    print(f"Bộ kiểu chữ: {bo_chu} — {tc.BO_CHU[bo_chu]['ten']}")
    # MẶC ĐỊNH chỉ làm PROJECT CAPCUT (nhân sự tự xuất trong CapCut — góp ý 16/11). MP4 xem thử + kiểm bản ra:
    # thêm --mp4 --qa, hoặc "xuat_mp4": true trong cau-hinh.json.
    flags = set(sys.argv[2:]) or ({"--pngs", "--mp4", "--capcut", "--qa"} if cfg.get("xuat_mp4") else {"--pngs", "--capcut"})
    raw = P / "raw"
    aroll = raw / cfg["aroll"]
    # GÓI BASIC (bảng giá TechPro 2026): 1 bối cảnh, 1 shot -> KHÔNG cảnh trám, KHÔNG hiệu ứng cảnh;
    # hậu kỳ "3 text + 3 sound đầu video" = thumbnail + 2 chữ nhấn trong ~15s đầu, mỗi chữ 1 tiếng.
    basic = str(cfg.get("goi", "")).lower() == "basic"
    # V4: KHO HIỆU ỨNG CAPCUT — phong cách: nang_dong | sang_trong | de_thuong | cong_nghe | co_dien (hồ sơ thương hiệu
    # "phong_cach" hoặc cau-hinh); được dùng hiệu ứng Pro nếu máy có CapCut Pro (may.json "capcut_pro", mặc định có)
    import kho_capcut as kc
    pc = cfg.get("phong_cach") or TH.get("phong_cach") or "nang_dong"
    pro = bool(cfg.get("capcut_pro", MAY.get("capcut_pro", True)))
    hat = P.name
    if basic:
        cfg["broll"], cfg["hieu_ung_capcut"], cfg["callouts"] = [], [], []
        print("Gói BASIC: không cảnh trám / hiệu ứng cảnh; 3 chữ (thumbnail + 2 chữ nhấn) + 3 tiếng nhấn đầu video")
    segs = json.loads((P / "transcript.json").read_text(encoding="utf-8"))
    sil = silences(aroll)
    env = envelope(aroll)
    words = [w for sg in segs for w in sg.get("words", [])]
    # Mốc từ ĐÃ SIẾT theo tiếng thật (cat_sach.py) -> cắt đúng như bản đã tự nghe lại (--kiem). Mốc Whisper thô hay
    # kéo đầu từ lùi vào quãng im -> chặn mất vết cắt -> còn khoảng trống ~1s (góp ý 18/11 O-5).
    sach = P / "cat" / "transcript-sach.json"
    if sach.exists() and sach.stat().st_mtime >= (P / "transcript.json").stat().st_mtime:
        try:
            words = [w for sg in json.loads(sach.read_text(encoding="utf-8")) for w in sg.get("words", [])] or words
        except Exception:
            pass
    pieces, total = build_pieces(cfg["keeps"], sil, words=words, env=env, dai_clip=clip_dur(aroll),
                                 cam=cfg.get("cat_tieng", []),
                                 tho=(float(cfg["cho_giua_cau"]) / 2 if cfg.get("cho_giua_cau") else None))
    m = mapper(pieces)
    # ĐIỂM NHẤN MIKE — bước 1: xuất edl cho Mike đúng các đoạn giữ của video này trong các khoảng giây nguồn đã chọn
    #   dung.py projects/<du-an> --mike-edl "3.2-8.5,40-46" [--mike-clip c1]  -> projects/<du-an>/mike-edl.json
    if "--mike-edl" in sys.argv:
        k = sys.argv.index("--mike-edl")
        spans = [tuple(float(x) for x in sp.split("-")) for sp in sys.argv[k + 1].split(",")]
        clip_id = sys.argv[sys.argv.index("--mike-clip") + 1] if "--mike-clip" in sys.argv else "c1"
        edl = []
        for p_ in pieces:
            for a0, b0 in spans:
                lo, hi = max(p_["s"], a0), min(p_["e"], b0)
                if hi - lo > 0.3:
                    edl.append({"id": f"d{len(edl)}", "clip": clip_id, "in": round(lo, 3), "out": round(hi, 3),
                                "zoom": 1.0, "cx": 0.5, "cy": 0.45})
        (P / "mike-edl.json").write_text(json.dumps(edl, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"mike-edl.json: {len(edl)} đoạn, {sum(e['out'] - e['in'] for e in edl):.1f}s -> chép làm edl.json của dự án Mike")
        return
    cues = make_cues(segs, cfg, pieces, m)
    total = fr(total)
    # V2 (góp ý 17/11): KHÔNG chỉnh màu, KHÔNG làm mịn da / làm đẹp — giữ nguyên hình gốc. Chỉnh màu (nếu cần) làm
    # trực tiếp trong CapCut (Điều chỉnh / Bộ lọc) để người dựng tự kiểm soát. Khoá "grade" cũ trong cấu hình bị bỏ qua.
    if cfg.get("grade"):
        print("! V2: bỏ qua \"grade\" trong cấu hình — không chỉnh màu tự động, chỉnh màu trong CapCut")
    if "--xem-mau" in flags:
        print("V2 không chỉnh màu tự động — chỉnh màu trực tiếp trong CapCut.")
        return
    aroll_v = aroll
    punch = float(cfg.get("punch", 1.08))
    print(f"A-roll: {len(pieces)} đoạn, tổng {total:.2f}s")

    # cảnh trám: (1) đủ dài để người xem kịp thấy (>= tram_min, mặc định 2,5s); (2) "from" = "auto" (mặc định)
    # -> tự chọn ĐOẠN HAY trong cả clip (nét, có người/sản phẩm, chuyển động vừa) — tram.py
    import tram
    # V2 (góp ý 17/11): cảnh trám ÍT mà CHẤT — đủ dài (>= 4s), có nội dung rõ, khớp lời / kịch bản; không rải nhiều cảnh
    # ngắn vô nghĩa. Tối đa ~1 cảnh trám / 9s video ("tram_toi_da"), điểm nội dung thấp thì bỏ ("tram_diem_min").
    tmin = float(cfg.get("tram_min", 4.0))
    toi_da = int(cfg.get("tram_toi_da", max(2, round(total / float(cfg.get("tram_chia", 9))))))
    diem_min = float(cfg.get("tram_diem_min", 0.4))
    spans = []
    for i, b in enumerate(cfg["broll"]):
        oa, ob = fr(m(b["src"][0], "start")), fr(m(b["src"][1], "end"))
        spans.append([i, b, oa, ob])
    spans.sort(key=lambda x: x[2])
    for k_, sp in enumerate(spans):
        lim = spans[k_ + 1][2] if k_ + 1 < len(spans) else total
        if sp[3] - sp[2] < tmin:
            sp[3] = fr(min(lim, sp[2] + tmin, total))
    broll, used, chon = [], {}, []
    for i, b, oa, ob in spans:
        if ob - oa < min(2.0, tmin):
            print(f"! Bỏ cảnh trám {b['file']} @{oa:.1f}s: chỉ còn {ob - oa:.1f}s (quá ngắn, không kịp thấy nội dung)")
            continue
        frm, an = b.get("from", "auto"), None
        if frm == "auto" or b.get("cham_diem", True):
            an = tram.analyze(raw / b["file"], raw / "_tram")
        scv = 1.0
        if frm == "auto":
            if not b.get("tim_trong"):
                print(f"! Cảnh trám {b['file']} @{oa:.1f}s chưa có \"tim_trong\" — phải xem bảng ảnh clip và khoanh đúng "
                      "đoạn khớp lời/kịch bản (đang tự chọn theo THỨ TỰ QUAY sau cảnh trước của cùng clip)")
            # XẾP THEO KỊCH BẢN: clip trám thường quay theo thứ tự kịch bản -> lần dùng sau của cùng clip lấy đoạn SAU lần trước
            sau = max((e for _, e in used.get(b["file"], [])), default=None) if not b.get("tim_trong") else None
            frm, scv = tram.pick(an, ob - oa + 0.3, used.get(b["file"], []), b.get("tim_trong"), b.get("tranh", []), sau=sau)
            if frm is None:
                print(f"! Không tìm được đoạn hay đủ {ob - oa:.1f}s trong {b['file']} -> bỏ cảnh trám này")
                continue
            if scv < diem_min:
                print(f"! Bỏ cảnh trám {b['file']} @{oa:.1f}s: nội dung chưa rõ (điểm {scv:.2f} < {diem_min}) — giữ hình người nói")
                continue
        used.setdefault(b["file"], []).append((frm, frm + ob - oa + 0.3))
        if an is not None:
            loi = " ".join(w["w"].strip() for w in words if b["src"][0] - 0.1 <= w["s"] <= b["src"][1])
            chon.append((f"{b['file']} {frm:.1f}-{frm + ob - oa:.1f}s -> ra {oa:.1f}s", an, frm, ob - oa, loi))
        bp = raw / b["file"]   # V2: không chỉnh màu cảnh trám
        broll.append({"path": str(bp), "start": oa, "duration": fr(ob - oa), "from": frm, "ref": f"b{i}", "diem": scv})
    if len(broll) > toi_da:   # quá nhiều cảnh trám -> giữ những cảnh điểm cao + dài nhất, theo đúng thứ tự thời gian
        giu = sorted(broll, key=lambda x: -(x["diem"] * x["duration"]))[:toi_da]
        bo_ = [x for x in broll if x not in giu]
        print(f"Bớt cảnh trám ({len(broll)} -> {toi_da}, tối đa ~1 cảnh / 9s): bỏ", ", ".join(f"@{x['start']:.1f}s" for x in bo_))
        broll = [x for x in broll if x in giu]
        chon = [c for c in chon if any(c[0].endswith(f"ra {x['start']:.1f}s") for x in broll)]
    if chon:
        tram.sheet(chon, P / "bang-tram.jpg")
        print("Cảnh trám:", "; ".join(c[0] for c in chon), f"· xem {P / 'bang-tram.jpg'}")
    for b in broll:   # cảnh trám bắt đầu sát sau 1 điểm cắt (< 0,6s) -> kéo lùi về điểm cắt, không để chớp hình người nói
        for p in pieces:
            d = b["start"] - p["o"]
            if 0 < d < 0.6 and b["from"] - d >= 0:
                b["from"] = round(b["from"] - d, 3)
                b["duration"] = fr(b["duration"] + d)
                b["start"] = fr(p["o"])
                break
    broll.sort(key=lambda b: b["start"])
    for x, y in zip(broll, broll[1:]):   # khe < 0,6s giữa 2 cảnh trám -> lấp; chồng nhau -> cắt bớt cảnh trước
        hole = y["start"] - (x["start"] + x["duration"])
        if hole < 1.0:   # khe người nói < 1s giữa 2 cảnh trám chỉ là chớp hình -> lấp bằng cảnh trám trước / sau
            if hole <= 0 or x["from"] + y["start"] - x["start"] <= clip_dur(x["path"]) - 0.2:
                x["duration"] = fr(y["start"] - x["start"])
            elif y["from"] - hole >= 0:
                y["from"] = round(y["from"] - hole, 3)
                y["duration"] = fr(y["duration"] + hole)
                y["start"] = fr(x["start"] + x["duration"])
    if broll and 0 < broll[0]["start"] < 0.6:   # đoạn người nói đầu video quá ngắn -> cảnh trám bắt đầu từ 0
        broll[0]["from"] = max(0.0, broll[0]["from"] - broll[0]["start"])
        broll[0]["duration"] = fr(broll[0]["duration"] + broll[0]["start"])
        broll[0]["start"] = 0.0
    mike_ds = mike_diem_nhan(cfg, m, fr, P)
    # CẢNH TRÁM ƯU TIÊN HƠN ĐIỂM NHẤN MIKE (góp ý 19/11 "chưa lấy đủ cảnh trám phù hợp nội dung"): chỗ có cảnh trám khớp lời
    # thì cắt đoạn Mike ra, cảnh trám hiện; phần Mike còn lại giữ nguyên (đúng khung, đúng giây)
    if mike_ds and broll:
        con = []
        for x in mike_ds:
            pcs = [(x["start"], x["start"] + x["duration"])]
            for b_ in broll:
                b0, b1 = b_["start"], b_["start"] + b_["duration"]
                pcs = [q for a0, a1 in pcs for q in ((a0, min(a1, b0)), (max(a0, b1), a1)) if q[1] - q[0] > 0.05]
            for a0, a1 in pcs:
                if a1 - a0 >= 0.5:
                    con.append(dict(x, start=fr(a0), duration=fr(a1 - a0), from_=0,
                                    **{"from": round(x["from"] + a0 - x["start"], 4), "ref": f"{x['ref']}_{len(con)}"}))
        bot = sum(x["duration"] for x in mike_ds) - sum(x["duration"] for x in con)
        if bot > 0.05:
            print(f"Cảnh trám phủ lên {bot:.1f}s của điểm nhấn Mike (cảnh trám ưu tiên); Mike còn {len(con)} đoạn")
        mike_ds = [{k: v for k, v in x.items() if k != "from_"} for x in con]
    if mike_ds and mike_ds[0]["start"] < 0.05 and cfg.get("thumb_dur", 2) > 0.1:
        # câu mở đầu đã do Mike làm (có chữ riêng) -> thumbnail chỉ còn ở khung đầu (ảnh bìa), không chồng chữ Mike
        cfg["thumb_dur"] = 0.04
        print("Điểm nhấn Mike ở câu mở đầu -> thumbnail chỉ ở khung đầu (ảnh bìa)")
    trans = chon_chuyen_canh(cfg, broll, total, hat=P.name)
    calls = []
    for i, c in enumerate(cfg["callouts"]):
        oa, ob = fr(m(c["src"][0], "start")), fr(m(c["src"][1], "end"))
        calls.append({"name": f"call{i}", "lines": c["lines"], "a": oa, "b": ob})
    co_cta = bool(cfg.get("cta_src")) and cfg.get("cta", True) is not False
    cta_a = fr(m(cfg["cta_src"][0], "start")) if co_cta else fr(max(0.0, total - 5.0))   # không nút giỏ hàng: pháp lý 5s cuối
    phu_de = bool(cfg.get("phu_de", False))  # mặc định KHÔNG chạy phụ đề suốt video: chỉ chữ nhấn
    nhans = []
    for i, n in enumerate(cfg.get("nhan", [])):
        if "src" in n:
            a_src, seg_end, w_end = n["src"][0], n["src"][1], n["src"][1]
        else:
            a_src, seg_end, w_end = find_phrase(segs, n["khi"], n.get("sau", 0))
            # ĐỒNG BỘ GIỌNG (góp ý 16/11 "chữ chưa xuất hiện đồng bộ với voice"): mốc Whisper lệch ±0,1–0,3s -> lấy
            # đúng lúc tiếng bắt đầu, hiện sớm 0,08s để hiệu ứng bật lên vừa chạm chữ đầu
            a_src = onset(env, a_src) - float(cfg.get("chu_som", 0.08))
        oa = fr(m(a_src, "start"))
        if "den" in n:  # giữ tới khi nói cụm này (hoặc giây nguồn)
            e_src = n["den"] if isinstance(n["den"], (int, float)) else find_phrase(segs, n["den"], a_src)[0]
            ob = fr(m(e_src, "end"))
        else:
            ob = fr(min(m(seg_end, "end") + 0.35, oa + float(n.get("giu", 3.0))))
        nhans.append(dict(n, name=f"nh{i:02d}", a=oa, b=max(ob, oa + 0.8)))
    nhans.sort(key=lambda x: x["a"])
    if basic and len(nhans) > int(cfg.get("so_chu_basic", 2)):
        print("Gói BASIC chỉ 2 chữ nhấn sau thumbnail -> bỏ:", [n["chu"] for n in nhans[int(cfg.get("so_chu_basic", 2)):]])
        nhans = nhans[:int(cfg.get("so_chu_basic", 2))]
    for j, n in enumerate(nhans):  # chữ không có "den" tắt khi chữ sau hiện; chữ có "den" (danh sách) giữ tới mốc đó
        # chữ nào cũng tắt khi chữ kế tiếp hiện (kể cả có "den") — trừ các dòng cùng 1 danh sách ("nhom")
        if j + 1 < len(nhans) and not (n.get("nhom") and nhans[j + 1].get("nhom") == n.get("nhom")):
            n["b"] = min(n["b"], nhans[j + 1]["a"])
        n["b"] = min(n["b"], total, cta_a if n["a"] < cta_a else total)
    td = min(cfg["thumb_dur"], total)
    for n in nhans:  # không hiện cùng lúc với thumbnail: chữ nói trong lúc thumbnail còn thì chờ thumbnail tắt
        if n["a"] < td:
            n["a"] = td
    # chữ nhấn phải đọc kịp: < 1,2s thì đẩy chữ sau lùi lại MỘT CHÚT (tối đa 0,25s — lùi nhiều là lệch giọng),
    # không được thì bỏ chữ này
    for j, n in enumerate(nhans):
        if "den" in n or n["b"] - n["a"] >= 1.2:
            continue
        nxt = nhans[j + 1] if j + 1 < len(nhans) else None
        need = n["a"] + 1.2
        if nxt and "den" not in nxt and nxt["b"] - need >= 1.2 and nxt["a"] < need <= nxt["a"] + 0.25:
            nxt["a"] = fr(need)
            n["b"] = fr(need)
    if mike_ds:
        trung = [n for n in nhans if any(n["a"] < x["start"] + x["duration"] and n["b"] > x["start"] for x in mike_ds)]
        if trung:
            print("Bỏ chữ nhấn trùng điểm nhấn Mike (Mike đã có chữ riêng):", [n["chu"] for n in trung])
            nhans = [n for n in nhans if n not in trung]
    dropped = [n["chu"] for n in nhans if "den" not in n and n["b"] - n["a"] < 1.2]
    nhans = [n for n in nhans if "den" in n or n["b"] - n["a"] >= 1.2]
    if dropped:
        print("Bỏ chữ nhấn quá ngắn (không kịp đọc):", dropped)
    nqc = cfg.get("nhan_qc", {})
    if nqc is not False:  # luật QC mỹ phẩm (hồ sơ ngành my-pham): nhãn quảng cáo + tên mỹ phẩm + đơn vị công bố
        nqc = {"tag": TH["nhan_qc"]["tag"],
               "phaply": TH["nhan_qc"]["phaply"], **(nqc or {})}
    print(f"Chữ nhấn: {len(nhans)} · phụ đề chạy: {'có' if phu_de else 'không'}")

    chu = P / "chu"
    chu.mkdir(exist_ok=True)
    if "--pngs" in flags:
        jobs = [("thumb", thumb_html(cfg)), ("thumb_band", thumb_html(cfg, "band")), ("thumb_big", thumb_html(cfg, "big")),
                ("cta", f'<div class="cta"><span class="ar">&#8601;</span><span>{TH["cta"]}</span></div>')]
        if not co_cta:
            jobs = [j for j in jobs if j[0] != "cta"]
        for c in calls:
            jobs.append((c["name"], stroked("call", "<br>".join(c["lines"]))))
        if nqc:
            jobs += [("nhan", f'<div class="nhan">{nqc["tag"]}</div>'), ("phaply", f'<div class="phaply">{nqc["phaply"].replace(" · ", "<br>")}</div>')]
        for n in nhans:            # chữ theo kho team: bản xem thử vẽ đúng kiểu kho (font, màu, viền, nền)
            jobs.append((n["name"], tc.html_kho(n, GREEN if cfg.get("kho_doi_mau") else None) if n.get("kho") else tc.html(n)))
        if phu_de:
            for i, c in enumerate(cues):
                jobs.append((f"sub{i:03d}", stroked("sub", keep_nbsp(c["text"]))))
        render_pngs(jobs, chu)
        if cfg.get("bo_cuc_tu_dong", True):
            import bo_cuc as bc
            # gói Basic quay 1 shot, nhiều cảnh cận tay thao tác sản phẩm: mặt + sản phẩm vẫn cấm tuyệt đối, tay/thân chỉ trừ nhẹ
            bc.W_NGUOI = float(cfg.get("trong_so_nguoi", 0.4 if basic else 20))
            inp, fv = base_video(aroll_v, pieces, broll + mike_ds, punch, with_audio=False)
            print("Dò mặt / sản phẩm để đặt chữ...")
            frames = bc.clean_frames(";".join(fv).replace("[base]", "[v]"), inp, total, P / "_nhap_bo_cuc.npz")
            person = bc.person_masks(frames, P / "_nguoi.npz")
            faces, prods = bc.scene_maps(frames, person)
            G = bc.GW, bc.GH

            def rect(x0, y0, x1, y1):
                m = np.zeros((bc.GH, bc.GW), bool)
                m[y0 // bc.S:y1 // bc.S, x0 // bc.S:x1 // bc.S] = True
                return m
            fixed = [(0, total, rect(42, 118, 246, 282)),                     # logo (đo đúng khung ảnh logo)
                     (0, total, rect(740, 144, 1040, 200)),                   # nhãn QC (góc phải trên)
                     ]
            all_rows = tc.ROWS["tren"] + tc.ROWS["duoi"]
            items = [{"name": "thumb", "png": chu / "thumb.png", "a": 0, "b": min(cfg["thumb_dur"], total),
                      "rows": tc.ROWS["tren"] if basic else all_rows, "pref_y": None if basic else 1170,
                      # thumbnail luôn phải có: được đè lên THÂN người (trừ nhẹ) nhưng KHÔNG đè MẶT / sản phẩm
                      "w_nguoi": 1.0}]   # Basic: thumbnail dải TRÊN (không đè thân/sản phẩm)
            # nút giỏ hàng + dòng pháp lý cũng phải né người / sản phẩm (cảnh cuối thường có hộp sản phẩm trên bàn)
            if nqc:
                items.append({"name": "phaply", "png": chu / "phaply.png", "a": cta_a, "b": total, "rows": all_rows,
                              "pref_y": 1390})
            if co_cta:
                items.append({"name": "cta", "png": chu / "cta.png", "a": cta_a, "b": total, "rows": all_rows, "pref_y": 1480})
            for n in nhans:
                vt = n.get("vi_tri")
                rws = tc.ROWS["tren"] if vt == "tren" else tc.ROWS["duoi"] if vt in ("duoi", "giua") else all_rows
                items.append({"name": n["name"], "png": chu / f"{n['name']}.png", "a": n["a"], "b": n["b"],
                              "nhom": n.get("nhom"), "rows": rws, "pref_y": None})
            res = bc.place_all(items, frames, person, faces, prods, fixed, P)
            (chu / "_bo_cuc.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
            bad = {k: v for k, v in res.items() if v[2] > 1.0}
            print(f"Bố cục: {len(res)} chữ · xem {P / 'bang-bo-cuc.jpg'}" + (f" · CÒN ĐÈ: {bad}" if bad else ""))
        print("Logo:", logo_png(chu))
        if cfg.get("nhac", False):
            make_music(P / "nhac-nen.wav", total)

    lufs = loudness(aroll)
    gain_db = max(-6, min(9, -14.0 - lufs))
    # V2: chỉ tăng/giảm âm lượng giọng (không nén, không lọc) và không để đỉnh vượt -1 dB -> không vỡ tiếng
    rv = run(["ffmpeg", "-hide_banner", "-i", str(aroll), "-vn", "-af", "volumedetect", "-f", "null", "-"])
    mv = re.findall(r"max_volume:\s*(-?[\d.]+) dB", rv.stderr)
    if mv:
        gain_db = min(gain_db, -1.0 - float(mv[-1]))
    vol = round(10 ** (gain_db / 20), 3)
    print(f"Giọng: {lufs:.1f} LUFS -> tăng {gain_db:+.1f} dB")

    # bảng cắt cho người đọc
    lines = [f"# {cfg['title']}", "", f"Tổng: {total:.1f}s", "", "| Ra (s) | Nguồn (s) |", "|---|---|"]
    lines += [f"| {p['o']:.2f} | {p['s']:.2f}–{p['e']:.2f} |" for p in pieces]
    lines += ["", "## Phụ đề", ""] + [f"- {c['a']:.2f}–{c['b']:.2f}: {c['text']}" for c in cues]
    (P / "bang-cat.md").write_text("\n".join(lines), encoding="utf-8")
    srt = []
    for i, c in enumerate(cues, 1):
        ts = lambda x: f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round(x % 1 * 1000)) % 1000:03d}"
        srt += [str(i), f"{ts(c['a'])} --> {ts(c['b'])}", c["text"], ""]
    (P / "transcript.srt").write_text("\n".join(srt), encoding="utf-8")

    def bbox(png):
        a = np.asarray(Image.open(png).getchannel("A"))
        ys, xs = np.where(a > 40)
        return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if len(ys) else (0, 0, W, H)
    bc_res = json.loads((chu / "_bo_cuc.json").read_text(encoding="utf-8")) if (chu / "_bo_cuc.json").exists() else {}
    # ngưỡng bỏ chữ: 0,5 (mặc định). Gói Basic (phải đủ 3 chữ, nhiều cảnh cận tay) 2,0 — vẫn bỏ nếu đè MẶT thật
    # (mặt trọng số 40: đè 1/10 vùng mặt đã > 4)
    nguong = float(cfg.get("nguong_bo_chu", 2.0 if basic else 0.5))
    bo = [n for n in nhans if n["name"] in bc_res and bc_res[n["name"]][2] > nguong]
    if bo:  # chữ tuyệt đối không che người / sản phẩm: không còn chỗ trống thì bỏ chữ đó
        print("Bỏ chữ nhấn vì không còn chỗ trống (sẽ che người/sản phẩm):", [n["chu"] for n in bo])
        nhans = [n for n in nhans if n not in bo]
    # TỪ CẤM (cơ bản theo luật + ngành, tự gộp với từ cấm riêng của khách): quét CHỮ TRÊN MÀN HÌNH và LỜI NÓI giữ lại
    cam = [c.strip().lower() for c in str(cfg.get("cam", CAM)).split(",") if c.strip()]
    def _trung(text):
        t = re.sub(r"<[^>]+>", "", text).lower()
        return [c for c in cam if re.search(rf"(?<!\w){re.escape(c)}(?!\w)", t)]
    tren_man = list(cfg.get("thumb", [])) + [l for n in nhans for l in n["chu"]] + ([TH.get("cta", "")] if co_cta else [])
    hit_chu = sorted({c for x in tren_man for c in _trung(x)})
    hit_loi = [(c["a"], c["text"], _trung(c["text"])) for c in cues if _trung(c["text"])]
    if hit_chu:
        print("!! TỪ CẤM TRONG CHỮ TRÊN MÀN HÌNH (phải sửa chữ):", ", ".join(hit_chu))
    for t_, tx, hs in hit_loi:
        print(f"!! TỪ CẤM TRONG LỜI NÓI @{t_:.1f}s: {', '.join(hs)} — \"{tx}\" (cắt câu này hoặc báo người dùng)")
    if TH.get("cau_bat_buoc"):
        print("Câu bắt buộc của ngành (nên có trong dòng pháp lý / mô tả):", TH["cau_bat_buoc"])
    dem_k = {}
    vao_ds = kc.chon("chu_vao", pc, so=max(1, len(nhans)), hat=hat, pro=pro, muot=cfg.get("kho_muot", True))
    ra_ds = kc.chon("chu_ra", pc, so=max(1, len(nhans)), hat=hat, pro=pro, muot=cfg.get("kho_muot", True))
    for j, n in enumerate(nhans):   # mỗi chữ 1 kiểu vào / ra KHÁC NHAU từ kho CapCut, tiếng đi theo đúng kiểu vào
        n["anim_idx"] = dem_k.get(tc.kieu(n), 0)
        dem_k[tc.kieu(n)] = n["anim_idx"] + 1
        if vao_ds and cfg.get("kho_capcut", True):
            n["vao"] = vao_ds[j % len(vao_ds)]
            n["sfx_vao"] = kc.thong_tin("chu_vao", n["vao"])["tieng"]
            n["lech"] = {"whoosh": -0.06, "sparkle": -0.04, "swipe": -0.02, "click": 0.0, "tick": 0.0}.get(n["sfx_vao"], 0.02)
            n["ra"] = ra_ds[j % len(ra_ds)] if ra_ds else None
    if not basic and cfg.get("hoat_anh_tram", False):   # cảnh trám: hoạt ảnh vào/ra CapCut — TẮT mặc định (góp ý 17/11: nhiều hiệu ứng -> rối)
        vv = kc.chon("video_vao", pc, so=max(1, len(broll)), hat=hat + "v", pro=pro, muot=cfg.get("kho_muot", True))
        vr = kc.chon("video_ra", pc, so=max(1, len(broll)), hat=hat + "r", pro=pro, muot=cfg.get("kho_muot", True))
        for j, b in enumerate(sorted(broll, key=lambda x: x["start"])):
            if vv:
                b["vao"] = vv[j % len(vv)]
                b["sfx_vao"] = kc.thong_tin("video_vao", b["vao"])["tieng"]
            if vr:
                b["ra"] = vr[j % len(vr)]
    # ĐA DẠNG (20/11): chỗ vào / ra cảnh trám từ người nói (khác track -> CapCut không đặt chuyển cảnh được) dùng HOẠT ẢNH
    # vào / ra CapCut cùng cảm giác với kiểu chuyển cảnh đã chọn; giữa 2 cảnh trám liền nhau vẫn là chuyển cảnh thật.
    if not basic:
        for b in broll:
            if (b["ref"], "vao") in trans and not b.get("vao") and not any(
                    abs(x["start"] + x["duration"] - b["start"]) < 0.05 for x in broll if x is not b):
                b["vao"] = anim_cho_chuyen(trans[(b["ref"], "vao")], "vao")
            if (b["ref"], "ra") in trans and not b.get("ra"):
                b["ra"] = anim_cho_chuyen(trans[(b["ref"], "ra")], "ra")
    # MẶT NẠ CapCut cho cảnh trám (mat_na.py): khung bo góc / tròn / chia đôi — thưa, theo ngành; "mat_na": false để tắt
    import mat_na
    mat_na_ds = mat_na.chon(cfg, broll, pc, hat, basic)
    for b in broll:
        if b["ref"] in mat_na_ds and not b.get("vao"):
            b["vao"] = mat_na.thong_so(mat_na_ds[b["ref"]]).get("vao")   # 'lộ dần' = mặt nạ + hoạt ảnh vào
    # tiếng nhấn tính SAU khi đã bỏ chữ không còn chỗ (trước đây chữ bị bỏ vẫn còn tiếng pop "trống")
    import kho_tieng
    bo_tieng = kho_tieng.BoChon(pc, hat=hat, sfx_dir=SFX_DIR, thu_vien=cfg.get("sfx_thu_vien", True) is not False,
                                da_dang=cfg.get("da_dang", "thuong"))
    cfg.setdefault("phong_cach", pc)
    sfx4 = sfx_events(cfg, broll, calls, cta_a, total, nhans, trans, chon=bo_tieng)
    sfx = [(t_, n_, db_) for t_, n_, db_, _ in sfx4]
    # TIẾNG THƯ VIỆN CAPCUT theo vai (kho/tieng-capcut.json): thay tiếng tự tạo ở bước CapCut; MP4 xem thử vẫn dùng tự tạo
    tieng_tv = []
    for t_, n_, _, vai_ in sfx4:
        muc = bo_tieng.thu_vien_cho(vai_) if vai_ != "co_dinh" else None
        if muc:
            tieng_tv.append((t_, muc))
    thieu = max(0.0, min(8.0, (-14.0 - lufs) - gain_db))   # giọng không tăng được tới -14 LUFS (đỉnh cao) -> hạ tiếng nhấn
    if thieu > 0.5 and sfx:                                # theo đúng phần thiếu để tiếng nhấn không át giọng
        sfx = [(t_, n_, db_ - thieu) for t_, n_, db_ in sfx]
        print(f"Tiếng nhấn hạ {thieu:.1f} dB cho cân với giọng gốc")
    if sfx:
        (P / "sfx").mkdir(exist_ok=True)
        for _, n, _ in sfx:
            shutil.copy2(sfx_file(n), P / "sfx" / f"{n}.wav")
        print("SFX:", ", ".join(f"{n}@{t:.1f}s" for t, n, _ in sfx))
        print("  theo vai:", ", ".join(f"{v}:{n}" for _, n, _, v in sfx4))
        if tieng_tv:
            print(f"  tiếng thư viện CapCut: {len(tieng_tv)} chỗ —", ", ".join(f"{m['ten']}@{t:.1f}s" for t, m in tieng_tv))
        elif cfg.get("sfx_thu_vien", True) is not False:
            print("  (chưa có kho tiếng thư viện CapCut -> dùng tiếng tự tạo; nạp kho: kho_tieng.py thu)")
    (P / "da-dang.json").write_text(json.dumps({
        "phong_cach": pc, "da_dang": cfg.get("da_dang", "thuong"),
        "tieng": [{"t": t_, "vai": v_, "tu_tao": n_} for t_, n_, _, v_ in sfx4],
        "tieng_thu_vien": [{"t": t_, "ten": m["ten"], "ma": m["ma"]} for t_, m in tieng_tv],
        "chuyen_canh": [{"canh": r, "cho": k, "kieu": s_} for (r, k), s_ in trans.items()],
        "hoat_anh_tram": [{"canh": b["ref"], "t": b["start"], "vao": b.get("vao"), "ra": b.get("ra")} for b in broll
                          if b.get("vao") or b.get("ra")],
        "mat_na": [{"canh": r, "kieu": k} for r, k in mat_na_ds.items()]}, ensure_ascii=False, indent=1), encoding="utf-8")
    if trans:
        print("Chuyển cảnh:", ", ".join(f"{s_}@{r}/{k}" for (r, k), s_ in trans.items()))
    if mat_na_ds:
        print("Mặt nạ cảnh trám:", ", ".join(f"{k}@{r}" for r, k in mat_na_ds.items()))
    centers, crops = {}, {}
    for nm in ["thumb", "cta"] + [n["name"] for n in nhans] + (["nhan", "phaply"] if nqc else []):
        if not (chu / f"{nm}.png").exists():
            continue
        x0, y0, x1, y1 = bbox(chu / f"{nm}.png")
        centers[nm] = ((x0 + x1) / 2, (y0 + y1) / 2)
        if nm.startswith("nh") and nm != "nhan":   # ảnh cắt sát chữ cho hoạt ảnh bật lên quanh tâm chữ (MP4)
            cp = chu / f"_{nm}_c.png"
            pad = 24
            Image.open(chu / f"{nm}.png").crop((max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad))).save(cp)
            crops[nm] = cp
    overlays = ([("logo", 0, total)] if (chu / "logo.png").exists() else []) + [("thumb", 0, min(cfg["thumb_dur"], total))]
    overlays += [(c["name"], c["a"], c["b"]) for c in calls]
    overlays += [(n["name"], n["a"], n["b"]) for n in nhans]
    if phu_de:
        overlays += [(f"sub{i:03d}", c["a"], c["b"]) for i, c in enumerate(cues)]
    anim = {n["name"]: "pop" for n in nhans}  # 1 kiểu bật lên cho cả video (đồng bộ, không rối)
    if co_cta:
        overlays += [("cta", cta_a, total)]
    if nqc:
        overlays += [("nhan", 0, total), ("phaply", cta_a, total)]

    # ảnh thumbnail (để đăng / gửi duyệt) khi KHÔNG xuất MP4: khung đầu video + logo + chữ thumbnail + nhãn QC
    if "--mp4" not in flags and "--pngs" in flags and cfg.get("out_thumb") and (chu / "thumb.png").exists():
        tmpf = P / "_khung_dau.png"
        t0 = (broll[0]["from"] if broll and broll[0]["start"] <= 0.01 else pieces[0]["s"]) + 0.3
        src0 = broll[0]["path"] if broll and broll[0]["start"] <= 0.01 else aroll_v
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.2f}", "-i", str(src0), "-frames:v", "1", "-vf",
             f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", str(tmpf)])
        if tmpf.exists():
            im = Image.open(tmpf).convert("RGBA")
            for nm in ["logo", "thumb"] + (["nhan"] if nqc else []):
                if (chu / f"{nm}.png").exists():
                    im.alpha_composite(Image.open(chu / f"{nm}.png").convert("RGBA").resize((W, H)))
            im.convert("RGB").save(cfg["out_thumb"])
            tmpf.unlink(missing_ok=True)
            print("Thumbnail:", cfg["out_thumb"])

    # ------------------------------------------------ MP4
    if "--mp4" in flags:
        out = Path(cfg["out_mp4"])
        inp, f = base_video(aroll_v, pieces, broll + mike_ds, punch, trans=trans)
        args = ["ffmpeg", "-v", "error", "-y"] + inp
        for name, a, b in overlays:
            if name in anim:
                args += ["-loop", "1", "-t", f"{b - a + 0.1:.3f}", "-framerate", str(FPS)]
            args += ["-i", str(crops.get(name, chu / f"{name}.png"))]
        nhac = bool(cfg.get("nhac", False)) and (P / "nhac-nen.wav").exists()
        if nhac:
            args += ["-i", str(P / "nhac-nen.wav")]
        for _, n, _ in sfx:
            args += ["-i", str(P / "sfx" / f"{n}.wav")]
        nb, no = len(broll + mike_ds), len(overlays)
        last = "base"
        for j, (name, a, b) in enumerate(overlays):
            k = 1 + nb + j
            if name in anim:
                sk, ak = ANIM[anim[name]]
                sc = _scale_expr(sk)
                cw = Image.open(crops[name]).width if name in crops else W
                cx, cy = centers.get(name, (W / 2, H / 2))
                f.append(f"[{k}:v]format=rgba,fade=in:st=0:d={ak[-1][0]}:alpha=1,"
                         f"scale=w='max(2,trunc({cw}*{sc}/2)*2)':h=-2:eval=frame,setpts=PTS-STARTPTS+{a}/TB[n{j}]")
                f.append(f"[{last}][n{j}]overlay=x='{cx:.1f}-w/2':y='{cy:.1f}-h/2':eval=frame:eof_action=pass:"
                         f"enable='between(t,{a},{b - 0.001})'[o{j}]")
            else:
                f.append(f"[{last}][{k}:v]overlay=0:0:enable='between(t,{a},{b - 0.001})'[o{j}]")
            last = f"o{j}"
        mk = 1 + nb + no
        f.append(f"[voice]{LOC_TAP_AM(cfg)}volume={gain_db}dB[vo]")
        if nhac:
            f.append(f"[{mk}:a]volume=0.10[mu]")
        s0 = mk + (1 if nhac else 0)
        for j, (t, n, db) in enumerate(sfx):
            ms = int(t * 1000)
            f.append(f"[{s0 + j}:a]adelay={ms}|{ms},volume={db}dB[s{j}]")
        f.append("[vo]" + ("[mu]" if nhac else "") + "".join(f"[s{j}]" for j in range(len(sfx)))
                 + f"amix=inputs={1 + (1 if nhac else 0) + len(sfx)}:duration=first:normalize=0,"
                 f"aresample=48000[aout]")
        args += ["-filter_complex", ";".join(f), "-map", f"[{last}]", "-map", "[aout]", "-t", f"{total:.3f}",
                 "-r", str(FPS), "-pix_fmt", "yuv420p"]
        enc = ["-c:v", "h264_nvenc", "-preset", "p6", "-cq", "18", "-b:v", "0"]
        tail = ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
        r = run(args + enc + tail)
        if r.returncode != 0:
            print("nvenc lỗi, dùng libx264:", r.stderr[-400:])
            r = run(args + ["-c:v", "libx264", "-preset", "medium", "-crf", "18"] + tail)
            if r.returncode != 0:
                print(r.stderr[-3000:])
                raise SystemExit("Xuất MP4 lỗi")
        run(["ffmpeg", "-v", "error", "-y", "-ss", "0.5", "-i", str(out), "-frames:v", "1", cfg["out_thumb"]])
        print("MP4:", out)

    # ------------------------------------------------ CapCut
    if "--capcut" in flags:
        # giọng đã LỌC TẠP ÂM (cùng bộ lọc với MP4) cho track "Giong" của CapCut
        # V3 (góp ý 18/11) — PHÂN LỚP RÕ RÀNG:
        #  · TIMELINE CHÍNH = video thoại đã cắt vấp, GIỮ NGUYÊN ÂM THANH trong video (không tách giọng ra track riêng)
        #  · CẢNH TRÁM = LỚP PHỦ phía trên (track "Canh tram"), tắt tiếng; khớp lời / kịch bản
        #  · ổn định âm thanh (chuẩn hoá âm lượng + cải thiện giọng + giảm ồn) bật bằng chức năng CapCut (cap_nhat_am.py)
        main, phu = [], []
        for i, p in enumerate(pieces):
            o0 = p["o"]
            o1 = pieces[i + 1]["o"] if i + 1 < len(pieces) else total
            main.append({"path": str(aroll_v), "start": fr(o0), "duration": fr(o1 - o0), "sourceStart": p["s"],
                         "volume": vol, "ref": f"a{i}", **({"scale": punch} if i % 2 and punch > 1.001 else {})})
        us = [round(x["start"] * 1e6) for x in main] + [round(total * 1e6)]   # khít tuyệt đối (micro giây nguyên)
        for k_, x in enumerate(main):
            x["start"] = us[k_] / 1e6
            x["duration"] = (us[k_ + 1] - us[k_]) / 1e6
        for b in sorted(broll, key=lambda b: b["start"]):
            phu.append({"path": b["path"], "start": b["start"], "duration": b["duration"], "sourceStart": b["from"],
                        "volume": 0, "ref": b["ref"]})
        tracks = [{"type": "video", "name": "Hinh chinh", "items": main}]
        if phu:
            tracks.append({"type": "video", "name": "Canh tram", "items": phu})
        if mike_ds:   # điểm nhấn Mike: lớp riêng trên cảnh trám, tắt tiếng (bật / tắt cả lớp trong CapCut)
            tracks.append({"type": "video", "name": "Mike", "items": [
                {"path": x["path"], "start": x["start"], "duration": x["duration"], "sourceStart": x["from"], "volume": 0,
                 "ref": x["ref"]} for x in mike_ds]})
        # chuyển cảnh: chỉ giữa 2 cảnh trám nối liền trên lớp phủ (chỗ vào/ra cảnh trám: cảnh trám phủ lên, cắt thẳng)
        trans_ops = []
        for x, y in zip(phu, phu[1:]):
            if abs(x["start"] + x["duration"] - y["start"]) < 0.05:
                slug = trans.get((y["ref"], "vao")) or trans.get((x["ref"], "ra"))
                if slug:
                    trans_ops.append({"op": "transition", "target": x["ref"], "slug": slug,
                                      "duration": min(0.5, x["duration"] / 3, y["duration"] / 3)})
        lanes = []
        for n in nhans:
            for ln in lanes:
                if ln[-1]["b"] <= n["a"] + 1e-6:
                    ln.append(n)
                    break
            else:
                lanes.append([n])
        groups = [("Logo", ["logo"]), ("Thumbnail", ["thumb"]), ("Chu nhan", [c["name"] for c in calls]),
                  *[(f"Nhan nha {li + 1}", [n["name"] for n in ln]) for li, ln in enumerate(lanes)],
                  ("Phu de", [f"sub{i:03d}" for i in range(len(cues))]), ("Gio hang", ["cta"]),
                  ("Nhan quang cao", ["nhan"]), ("Dong phap ly", ["phaply"])]
        ov = {n: (a, b) for n, a, b in overlays}
        chu_capcut = cfg.get("chu_capcut", MAY.get("chu_capcut", True))
        text_style_ops = []
        thumb_font = {}
        if chu_capcut:
            # CHỮ THẬT: mọi chữ (trừ logo) là chữ CapCut, sửa nội dung / màu / vị trí trực tiếp trong CapCut
            tracks_txt = []

            def add_txt(track, nm, a, b, item, style):
                item.update({"start": a, "duration": fr(b - a), "ref": "t_" + nm})
                tracks_txt.append((track, item))
                text_style_ops.append({"op": "text-style", "target": "t_" + nm, "style": style})
            if "thumb" in centers:
                # 2 chữ CapCut: dải nền (dòng 1) + chữ to viền trắng (các dòng sau), đặt theo khối thumbnail bố cục đã chọn
                band, big = thumb_parts(cfg)
                pb, pg = thumb_px(cfg)
                x0, y0, x1, y1 = bbox(chu / "thumb.png")
                hA = (lambda b: b[3] - b[1])(bbox(chu / "thumb_band.png")) if band else 0
                hB = (lambda b: b[3] - b[1])(bbox(chu / "thumb_big.png")) if big else 0
                k_ = (y1 - y0) / max(1, hA + hB + (16 if band and big else 0))
                cx = (x0 + x1) / 2
                td_ = min(cfg["thumb_dur"], total)
                if band:
                    it_, st_ = tc.fixed_text(band, pb * k_, "#FFFFFF", cx, y0 + k_ * hA / 2, bg=(GREEN, 1.0))
                    add_txt("Thumbnail", "thumb_a", 0, td_, it_, st_)
                    thumb_font[band] = 800
                if big:
                    it_, st_ = tc.fixed_text("\n".join(big), pg * k_, GREEN, cx, y1 - k_ * hB / 2, border="#FFFFFF")
                    st_["borderWidth"] = 0.08
                    st_["shadowAlpha"] = 0.45
                    add_txt("Thumbnail 2", "thumb_b", 0, td_, it_, st_)
                    thumb_font["\n".join(big)] = 800
            nh_by = {n["name"]: n for n in nhans}
            for li, ln in enumerate(lanes):
                for n in ln:
                    if n["name"] not in centers:
                        continue
                    sc_ = bc_res.get(n["name"], [0, 0, 0, 1.0])
                    sc_ = sc_[3] if len(sc_) > 3 else 1.0
                    it_, st_ = tc.capcut_text(n, *centers[n["name"]], scale=sc_)
                    add_txt(f"Nhan nha {li + 1}", n["name"], n["a"], n["b"], it_, st_)
            if co_cta and "cta" in centers:
                it_, st_ = tc.fixed_text("↙ " + TH["cta"], 46, "#FFFFFF", *centers["cta"], bg=(GREEN, 1.0))
                add_txt("Gio hang", "cta", cta_a, total, it_, st_)
            if nqc and "nhan" in centers:
                it_, st_ = tc.fixed_text(nqc["tag"], 26, "#FFFFFF", *centers["nhan"], bg=("#000000", 0.4), shadow=False)
                add_txt("Nhan quang cao", "nhan", 0, total, it_, st_)
            if nqc and "phaply" in centers:
                it_, st_ = tc.fixed_text(nqc["phaply"].replace(" · ", chr(10)), 27, "#FFFFFF", *centers["phaply"])
                add_txt("Dong phap ly", "phaply", cta_a, total, it_, st_)
            for tname in dict.fromkeys(t for t, _ in tracks_txt):
                tracks.append({"type": "text", "name": tname, "items": [i for t, i in tracks_txt if t == tname]})
            groups = [("Logo", ["logo"])]
        for tname, names in groups:
            items = [{"type": "photo", "path": str(chu / f"{n}.png"), "start": ov[n][0], "duration": fr(ov[n][1] - ov[n][0]),
                      "ref": "p_" + n} for n in names if n in ov and ov[n][1] - ov[n][0] > 0.05]
            if items:
                tracks.append({"type": "video", "name": tname, "items": items})
        if cfg.get("nhac", False) and (P / "nhac-nen.wav").exists():
            tracks.append({"type": "audio", "name": "Nhac nen", "items": [
                {"path": str(P / "nhac-nen.wav"), "start": 0, "duration": total, "volume": 0.10, "ref": "music"}]})
        if sfx:
            sfx_lanes = []   # tiếng chồng lên nhau -> track SFX thứ 2, 3… (CapCut không cho 2 đoạn chồng trên 1 track)
            for j, (t, n, db) in enumerate(sfx):
                it_ = {"path": str(P / "sfx" / f"{n}.wav"), "start": t,
                       "duration": max(1, math.floor(min(wav_dur(P / "sfx" / f"{n}.wav"), total - t) * FPS)) / FPS,
                       "volume": round(min(1.0, 10 ** (db / 20)), 3), "ref": f"sfx{j}"}
                for ln in sfx_lanes:
                    if ln[-1]["start"] + ln[-1]["duration"] <= t + 1e-6:
                        ln.append(it_)
                        break
                else:
                    sfx_lanes.append([it_])
            for li, ln in enumerate(sfx_lanes):
                tracks.append({"type": "audio", "name": "SFX" if li == 0 else f"SFX {li + 1}", "items": ln})
        drafts = MAY["capcut_drafts"]
        # MẶC ĐỊNH: cập nhật TẠI CHỖ project đang được góp ý (ghi trong du-an.json), không tạo bản v2/v3...
        # --moi = tạo project mới (lần đầu, hoặc khi người dùng muốn giữ bản cũ để so)
        dang_xem = None
        if "--moi" not in flags and cfg.get("cap_nhat", True) and (P / "du-an.json").exists():
            dang_xem = json.loads((P / "du-an.json").read_text(encoding="utf-8")).get("draft")
            if not dang_xem or not os.path.isdir(os.path.join(drafts, dang_xem)):
                dang_xem = None
        if dang_xem:
            name = dang_xem + "__moi"
            if os.path.exists(os.path.join(drafts, name)):   # bản tạm sót lại từ lần lỗi trước -> cất đi, không xoá
                (P / "_draft-cu").mkdir(exist_ok=True)
                shutil.move(os.path.join(drafts, name), str(P / "_draft-cu" / f"{name}-{int(time.time())}"))
        else:
            name, v = cfg["draft"], 1
            while os.path.exists(os.path.join(drafts, name)):
                v += 1
                name = f"{cfg['draft']} v{v}"
        ops = list(text_style_ops) + trans_ops
        if "hieu_ung_capcut" not in cfg and not basic and cfg.get("kho_capcut", True):
            hu = []   # KHÔNG hiệu ứng mở đầu (góp ý 17/11: "hiệu ứng mở đầu bị chớp, bỏ đi") — chỉ nhấn nhẹ ở ý chính
            nhan_moc = [n["a"] for n in nhans if n.get("san_pham")] + [n["a"] for n in nhans if tc.kieu(n) == "chinh"][-1:]
            ds_nhan = kc.chon("hieu_ung_canh", pc, 3, vai="nhan", hat=hat + "n", pro=pro, muot=cfg.get("kho_muot", True))
            for k_, t_ in enumerate(sorted(set(nhan_moc))[:int(cfg.get("hieu_ung_toi_da", 2))]):
                if ds_nhan:
                    hu.append({"slug": ds_nhan[k_ % len(ds_nhan)], "at": t_, "dur": 0.7})
            cfg["hieu_ung_capcut"] = hu
            print("Hiệu ứng cảnh CapCut (tự chọn theo phong cách " + pc + "):", ", ".join(f"{e['slug']}@{e['at']:.1f}s" for e in hu))
        so_hu = 0
        for e in cfg.get("hieu_ung_capcut", []):   # hiệu ứng cảnh có sẵn của CapCut (capcut enums --scene-effects)
            if so_hu >= int(cfg.get("hieu_ung_toi_da", 2)):
                break
            # góp ý 17/11: không chớp / lắc / nhấp nháy, không hiệu ứng ngay mở đầu video
            if re.search(r"flash|strobe|shake|blink|flicker|glitch", e["slug"]) or (
                    "khi" not in e and float(e.get("at", 0)) < 0.5):
                print("  bỏ hiệu ứng cảnh (chớp/lắc hoặc ngay mở đầu):", e["slug"])
                continue
            if "khi" in e:
                t0 = fr(m(find_phrase(segs, e["khi"], e.get("sau", 0))[0], "start"))
            else:
                t0 = float(e.get("at", 0))
            if t0 < total - 0.2:
                ops.append({"op": "effect", "slug": e["slug"], "start": t0, "duration": min(float(e.get("dur", 0.6)), total - t0)})
                so_hu += 1
        for n in nhans:
            if chu_capcut:
                continue  # chữ thật: dùng hiệu ứng chữ vào/ra của CapCut (gắn sau khi tạo draft)
            ref = "p_" + n["name"]
            sk, ak = ANIM[anim[n["name"]]]
            for t, v in sk:
                ops.append({"op": "keyframe", "target": ref, "property": "uniform_scale", "time": t, "value": v})
            for t, v in ak:
                ops.append({"op": "keyframe", "target": ref, "property": "alpha", "time": t, "value": v})
        spec = {"name": name, "width": W, "height": H, "fps": FPS, "tracks": tracks, "operations": ops}
        sp = P / "spec.json"
        sp.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
        # thông tin hậu kỳ để ghep_du_an.py gắn lại hiệu ứng chữ + font sau khi ghép nhiều video vào 1 project
        hk = {"total": total, "chu_capcut": bool(chu_capcut), "thumb_font": thumb_font,
              "nhan": [{"text": chr(10).join(tc.lines(n)), "a": n["a"], "dur": n["b"] - n["a"], "vao": tc.anim(n)[0],
                        "vd": tc.ANIM_CAPCUT[tc.kieu(n)][1], "ra": n.get("ra") or tc.ANIM_CAPCUT[tc.kieu(n)][2],
                        "rd": tc.ANIM_CAPCUT[tc.kieu(n)][3], "w": tc.FONT_W[tc.kieu(n)]} for n in nhans]}
        hk["video"] = [{"start": b["start"], "dur": b["duration"], "vao": b.get("vao"), "ra": b.get("ra")} for b in broll]
        (P / "hau-ky.json").write_text(json.dumps(hk, ensure_ascii=False, indent=1), encoding="utf-8")
        if "--chi-spec" in flags:
            print("Đã ghi spec.json + hau-ky.json (ghép dự án bằng ghep_du_an.py)")
            return
        tl = run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe"])
        if "CapCut.exe" in tl.stdout:
            raise SystemExit("CapCut đang mở -> đóng CapCut rồi chạy lại với --capcut")
        r = run(["capcut", "compile", str(sp), "--drafts", drafts, "--template", "auto"], shell=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], r.stderr[-2000:])
            raise SystemExit("capcut compile lỗi")
        res = json.loads(r.stdout)
        if not dang_xem:
            (P / "du-an.json").write_text(json.dumps({"draft": name, "draft_path": res.get("draft_path")}, ensure_ascii=False, indent=2), encoding="utf-8")
        if chu_capcut:
            fp = tc.project_font(P, 600)
            if fp:
                by_text = {}
                for n in nhans:
                    k_ = tc.kieu(n)
                    fw = tc.project_font(P, tc.FONT_W[k_]) or fp
                    by_text["\n".join(tc.lines(n))] = (fw, tc.FONT_TEN[tc.FONT_W[k_]])
                for txt_, w_ in thumb_font.items():
                    by_text[txt_] = (tc.project_font(P, w_) or fp, tc.FONT_TEN[w_])
                for n in nhans:            # chữ theo KHO CHỮ team: giữ font của kho (kho_text.ap_kho tự gắn font)
                    if n.get("kho"):
                        by_text["\n".join(tc.lines(n))] = None
                print(f"Font: Be Vietnam Pro cho {tc.patch_fonts(res['draft_path'], fp, by_text)} chữ")
            else:
                print("! Chưa có font Be Vietnam Pro (chạy: font_viet.py tai be-vietnam-pro) — CapCut dùng font mặc định")
            # KHO CHỮ TEAM (kho/kho-text.md): chữ nhấn ghi "kho": "<mã>" -> nhân bản đúng kiểu (font, màu, viền, hiệu ứng, hoạt ảnh)
            kho_muc = [{"text": "\n".join(tc.lines(n)), "start": n["a"], "kho": n["kho"]} for n in nhans if n.get("kho")]
            if kho_muc:
                import kho_text
                mau_ = GREEN if cfg.get("kho_doi_mau") else None
                print(f"Kho chữ team: {kho_text.ap_kho(res['draft_path'], kho_muc, P, mau=mau_)}/{len(kho_muc)} chữ theo kiểu kho")
            # hiệu ứng chữ vào/ra có sẵn của CapCut cho từng chữ nhấn
            dc = json.loads((Path(res["draft_path"]) / "draft_content.json").read_text(encoding="utf-8"))
            mat = {t["id"]: json.loads(t["content"]).get("text", "") for t in dc["materials"].get("texts", [])}
            segs_t = [(sg["id"], mat.get(sg["material_id"], ""), sg["target_timerange"]["start"] / 1e6)
                      for tr in dc["tracks"] if tr["type"] == "text" for sg in tr["segments"]]
            na = 0
            for n in nhans:
                if n.get("kho"):
                    continue            # kiểu kho đã có hoạt ảnh riêng
                txt = "\n".join(tc.lines(n))
                hit = [sid for sid, tx, st in segs_t if tx == txt and abs(st - n["a"]) < 0.05]
                if not hit:
                    continue
                _, vd, ra, rd = tc.ANIM_CAPCUT[tc.kieu(n)]
                ra = n.get("ra") or ra
                vi = tc.anim(n)[0]                   # kiểu hiện xoay vòng, khớp với tiếng nhấn
                dur = n["b"] - n["a"]
                cmd = ["capcut", "text-anim", res["draft_path"], hit[0], "--intro", vi, "--intro-duration", f"{min(vd, dur / 3):.2f}"]
                if dur > 1.2:
                    cmd += ["--outro", ra, "--outro-duration", f"{min(rd, dur / 4):.2f}"]
                rr = run(cmd, shell=True)
                na += rr.returncode == 0
                if rr.returncode:
                    print("  ! hiệu ứng chữ lỗi:", (rr.stdout + rr.stderr)[-300:])
            import hau_ky
            nv = hau_ky.ap_video_anim(res["draft_path"], [{"start": b["start"], "dur": b["duration"], "vao": b.get("vao"),
                                                           "ra": b.get("ra")} for b in broll])
            if nv:
                print(f"Hoạt ảnh cảnh trám CapCut: {nv}/{len(broll)}")
            # sửa lệch làm tròn (chồng 1µs / hở 0ms trên track chính) trước khi CapCut tự dồn đoạn
            run(["capcut", "lint", res["draft_path"], "--fix"], shell=True)
            # MỜ TIẾNG Ở VẾT CẮT (19/11): mỗi mảnh thoại trên track chính làm mờ vào 15 ms / ra 20 ms -> không nghe "tách"
            try:
                print(f"Mờ tiếng ở vết cắt (CapCut): {mo_tieng_vet_cat(res['draft_path'])} mảnh")
            except Exception as ex:
                print("  ! mờ tiếng vết cắt CapCut lỗi:", ex)
            if fp:
                tc.patch_fonts(res["draft_path"], fp, by_text)
            print(f"Hiệu ứng chữ CapCut: {na}/{len(nhans)} chữ · chuyển cảnh: {len(trans_ops)} · hiệu ứng cảnh: "
                  f"{so_hu}")
        if mat_na_ds:   # mặt nạ CapCut lên cảnh trám (capcut mask)
            kq = mat_na.ap(res["draft_path"], [{"start": b["start"], "kieu": mat_na_ds[b["ref"]]} for b in broll
                                               if b["ref"] in mat_na_ds])
            print(f"Mặt nạ CapCut: {sum(1 for x in kq if x[2])}/{len(kq)}",
                  "; ".join(f"{k}@{t:.1f}s" + ("" if ok else f" LỖI {e}") for t, k, ok, e in kq))
        if tieng_tv:    # đổi tiếng tự tạo -> tiếng thư viện CapCut (chép đúng mẫu material từ draft thật)
            try:
                print(f"Tiếng thư viện CapCut: {kho_tieng.gan_vao_draft(res['draft_path'], tieng_tv)}/{len(tieng_tv)} chỗ")
            except Exception as ex:
                print("  ! gắn tiếng thư viện CapCut lỗi (giữ tiếng tự tạo):", ex)
        if dang_xem:
            import cap_nhat as cn
            res["draft_path"] = str(cn.replace_draft(drafts, name, dang_xem, P / "_draft-cu"))
            name = dang_xem
            (P / "du-an.json").write_text(json.dumps({"draft": name, "draft_path": res["draft_path"]}, ensure_ascii=False,
                                                     indent=2), encoding="utf-8")
            print(f"Đã cập nhật TẠI CHỖ project \"{name}\" (không tạo bản mới)")
        lint = run(["capcut", "lint", res["draft_path"], "-H"], shell=True)
        print("Draft CapCut:", name, "· chữ:", "CHỮ THẬT (sửa được)" if chu_capcut else "ảnh PNG (máy lỗi chữ)")
        print(lint.stdout.strip()[-1500:] or "lint sạch")

    if "--qa" in flags and Path(cfg["out_mp4"]).exists():
        qa(P, cfg, cues, calls)


if __name__ == "__main__":
    main()
