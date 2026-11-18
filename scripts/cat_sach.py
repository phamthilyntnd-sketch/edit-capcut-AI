"""CẮT SẠCH (nâng cấp cắt vấp, 19/11/2026) — nói sai nói lại, nói vấp / lắp, tiếng ậm ừ, khoảng trống.

Chạy (python của skill, -I):
  cat_sach.py <du-an> [--tu <giây>] [--den <giây>] [--hoi-thoai] [--khong-nghe-lai]
      -> phân tích, ghi cat/de-xuat.json + cat/bang-cat.md (AI ĐỌC LẠI, sửa "giu" từng câu nếu cần)
  cat_sach.py <du-an> --duyet   -> cat/duyet.html: từng chỗ cắt có nút nghe TRƯỚC / SAU, bấm Cắt / Giữ lại, tải duyet.json
  cat_sach.py <du-an> --chot    -> ghi "keeps" + "cat_tieng" vào cau-hinh.json (áp sửa trong de-xuat.json + cat/duyet.json)
  cat_sach.py <du-an> --kiem    -> dựng tiếng bản đã cắt (đúng điểm cắt thật của dung.py), NGHE LẠI, tự sửa chỗ còn sót
                                   (lặp, ậm ừ, tiếng không thành chữ), chốt lại; tối đa 2 vòng -> cat/kiem.md

6 phần:
  1. KHỚP KỊCH BẢN (kich-ban.txt trong dự án, hoặc cau-hinh "kich_ban"): mỗi câu kịch bản giữ LẦN NÓI ĐẦY ĐỦ CUỐI CÙNG;
     các lần nói khác (kể cả nói lại bằng câu chữ khác) và lời ngoài lề ngắn -> bỏ. Không có kịch bản: bỏ qua phần này.
  2. BẢNG ĐỌC LẠI (cat/bang-cat.md): AI đọc như người dựng, sửa "giu" trong de-xuat.json trước khi --chot.
  3. DÒ BẰNG TIẾNG THẬT: (a) từ dài bất thường (Whisper nuốt chỗ vấp) -> nghe lại riêng khúc đó;
     (b) vùng có tiếng mà không có chữ nào (ậm ừ, lắp, nói dở bị Whisper bỏ) -> cắt; (c) 1 từ có 2 cụm tiếng tách bởi
     khoảng lặng, cụm đầu ngắn ("sả… sản") -> cắt cụm đầu. Ghi vào cau-hinh "cat_tieng" (dung.py cắt cứng).
  4. KHOẢNG TRỐNG: dung.py tự chừa theo nhịp người nói + làm mờ tiếng ở mỗi vết cắt (cả MP4 và CapCut).
  5. TỰ KIỂM: --kiem.
  6. TRANG DUYỆT: --duyet.
Vẫn dùng toàn bộ luật cũ của cat_vap.py (nói sai rồi nói lại, tiếng đệm, câu trùng, mảnh lẻ, Whisper bịa).
"""
import base64, contextlib, difflib, io, json, os, re, subprocess, sys, unicodedata
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cat_vap  # noqa: E402

HOP = 0.01
DAU_CAU = ("câu lẻ ngắn", "nói lại (lần sau", "lời chen giữa")   # luật cấp CÂU — kịch bản được ưu tiên hơn
# ("câu trùng ý" KHÔNG gỡ: kịch bản lặp ý thì người dựng vẫn bỏ câu nói trùng — đo T-5 so với bản cắt tay)


def run(cmd):
    return subprocess.run(cmd, capture_output=True)


def bo_dau(s):
    s = unicodedata.normalize("NFD", s.lower()).replace("đ", "d")
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def toks(text):
    return [bo_dau(t) for t in re.findall(r"\w+", text.lower())]


def doc_am(path):
    r = run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"])
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768.0


def env_db(x):
    n = len(x) // 160
    db = 20 * np.log10(np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1)) + 1e-6)
    f, sp = np.percentile(db, 10), np.percentile(db, 90)
    return db, f + 0.35 * (sp - f)


# ---------------------------------------------------------------- dự án
def du_an(P):
    cfg = json.loads((P / "cau-hinh.json").read_text(encoding="utf-8"))
    mp4 = P / "raw" / cfg["aroll"]
    wav = mp4.with_suffix(".wav")
    if not wav.exists():
        run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
    return cfg, mp4, wav


_MODEL = {}


def nghe(am, moi=True):
    """faster-whisper large-v3-turbo, NGUYÊN VĂN (câu mồi kiểu nói vấp), mốc từng từ."""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    if "m" not in _MODEL:
        from faster_whisper import WhisperModel
        _MODEL["m"] = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    try:
        import thuong_hieu as th
        tv = th.TH.get("tu_vung", "")
    except Exception:
        tv = ""
    MOI = "Ờ, ừm… thì, thì cái này… à không, cái này rất là… rất là tốt, dạ dạ. "
    sg, _ = _MODEL["m"].transcribe(am, language="vi", word_timestamps=True, vad_filter=False,
                                   condition_on_previous_text=False, initial_prompt=(MOI if moi else "") + tv + ".")
    return [{"start": s.start, "end": s.end, "text": s.text, "words": [{"w": w.word, "s": w.start, "e": w.end} for w in (s.words or [])]}
            for s in sg]


def nghe_lai_cuc_bo(segs, am, tu, den, cache=None):
    """Phần 3a: từ dài bất thường (> 1s, ngắn chữ) = Whisper nuốt chỗ vấp / khoảng lặng -> nghe lại RIÊNG khúc đó."""
    # nghe lại TRỌN câu (segment Whisper) chứa từ khả nghi: ranh giới câu nằm ở chỗ ngừng nói -> không cắt giữa tiếng,
    # thay toàn bộ chữ của câu đó (tránh chồng chữ cũ / mới ở mép khúc)
    doi = 0
    for gi, sg in enumerate(segs):
        ws = sg.get("words", [])
        if not ws or not any(tu <= w["s"] <= den and w["e"] - w["s"] > 1.0 and len(cat_vap.norm(w["w"])) <= 7 for w in ws):
            continue
        truoc = segs[gi - 1]["words"][-1]["e"] if gi and segs[gi - 1].get("words") else 0.0
        sau = segs[gi + 1]["words"][0]["s"] if gi + 1 < len(segs) and segs[gi + 1].get("words") else len(am) / 16000
        a, b = max(truoc, ws[0]["s"] - 0.3), min(sau, ws[-1]["e"] + 0.3)
        key = f"{a:.2f}-{b:.2f}"
        kho = json.loads(cache.read_text(encoding="utf-8")) if cache and cache.exists() else {}
        if key in kho:
            moi = kho[key]
        else:
            moi = [w for s in nghe(am[int(a * 16000):int(b * 16000)]) for w in s["words"]]
            moi = [dict(w, s=round(w["s"] + a, 3), e=round(w["e"] + a, 3)) for w in moi if cat_vap.norm(w["w"])]
            if cache:
                kho[key] = moi
                cache.write_text(json.dumps(kho, ensure_ascii=False), encoding="utf-8")
        dai_cu = sum(w["e"] - w["s"] > 1.0 for w in ws)
        dai_moi = sum(w["e"] - w["s"] > 1.0 for w in moi)
        if not moi or len(moi) > 3 * len(ws) + 4 or len(moi) < 0.6 * len(ws) or dai_moi >= dai_cu:
            print(f"  nghe lại {a:.1f}–{b:.1f}s: không tốt hơn bản cũ, giữ nguyên")
            continue
        sg["words"] = moi
        sg["text"] = " ".join(w["w"].strip() for w in moi)
        doi += 1
        print(f"  nghe lại {a:.1f}–{b:.1f}s: {sg['text']}")
    return doi


# ---------------------------------------------------------------- phần 1: kịch bản
def doc_kich_ban(P, cfg):
    kb = cfg.get("kich_ban")
    if kb and Path(str(kb)).exists():
        kb = Path(kb).read_text(encoding="utf-8")
    elif not kb and (P / "kich-ban.txt").exists():
        kb = (P / "kich-ban.txt").read_text(encoding="utf-8")
    if not kb:
        return []
    cau = [c.strip() for c in re.split(r"[.!?…\n]+", kb) if len(toks(c)) >= 3]
    return cau


def khop(S, T):
    if not S or not T:
        return 0.0, 0.0
    m = sum(b.size for b in difflib.SequenceMatcher(None, S, T, autojunk=False).get_matching_blocks())
    return m / len(S), m / len(T)


def khop_kich_ban(W, cau, tu_):
    """-> (chọn: {đơn vị: câu kịch bản}, quyết định bỏ {đơn vị: lý do}, báo cáo từng câu kịch bản, đơn vị)."""
    U, cur = [], [0]
    for k in range(1, len(W)):
        if W[k]["s"] - W[k - 1]["e"] >= 0.5 or W[k]["g"] != W[k - 1]["g"]:
            U.append((cur[0], k - 1)); cur = [k]
        else:
            pass
    if W:
        U.append((cur[0], len(W) - 1))
    UT = [[tu_[k] for k in range(a, b + 1)] for a, b in U]
    chon, bao, keo = {}, [], []
    het = -1.0
    for j, c in enumerate(cau):
        S = toks(c)
        cand = []
        for u in range(len(U)):
            T = []
            for L in range(1, 5):
                if u + L > len(U):
                    break
                T = T + UT[u + L - 1]
                r, p = khop(S, T)
                if r >= 0.5:
                    f = 2 * r * p / (r + p)
                    cand.append((u, u + L - 1, r, p, f, W[U[u][0]]["s"]))
        du = [c_ for c_ in cand if c_[2] >= 0.8 and c_[3] >= 0.55]
        if du:
            sau = [c_ for c_ in du if c_[5] >= het - 0.1] or du
            moc = max(c_[5] for c_ in sau)                       # lần nói ĐẦY ĐỦ MUỘN NHẤT
            gan = [c_ for c_ in sau if c_[5] >= moc - 4.0]       # các cách gom quanh lần đó: lấy khớp nhất
            best = max(gan, key=lambda c_: (c_[4], c_[5]))
        elif cand:
            best = max(cand, key=lambda c_: (round(c_[2], 2), c_[5]))
        else:
            bao.append((j, c, None, 0.0)); continue
        u0, u1, r, p, f, t = best
        for u in range(u0, u1 + 1):
            chon.setdefault(u, j)
        # đầu lần nói được chọn THIẾU chữ đầu câu kịch bản mà chữ đó nằm ngay cuối đơn vị trước (Whisper gán lệch) -> kéo vào
        k0 = U[u0][0]
        dau = [x for x in S[:3]]
        if k0 > 0 and dau and tu_[k0] != dau[0]:
            for n_ in (1, 2):
                if k0 - n_ >= 0 and [tu_[k] for k in range(k0 - n_, k0)] == dau[:n_] and W[k0]["s"] - W[k0 - n_]["e"] < 2.0:
                    keo.extend(range(k0 - n_, k0))
                    break
        het = max(het, W[U[u1][1]]["e"])
        bao.append((j, c, (u0, u1), r))
    quyet = {}
    if chon:
        dau, cuoi = min(chon), max(chon)
        for u, (a, b) in enumerate(U):
            if u in chon:
                continue
            T = UT[u]
            pmax = max((khop(toks(c), T)[1] for c in cau), default=0)
            dai = W[b]["e"] - W[a]["s"]
            if u < dau or u > cuoi:
                quyet[u] = "ngoài kịch bản (trước câu đầu / sau câu cuối)"
            elif pmax >= 0.4:
                quyet[u] = "lần nói khác của câu kịch bản — giữ lần đầy đủ cuối"
            else:
                ke = [v for v in chon if abs(v - u) == 1]
                sat = any((W[U[v][0]]["s"] - W[b]["e"] if v > u else W[a]["s"] - W[U[v][1]]["e"]) < 0.6 for v in ke)
                if sat and dai >= 1.0:
                    quyet[u] = None          # lời thêm dính liền câu kịch bản: giữ, đánh dấu xem lại
                else:
                    quyet[u] = "lời ngoài kịch bản (ngắn / tách rời)"
    return chon, quyet, bao, U, keo


# ---------------------------------------------------------------- phần 3: dò bằng tiếng thật
def do_tieng(W, bo, db, thr, tu, den):
    vung = []
    co = db > thr
    i, n = 0, len(db)
    runs = []
    while i < n:
        if co[i]:
            j = i
            while j < n and (co[j] or (j + 5 < n and co[j:j + 5].any())):
                j += 1
            runs.append((i * HOP, j * HOP)); i = j
        else:
            i += 1
    giu = [w for k, w in enumerate(W) if not bo[k]]
    if not giu:
        return vung
    lo, hi = giu[0]["s"], giu[-1]["e"]
    for a, b in runs:
        if b - a < 0.25 or a < max(lo, tu) or b > min(hi, den):
            continue
        if any(w["s"] - 0.05 < b and w["e"] + 0.05 > a for w in W):
            continue
        truoc = [k for k, w in enumerate(W) if w["e"] <= a]
        sau = [k for k, w in enumerate(W) if w["s"] >= b]
        if truoc and sau and not bo[truoc[-1]] and not bo[sau[0]]:
            vung.append({"a": round(a - 0.02, 2), "b": round(b + 0.02, 2), "ly_do": "tiếng không thành chữ (ậm ừ / vấp)"})
    for k, w in enumerate(W):   # 1 từ (tiếng Việt 1 âm tiết) mà có 2 cụm tiếng tách bởi lặng, cụm đầu ngắn = lắp
        if bo[k] or w["e"] - w["s"] <= 0.6:
            continue
        i0, i1 = int(w["s"] / HOP), int(w["e"] / HOP)
        seg = co[i0:i1]
        if seg.size < 10:
            continue
        on = np.where(seg)[0]
        if on.size == 0:
            continue
        first_on = on[0]
        lang = next((t for t in range(first_on, seg.size - 6) if not seg[t:t + 6].any()), None)
        if lang is None:
            continue
        lai = next((t for t in range(lang + 6, seg.size) if seg[t]), None)
        if lai is None:
            continue
        cum1 = (lang - first_on) * HOP
        cum2 = seg[lai:].sum() * HOP
        if 0.06 <= cum1 < 0.35 and cum2 > 0.45:
            # cụm sau DÀI (ậm ừ / kéo dài tiếng "em… ờờ") -> chữ thật là cụm đầu, cắt phần kéo dài phía sau
            vung.append({"a": round(w["s"] + (lang + 2) * HOP, 2), "b": round(w["e"] + 0.01, 2),
                         "ly_do": f"kéo dài / ậm ừ sau từ «{w['w'].strip()}» ({cum2:.2f}s)"})
        elif 0.06 <= cum1 < 0.35 and cum2 >= 0.15:
            vung.append({"a": round(w["s"] - 0.02, 2), "b": round(w["s"] + (lai - 2) * HOP, 2),
                         "ly_do": f"lắp trong từ «{w['w'].strip()}» (cụm tiếng đầu {cum1:.2f}s)"})
    return vung


# ---------------------------------------------------------------- keeps
def tinh_keeps(W, bo, tu=0.0):
    keeps, cur = [], None
    for i, w in enumerate(W):
        if bo[i]:
            if cur:
                keeps.append(cur); cur = None
            continue
        if cur and w["s"] - cur[1] > 1.2:
            keeps.append(cur); cur = None
        lo = W[i - 1]["e"] + 0.01 if i and bo[i - 1] else tu
        hi = W[i + 1]["s"] - 0.01 if i + 1 < len(W) and bo[i + 1] else 1e9
        if cur is None:
            cur = [round(max(lo, w["s"] - 0.12), 2), round(min(hi, w["e"] + 0.15), 2)]
        else:
            cur[1] = round(min(hi, w["e"] + 0.15), 2)
    if cur:
        keeps.append(cur)
    return keeps


def cho_cat(W, bo, ly_do, cat_tieng):
    """Danh sách chỗ cắt (để duyệt): dải từ bị bỏ liền nhau + vùng cắt bằng tiếng."""
    out, k = [], 0
    while k < len(W):
        if bo[k]:
            j = k
            while j + 1 < len(W) and bo[j + 1] and W[j + 1]["s"] - W[j]["e"] < 0.6:
                j += 1
            ld = sorted({ly_do.get(x, "") for x in range(k, j + 1)} - {""})
            out.append({"id": f"c{len(out) + 1}", "loai": "tu", "k0": k, "k1": j, "a": W[k]["s"], "b": W[j]["e"],
                        "text": " ".join(W[x]["w"].strip() for x in range(k, j + 1)), "ly_do": "; ".join(ld)})
            k = j + 1
        else:
            k += 1
    for v in cat_tieng:
        out.append({"id": f"c{len(out) + 1}", "loai": "tieng", "a": v["a"], "b": v["b"], "text": "(tiếng)", "ly_do": v["ly_do"]})
    out = sorted(out, key=lambda c: c["a"])
    for i, c in enumerate(out, 1):
        c["id"] = f"c{i}"
    return out


# ---------------------------------------------------------------- phân tích
def phan_tich(P, argv):
    cfg, mp4, wav = du_an(P)
    tu = float(argv[argv.index("--tu") + 1]) if "--tu" in argv else 0.0
    den = float(argv[argv.index("--den") + 1]) if "--den" in argv else 1e9
    segs = json.loads((P / "transcript.json").read_text(encoding="utf-8"))
    am = doc_am(wav)
    (P / "cat").mkdir(exist_ok=True)
    if "--khong-nghe-lai" not in argv:
        print("== Phần 3a: nghe lại riêng các từ dài bất thường (Whisper nuốt chỗ vấp)")
        n = nghe_lai_cuc_bo(segs, am, tu, den, P / "cat" / "nghe-lai.json")
        print(f"  {n} khúc đã nghe lại")
    db, thr = env_db(am)
    co = db > thr
    siet = 0
    for sg in segs:   # SIẾT MỐC TỪ theo tiếng thật: Whisper hay kéo từ phủ cả chỗ ngừng -> mất dấu nhịp ngập ngừng
        for w in sg.get("words", []):
            i0, i1 = int(w["s"] / HOP), int(w["e"] / HOP)
            on = np.where(co[i0:i1])[0]
            if on.size == 0 or i1 - i0 < 20:
                continue
            s_, e_ = w["s"], w["e"]
            if on[0] >= 15:
                s_ = (i0 + on[0] - 3) * HOP
            if (i1 - i0) - on[-1] >= 15:
                e_ = (i0 + on[-1] + 4) * HOP
            if (s_, e_) != (w["s"], w["e"]) and e_ - s_ >= 0.06:
                w["s"], w["e"] = round(s_, 3), round(e_, 3)
                siet += 1
    print(f"== Siết mốc {siet} từ theo tiếng thật")
    (P / "cat" / "transcript-sach.json").write_text(json.dumps(segs, ensure_ascii=False), encoding="utf-8")
    pass_ = [a for a in argv if a in ("--hoi-thoai",)]
    if "--tu" in argv:
        pass_ += ["--tu", str(tu)]
    if "--den" in argv:
        pass_ += ["--den", str(den)]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        W, bo, ly_do, _ = cat_vap.main([str(P)] + pass_, segs=segs, tra_ve=True)
    tu_ = [bo_dau(w["n"]) for w in W]
    cau = doc_kich_ban(P, cfg)
    chon, quyet, bao, U, keo = ({}, {}, [], [], [])
    if cau and not ("--hoi-thoai" in argv or cfg.get("hoi_thoai")):
        chon, quyet, bao, U, keo = khop_kich_ban(W, cau, tu_)
        for u, (a, b) in enumerate(U):
            if u in chon:     # câu khớp kịch bản: gỡ các luật cấp câu của cat_vap (vd "câu lẻ ngắn") — giữ luật cấp từ
                for k in range(a, b + 1):
                    if bo[k] and ly_do.get(k, "").startswith(DAU_CAU):
                        bo[k] = False; ly_do.pop(k, None)
            elif quyet.get(u):
                for k in range(a, b + 1):
                    if not bo[k]:
                        bo[k] = True; ly_do[k] = quyet[u]
        for k in keo:     # chữ đầu câu bị gán lệch: giữ, và đặt sát ngay trước chữ kế (mốc Whisper lệch vào chỗ ngừng)
            bo[k] = False; ly_do.pop(k, None)
            nx = W[k + 1]
            if nx["s"] - W[k]["e"] > 0.3:
                W[k]["s"], W[k]["e"] = round(nx["s"] - 0.32, 3), round(nx["s"] - 0.02, 3)
    elif cau:
        print("(hội thoại: không khớp kịch bản từng câu — chỉ dùng luật cat_vap)")
    else:
        print("! Chưa có kịch bản (kich-ban.txt / cau-hinh \"kich_ban\") — bỏ qua phần khớp kịch bản")
    cat_tieng = do_tieng(W, bo, db, thr, tu, den)
    if not U:
        U, cur = [], 0
        for k in range(1, len(W) + 1):
            if k == len(W) or W[k]["s"] - W[k - 1]["e"] >= 0.5 or W[k]["g"] != W[k - 1]["g"]:
                U.append((cur, k - 1)); cur = k
    don_vi = []
    for u, (a, b) in enumerate(U):
        nb = sum(bo[k] for k in range(a, b + 1))
        don_vi.append({"id": u + 1, "a": round(W[a]["s"], 2), "b": round(W[b]["e"], 2),
                       "text": " ".join(("~~" + W[k]["w"].strip() + "~~") if bo[k] else W[k]["w"].strip() for k in range(a, b + 1)),
                       "giu": "bo" if nb == b - a + 1 else ("giu" if nb == 0 else "mot_phan"),
                       "kich_ban": (chon[u] + 1) if u in chon else None,
                       "xem_lai": u in quyet and quyet[u] is None,
                       "ly_do": sorted({ly_do[k] for k in range(a, b + 1) if k in ly_do}), "k0": a, "k1": b})
    cuts = cho_cat(W, bo, ly_do, cat_tieng)
    dx = {"tu": tu, "don_vi": don_vi, "cat_tieng": cat_tieng, "cuts": cuts,
          "W": [{"w": w["w"], "s": w["s"], "e": w["e"], "bo": bo[k], "ly_do": ly_do.get(k, "")} for k, w in enumerate(W)],
          "kich_ban": [{"cau": j + 1, "text": c, "don_vi": (r[0] + 1, r[1] + 1) if r else None, "do_khop": round(rr, 2)}
                       for j, c, r, rr in bao]}
    (P / "cat" / "de-xuat.json").write_text(json.dumps(dx, ensure_ascii=False, indent=1), encoding="utf-8")
    ghi_bang(P, dx)
    keeps = tinh_keeps(W, bo, tu)
    giu_s = sum(w["e"] - w["s"] for k, w in enumerate(W) if not bo[k])
    print(f"== Đơn vị lời: {len(don_vi)} · giữ {sum(d['giu'] != 'bo' for d in don_vi)} · bỏ trọn {sum(d['giu'] == 'bo' for d in don_vi)}"
          f" · chỗ cắt bằng tiếng {len(cat_tieng)} · lời giữ ~{giu_s:.1f}s trong {len(keeps)} đoạn")
    if bao:
        thieu = [b_ for b_ in bao if not b_[2] or b_[3] < 0.8]
        print(f"== Kịch bản: {len(bao)} câu, khớp đầy đủ {len(bao) - len(thieu)}" + (f", CHƯA ĐỦ: {', '.join(str(b_[0] + 1) for b_ in thieu)}" if thieu else ""))
    print(f"-> ĐỌC {P / 'cat' / 'bang-cat.md'} ; sửa \"giu\" trong cat/de-xuat.json nếu cần ; rồi --duyet (tuỳ chọn) và --chot")


def ghi_bang(P, dx):
    L = ["# Bảng cắt — AI đọc lại như người dựng trước khi chốt", "",
         "Sửa trong `cat/de-xuat.json` -> `don_vi[].giu`: `giu` (giữ trọn) · `bo` (bỏ trọn) · `mot_phan` (theo từng từ: chữ ~~gạch~~ là bỏ).",
         "Soát: câu bỏ dở không lặp chữ nào · nói lại bằng câu khác · lời ngoài lề · câu kịch bản bị THIẾU · chỗ cắt giữa câu làm mất nghĩa.", ""]
    if dx["kich_ban"]:
        L += ["## Kịch bản -> đơn vị lời đã chọn", ""]
        for c in dx["kich_ban"]:
            L.append(f"- câu {c['cau']} ({c['do_khop']:.0%}) -> {('đơn vị ' + str(c['don_vi'][0]) + '–' + str(c['don_vi'][1])) if c['don_vi'] else '**KHÔNG THẤY**'}: {c['text'][:80]}")
        L.append("")
    L += ["## Từng đơn vị lời", "", "| # | giây | quyết định | lời (~~bỏ~~) | lý do |", "|---|---|---|---|---|"]
    for d in dx["don_vi"]:
        q = {"giu": "GIỮ", "bo": "**BỎ**", "mot_phan": "1 phần"}[d["giu"]] + (" ⚠xem" if d["xem_lai"] else "") + (f" (kb {d['kich_ban']})" if d["kich_ban"] else "")
        L.append(f"| {d['id']} | {d['a']:.1f}–{d['b']:.1f} | {q} | {d['text']} | {'; '.join(d['ly_do'])} |")
    if dx["cat_tieng"]:
        L += ["", "## Cắt bằng tiếng (không có chữ)", ""] + [f"- {v['a']:.2f}–{v['b']:.2f}s: {v['ly_do']}" for v in dx["cat_tieng"]]
    (P / "cat" / "bang-cat.md").write_text("\n".join(L), encoding="utf-8")


# ---------------------------------------------------------------- chốt
def ap_sua(P):
    dx = json.loads((P / "cat" / "de-xuat.json").read_text(encoding="utf-8"))
    W = dx["W"]
    bo = [w["bo"] for w in W]
    for d in dx["don_vi"]:
        if d["giu"] in ("giu", "bo"):
            for k in range(d["k0"], d["k1"] + 1):
                bo[k] = d["giu"] == "bo"
    cat_tieng = [v for v in dx["cat_tieng"] if v.get("cat", True)]
    dj = P / "cat" / "duyet.json"
    if dj.exists():
        dv = json.loads(dj.read_text(encoding="utf-8"))
        giu_lai = {k for k, v in dv.items() if v == "giu"}
        for c in dx["cuts"]:
            if c["id"] in giu_lai:
                if c["loai"] == "tu":
                    for k in range(c["k0"], c["k1"] + 1):
                        bo[k] = False
                else:
                    cat_tieng = [v for v in cat_tieng if not (abs(v["a"] - c["a"]) < 0.01 and abs(v["b"] - c["b"]) < 0.01)]
        print(f"Áp trang duyệt: giữ lại {len(giu_lai)} chỗ")
    return dx, W, bo, cat_tieng


def chot(P, dx=None, W=None, bo=None, cat_tieng=None, im=False):
    if dx is None:
        dx, W, bo, cat_tieng = ap_sua(P)
    keeps = tinh_keeps(W, bo, dx.get("tu", 0.0))
    p = P / "cau-hinh.json"
    cfg = json.loads(p.read_text(encoding="utf-8"))
    if not (P / "cau-hinh.truoc-cat.json").exists():
        (P / "cau-hinh.truoc-cat.json").write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    cfg["keeps"] = keeps
    cfg["cat_tieng"] = [[v["a"], v["b"]] for v in cat_tieng]
    p.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    if not im:
        print(f"Đã chốt vào cau-hinh.json: {len(keeps)} đoạn giữ, {len(cat_tieng)} chỗ cắt bằng tiếng")
    return keeps


# ---------------------------------------------------------------- phần 6: trang duyệt
def mp3_b64(wav, doan):
    f = "".join(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS[x{i}];" for i, (a, b) in enumerate(doan))
    f += "".join(f"[x{i}]" for i in range(len(doan))) + f"concat=n={len(doan)}:v=0:a=1[o]"
    r = run(["ffmpeg", "-v", "error", "-i", str(wav), "-filter_complex", f, "-map", "[o]", "-ac", "1", "-b:a", "48k", "-f", "mp3", "-"])
    return "data:audio/mpeg;base64," + base64.b64encode(r.stdout).decode()


def duyet(P):
    import html as H
    cfg, mp4, wav = du_an(P)
    dx = json.loads((P / "cat" / "de-xuat.json").read_text(encoding="utf-8"))
    rows = []
    for c in dx["cuts"]:
        a, b = c["a"], c["b"]
        truoc = mp3_b64(wav, [(max(0, a - 1.5), b + 1.5)])
        sau = mp3_b64(wav, [(max(0, a - 1.5), a), (b, b + 1.5)])
        rows.append(f'<div class="c" data-id="{c["id"]}"><div class="h"><b>{c["id"]}</b> · {a:.1f}–{b:.1f}s · <span>{H.escape(c["ly_do"])}</span></div>'
                    f'<div class="t">Bỏ: «{H.escape(c["text"])}»</div><div class="p"><label>Trước khi cắt<audio controls preload="none" src="{truoc}"></audio></label>'
                    f'<label>Sau khi cắt<audio controls preload="none" src="{sau}"></audio></label></div>'
                    f'<div class="b"><button class="on" data-v="cat">Cắt</button><button data-v="giu">Giữ lại</button></div></div>')
    page = f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Duyệt chỗ cắt</title><style>body{{margin:0;font:15px/1.5 system-ui,'Segoe UI',sans-serif;background:#f4f6f3;color:#1d2a1f}}
.w{{max-width:900px;margin:0 auto;padding:20px 16px 80px}}h1{{font-size:22px;margin:0 0 4px}}.c{{background:#fff;border:1px solid #dfe5df;border-radius:12px;padding:12px 14px;margin:12px 0}}
.c.giu{{border-color:#e0a100;background:#fffaf0}}.h span{{color:#5d6b60}}.t{{margin:4px 0 8px}}.p{{display:flex;flex-wrap:wrap;gap:12px}}.p label{{display:flex;flex-direction:column;font-size:13px;color:#5d6b60}}
audio{{width:300px;max-width:100%}}.b{{margin-top:8px;display:flex;gap:8px}}button{{font:inherit;padding:6px 14px;border-radius:8px;border:1px solid #2f7a3a;background:#fff;color:#2f7a3a;cursor:pointer}}
button.on{{background:#2f7a3a;color:#fff}}.c.giu button.on{{background:#e0a100;border-color:#e0a100}}#bar{{position:fixed;left:0;right:0;bottom:0;background:#fff;border-top:1px solid #dfe5df;padding:10px 16px;display:flex;gap:10px;justify-content:center;align-items:center}}</style></head>
<body><div class="w"><h1>Duyệt chỗ cắt — {H.escape(P.name)}</h1><p>{len(dx['cuts'])} chỗ. Nghe “Trước / Sau”, chỗ nào không muốn cắt bấm <b>Giữ lại</b>. Xong bấm <b>Tải kết quả</b>, lưu file <code>duyet.json</code> vào thư mục <code>cat</code> của dự án (hoặc bấm Chép rồi dán cho Claude).</p>
{''.join(rows)}</div><div id="bar"><span id="n"></span><button id="dl" class="on">Tải kết quả (duyet.json)</button><button id="cp">Chép</button></div>
<script>const C=[...document.querySelectorAll('.c')];function kq(){{const o={{}};C.forEach(c=>o[c.dataset.id]=c.classList.contains('giu')?'giu':'cat');return o}}
function n(){{document.getElementById('n').textContent=C.filter(c=>c.classList.contains('giu')).length+' chỗ giữ lại / '+C.length}}
C.forEach(c=>c.querySelectorAll('button').forEach(b=>b.onclick=()=>{{c.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));c.classList.toggle('giu',b.dataset.v==='giu');n()}}));n();
document.getElementById('dl').onclick=()=>{{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(kq(),null,1)],{{type:'application/json'}}));a.download='duyet.json';a.click()}};
document.getElementById('cp').onclick=()=>navigator.clipboard.writeText('duyet.json '+JSON.stringify(kq()));</script></body></html>"""
    out = P / "cat" / "duyet.html"
    out.write_text(page, encoding="utf-8")
    print(f"Trang duyệt: {out} ({len(dx['cuts'])} chỗ cắt)")


# ---------------------------------------------------------------- phần 5: tự kiểm
def kiem(P, vong=2):
    import dung
    cfg, mp4, wav = du_an(P)
    dx, W, bo, cat_tieng = ap_sua(P)
    am_goc = doc_am(wav)
    env = dung.envelope(mp4)
    sil = dung.silences(mp4)
    words = [{"w": w["w"], "s": w["s"], "e": w["e"]} for w in W]
    bao = []
    for v in range(1, vong + 1):
        keeps = chot(P, dx, W, bo, cat_tieng, im=True)
        pieces, total = dung.build_pieces(keeps, sil, words=words, env=env, dai_clip=len(am_goc) / 16000,
                                          cam=[[c["a"], c["b"]] for c in cat_tieng])
        ra = np.concatenate([am_goc[int(p["s"] * 16000):int(p["e"] * 16000)] for p in pieces]) if pieces else np.zeros(16000, np.float32)

        def ve_nguon(t):
            for p in pieces:
                if p["o"] <= t <= p["o"] + p["e"] - p["s"]:
                    return p["s"] + t - p["o"]
            return None
        OW = [w for s in nghe(ra) for w in s["words"] if cat_vap.norm(w["w"])]
        sua = []
        # a) còn lặp cụm (>= 2 từ, không phải từ phổ biến) sau nhịp ngừng -> bỏ lần trước
        for j in range(1, len(OW)):
            for i in range(max(0, j - 12), j):
                L = 0
                while i + L < j and j + L < len(OW) and cat_vap.norm(OW[i + L]["w"]) == cat_vap.norm(OW[j + L]["w"]):
                    L += 1
                if L >= 2 and not all(cat_vap.norm(OW[i + t]["w"]) in cat_vap.PHO for t in range(L)) \
                        and OW[j]["s"] - OW[j - 1]["e"] >= 0.12 and OW[j]["s"] - OW[i]["s"] < 6:
                    a, b = ve_nguon(OW[i]["s"]), ve_nguon(OW[j]["s"] - 0.02)
                    if a is not None and b is not None and b > a:
                        sua.append(("lặp", a, b, " ".join(w["w"].strip() for w in OW[i:j])))
                    break
        # b) tiếng đệm có nhịp ngừng
        for k, w in enumerate(OW):
            if cat_vap.norm(w["w"]) in cat_vap.DEM and not cfg.get("hoi_thoai"):
                truoc = w["s"] - OW[k - 1]["e"] if k else 1
                sau = OW[k + 1]["s"] - w["e"] if k + 1 < len(OW) else 1
                if (w["e"] - w["s"]) + truoc + sau >= 0.35:
                    a, b = ve_nguon(w["s"] - 0.02), ve_nguon(w["e"] + 0.02)
                    if a is not None and b is not None:
                        sua.append(("đệm", a, b, w["w"].strip()))
        # c) khoảng lặng còn dài
        db, thr = env_db(ra)
        lang, i = [], 0
        while i < len(db):
            if db[i] <= thr:
                j = i
                while j < len(db) and db[j] <= thr:
                    j += 1
                if (j - i) * HOP > 0.45 and i > 0 and j < len(db):
                    lang.append((i * HOP, (j - i) * HOP))
                i = j
            else:
                i += 1
        moi = 0
        for loai, a, b, tx in sua:
            ks = [k for k, w in enumerate(W) if a - 0.03 <= (w["s"] + w["e"]) / 2 <= b + 0.03 and not bo[k]]
            if ks:
                for k in ks:
                    bo[k] = True
                moi += 1
            elif loai == "đệm":
                cat_tieng.append({"a": round(a, 2), "b": round(b, 2), "ly_do": "tự kiểm: tiếng đệm còn sót"}); moi += 1
        bao.append(f"- Vòng {v}: bản cắt dài {total:.1f}s · còn lặp {sum(s[0] == 'lặp' for s in sua)} · còn tiếng đệm "
                   f"{sum(s[0] == 'đệm' for s in sua)} · lặng > 0,45s: {len(lang)}" + (f" ({', '.join(f'{t:.1f}s/{d:.2f}s' for t, d in lang[:6])})" if lang else "")
                   + "".join(f"\n    · {s[0]} {s[1]:.1f}–{s[2]:.1f}s nguồn «{s[3][:50]}»" for s in sua))
        print(bao[-1])
        if not moi:
            break
    for k in range(len(W)):
        dx["W"][k]["bo"] = bo[k]
    for d in dx["don_vi"]:
        d["giu"] = "mot_phan"           # đã áp xuống từng từ
    dx["cat_tieng"] = cat_tieng
    (P / "cat" / "de-xuat.json").write_text(json.dumps(dx, ensure_ascii=False, indent=1), encoding="utf-8")
    keeps = chot(P, dx, W, bo, cat_tieng, im=True)
    (P / "cat" / "kiem.md").write_text("# Tự kiểm bản cắt\n\n" + "\n".join(bao), encoding="utf-8")
    print(f"Đã chốt sau tự kiểm: {len(keeps)} đoạn · báo cáo {P / 'cat' / 'kiem.md'}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit()
    P = Path(a[0]).resolve()
    if "--duyet" in a:
        duyet(P)
    elif "--chot" in a:
        chot(P)
    elif "--kiem" in a:
        kiem(P)
    else:
        phan_tich(P, a[1:])
