"""GHÉP NHIỀU VIDEO CỦA 1 DỰ ÁN VÀO 1 PROJECT CAPCUT (V3 — góp ý 18/11).

- Tên project = "-" + tên folder dự án, vd folder "11B17.2 -STV T11_400K" -> project "-11B17.2 -STV T11_400K".
- Các video nằm nối tiếp trên cùng timeline, NGĂN CÁCH BẰNG ĐIỂM ĐÁNH DẤU (tên điểm = mã video) để nhân sự tự xuất từng đoạn.
- Lớp: "Hinh chinh" = video thoại đã cắt vấp (giữ âm thanh gốc) · "Canh tram" = lớp phủ, tắt tiếng · chữ / tiếng nhấn ở trên.
- Ổn định âm thanh bằng chức năng CapCut (chuẩn hoá âm lượng + cải thiện giọng nói + giảm tiếng ồn) cho mọi đoạn thoại —
  chép đúng cấu trúc từ project MẪU người dùng tạo trong CapCut (mặc định tên "-MAU"; xem cap_nhat_am.py).

Chạy:
  ghep_du_an.py chia "<folder dự án>" [--lam "<thư mục làm việc>"]
      -> nhóm clip theo MÃ ở đầu tên file (vd O5_thoai.mov, O5_tram1.mov, O5 kịch bản.txt -> video "O5"),
         tạo <lam>/footage/<mã>/ (liên kết cứng, không tốn dung lượng) để chuan_bi.py chạy từng video.
  ghep_du_an.py ghep "<folder dự án>" <du-an-1> <du-an-2> ... [--lam "<thư mục làm việc>"] [--moi]
      -> mỗi du-an đã chạy  dung.py projects/<du-an> --pngs --chi-spec ; ghép spec, dựng 1 project CapCut,
         gắn hiệu ứng chữ + font, điểm đánh dấu, ổn định âm thanh. Mặc định CẬP NHẬT TẠI CHỖ project đã có.
"""
import json, os, re, shutil, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import thuong_hieu as th
import chu as tc

VIDEO = {".mov", ".mp4", ".m4v", ".mkv"}
ANH = {".jpg", ".jpeg", ".png", ".webp"}
TAI_LIEU = {".txt", ".docx", ".doc", ".md", ".pdf", ".xlsx", ".csv"}


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def ma_cua(ten):
    """Mã video = cụm đầu tên file trước dấu _ / - / khoảng trắng (O5_thoai.mov -> O5, 11B17.2-tram.mov -> 11B17.2)."""
    m = re.match(r"\s*([^_\s-]+)", Path(ten).stem)
    return m.group(1) if m else Path(ten).stem


def lien_ket(src, dst):
    if dst.exists():
        return
    try:
        os.link(src, dst)            # cùng ổ đĩa: liên kết cứng, không tốn thêm dung lượng
    except OSError:
        shutil.copy2(src, dst)


def cmd_chia(goc, lam):
    goc, lam = Path(goc), Path(lam)
    nhom = {}
    for f in sorted(goc.iterdir()):
        if f.is_file() and f.suffix.lower() in VIDEO | ANH | TAI_LIEU:
            nhom.setdefault(ma_cua(f.name), []).append(f)
    for ma, fs in nhom.items():
        if not any(f.suffix.lower() in VIDEO for f in fs):
            print(f"! Mã {ma}: không có clip video -> bỏ qua ({', '.join(f.name for f in fs)})")
            continue
        d = lam / "footage" / ma
        d.mkdir(parents=True, exist_ok=True)
        for f in fs:
            lien_ket(f, d / f.name)
        print(f"{ma}: " + ", ".join(f.name for f in fs))
    print(f"\nĐã chia vào {lam / 'footage'} — chạy chuan_bi.py footage cho từng mã.")


def doc(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def cmd_ghep(goc, du_an, lam, moi=False):
    goc, lam = Path(goc), Path(lam)
    ten = "-" + goc.name.strip()
    drafts = th.MAY["capcut_drafts"]
    tracks, ops, hk_all, marks, t0, vids = {}, [], [], [], 0.0, []
    for k, da in enumerate(du_an):
        P = lam / "projects" / da
        sp, hk = doc(P / "spec.json"), doc(P / "hau-ky.json")
        pre = f"v{k}_"
        marks.append({"t": t0, "ten": doc(P / "cau-hinh.json").get("ma") or da})
        for tr in sp["tracks"]:
            key = (tr["type"], tr["name"])
            if key not in tracks:
                tracks[key] = {"type": tr["type"], "name": tr["name"], "items": []}
            for it in tr["items"]:
                it = dict(it, start=round(it["start"] + t0, 6), ref=pre + it["ref"])
                tracks[key]["items"].append(it)
        for op in sp.get("operations", []):
            op = dict(op)
            if "target" in op:
                op["target"] = pre + op["target"]
            if op.get("op") == "effect":
                op["start"] = round(op["start"] + t0, 6)
            ops.append(op)
        for n in hk["nhan"]:
            hk_all.append(dict(n, a=n["a"] + t0, P=str(P)))
        vids += [dict(v, start=v["start"] + t0) for v in hk.get("video", [])]
        hk_all += [{"thumb": t, "w": w, "P": str(P)} for t, w in hk.get("thumb_font", {}).items()]
        t0 = round(t0 + hk["total"], 6)
    # thứ tự lớp: video chính dưới cùng, cảnh trám, rồi chữ / ảnh, âm thanh
    ds = sorted(tracks.values(), key=lambda t: (t["type"] != "video", t["name"] != "Hinh chinh", t["name"] != "Canh tram"))
    spec = {"name": ten + "__moi", "width": 1080, "height": 1920, "fps": 30, "tracks": ds, "operations": ops}
    sp = lam / f"spec-du-an.json"
    sp.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    if "CapCut.exe" in run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe"]).stdout:
        raise SystemExit("CapCut đang mở -> đóng hẳn CapCut rồi chạy lại")
    dang = (Path(drafts) / ten).is_dir() and not moi
    if not dang:
        spec["name"] = ten
        sp.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    elif (Path(drafts) / (ten + "__moi")).exists():
        shutil.move(str(Path(drafts) / (ten + "__moi")), str(lam / f"_draft-cu-{ten}__moi-sot"))
    r = run(["capcut", "compile", str(sp), "--drafts", drafts, "--template", "auto"], shell=True)
    if r.returncode:
        print(r.stdout[-1500:], r.stderr[-1500:])
        raise SystemExit("capcut compile lỗi")
    dp = json.loads(r.stdout)["draft_path"]
    # chữ CapCut: font Be Vietnam Pro + hiệu ứng chữ vào/ra
    fp = tc.project_font(lam, 600)
    if fp:
        by_text = {}
        for n in hk_all:
            if "text" in n:
                by_text[n["text"]] = (tc.project_font(lam, n["w"]) or fp, tc.FONT_TEN[n["w"]])
            elif "thumb" in n:
                by_text[n["thumb"]] = (tc.project_font(lam, n["w"]) or fp, tc.FONT_TEN[n["w"]])
        tc.patch_fonts(dp, fp, by_text)
    dc = doc(Path(dp) / "draft_content.json")
    mat = {t["id"]: json.loads(t["content"]).get("text", "") for t in dc["materials"].get("texts", [])}
    segs_t = [(sg["id"], mat.get(sg["material_id"], ""), sg["target_timerange"]["start"] / 1e6)
              for tr in dc["tracks"] if tr["type"] == "text" for sg in tr["segments"]]
    na = 0
    for n in (x for x in hk_all if "text" in x):
        hit = [sid for sid, tx, st in segs_t if tx == n["text"] and abs(st - n["a"]) < 0.05]
        if not hit:
            continue
        cmd = ["capcut", "text-anim", dp, hit[0], "--intro", n["vao"], "--intro-duration", f"{min(n['vd'], n['dur'] / 3):.2f}"]
        if n["dur"] > 1.2:
            cmd += ["--outro", n["ra"], "--outro-duration", f"{min(n['rd'], n['dur'] / 4):.2f}"]
        na += run(cmd, shell=True).returncode == 0
    import hau_ky
    nv = hau_ky.ap_video_anim(dp, vids)
    run(["capcut", "lint", dp, "--fix"], shell=True)
    if fp:
        tc.patch_fonts(dp, fp, by_text)
    # điểm đánh dấu + ổn định âm thanh (chép cấu trúc từ project mẫu CapCut)
    import cap_nhat_am as ca
    so_mark = ca.diem_danh_dau(dp, marks)
    so_doan = ca.on_dinh_am(dp, track_name="Hinh chinh")
    run(["capcut", "sync-timelines", dp, "--apply"], shell=True)   # đồng bộ các bản sao timeline CapCut đọc
    if dang:
        import cap_nhat as cn
        dp = str(cn.replace_draft(drafts, ten + "__moi", ten, lam / "_draft-cu"))
        print(f"Đã cập nhật TẠI CHỖ project \"{ten}\"")
    lint = run(["capcut", "lint", dp, "-H"], shell=True)
    print(f"Project CapCut: {ten} · {len(du_an)} video · tổng {t0:.1f}s · hiệu ứng chữ {na} · hoạt ảnh cảnh trám {nv}/{len(vids)} · điểm đánh dấu {so_mark}/{len(marks)}"
          f" · ổn định âm thanh {so_doan} đoạn")
    for m in marks:
        print(f"  ▸ {m['t']:7.2f}s  {m['ten']}")
    print(lint.stdout.strip()[-800:] or "lint sạch")


if __name__ == "__main__":
    a = sys.argv[1:]
    lam = a[a.index("--lam") + 1] if "--lam" in a else None
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] != "--lam")]
    if pos[0] == "chia":
        cmd_chia(pos[1], lam or str(Path(pos[1]) / "_lam"))
    elif pos[0] == "ghep":
        cmd_ghep(pos[1], pos[2:], lam or str(Path(pos[1]) / "_lam"), moi="--moi" in a)
    else:
        print(__doc__)
