"""Hồ sơ THƯƠNG HIỆU + cấu hình MÁY cho bộ dựng video CapCut.

Thương hiệu: thuong-hieu/<ma>.json (màu, logo, nút kêu gọi, nhãn pháp lý, từ cấm, màu bao bì để dò sản phẩm, từ vựng
cho Whisper, hồ sơ ngành, số liệu được phép). Dự án chọn thương hiệu bằng "thuong_hieu": "<ma>" trong cau-hinh.json
(hoặc đường dẫn tới 1 file .json). Thiếu khoá nào thì lấy từ thuong-hieu/_mau.json.

Máy: may.json ở thư mục gốc skill (không đẩy lên git) — mọi khoá đều tự dò nếu bỏ trống:
  python_whisper, eng (bộ dùng chung bo-skill-video: chỉnh màu/kiểm bản ra/luật ngành — không bắt buộc),
  u2net (mô hình tách người .onnx — không bắt buộc), sfx (thư mục tiếng nhấn), chu_capcut (true/false),
  capcut_drafts (thư mục project CapCut).
"""
import json, os, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
FONTS = SKILL / "fonts"


def _doc(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _gop(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = _gop(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def tai_thuong_hieu(project_dir=None, ma=None):
    mau = _doc(SKILL / "thuong-hieu" / "_mau.json")
    if ma is None and project_dir:
        ma = _doc(Path(project_dir) / "cau-hinh.json").get("thuong_hieu")
    if not ma:
        return mau
    p = Path(ma)
    if not p.suffix:
        p = SKILL / "thuong-hieu" / f"{ma}.json"
    elif not p.is_absolute() and project_dir:
        p = (Path(project_dir) / p) if (Path(project_dir) / p).exists() else SKILL / p
    th = _doc(p)
    if not th:
        print(f"! Không đọc được hồ sơ thương hiệu {p} -> dùng mẫu chung")
    out = _gop(mau, th)
    cfg_logo = _doc(Path(project_dir) / "cau-hinh.json").get("logo") if project_dir else None
    if cfg_logo:                       # logo riêng của dự án (đường dẫn trên máy, không đưa lên repo)
        out["logo"] = cfg_logo
    if out.get("logo") and not Path(out["logo"]).is_absolute():
        out["logo"] = str((p.parent / out["logo"]).resolve())
    return out


def tai_may():
    m = _doc(SKILL / "may.json")
    la = os.environ.get("LOCALAPPDATA", "")
    goi_y = {
        "eng": next((d for d in ("D:/bo-skill-video/shared", str(Path.home() / "bo-skill-video/shared"))
                     if Path(d, "scripts").exists()), ""),
        "u2net": str(Path.home() / ".cache/hyperframes/background-removal/models/u2net_human_seg.onnx"),
        "capcut_drafts": str(Path(la) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"),
        "chu_capcut": True,
        "techpro": str(Path.home() / ".claude/skills/techpro-video-master/scripts"),
    }
    out = _gop(goi_y, m)
    if not out.get("sfx"):
        eng_sfx = Path(out["eng"], "remotion", "public", "sfx") if out.get("eng") else None
        out["sfx"] = str(eng_sfx) if eng_sfx and eng_sfx.exists() and (eng_sfx / "pop.wav").exists() else str(SKILL / "sfx")
    return out


# nạp sẵn theo dự án đang dựng (đối số đầu của dung.py / tram / bo_cuc khi gọi từ dung.py)
_pd = next((a for a in sys.argv[1:] if not a.startswith("-") and Path(a, "cau-hinh.json").exists()), None)
_ma = sys.argv[sys.argv.index("--th") + 1] if "--th" in sys.argv[:-1] else None
TH = tai_thuong_hieu(_pd, _ma)
MAY = tai_may()
