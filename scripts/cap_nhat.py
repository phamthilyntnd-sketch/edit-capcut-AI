"""Cập nhật TẠI CHỖ project CapCut đang được góp ý (người dùng: "sửa trực tiếp trong bản đang feedback, không tạo thêm").

Cách làm (không xoá gì):
  1. Bản mới đã được dựng vào thư mục tạm  <tên>__moi  (capcut compile không ghi đè project có nội dung).
  2. Bản đang xem được CHUYỂN (không xoá) sang  projects/<du-an>/_draft-cu/<tên>-<thời gian>/  -> khôi phục được.
  3. Thư mục tạm đổi về đúng tên cũ; giữ nguyên draft_id cũ để CapCut coi là cùng 1 project.
  4. root_meta_info.json (danh sách project của CapCut) được sao lưu rồi sửa: bỏ mục tạm, mục cũ trỏ sang nội dung mới.
"""
import json, os, shutil, time
from pathlib import Path


def _rewrite_paths(folder, old_name, new_name):
    """Thay tên thư mục tạm -> tên thật trong mọi file json của draft (đường dẫn dạng \\ \\\\ và /)."""
    n = 0
    for f in Path(folder).rglob("*"):
        if not f.is_file() or f.suffix.lower() not in (".json", ".tmp", ".bak") and f.name != "draft_settings":
            continue
        try:
            t = f.read_text(encoding="utf-8")
        except Exception:
            continue
        if old_name in t:
            f.write_text(t.replace(old_name, new_name), encoding="utf-8")
            n += 1
    return n


def replace_draft(drafts_dir, tmp_name, target_name, backup_root):
    drafts_dir = Path(drafts_dir)
    tmp, target = drafts_dir / tmp_name, drafts_dir / target_name
    if not tmp.is_dir():
        raise SystemExit(f"Không thấy bản tạm {tmp}")
    old_id = None
    if target.is_dir():
        try:
            old_id = json.loads((target / "draft_meta_info.json").read_text(encoding="utf-8")).get("draft_id")
        except Exception:
            old_id = None
        backup_root = Path(backup_root)
        backup_root.mkdir(parents=True, exist_ok=True)
        bak = backup_root / f"{target_name}-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.move(str(target), str(bak))
        print(f"  Bản đang xem đã chuyển sang sao lưu: {bak}")
        # người dùng 14/11: chỉ giữ BẢN SAO LƯU GẦN NHẤT (mỗi bản ~0,7 GB, ổ C: từng đầy) -> xoá các bản cũ hơn
        # của đúng project này, chỉ trong thư mục _draft-cu của dự án
        cu = sorted((d for d in backup_root.iterdir() if d.is_dir() and d.name.startswith(f"{target_name}-")
                     and d != bak), key=lambda d: d.stat().st_mtime)
        for d in cu:
            shutil.rmtree(d, ignore_errors=True)
            print(f"  Đã xoá bản sao lưu cũ: {d.name}")
    os.rename(tmp, target)
    _rewrite_paths(target, tmp_name, target_name)
    meta_f = target / "draft_meta_info.json"
    meta = json.loads(meta_f.read_text(encoding="utf-8"))
    new_id = meta.get("draft_id")
    if old_id:
        meta["draft_id"] = old_id
    meta["draft_name"] = target_name
    meta["draft_fold_path"] = str(target)
    meta_f.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    # danh sách project của CapCut
    rf = drafts_dir / "root_meta_info.json"
    if rf.exists():
        shutil.copy2(rf, drafts_dir / f"root_meta_info.json.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        root = json.loads(rf.read_text(encoding="utf-8"))
        store = root.get("all_draft_store", [])
        tmp_entry = next((e for e in store if Path(e.get("draft_fold_path", "")).name == tmp_name), None)
        old_entry = next((e for e in store if Path(e.get("draft_fold_path", "")).name == target_name), None)
        store = [e for e in store if e is not tmp_entry]
        if tmp_entry is not None:
            ent = old_entry if old_entry is not None else tmp_entry
            for k in ("tm_duration", "draft_timeline_materials_size", "tm_draft_modified"):
                if k in tmp_entry:
                    ent[k] = tmp_entry[k]
            ent.update(draft_name=target_name, draft_fold_path=str(target),
                       draft_json_file=str(target / "draft_content.json"),
                       draft_cover=str(target / "draft_cover.jpg"), draft_id=old_id or new_id)
            if old_entry is None:
                store.append(ent)
        root["all_draft_store"] = store
        if isinstance(root.get("draft_ids"), int):
            root["draft_ids"] = len(store)
        rf.write_text(json.dumps(root, ensure_ascii=False), encoding="utf-8")
    return target
