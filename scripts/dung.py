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
    r = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vn", "-af", "silencedetect=n=-35dB:d=0.3", "-f", "null", "-"])
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


def build_pieces(keeps, sil, min_gap=0.45, pad=0.12, words=(), env=None):
    """Đoạn giữ -> các mảnh A-roll. Mọi điểm cắt đặt ở CHỖ IM giữa 2 từ (đáy âm lượng, như do_am của bộ dùng chung) —
    không bao giờ cắt giữa 1 từ được giữ (lỗi 'rất hiệ/u/ quả', góp ý 16/11): đầu đoạn = chỗ im ngay trước tiếng đầu tiên,
    cuối đoạn = chỗ đuôi từ cuối tắt hẳn. Khoảng lặng bên trong chỉ cắt phần im thật (đuôi tiếng nhẹ được giữ)."""
    ws = sorted(words, key=lambda w: w["s"])
    pieces = []
    for s, e in keeps:
        kin = [w for w in ws if s <= (w["s"] + w["e"]) / 2 <= e]
        ref_s = min([s] + ([kin[0]["s"]] if kin and kin[0]["s"] > s - 0.3 else []))
        ref_e = max([e] + ([kin[-1]["e"]] if kin and kin[-1]["e"] < e + 0.4 else []))
        s, e = quiet_before(env, ref_s), quiet_after(env, ref_e)
        db = env["db"] if env is not None else None
        cur = s
        for a, b in sil:
            if b - a >= min_gap and a > cur + 0.05 and b < e - 0.05:
                cut_a, cut_b = a + pad, b - pad
                if db is not None:   # đuôi tiếng nhẹ (dưới -35 dB) vẫn là chữ: chỉ cắt khi đã xuống tới đáy khoảng lặng
                    i0, i1 = _i(env, a), _i(env, b)
                    m = db[i0:i1 + 1].min()
                    q = [i for i in range(i0, i1 + 1) if db[i] <= m + 6]
                    if q:
                        cut_a = max(cut_a, q[0] * ENV_HOP + 0.06)
                        cut_b = min(cut_b, q[-1] * ENV_HOP - 0.04)
                if cut_b - cut_a < 0.15:
                    continue
                if cut_a > cur:
                    pieces.append([cur, cut_a])
                cur = cut_b
        pieces.append([cur, e])
    pieces.sort()
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
CSS = CSS + CSS2 + tc.CSS

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
            f'<link rel="stylesheet" href="fonts.css"><style>{CSS}</style></head><body>{body}'
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
SFX_PRIO = {"whoosh": 1, "whip": 1, "swipe": 1, "click": 2, "pop": 2, "tick": 2, "bubble": 2, "snare": 2,
            "impact": 2, "notify": 2, "shutter": 2, "riser": 1, "chime": 3, "sparkle": 3, "ding": 3, "cash": 3}
SFX_KIEU = {"xanh": ("pop", -16), "trang": ("pop", -16), "pill": ("pop", -17), "list": ("click", -14),
            "the": ("swipe", -18), "lock": ("swipe", -18), "hook": ("swipe", -17), "quote": ("whip", -21),
            "punch": ("impact", -21), "note": ("tick", -15), "benefit": ("pop", -16), "product": ("sparkle", -17)}


def sfx_events(cfg, broll, calls, cta_a, total, nhans=(), trans=None):
    """Mỗi điểm nhấn 1 tiếng, cách nhau >= 0.8s (trùng thì giữ tiếng ưu tiên hơn). Tiếng nằm dưới giọng."""
    if cfg.get("sfx") is False or not SFX_DIR.exists():
        return []
    # NHIỀU + NGHE RÕ (người dùng 14/11: "nhỏ quá không nghe được gì", "thêm nhiều sound effect"):
    #  mọi chữ nhấn có tiếng (pop/bubble xen kẽ; chữ nền: click), mỗi lần vào cảnh trám: swipe/whoosh xen kẽ,
    #  chuyển cảnh: whoosh, tên sản phẩm: sparkle, câu hỏi (?): notify, nút giỏ hàng: ding + cash.
    #  Mức (dB so với file gốc ~ -3 dBFS) đặt để nghe rõ trên nền giọng -14 LUFS nhưng không át lời.
    L = float(cfg.get("sfx_db", 0))   # chỉnh chung: +3 = to hơn, -3 = nhỏ hơn
    trans = trans or {}
    ev = []
    for i, b in enumerate(sorted(broll, key=lambda x: x["start"])):
        if (b["ref"], "vao") in trans:
            ev.append((b["start"], TIENG_CHUYEN.get(trans[(b["ref"], "vao")], "whoosh"), -9 + L))
        elif b["start"] > 0.3:
            ev.append((b["start"], ("swipe", "whoosh")[i % 2], -11 + L))
        if (b["ref"], "ra") in trans:
            ev.append((b["start"] + b["duration"], TIENG_CHUYEN.get(trans[(b["ref"], "ra")], "whoosh"), -10 + L))
    for n in nhans:   # tiếng dồn lên ngay trước khi gọi tên sản phẩm -> tạo cao trào
        if n.get("san_pham") and n["a"] > 1.5:
            ev.append((n["a"] - 1.0, "riser", -14 + L))
    ev = [(t, n, db, False) for t, n, db in ev]
    ev += [(cta_a, "ding", -7 + L, True), (cta_a + 0.45, "cash", -12 + L, False)]
    k = 0
    cuoi = [n for n in nhans if tc.kieu(n) == "chinh"][-1:]   # câu chốt cảm xúc cuối: chuông nhẹ
    # TIẾNG KHỚP HIỆU ỨNG CHỮ (góp ý 16/11): tiếng đặt đúng lúc chữ bật lên (tc.SFX_CHU), loại tiếng hợp kiểu hiện
    # (pop-up -> pop/bubble, trượt lên -> whip), và LUÔN được ưu tiên hơn tiếng chuyển cảnh khi trùng giờ.
    for n in nhans:
        ten, lech = tc.SFX_CHU[tc.kieu(n)]
        t = n["a"] + lech
        if n.get("sfx"):
            ev.append((t, n["sfx"], -8 + L, True))
        elif n in cuoi:
            ev.append((t, "chime", -8 + L, True))
        elif n.get("san_pham"):
            ev.append((t, "sparkle", -7 + L, True))
        elif any(c.rstrip().endswith("?") for c in n["chu"]):
            ev.append((t, "notify", -9 + L, True))
        else:
            ev.append((t, ten[k % len(ten)], (-7 if tc.kieu(n) == "chinh" else -9) + L, True)); k += 1
    keep = []
    for t, n, db, chu_ in sorted(ev):
        if keep and t - keep[-1][0] < 0.35:
            cu = keep[-1]
            if (chu_, SFX_PRIO[n]) > (cu[3], SFX_PRIO[cu[1]]):   # tiếng của chữ thắng tiếng chuyển cảnh
                keep[-1] = (t, n, db, chu_)
            continue
        keep.append((t, n, db, chu_))
    return [(fr(t), n, db) for t, n, db, _ in keep if t < total - 0.3]


# Chuyển cảnh CÓ SẴN của CapCut, chia theo ngữ cảnh (slug đều có trong `capcut enums --transitions`)
CHUYEN = {
    "vao": ["pull-in", "slide", "wipe-left", "inhale", "wipe-right"],          # người nói -> cảnh trám
    "san_pham": ["light-sweep-ii", "white-flash", "twinkle-zoom"],             # -> cảnh cận sản phẩm
    "doi": ["slide", "wipe-up", "mix", "flash"],                                # cảnh trám -> cảnh trám khác
    "ra": ["pull-out", "dissolve", "blur", "camera-glow"],                      # cảnh trám -> người nói
}
# tiếng đi kèm từng kiểu chuyển cảnh (kho ENG/remotion/public/sfx)
TIENG_CHUYEN = {"pull-in": "whoosh", "pull-out": "whoosh", "dissolve": "whoosh", "blur": "whoosh",
                "slide": "swipe", "wipe-left": "swipe", "wipe-right": "swipe", "wipe-up": "swipe",
                "inhale": "whip", "mix": "whip", "white-flash": "shutter", "flash": "shutter",
                "camera-glow": "shutter", "light-sweep-ii": "sparkle", "twinkle-zoom": "sparkle"}


def chon_chuyen_canh(cfg, broll, total):
    """Chuyển cảnh ĐA DẠNG ở mọi chỗ vào/ra cảnh trám và giữa 2 cảnh trám khác cảnh quay — mỗi chỗ 1 kiểu hợp ngữ cảnh,
    không lặp kiểu liền nhau. Không đặt khi 1 phía < 1,2s (tránh chớp), cách nhau >= 2,5s, tối đa 10/video.
    Cảnh trám có "san_pham": true trong cấu hình (cận sản phẩm) -> kiểu ánh sáng (vệt sáng / chớp trắng).
    Trả {(ref cảnh trám, 'vao'|'ra'): slug}."""
    if cfg.get("chuyen_canh") is False:
        return {}
    toi_da, cach = int(cfg.get("chuyen_toi_da", 10)), float(cfg.get("chuyen_cach", 2.5))
    sp_refs = {f"b{i}" for i, x in enumerate(cfg.get("broll", [])) if x.get("san_pham")}
    bs = sorted(broll, key=lambda b: b["start"])
    ev = []   # (thời điểm, ref, vao|ra, nhóm kiểu, độ dài 2 phía)
    for i, b in enumerate(bs):
        prev = bs[i - 1] if i and abs(bs[i - 1]["start"] + bs[i - 1]["duration"] - b["start"]) < 0.05 else None
        nhom = "san_pham" if b["ref"] in sp_refs else "vao"
        if prev is None:   # vào từ người nói
            ev.append((b["start"], b["ref"], "vao", nhom, min(b["duration"], 99.0 if b["start"] > 1.2 else b["start"])))
        elif (os.path.basename(prev["path"]) != os.path.basename(b["path"])
              or abs((prev["from"] + prev["duration"]) - b["from"]) > 3.0):   # khác clip / khác cảnh quay
            ev.append((b["start"], b["ref"], "vao", "san_pham" if nhom == "san_pham" else "doi",
                       min(b["duration"], prev["duration"])))
        nxt = bs[i + 1] if i + 1 < len(bs) and abs(b["start"] + b["duration"] - bs[i + 1]["start"]) < 0.05 else None
        end = b["start"] + b["duration"]
        if nxt is None and end < total - 1.2:   # ra lại người nói
            ev.append((end, b["ref"], "ra", "ra", b["duration"]))
    chosen, last, dem = {}, -99.0, {}
    for t, ref, k, nhom, d in sorted(ev):
        if d < 1.2 or t - last < cach or len(chosen) >= toi_da or t < 0.5:
            continue
        pool = cfg.get("chuyen_" + nhom, CHUYEN[nhom])
        slug = pool[dem.get(nhom, 0) % len(pool)]
        if chosen and slug == list(chosen.values())[-1]:      # không lặp kiểu liền nhau
            slug = pool[(dem.get(nhom, 0) + 1) % len(pool)]
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
    segs, _ = model.transcribe(str(mp4), language="vi", vad_filter=True,
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
    """Lọc tạp âm giọng nói (người dùng 14/11: "loại bỏ tạp âm"): cắt ù tiếng trầm (quạt, xe) < 80 Hz, khử nhiễu nền
    theo phổ (afftdn tự đo nền ồn), bỏ rít cao > 14 kHz. "loc_tap_am": 0 = tắt, 1 = nhẹ, 2 = vừa (mặc định), 3 = mạnh."""
    k = int(cfg.get("loc_tap_am", 2))
    if k <= 0:
        return "highpass=f=80,"
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
    # MẶC ĐỊNH chỉ làm PROJECT CAPCUT (nhân sự tự xuất trong CapCut — góp ý 16/11). MP4 xem thử + kiểm bản ra:
    # thêm --mp4 --qa, hoặc "xuat_mp4": true trong cau-hinh.json.
    flags = set(sys.argv[2:]) or ({"--pngs", "--mp4", "--capcut", "--qa"} if cfg.get("xuat_mp4") else {"--pngs", "--capcut"})
    raw = P / "raw"
    aroll = raw / cfg["aroll"]
    segs = json.loads((P / "transcript.json").read_text(encoding="utf-8"))
    sil = silences(aroll)
    env = envelope(aroll)
    words = [w for sg in segs for w in sg.get("words", [])]
    pieces, total = build_pieces(cfg["keeps"], sil, words=words, env=env)
    m = mapper(pieces)
    cues = make_cues(segs, cfg, pieces, m)
    total = fr(total)
    # LÀM ĐẸP THEO NGƯỜI NÓI (góp ý 16/11: KOC nam bị mịn da kiểu nữ): "nguoi_noi": "nam" | "nu"
    #   nam -> không mịn da, chỉ chỉnh màu + làm nét nhẹ · nu -> mịn da 1 · chưa rõ -> KHÔNG mịn da (an toàn)
    nn = str(cfg.get("nguoi_noi", "")).lower()
    g_mac_dinh = ({"skin": 0, "net": 0.3} if nn in ("nam", "male", "m") else
                  {"skin": 1, "net": 0.4} if nn in ("nu", "nữ", "female", "f") else {"skin": 0, "net": 0.3})
    g = cfg.get("grade", g_mac_dinh)
    if g and "skin" not in g:
        g = dict(g, skin=g_mac_dinh["skin"])
    if g and nn in ("nam", "male", "m"):   # nam: luôn tắt mịn da (kể cả cấu hình chép từ video nữ), không kiểu "sang trọng"
        g = dict(g, skin=0, kieu=None if g.get("kieu") == "sang-trong" else g.get("kieu"))
    if not nn:
        print("! Chưa ghi \"nguoi_noi\": \"nam\"|\"nu\" trong cau-hinh.json -> không làm mịn da")
    if "--xem-mau" in flags:  # ảnh trước|sau để duyệt màu, không dựng
        mid = pieces[len(pieces) // 2]
        grade_preview(aroll, g or {}, (mid["s"] + mid["e"]) / 2, P)
        print("Xem:", P / "preview_grade.jpg")
        return
    aroll_v = grade_clip(aroll, g, g.get("skin", 1)) if g else aroll
    punch = float(cfg.get("punch", 1.08))
    print(f"A-roll: {len(pieces)} đoạn, tổng {total:.2f}s")

    # cảnh trám: (1) đủ dài để người xem kịp thấy (>= tram_min, mặc định 2,5s); (2) "from" = "auto" (mặc định)
    # -> tự chọn ĐOẠN HAY trong cả clip (nét, có người/sản phẩm, chuyển động vừa) — tram.py
    import tram
    tmin = float(cfg.get("tram_min", 3.0))   # góp ý 16/11 "đoạn trám hơi ngắn": 2,5 -> 3,0s
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
        if frm == "auto":
            frm, scv = tram.pick(an, ob - oa + 0.3, used.get(b["file"], []), b.get("tim_trong"), b.get("tranh", []))
            if frm is None:
                print(f"! Không tìm được đoạn hay đủ {ob - oa:.1f}s trong {b['file']} -> bỏ cảnh trám này")
                continue
        used.setdefault(b["file"], []).append((frm, frm + ob - oa + 0.3))
        if an is not None:
            loi = " ".join(w["w"].strip() for w in words if b["src"][0] - 0.1 <= w["s"] <= b["src"][1])
            chon.append((f"{b['file']} {frm:.1f}-{frm + ob - oa:.1f}s -> ra {oa:.1f}s", an, frm, ob - oa, loi))
        bp = grade_clip(raw / b["file"], dict(g, auto=False), 0) if g else raw / b["file"]
        broll.append({"path": str(bp), "start": oa, "duration": fr(ob - oa), "from": frm, "ref": f"b{i}"})
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
    trans = chon_chuyen_canh(cfg, broll, total)
    calls = []
    for i, c in enumerate(cfg["callouts"]):
        oa, ob = fr(m(c["src"][0], "start")), fr(m(c["src"][1], "end"))
        calls.append({"name": f"call{i}", "lines": c["lines"], "a": oa, "b": ob})
    cta_a = fr(m(cfg["cta_src"][0], "start"))
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
                ("cta", '<div class="cta"><span class="ar">&#8601;</span><span>{TH["cta"]}</span></div>')]
        for c in calls:
            jobs.append((c["name"], stroked("call", "<br>".join(c["lines"]))))
        if nqc:
            jobs += [("nhan", f'<div class="nhan">{nqc["tag"]}</div>'), ("phaply", f'<div class="phaply">{nqc["phaply"].replace(" · ", "<br>")}</div>')]
        for n in nhans:
            jobs.append((n["name"], tc.html(n)))
        if phu_de:
            for i, c in enumerate(cues):
                jobs.append((f"sub{i:03d}", stroked("sub", keep_nbsp(c["text"]))))
        render_pngs(jobs, chu)
        if cfg.get("bo_cuc_tu_dong", True):
            import bo_cuc as bc
            inp, fv = base_video(aroll_v, pieces, broll, punch, with_audio=False)
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
                      "rows": all_rows, "pref_y": 1170}]
            # nút giỏ hàng + dòng pháp lý cũng phải né người / sản phẩm (cảnh cuối thường có hộp sản phẩm trên bàn)
            if nqc:
                items.append({"name": "phaply", "png": chu / "phaply.png", "a": cta_a, "b": total, "rows": all_rows,
                              "pref_y": 1390})
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
    bo = [n for n in nhans if n["name"] in bc_res and bc_res[n["name"]][2] > 0.5]
    if bo:  # chữ tuyệt đối không che người / sản phẩm: không còn chỗ trống thì bỏ chữ đó
        print("Bỏ chữ nhấn vì không còn chỗ trống (sẽ che người/sản phẩm):", [n["chu"] for n in bo])
        nhans = [n for n in nhans if n not in bo]
    # tiếng nhấn tính SAU khi đã bỏ chữ không còn chỗ (trước đây chữ bị bỏ vẫn còn tiếng pop "trống")
    sfx = sfx_events(cfg, broll, calls, cta_a, total, nhans, trans)
    if sfx:
        (P / "sfx").mkdir(exist_ok=True)
        for _, n, _ in sfx:
            shutil.copy2(SFX_DIR / f"{n}.wav", P / "sfx" / f"{n}.wav")
        print("SFX:", ", ".join(f"{n}@{t:.1f}s" for t, n, _ in sfx))
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
    overlays = [("logo", 0, total), ("thumb", 0, min(cfg["thumb_dur"], total))]
    overlays += [(c["name"], c["a"], c["b"]) for c in calls]
    overlays += [(n["name"], n["a"], n["b"]) for n in nhans]
    if phu_de:
        overlays += [(f"sub{i:03d}", c["a"], c["b"]) for i, c in enumerate(cues)]
    anim = {n["name"]: "pop" for n in nhans}  # 1 kiểu bật lên cho cả video (đồng bộ, không rối)
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
        inp, f = base_video(aroll_v, pieces, broll, punch, trans=trans)
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
        nb, no = len(broll), len(overlays)
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
        f.append(f"[voice]{LOC_TAP_AM(cfg)}volume={gain_db}dB,alimiter=limit=0.89[vo]")
        if nhac:
            f.append(f"[{mk}:a]volume=0.10[mu]")
        s0 = mk + (1 if nhac else 0)
        for j, (t, n, db) in enumerate(sfx):
            ms = int(t * 1000)
            f.append(f"[{s0 + j}:a]adelay={ms}|{ms},volume={db}dB[s{j}]")
        f.append("[vo]" + ("[mu]" if nhac else "") + "".join(f"[s{j}]" for j in range(len(sfx)))
                 + f"amix=inputs={1 + (1 if nhac else 0) + len(sfx)}:duration=first:normalize=0,"
                 f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
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
        # GIỌNG ĐÃ NỐI SẴN, có làm mờ 15–20 ms ở mỗi vết cắt (capcut-cli không đặt được fade âm thanh) -> vết cắt êm,
        # không "bụp"/cụt tiếng (góp ý 16/11). Vẫn chia thành từng đoạn trên track Giong để sửa được trong CapCut.
        lk = hashlib.md5((LOC_TAP_AM(cfg) + json.dumps([(p["s"], p["e"]) for p in pieces])).encode()).hexdigest()[:8]
        giong = raw / f"{Path(cfg['aroll']).stem}_giong_noi_{lk}.wav"
        if not giong.exists():
            fa = [f"[0:a]asplit={len(pieces)}" + "".join(f"[a{i}]" for i in range(len(pieces)))]
            for i, p in enumerate(pieces):
                fa.append(f"[a{i}]atrim={p['s']}:{p['e']},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,"
                          f"afade=t=out:st={p['e'] - p['s'] - 0.02:.3f}:d=0.02[at{i}]")
            fa.append("".join(f"[at{i}]" for i in range(len(pieces))) + f"concat=n={len(pieces)}:v=0:a=1,"
                      + LOC_TAP_AM(cfg) + "aresample=48000[out]")
            rr = run(["ffmpeg", "-v", "error", "-y", "-i", str(aroll), "-filter_complex", ";".join(fa), "-map", "[out]",
                      "-ac", "2", str(giong)])
            if rr.returncode:
                raise SystemExit("Tạo giọng đã nối lỗi: " + rr.stderr[-500:])
        main, voice = [], []
        bsorted = sorted(broll, key=lambda b: b["start"])
        for i, p in enumerate(pieces):
            o0 = p["o"]
            o1 = pieces[i + 1]["o"] if i + 1 < len(pieces) else total
            voice.append({"path": str(giong), "start": o0, "duration": round(o1 - o0, 6), "sourceStart": o0,
                          "volume": vol, "ref": f"v{i}"})
            # phần A-roll không bị cảnh trám phủ
            cur, k = o0, 0
            for b in bsorted:
                b0, b1 = b["start"], b["start"] + b["duration"]
                if b1 <= cur or b0 >= o1:
                    continue
                if b0 > cur + 1 / FPS:
                    main.append({"path": str(aroll_v), "start": fr(cur), "duration": fr(b0 - cur),
                                 "sourceStart": round(p["s"] + cur - o0, 6), "volume": 0, "ref": f"a{i}_{k}",
                                 **({"scale": punch} if i % 2 and punch > 1.001 else {})}); k += 1
                cur = max(cur, b1)
            if o1 > cur + 1 / FPS:
                main.append({"path": str(aroll_v), "start": fr(cur), "duration": fr(o1 - cur),
                             "sourceStart": round(p["s"] + cur - o0, 6), "volume": 0, "ref": f"a{i}_{k}",
                             **({"scale": punch} if i % 2 and punch > 1.001 else {})})
        for b in bsorted:
            main.append({"path": b["path"], "start": b["start"], "duration": b["duration"], "sourceStart": b["from"],
                         "volume": 0, "ref": b["ref"]})
        main.sort(key=lambda x: x["start"])
        # khít tuyệt đối: mốc tính bằng micro giây nguyên (tránh hở/chồng 1µs làm CapCut tự dồn đoạn)
        us = [round(x["start"] * 1e6) for x in main] + [round(total * 1e6)]
        for k_, x in enumerate(main):
            x["start"] = us[k_] / 1e6
            x["duration"] = (us[k_ + 1] - us[k_]) / 1e6
        tracks = [{"type": "video", "name": "Hinh chinh", "items": main},
                  {"type": "audio", "name": "Giong", "items": voice}]
        # chuyển cảnh CapCut chỉ ở chỗ vào / ra cảnh trám (không ở vết cắt nhảy của người nói — đã có phóng khung)
        trans_ops = []
        for x, y in zip(main, main[1:]):   # transition gắn vào đoạn ĐỨNG TRƯỚC chỗ nối
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
            if "cta" in centers:
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
        for e in cfg.get("hieu_ung_capcut", []):   # hiệu ứng cảnh có sẵn của CapCut (capcut enums --scene-effects)
            if "khi" in e:
                t0 = fr(m(find_phrase(segs, e["khi"], e.get("sau", 0))[0], "start"))
            else:
                t0 = float(e.get("at", 0))
            if t0 < total - 0.2:
                ops.append({"op": "effect", "slug": e["slug"], "start": t0, "duration": min(float(e.get("dur", 0.6)), total - t0)})
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
                print(f"Font: Be Vietnam Pro cho {tc.patch_fonts(res['draft_path'], fp, by_text)} chữ")
            else:
                print("! Chưa có font Be Vietnam Pro (chạy: font_viet.py tai be-vietnam-pro) — CapCut dùng font mặc định")
            # hiệu ứng chữ vào/ra có sẵn của CapCut cho từng chữ nhấn
            dc = json.loads((Path(res["draft_path"]) / "draft_content.json").read_text(encoding="utf-8"))
            mat = {t["id"]: json.loads(t["content"]).get("text", "") for t in dc["materials"].get("texts", [])}
            segs_t = [(sg["id"], mat.get(sg["material_id"], ""), sg["target_timerange"]["start"] / 1e6)
                      for tr in dc["tracks"] if tr["type"] == "text" for sg in tr["segments"]]
            na = 0
            for n in nhans:
                txt = "\n".join(tc.lines(n))
                hit = [sid for sid, tx, st in segs_t if tx == txt and abs(st - n["a"]) < 0.05]
                if not hit:
                    continue
                vi, vd, ra, rd = tc.ANIM_CAPCUT[tc.kieu(n)]
                dur = n["b"] - n["a"]
                cmd = ["capcut", "text-anim", res["draft_path"], hit[0], "--intro", vi, "--intro-duration", f"{min(vd, dur / 3):.2f}"]
                if dur > 1.2:
                    cmd += ["--outro", ra, "--outro-duration", f"{min(rd, dur / 4):.2f}"]
                rr = run(cmd, shell=True)
                na += rr.returncode == 0
                if rr.returncode:
                    print("  ! hiệu ứng chữ lỗi:", (rr.stdout + rr.stderr)[-300:])
            # sửa lệch làm tròn (chồng 1µs / hở 0ms trên track chính) trước khi CapCut tự dồn đoạn
            run(["capcut", "lint", res["draft_path"], "--fix"], shell=True)
            if fp:
                tc.patch_fonts(res["draft_path"], fp, by_text)
            print(f"Hiệu ứng chữ CapCut: {na}/{len(nhans)} chữ · chuyển cảnh: {len(trans_ops)} · hiệu ứng cảnh: "
                  f"{len(cfg.get('hieu_ung_capcut', []))}")
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
