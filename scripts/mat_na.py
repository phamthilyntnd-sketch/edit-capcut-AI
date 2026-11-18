"""MẶT NẠ CAPCUT cho CẢNH TRÁM (20/11/2026) — khung bo góc / khung tròn / chia đôi màn hình / trái tim.

Mặt nạ ghi bằng `capcut mask` (capcut-cli): mã mặt nạ (resource_id / effect_id) lấy từ `capcut enums --masks`, cấu trúc
material do capcut-cli viết theo draft CapCut thật — skill không tự bịa JSON. Cảnh trám nằm ở lớp phủ trên người nói, nên
phần ngoài mặt nạ lộ ra người nói phía dưới (thẻ sản phẩm lồng trên video người nói).

Dùng THƯA (mặc định 1 cảnh / video, theo ngành trong kho/cong-thuc.json "mat_na_toi_da"), ưu tiên cảnh cận sản phẩm
("san_pham": true) và cảnh >= 2,5s, không đặt ở 1s đầu, không 2 cảnh mặt nạ liền nhau.
Cấu hình:  "mat_na": false            tắt hẳn
           "mat_na_toi_da": 2          số cảnh có mặt nạ
           "mat_na_kieu": ["tron"]     chỉ dùng các kiểu này (bo_goc | tron | chia_doi | tim)
           broll[i]["mat_na"]: "tron" | false   ép / cấm cho 1 cảnh trám
CHƯA làm "lộ dần bằng keyframe mặt nạ": cấu trúc keyframe mặt nạ chưa ai bắt được từ draft thật (capcut-cli #44, ghi sai thì
CapCut im lặng bỏ qua) -> 'lộ dần' = mặt nạ + hoạt ảnh vào CapCut (phóng nhẹ / trượt / mờ dần) trên cùng cảnh trám.
"""
import hashlib, json, subprocess
from pathlib import Path

SK = Path(__file__).resolve().parent.parent
CT = SK / "kho" / "cong-thuc.json"


def _ct():
    try:
        return json.loads(CT.read_text(encoding="utf-8")).get("mat_na", {})
    except Exception:
        return {}


def chon(cfg, broll, phong_cach="nang_dong", hat="", basic=False):
    """-> {ref cảnh trám: tên kiểu}."""
    if basic or cfg.get("mat_na") is False:
        return {}
    ct = _ct()
    kieu_ok = ct.get("kieu", {})
    toi_da = int(cfg.get("mat_na_toi_da", 1))
    ds_kieu = [k for k in (cfg.get("mat_na_kieu") or ct.get("theo_phong_cach", {}).get(phong_cach) or ["bo_goc"])
               if k in kieu_ok]
    if not ds_kieu:
        return {}
    goc = {f"b{i}": x for i, x in enumerate(cfg.get("broll", []))}
    bs = sorted(broll, key=lambda b: b["start"])
    ep = {b["ref"]: goc[b["ref"]]["mat_na"] for b in bs if isinstance(goc.get(b["ref"], {}).get("mat_na"), str)
          and goc[b["ref"]]["mat_na"] in kieu_ok}
    if toi_da <= 0 and not ep:
        return {}
    cam = {b["ref"] for b in bs if goc.get(b["ref"], {}).get("mat_na") is False}
    ung = [b for b in bs if b["ref"] not in cam and b["ref"] not in ep and b["duration"] >= 2.5 and b["start"] >= 1.0]
    ung.sort(key=lambda b: (not goc.get(b["ref"], {}).get("san_pham"), -b["duration"]))
    lech = int(hashlib.md5(hat.encode()).hexdigest(), 16) % len(ds_kieu) if hat else 0
    out = dict(ep)
    idx = {b["ref"]: i for i, b in enumerate(bs)}
    for b in ung:
        if len(out) >= max(toi_da, len(ep)):
            break
        if any(abs(idx[b["ref"]] - idx[r]) <= 1 for r in out):   # không 2 cảnh mặt nạ liền nhau
            continue
        out[b["ref"]] = ds_kieu[(len(out) + lech) % len(ds_kieu)]
    return out


def thong_so(kieu):
    return _ct().get("kieu", {}).get(kieu, {})


def ap(draft_path, items, track="Canh tram"):
    """items: [{"start": giây, "kieu": tên}] -> `capcut mask` lên đoạn cảnh trám khớp mốc. Trả [(start, kieu, ok, lỗi)]."""
    dc = json.loads((Path(draft_path) / "draft_content.json").read_text(encoding="utf-8"))
    segs = [(sg["id"], sg["target_timerange"]["start"] / 1e6) for tr in dc["tracks"]
            if tr["type"] == "video" and tr.get("name") == track for sg in tr["segments"]]
    kq = []
    for it in items:
        hit = [sid for sid, st in segs if abs(st - it["start"]) < 0.05]
        ts = thong_so(it["kieu"])
        if not hit or not ts:
            kq.append((it["start"], it["kieu"], False, "không thấy đoạn cảnh trám"))
            continue
        cmd = ["capcut", "mask", str(draft_path), hit[0], ts["slug"], "--size", str(ts.get("size", 0.5)),
               "--center-x", str(ts.get("center_x", 0)), "--center-y", str(ts.get("center_y", 0)),
               "--feather", str(ts.get("feather", 0))]
        if ts["slug"] == "rectangle":
            cmd += ["--rect-width", str(ts.get("rect_width", ts.get("size", 0.5))),
                    "--round-corner", str(ts.get("round_corner", 0))]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", shell=True)
        kq.append((it["start"], it["kieu"], r.returncode == 0, (r.stdout + r.stderr)[-200:] if r.returncode else ""))
    return kq
