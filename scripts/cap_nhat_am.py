"""Ổn định âm thanh + điểm đánh dấu bằng CHỨC NĂNG CỦA CAPCUT (V3 — góp ý 18/11), chép đúng cấu trúc từ PROJECT MẪU.

capcut-cli không có lệnh bật "Chuẩn hoá âm lượng / Cải thiện giọng nói / Giảm tiếng ồn" hay đặt "điểm đánh dấu", và cấu
trúc dữ liệu của các mục này đổi theo phiên bản CapCut. Vì vậy skill CHÉP từ 1 project mẫu người dùng tự tạo trong CapCut
(cùng phiên bản CapCut của máy):
    project tên "-MAU" (đổi được bằng may.json "mau_capcut"), 1 clip có người nói, đã BẬT 3 mục âm thanh trên clip đó
    và đặt 1 điểm đánh dấu trên timeline.
Không có project mẫu -> bỏ qua 2 việc này và in hướng dẫn (nhân sự bấm tay trong CapCut).
"""
import copy, json, uuid
from pathlib import Path

import thuong_hieu as th


def _doc(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _mau():
    ten = th.MAY.get("mau_capcut", "-MAU")
    p = Path(th.MAY["capcut_drafts"]) / ten / "draft_content.json"
    if not p.exists():
        print(f"! Chưa có project mẫu \"{ten}\" trong CapCut -> chưa tự bật chuẩn hoá âm lượng / cải thiện giọng / giảm ồn"
              f" và điểm đánh dấu. Tạo project mẫu theo SKILL.md (mục V3) rồi chạy lại.")
        return None
    return _doc(p)


def _id():
    return str(uuid.uuid4()).upper()


def _tim_list(materials, mid):
    for k, v in materials.items():
        if isinstance(v, list) and any(isinstance(x, dict) and x.get("id") == mid for x in v):
            return k
    return None


def _ghi(dp, dc):
    """Ghi draft_content.json + bản sao timeline mà CapCut đọc (template-2.tmp nếu có)."""
    for f in [Path(dp) / "draft_content.json"] + list(Path(dp).glob("template-2.tmp")):
        f.write_text(json.dumps(dc, ensure_ascii=False), encoding="utf-8")


def on_dinh_am(dp, track_name="Hinh chinh"):
    """Bật trên MỌI đoạn của track video chính đúng những hiệu ứng âm thanh có trong đoạn mẫu. Trả số đoạn đã bật."""
    mau = _mau()
    if mau is None:
        return 0
    vtr = [t for t in mau["tracks"] if t["type"] == "video" and t.get("segments")]
    if not vtr:
        return 0
    sm = vtr[0]["segments"][0]
    lists = {}
    for rid in sm.get("extra_material_refs", []):
        k = _tim_list(mau["materials"], rid)
        if k and any(w in k for w in ("loud", "vocal", "denois", "noise", "enhanc", "voice")):
            lists.setdefault(k, []).append(next(x for x in mau["materials"][k] if x["id"] == rid))
    fa_mau = mau.get("function_assistant_info", {})
    seg_lists = [k for k, v in fa_mau.items() if isinstance(v, list) and sm["id"] in v]
    flags = {k: v for k, v in fa_mau.items() if isinstance(v, bool) and v}
    if not lists and not seg_lists:
        print("! Project mẫu chưa bật mục âm thanh nào trên clip đầu tiên -> bỏ qua")
        return 0
    dc = _doc(Path(dp) / "draft_content.json")
    n = 0
    for tr in dc["tracks"]:
        if tr["type"] != "video" or tr.get("name") not in (track_name, None, ""):
            continue
        if tr.get("name") != track_name and any(t.get("name") == track_name for t in dc["tracks"]):
            continue
        for sg in tr["segments"]:
            for k, items in lists.items():
                for it in items:
                    moi = copy.deepcopy(it)
                    moi["id"] = _id()
                    if isinstance(moi.get("time_range"), dict):
                        moi["time_range"] = dict(sg["source_timerange"])
                    dc["materials"].setdefault(k, []).append(moi)
                    sg.setdefault("extra_material_refs", []).append(moi["id"])
            fa = dc.setdefault("function_assistant_info", {})
            for k in seg_lists:
                fa.setdefault(k, [])
                if sg["id"] not in fa[k]:
                    fa[k].append(sg["id"])
            n += 1
        break
    dc.setdefault("function_assistant_info", {}).update(flags)
    _ghi(dp, dc)
    return n


def diem_danh_dau(dp, marks):
    """marks: [{"t": giây, "ten": nhãn}] -> điểm đánh dấu trên timeline, chép dạng từ project mẫu."""
    mau = _mau()
    if mau is None or not marks:
        return 0
    tm = mau.get("time_marks")
    items = (tm or {}).get("mark_items") if isinstance(tm, dict) else None
    if not items:
        print("! Project mẫu chưa có điểm đánh dấu (phím M trong CapCut) -> bỏ qua điểm đánh dấu")
        return 0
    mau_item = items[0]
    dc = _doc(Path(dp) / "draft_content.json")
    out = copy.deepcopy(tm)
    out["mark_items"] = []
    for m in marks:
        it = copy.deepcopy(mau_item)
        it["id"] = _id()
        if isinstance(it.get("time_range"), dict):
            it["time_range"] = dict(it["time_range"], start=int(round(m["t"] * 1e6)))
        for k in ("title", "name", "text", "content"):
            if k in it:
                it[k] = m["ten"]
        out["mark_items"].append(it)
    dc["time_marks"] = out
    _ghi(dp, dc)
    return len(marks)
