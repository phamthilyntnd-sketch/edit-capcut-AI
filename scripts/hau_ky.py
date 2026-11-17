"""Hậu kỳ trên draft CapCut đã dựng (dùng chung cho dung.py và ghep_du_an.py):
hoạt ảnh VÀO / RA có sẵn của CapCut cho từng cảnh trám trên lớp phủ (V4 — dùng kho hiệu ứng CapCut)."""
import json, subprocess
from pathlib import Path


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", shell=True)


def ap_video_anim(dp, items, track="Canh tram"):
    """items: [{"start": giây trên timeline, "dur": giây, "vao": slug, "ra": slug}] -> gắn hoạt ảnh cho đoạn khớp mốc."""
    dc = json.loads((Path(dp) / "draft_content.json").read_text(encoding="utf-8"))
    segs = [(sg["id"], sg["target_timerange"]["start"] / 1e6) for tr in dc["tracks"]
            if tr["type"] == "video" and tr.get("name") == track for sg in tr["segments"]]
    n = 0
    for it in items:
        hit = [sid for sid, st in segs if abs(st - it["start"]) < 0.05]
        if not hit:
            continue
        d = max(0.2, min(0.45, it["dur"] / 4))
        cmd = ["capcut", "image-anim", dp, hit[0]]
        if it.get("vao"):
            cmd += ["--intro", it["vao"], "--intro-duration", f"{d:.2f}"]
        if it.get("ra") and it["dur"] > 2.0:
            cmd += ["--outro", it["ra"], "--outro-duration", f"{d:.2f}"]
        n += _run(cmd).returncode == 0
    return n
