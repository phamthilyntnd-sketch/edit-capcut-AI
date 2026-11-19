"""CHẾ ĐỘ MIKE TRỌN VIDEO của edit-capcut-ai: chuyển 1 dự án /edit-video-mike-2 ĐÃ RENDER thành project CapCut sửa được.
Chỉ ĐỌC kết quả Mike xuất ra (segments.json, work/editor-map.json, index.html, assets/, renders/) — không chứa và không chép
mã Mike (giấy phép Mike: 1 người dùng, cấm phát tán). Máy phải tự cài Mike bằng bản quyền của người dùng máy đó.

    PY -I SK/scripts/mike_capcut.py "<thư mục dự án Mike>" [--name ten-draft] [--check] [--chu-capcut]
    (chạy trong thư mục làm việc: công thức + ảnh phụ đề ghi vào ./projects/<tên>/)

Dựng các lớp (track) riêng trong CapCut:
  A-roll      người nói đã cắt + làm sạch giọng (assets/aroll.mp4), tách đúng từng vết cắt của Mike
  B-roll      cảnh trám đặt đúng câu, đúng giây
  Hieu ung    các đoạn đồ hoạ / chuyển cảnh Mike tự vẽ (lấy từ bản render), để nguyên như ảnh động
  Phu de      chữ Mike -> chữ CapCut thật (sửa chữ, màu, cỡ, vị trí ngay trong CapCut)
  Nhac / SFX  nhạc nền và tiếng hiệu ứng thành 2 track âm thanh riêng

Cần: CapCut đang ĐÓNG, capcut-cli đã cài. Chỉ đọc dự án Mike, không sửa gì trong đó.
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path.cwd()                      # nơi làm việc (projects/<tên>/)
SK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
W, H = 1080, 1920
# Cỡ chữ Mike (px, khung 1080x1920) theo class; dòng nhấn "md y" = 106px nghiêng
MIKE_PX = {"sm": 56, "md": 60, "lg": 80, "xl": 100}
PX_PER_SIZE = 4.0  # px Mike / cỡ chữ CapCut — căn bằng mắt trên CapCut 9.7.1

# Font kèm skill (Be Vietnam Pro, OFL, đủ dấu tiếng Việt) — chép vào thư mục dự án, máy nào cũng có
FONT_TITLE = "Be Vietnam Pro ExtraBold"
_FONT = {"p": None}


def find_font():
    return _FONT["p"]


def patch_fonts(draft_dir, looks):
    """Gắn font đã tải + đậm/nghiêng cho mọi chữ, trong mọi bản sao timeline của draft."""
    fp = find_font()
    if not fp:
        print("  ! Không thấy font Noto Sans đã tải trong CapCut — chữ có thể hiện 'Input text'.")
        print("    Mở CapCut, thêm 1 chữ bất kỳ, chọn font Noto Sans (để CapCut tải về), rồi chạy lại.")
        return 0
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
        seg_ref = {}
        for t in j.get("tracks", []):
            for s in t.get("segments", []):
                seg_ref[s.get("material_id")] = s.get("id")
        for t in texts:
            look = looks.get(seg_ref.get(t["id"]), {})
            t.update(font_path=fp, font_resource_id="", font_id="", font_source_platform=0, font_title=FONT_TITLE,
                     initial_scale=1.0, fonts=[])
            c = json.loads(t["content"])
            for st in c.get("styles", []):
                st["font"] = {"path": fp, "id": ""}
                st["bold"] = True
                st["italic"] = bool(look.get("italic"))
                st["useLetterColor"] = True
            t["content"] = json.dumps(c, ensure_ascii=False)
            t["bold_width"] = 0.008
            n += 1
        f.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    return n


def die(msg):
    print(f"\nLỖI: {msg}")
    sys.exit(1)


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def drafts_dir():
    import thuong_hieu as th
    return th.MAY["capcut_drafts"]


def capcut_running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe"], capture_output=True, text=True).stdout
    return "CapCut.exe" in out


def parse_html(index_html):
    """id -> {src, start, mstart, dur} cho B-roll; id -> {top, size_px} cho chữ."""
    broll, caps = {}, {}
    for m in re.finditer(r'<div[^>]*\bid="(bf\d+)"[^>]*>.*?<video[^>]*src="([^"]+)"[^>]*'
                         r'data-start="([\d.]+)"[^>]*data-media-start="([\d.]+)"[^>]*data-duration="([\d.]+)"',
                         index_html, re.S):
        broll[m.group(1)] = dict(src=m.group(2), start=float(m.group(3)), mstart=float(m.group(4)), dur=float(m.group(5)))
    for m in re.finditer(r'<div[^>]*\bid="(w\d+)"[^>]*style="([^"]*)"', index_html):
        st = m.group(2)
        top = re.search(r"top:(-?[\d.]+)px", st)
        fs = re.search(r"font-size:([\d.]+)px", st)
        caps[m.group(1)] = dict(top=float(top.group(1)) if top else None, fs=float(fs.group(1)) if fs else None)
    return broll, caps


_DUR = {}


def media_dur(path):
    p = str(path)
    if p not in _DUR:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                           capture_output=True, text=True)
        try:
            _DUR[p] = float(r.stdout.strip())
        except ValueError:
            _DUR[p] = None
    return _DUR[p]


def fit(item):
    """Nguồn ngắn hơn khoảng cần lấp -> làm chậm nhẹ cho vừa (Mike giữ khung cuối)."""
    d = media_dur(item["path"])
    if not d:
        return item
    avail = d - item.get("sourceStart", 0) - 0.04
    if avail <= 0:
        return None
    if item["duration"] > avail:
        if item["ref"].startswith("a_") or item["duration"] - avail < 0.1:
            item["duration"] = round(avail, 4)  # giọng nói: không đổi tốc độ, chỉ cắt vài khung cuối
        else:
            item["speed"] = round(avail / item["duration"], 4)
    return item


def find_chrome():
    """Tìm Chrome (hoặc Edge — cùng lõi Chromium) ở các chỗ cài thường gặp trên Windows."""
    cands = [os.environ.get("CHROME_PATH", "")]
    for base in (os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", ""),
                 os.environ.get("LOCALAPPDATA", "")):
        if base:
            cands += [os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                      os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe")]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return r"C:\Program Files\Google\Chrome\Application\chrome.exe"


CHROME = find_chrome()


def render_caption_pngs(P, ids, out_dir):
    """Vẽ từng dòng phụ đề của Mike thành ảnh PNG trong suốt 1080x1920, đúng font/kiểu/vị trí của Mike.
    Dùng Chrome chạy ngầm với hồ sơ tạm (không đụng hồ sơ Chrome của người dùng)."""
    page = (P / "index.html").read_text(encoding="utf-8")
    styles = "\n".join(re.findall(r"<style[^>]*>.*?</style>", page, re.S))
    lines = {}
    for ln in page.splitlines():
        m = re.search(r'<div[^>]*\bid="(w\d+)"', ln)
        if m and 'class="dw' in ln:
            lines[m.group(1)] = ln.strip()
    out_dir.mkdir(parents=True, exist_ok=True)
    prof = out_dir / "_chrome-profile"
    fix = ("<style>html,body{margin:0;padding:0;width:1080px;height:1920px;background:transparent!important;overflow:hidden}"
           ".dw,.dw *{opacity:1!important;visibility:visible!important;transform:none!important;animation:none!important;"
           "transition:none!important;clip-path:none!important}</style>")
    done = {}
    for wid in ids:
        if wid not in lines:
            continue
        html_page = (f'<!doctype html><html><head><meta charset="utf-8"><base href="{P.as_uri()}/">'
                     f'<link rel="stylesheet" href="assets/fonts/fonts.css">{styles}{fix}</head>'
                     f'<body><div style="position:absolute;left:0;top:0;width:1080px;height:1920px">{lines[wid]}</div></body></html>')
        hp = out_dir / f"_{wid}.html"
        hp.write_text(html_page, encoding="utf-8")
        png = out_dir / f"{wid}.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                        f"--user-data-dir={prof}", "--allow-file-access-from-files", "--force-device-scale-factor=1",
                        "--default-background-color=00000000", "--window-size=1080,1920", "--virtual-time-budget=3000",
                        f"--screenshot={png}", hp.as_uri()], capture_output=True, timeout=90)
        if png.exists():
            done[wid] = png
        hp.unlink(missing_ok=True)
    return done


def color_of(cls, palette):
    accent = palette[0] if palette else "#FFD45C"
    if "y" in cls.split():
        return accent
    return "#FFFFFF"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--name")
    ap.add_argument("--check", action="store_true", help="chỉ kiểm tra, không ghi vào CapCut")
    ap.add_argument("--chu-capcut", action="store_true",
                    help="phụ đề là chữ CapCut (sửa được trong CapCut). Mặc định: phụ đề là ảnh đúng kiểu Mike")
    a = ap.parse_args()

    P = Path(a.project)
    need = ["work/editor-map.json", "segments.json", "index.html", "assets/aroll.mp4"]
    for f in need:
        if not (P / f).exists():
            die(f"dự án Mike chưa dựng xong (thiếu {f}). Chạy /edit-video-mike-2 tới bước render trước.")

    emap = load(P / "work/editor-map.json")
    segs = load(P / "segments.json")
    broll_html, cap_html = parse_html((P / "index.html").read_text(encoding="utf-8"))
    fps = emap.get("fps", 30)
    dur = emap["dur"]
    palette = emap.get("palette", [])
    base = a.name or f"{P.name}-capcut"
    name, v = base, 1
    while os.path.exists(os.path.join(drafts_dir(), name)):  # không bao giờ ghi đè bản bạn đã chỉnh tay
        v += 1
        name = f"{base}-v{v}"

    renders = sorted([r for r in (P / "renders").glob("*.mp4") if not re.search(r"-(phone|raw)\.mp4$", r.name)],
                     key=lambda r: r.stat().st_mtime) if (P / "renders").exists() else []
    final = renders[-1] if renders else None

    tracks, report = [], {"aroll": 0, "broll": 0, "fx": 0, "caps": 0, "skipped": []}

    # 1. A-roll: 1 đoạn cho mỗi vết cắt của Mike
    aroll = []
    for s in segs:
        # mốc tính theo micro-giây nguyên để các đoạn khít nhau tuyệt đối (CapCut tự dồn khe hở)
        st_us = round(s["frame"] * 1_000_000 / fps)
        en_us = round((s["frame"] + s["frames"]) * 1_000_000 / fps)
        aroll.append({"path": str(P / "assets/aroll.mp4"), "start": st_us / 1e6, "duration": (en_us - st_us) / 1e6,
                      "sourceStart": st_us / 1e6, "ref": f"a_{s['id']}"})
    tracks.append({"type": "video", "name": "A-roll", "items": aroll})
    report["aroll"] = len(aroll)

    # 2. B-roll (tắt tiếng như Mike)
    items = []
    for it in emap["items"]:
        if it.get("kind") != "broll":
            continue
        b = broll_html.get(it["id"])
        if not b:
            report["skipped"].append(f"B-roll {it['key']}: không tìm thấy file")
            continue
        items.append({"path": str(P / b["src"]), "start": round(b["start"], 4), "duration": round(b["dur"], 4),
                      "sourceStart": round(b["mstart"], 4), "volume": 0, "ref": f"b_{it['id']}"})
    if items:
        tracks.append({"type": "video", "name": "B-roll", "items": sorted(items, key=lambda x: x["start"])})
    report["broll"] = len(items)

    # 3. Đồ hoạ / chuyển cảnh Mike tự vẽ -> lấy đúng đoạn đó từ bản render
    fx = []
    if final:
        spans = []
        for it in emap["items"]:
            if it.get("kind") in ("graphic", "full") and it.get("b", 0) > it.get("a", 0):
                spans.append((max(0, it["a"]), min(dur, it["b"]), it.get("cls") or it.get("label")))
        spans.sort()
        merged = []
        for s0, s1, lab in spans:
            if merged and s0 <= merged[-1][1] + 0.05:
                merged[-1] = (merged[-1][0], max(merged[-1][1], s1), merged[-1][2] + "+" + lab)
            else:
                merged.append((s0, s1, lab))
        for i, (s0, s1, lab) in enumerate(merged):
            if s1 - s0 < 0.05:
                continue
            fx.append({"path": str(final), "start": round(s0, 4), "duration": round(s1 - s0, 4),
                       "sourceStart": round(s0, 4), "volume": 0, "ref": f"fx_{i}"})
    elif any(it.get("kind") in ("graphic", "full") for it in emap["items"]):
        report["skipped"].append("chưa có bản render -> bỏ qua các đoạn đồ hoạ Mike")
    if fx:
        tracks.append({"type": "video", "name": "Hieu ung Mike", "items": fx})
    report["fx"] = len(fx)

    # 4. Phụ đề -> chữ CapCut
    caps, ops, text_look = [], [], {}
    for it in emap["items"]:
        if it.get("kind") != "cap" or it.get("hidden"):
            continue
        text = html.unescape(it.get("text") or "").strip()
        if not text or it["b"] <= it["a"]:
            continue
        cls = it.get("cls", "")
        parts = cls.split()
        h = cap_html.get(it["id"], {})
        accent = "y" in parts and "md" in parts
        px = h.get("fs") or (106 if accent else MIKE_PX.get(next((k for k in MIKE_PX if k in parts), "sm")))
        size = round(px / PX_PER_SIZE, 1)
        top = h.get("top")
        if top is None:
            top = 1300
        cy = top + px * 0.55
        y = round(1 - 2 * cy / H, 4)  # CapCut: 0 = giữa khung, +1 = mép trên
        ref = f"t_{it['id']}"
        caps.append({"text": text, "start": round(it["a"], 4), "duration": round(it["b"] - it["a"], 4),
                     "fontSize": size, "color": color_of(cls, palette), "x": 0, "y": y, "ref": ref})
        text_look[ref] = {"italic": accent}
        ops.append({"op": "text-style", "target": ref,
                    "style": {"shadow": True, "shadowAlpha": 0.8, "shadowDistance": 3, "shadowSmoothing": 0.6}})
    # Mike hiện 2 dòng cùng lúc (dòng dẫn + dòng nhấn) -> mỗi dòng 1 track để không chồng nhau
    lanes = []
    for c in sorted(caps, key=lambda x: (x["start"], -x["y"])):
        for lane in lanes:
            if lane[-1]["start"] + lane[-1]["duration"] <= c["start"] + 1e-6:
                lane.append(c)
                break
        else:
            lanes.append([c])
    if a.chu_capcut:
        for i, lane in enumerate(lanes):
            tracks.append({"type": "text", "name": f"Phu de {i + 1}", "items": lane})
    else:
        # Phụ đề dạng ảnh trong suốt: giống hệt Mike, không phụ thuộc bộ vẽ chữ của CapCut
        ops = [o for o in ops if o["op"] != "text-style"]
        text_look.clear()
        pngs = render_caption_pngs(P, [c["ref"][2:] for c in caps], ROOT / "projects" / base / "chu")
        print(f"Vẽ phụ đề thành ảnh: {len(pngs)}/{len(caps)} dòng")
        for i, lane in enumerate(lanes):
            imgs = [{"type": "photo", "path": str(pngs[c["ref"][2:]]), "start": c["start"], "duration": c["duration"],
                     "ref": "p" + c["ref"]} for c in lane if c["ref"][2:] in pngs]
            if imgs:
                tracks.append({"type": "video", "name": f"Phu de {i + 1}", "items": imgs})
    report["caps"] = len(caps)

    # 5. Âm thanh
    music_vol = 0.13
    bp = P / "build.py"
    if bp.exists():
        m = re.search(r"r\.music\([^,]+,\s*([\d.]+)", bp.read_text(encoding="utf-8"))
        if m:
            music_vol = float(m.group(1))
    if (P / "assets/music.wav").exists():
        tracks.append({"type": "audio", "name": "Nhac nen", "items": [
            {"path": str(P / "assets/music.wav"), "start": 0, "duration": round(dur, 4), "volume": music_vol, "ref": "music"}]})
        ops.append({"op": "audio-fade", "target": "music", "fadeIn": 0.5, "fadeOut": 1.5})
    if (P / "assets/sfx_bed.wav").exists():
        tracks.append({"type": "audio", "name": "SFX", "items": [
            {"path": str(P / "assets/sfx_bed.wav"), "start": 0, "volume": 1.0, "ref": "sfx"}]})

    for t in tracks:
        if t["type"] == "video":
            t["items"] = [x for x in (i if i.get("type") == "photo" else fit(i) for i in t["items"]) if x]
            for x in t["items"]:
                if "speed" in x:
                    print(f"  · {Path(x['path']).name} ngắn hơn chỗ cần lấp -> chạy {x['speed']}x")

    spec = {"name": name, "width": W, "height": H, "fps": fps, "tracks": tracks, "operations": ops}
    out_dir = ROOT / "projects" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    (out_dir / "font").mkdir(exist_ok=True)
    fp_ = out_dir / "font" / "be-vietnam-pro-800.ttf"
    shutil.copy2(SK / "fonts" / "be-vietnam-pro-800.ttf", fp_)
    _FONT["p"] = fp_.as_posix()
    spec_path = out_dir / "spec.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "du-an.json").write_text(json.dumps({"draft": name, "nguon": "mike", "mike_project": str(P)},
                                                   ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Dự án Mike : {P}")
    print(f"Draft      : {name}")
    print(f"A-roll {report['aroll']} đoạn · B-roll {report['broll']} · Hiệu ứng Mike {report['fx']} · Phụ đề {report['caps']} dòng")
    for s in report["skipped"]:
        print("  ! " + s)
    print(f"Công thức  : {spec_path}")

    if capcut_running() and not a.check:
        die("CapCut đang mở. Hãy đóng CapCut rồi chạy lại.")
    cmd = ["capcut", "compile", str(spec_path), "--drafts", drafts_dir(), "--template", "auto"]
    if a.check:
        cmd.append("--check")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", shell=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:])
        die("capcut compile thất bại")
    if a.check:
        print("Kiểm tra OK (chưa ghi gì vào CapCut).")
        return
    res = json.loads(r.stdout)
    draft = res["draft_path"]
    refs = res.get("refs", {})
    # đồng bộ tốc độ cho các cảnh đã làm chậm (compile chỉ ghi vào segment)
    for t in tracks:
        for x in t["items"]:
            if "speed" in x and x["ref"] in refs:
                subprocess.run(["capcut", "speed", draft, refs[x["ref"]], str(x["speed"]), "-q"], shell=True)
    looks = {refs[r]: v for r, v in text_look.items() if r in refs}
    print(f"Font chữ: đã gắn Be Vietnam Pro cho {patch_fonts(draft, looks)} chữ (mọi bản sao timeline)")
    lint = subprocess.run(["capcut", "lint", draft, "-H"], capture_output=True, text=True, encoding="utf-8", shell=True)
    print(lint.stdout.strip() or "lint: sạch")
    print("XONG. Mở CapCut, chọn project:", name)


if __name__ == "__main__":
    main()
