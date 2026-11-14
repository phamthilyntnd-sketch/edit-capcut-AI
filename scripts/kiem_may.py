"""Kiểm máy có đủ công cụ để dựng chưa. Chạy:  <python> scripts/kiem_may.py
In từng mục ĐỦ / THIẾU (bắt buộc) / TUỲ CHỌN và cách sửa. Thoát 1 nếu thiếu mục bắt buộc.
"""
import importlib, os, shutil, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import thuong_hieu as th

loi = 0


def dong(ok, ten, ghi, bat_buoc=True):
    global loi
    tag = "ĐỦ      " if ok else ("THIẾU   " if bat_buoc else "TUỲ CHỌN")
    if not ok and bat_buoc:
        loi += 1
    print(f"[{tag}] {ten}" + (f" — {ghi}" if ghi and not ok else ""))


for m in ("numpy", "PIL", "faster_whisper", "onnxruntime"):
    try:
        importlib.import_module(m)
        dong(True, f"Python: {m}", "")
    except ImportError:
        dong(m != "onnxruntime", f"Python: {m}", "pip install -r requirements.txt" if m != "onnxruntime"
             else "không có: bố cục chữ không né được NGƯỜI (vẫn né sản phẩm)", bat_buoc=m != "onnxruntime")
for exe in ("ffmpeg", "ffprobe"):
    dong(bool(shutil.which(exe)), exe, "cài ffmpeg (winget install Gyan.FFmpeg) rồi mở lại terminal")
cc = shutil.which("capcut") or shutil.which("capcut.cmd")
dong(bool(cc), "capcut-cli", "npm i -g capcut-cli (cần Node.js)")
chrome = next((p for b in (os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", ""),
                          os.environ.get("LOCALAPPDATA", ""))
               for p in (Path(b, "Google/Chrome/Application/chrome.exe"), Path(b, "Microsoft/Edge/Application/msedge.exe"))
               if b and p.exists()), None)
dong(bool(chrome), "Chrome / Edge (vẽ chữ PNG)", "cài Google Chrome")
M = th.MAY
dong(Path(M["capcut_drafts"]).exists(), "Thư mục project CapCut: " + M["capcut_drafts"], M["capcut_drafts"] + " (mở CapCut 1 lần, hoặc ghi may.json)")
fonts = [th.FONTS / f"be-vietnam-pro-{w}.ttf" for w in (600, 700, 800)]
dong(all(f.exists() for f in fonts), "Font Be Vietnam Pro (kèm skill)", "thiếu file trong fonts/")
sfx = Path(M["sfx"])
dong((sfx / "pop.wav").exists(), f"Tiếng nhấn (SFX): {sfx}", f"{sfx} — chạy: python scripts/tao_sfx.py")
dong(Path(M.get("u2net", "")).exists(), "Mô hình tách người u2net_human_seg.onnx",
     "không có: chữ chỉ né sản phẩm (tải u2net_human_seg.onnx, ghi đường dẫn vào may.json \"u2net\")", bat_buoc=False)
eng = Path(M.get("eng") or "__")
dong(eng.exists(), "Bộ dùng chung bo-skill-video (chỉnh màu, cắt vấp plan_cuts, kiểm bản ra, luật ngành)",
     "không có: bỏ qua chỉnh màu + kiểm luật; cắt vấp làm bằng Whisper của skill", bat_buoc=False)
try:
    free = shutil.disk_usage(Path(M["capcut_drafts"]).anchor or "C:\\").free / 1e9
    dong(free >= 2, f"Ổ đĩa còn {free:.1f} GB", "cần ≥ 2 GB (mỗi project CapCut chép video ~0,5–1 GB)")
except Exception:
    pass
print()
print("Thương hiệu mặc định:", th.TH.get("ten"), "· hồ sơ có:", ", ".join(sorted(p.stem for p in (th.SKILL / "thuong-hieu").glob("*.json"))))
print("SẴN SÀNG" if loi == 0 else f"CÒN THIẾU {loi} MỤC BẮT BUỘC")
sys.exit(1 if loi else 0)
