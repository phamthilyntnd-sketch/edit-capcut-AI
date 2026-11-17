"""Chuẩn bị 1 video trước khi dựng bằng dung.py.

Chạy (bằng python của Mike venv):
  chuan_bi.py footage "<thư mục footage>" <du-an> [--aroll IMG_xxxx] [--th <mã thương hiệu>]
      -> projects/<du-an>/raw/*.mp4 (1080x1920 30fps), *.wav, phiên âm A-roll -> transcript.json,
         bảng ảnh từng clip -> projects/<du-an>/xem/*.jpg, in lời thoại có số thứ tự đoạn.
         A-roll mặc định = clip dài nhất.
  chuan_bi.py brief "C-6" --th <mã thương hiệu>
      -> in kịch bản mã đó trong file brief trong hồ sơ thương hiệu ("brief") (cột ngay sau mã = chữ thumbnail).
"""
import json, os, re, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import thuong_hieu as th
ROOT = Path.cwd()                                   # dự án tạo ở <thư mục đang đứng>/projects/<du-an>
BRIEF = Path(th.TH.get("brief") or "__khong_co_brief__")
EXTS = {".mov", ".mp4", ".m4v", ".mkv"}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def dur(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).stdout.strip() or 0)


def transcode(src, dst):
    vf = "scale=1080:1920:flags=lanczos,fps=30,format=yuv420p"
    base = ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf]
    aud = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(dst)]
    r = run(base + ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "19", "-b:v", "0"] + aud)
    if r.returncode:
        r = run(base + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18"] + aud)
    if r.returncode:
        raise SystemExit(f"Chuyển định dạng lỗi: {src}\n{r.stderr[-800:]}")


def sheet(mp4, jpg, n=12):
    d = dur(mp4) or 1
    run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-vf",
         f"fps={n / d},scale=180:-1,drawtext=text='%{{pts\\:hms}}':x=4:y=4:fontsize=18:fontcolor=yellow:box=1,tile=6x2",
         "-frames:v", "1", str(jpg)])


def doc_am(path):
    """Âm thanh -> mảng 16 kHz mono bằng ffmpeg (không qua thư viện av: bản av / faster-whisper lệch nhau sẽ lỗi
    "open() got an unexpected keyword argument 'metadata_errors'")."""
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                       capture_output=True)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0


def transcribe(wav):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from faster_whisper import WhisperModel
    m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(doc_am(wav), language="vi", word_timestamps=True, vad_filter=False,
                           initial_prompt=th.TH.get("tu_vung", "") + ".")
    segs = list(segs)
    # Whisper "bịa" (subscribe / Ghiền Mì Gõ…) hoặc gần như không nghe được lời -> nghe lại có lọc khoảng lặng (VAD)
    loi = " ".join(x.text for x in segs).lower()
    nwords = sum(len(x.words or []) for x in segs)
    if nwords < 30 or loi.count("subscribe") >= 2:
        print("  ! Phiên âm lần 1 không đáng tin -> nghe lại có lọc khoảng lặng")
        segs, _ = m.transcribe(doc_am(wav), language="vi", word_timestamps=True, vad_filter=True,
                               initial_prompt=th.TH.get("tu_vung", "") + ".")
        segs = list(segs)
    out = []
    for s in segs:
        out.append({"start": s.start, "end": s.end, "text": s.text,
                    "words": [{"w": w.word, "s": w.start, "e": w.end} for w in s.words]})
    return out


def cmd_footage(src_dir, name, aroll=None):
    src_dir = Path(src_dir)
    P = ROOT / "projects" / name
    raw, xem = P / "raw", P / "xem"
    raw.mkdir(parents=True, exist_ok=True)
    xem.mkdir(exist_ok=True)
    files = sorted(f for f in src_dir.rglob("*") if f.suffix.lower() in EXTS)
    if not files:
        raise SystemExit(f"Không thấy video trong {src_dir}")
    for f in files:
        dst = raw / (f.stem + ".mp4")
        if not dst.exists():
            transcode(f, dst)
        run(["ffmpeg", "-v", "error", "-y", "-i", str(dst), "-vn", "-ac", "1", "-ar", "16000", str(raw / (f.stem + ".wav"))])
        sheet(dst, xem / (f.stem + ".jpg"))
        print(f"{dst.name}  {dur(dst):.1f}s  (gốc: {f.relative_to(src_dir)})")
    # ẢNH MINH HOẠ (jpg/png) trong thư mục -> clip 6s dọc 1080x1920 (ảnh giữa, nền là chính ảnh làm mờ) để dùng làm cảnh trám
    for f in sorted(x for x in src_dir.rglob("*") if x.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}):
        dst = raw / (f.stem + "_anh.mp4")
        if not dst.exists():
            vf = ("split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30[bg];"
                  "[b]scale=1080:1920:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,fps=30,"
                  "format=yuv420p")
            run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", "6", "-i", str(f), "-vf", vf, "-c:v", "libx264",
                 "-crf", "18", "-an", str(dst)])
        if dst.exists():
            sheet(dst, xem / (dst.stem + ".jpg"))
            print(f"{dst.name}  6.0s  (ảnh minh hoạ: {f.name})")
    if not aroll:   # clip THOẠI: tên có "thoai"/"noi" thì dùng, không thì clip dài nhất
        ten_thoai = [f for f in files if re.search(r"tho[aạ]i|n[oó]i|aroll|a-roll", f.stem.lower())]
        if ten_thoai:
            aroll = ten_thoai[0].stem
    a = raw / ((aroll or max((raw / (f.stem + ".mp4") for f in files), key=dur).stem) + ".mp4")
    print(f"\nA-roll: {a.name} — đang phiên âm...")
    segs = transcribe(a.with_suffix(".wav"))
    (P / "transcript.json").write_text(json.dumps(segs, ensure_ascii=False), encoding="utf-8")
    for i, s in enumerate(segs):
        print(f"{i:3d} [{s['start']:6.2f}-{s['end']:6.2f}] {s['text'].strip()}")
    sil = run(["ffmpeg", "-hide_banner", "-i", str(a.with_suffix(".wav")), "-af", "silencedetect=n=-35dB:d=0.3", "-f", "null", "-"]).stderr
    st = re.findall(r"silence_start: ([\d.]+)", sil)
    en = re.findall(r"silence_end: ([\d.]+)", sil)
    print("\nKhoảng lặng:", ", ".join(f"{float(x):.2f}-{float(y):.2f}" for x, y in zip(st, en)))
    print(f"Bảng ảnh: {xem}")


def cmd_brief(code):
    if not BRIEF.exists():
        raise SystemExit(f"Chưa có {BRIEF} — tải brief từ Google Drive (xem SKILL.md) rồi lưu dạng text vào đó.")
    t = BRIEF.read_text(encoding="utf-8", errors="replace")
    # "C-6", "Man C-6", "man c 6" -> khớp "Man C - 6" trong brief
    m = re.match(r"(?:(\w+)\s+)?([A-Za-z])\s*-?\s*(\d+)$", code.strip())
    pat = rf"{m.group(1) or 'Man'}\s+{m.group(2)}\s*-\s*{m.group(3)}(?!\d)" if m else re.escape(code)
    hits = [x.start() for x in re.finditer(pat, t, re.I)]
    if not hits:
        raise SystemExit(f"Không thấy mã {code} trong brief")
    for h in hits:
        print("=" * 60)
        print(t[h:h + 3500])


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--th" in a[:-1]:          # --th <mã thương hiệu>: chọn từ vựng / brief theo hồ sơ thương hiệu
        i = a.index("--th"); a = a[:i] + a[i + 2:]
    if len(a) >= 3 and a[0] == "footage":
        ar = a[a.index("--aroll") + 1] if "--aroll" in a else None
        cmd_footage(a[1], a[2], ar)
    elif len(a) == 2 and a[0] == "brief":
        cmd_brief(a[1])
    else:
        print(__doc__)
