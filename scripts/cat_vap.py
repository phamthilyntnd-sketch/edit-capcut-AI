"""TÌM CHỖ NÓI VẤP từ phiên âm (transcript.json có mốc từng từ) — chạy được trên MỌI máy (không cần bộ bo-skill-video).

Góp ý 16/11: "cắt vấp KOC chưa cắt được, mình vẫn phải cắt lại". Công cụ này liệt kê:
  - NÓI SAI RỒI NÓI LẠI: bỏ TRỌN đoạn nói hỏng (từ đầu câu/cụm bị hỏng tới chỗ bắt đầu nói lại), giữ LẦN NÓI CUỐI —
    không ghép nửa câu sai với nửa câu đúng (góp ý 18/11)
  - TIẾNG ĐỆM: ừ, ờ, à, ừm, ơ… — chỉ cắt khi có nhịp ngừng quanh nó; lướt nhanh giữa câu thì giữ (cắt sẽ giật)
  - MẢNH LẺ: lời còn sót < 0,8s kẹp giữa 2 chỗ cắt -> bỏ, không cắt lắt nhắt
  - TỪ KÉO DÀI: 1 từ dài > 0,8s (ngập ngừng "ờ…ờ" Whisper gộp vào từ)
  - NGẮT GIỮA CÂU: khoảng lặng > 1,2s rồi nói tiếp câu cũ
rồi ĐỀ XUẤT `keeps` (các đoạn giữ, mốc nguồn) đã bỏ hết các chỗ trên — dán vào cau-hinh.json, rồi NGHE LẠI để chốt.

Chạy:  <python> -I scripts/cat_vap.py projects/<du-an> [--tu 0] [--den 999] [--json]
   --tu/--den: chỉ xét đoạn nguồn [tu, den] (bỏ phần chờ đầu/cuối clip)
"""
import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PHO = {"mọi", "người", "các", "bác", "bạn", "em", "anh", "chị", "mình", "này", "đây", "đó", "là", "thì", "và", "với", "cho",
       "của", "rất", "lắm", "quá", "cực", "kỳ", "đúng", "không", "ạ", "nhé", "nhá", "nha", "nhớ", "luôn", "có", "được", "một",
       "những", "cái", "chiếc", "cả", "nữa", "đi", "về", "từ", "khi", "nên", "nó", "như", "thế", "nào", "đấy", "ấy", "ơi", "rồi", "cũng", "mà", "để", "ở", "vào", "ra", "lên"}
DEM = {"ừ", "ờ", "à", "ừm", "ờm", "ơ", "um", "uhm", "ah", "hừm", "ê", "e", "ư", "hmm", "mm", "ừa"}


def norm(w):
    return re.sub(r"[^\w]", "", w.lower())


def main(argv=None, segs=None, tra_ve=False):
    """CLI. Module khác (cat_sach.py) gọi: main([du_an, ...], segs=<phiên âm đã sửa>, tra_ve=True) -> (W, bo, ly_do, keeps)."""
    argv = sys.argv[1:] if argv is None else argv
    P = Path(argv[0])
    a = argv[1:]
    tu = float(a[a.index("--tu") + 1]) if "--tu" in a else 0.0
    den = float(a[a.index("--den") + 1]) if "--den" in a else 1e9
    if segs is None:
        segs = json.loads((P / "transcript.json").read_text(encoding="utf-8"))
    # HỘI THOẠI 2 người (vợ hỏi – chồng đáp…): câu đáp hay lặp lại lời người kia ("Anh tìm hiểu kỹ đó." – "Ừ, anh tìm hiểu kỹ
    # chứ sao?") và "Ừ / Dạ" là câu trả lời, KHÔNG phải nói vấp -> tắt dò "nói sai rồi nói lại" + tiếng đệm; chỉ bỏ Whisper
    # bịa, câu lặp NGUYÊN câu (>= 90%) và mẩu lẻ. Bật: --hoi-thoai hoặc cau-hinh "hoi_thoai": true
    cfg_ = json.loads((P / "cau-hinh.json").read_text(encoding="utf-8")) if (P / "cau-hinh.json").exists() else {}
    hoi_thoai = "--hoi-thoai" in a or bool(cfg_.get("hoi_thoai"))
    if hoi_thoai:
        print("(chế độ HỘI THOẠI: không coi câu đáp / 'Ừ' là vấp)")
    W = [dict(w, n=norm(w["w"]), g=gi) for gi, sg in enumerate(segs) for w in sg.get("words", [])
         if tu <= w["s"] <= den and norm(w["w"])]
    bo = [False] * len(W)
    ly_do = {}

    def danh(i, j, why):   # bỏ từ i..j-1
        for k in range(i, j):
            if not bo[k]:
                bo[k] = True
                ly_do[k] = why

    import difflib

    def giong(a, b):
        """2 từ coi là CÙNG 1 từ nói lại: y hệt, hoặc 1 từ bị nói dở (tiền tố: 'hiệ' / 'hiệu'), hoặc Whisper viết lệch."""
        if a == b:
            return True
        if min(len(a), len(b)) >= 2 and (a.startswith(b) or b.startswith(a)):
            return True
        return min(len(a), len(b)) >= 3 and difflib.SequenceMatcher(None, a, b).ratio() >= 0.75

    def lang(j):
        """Khoảng lặng ngay trước từ j (bỏ qua tiếng đệm chen giữa)."""
        k = j - 1
        while k >= 0 and W[k]["n"] in DEM:
            k -= 1
        return W[j]["s"] - W[k]["e"] if k >= 0 else 9.0

    def dau_cau(i):
        """Đầu câu / cụm chứa từ i: lùi tới chỗ có khoảng lặng >= 0,35s hoặc dấu kết câu (tối đa 8s, 14 từ)."""
        k = i
        while k > 0 and i - k < 14 and W[i]["s"] - W[k - 1]["s"] < 8:
            if (W[k]["s"] - W[k - 1]["e"] >= 0.35 or re.search(r"[.?!…,]$", W[k - 1]["w"].strip()) or bo[k - 1]
                    or W[k]["g"] != W[k - 1]["g"]):      # Whisper tách câu (đoạn) ở đây = đầu câu
                break
            k -= 1
        return k

    # 1) NÓI SAI RỒI NÓI LẠI (góp ý 18/11: "nói sai và nói lại đoạn nào thì cắt bỏ CẢ đoạn nói sai, chỉ lấy từ đoạn nói
    #    đúng"): tìm chỗ KOC quay lại nói lại (cụm từ ở j lặp lại cụm từ ở i phía trước, trong 8s / 14 từ, cho phép từ nói
    #    dở và tiếng đệm chen giữa) -> BỎ TRỌN từ đầu câu/cụm bị nói hỏng tới ngay trước chỗ nói lại, giữ LẦN NÓI CUỐI.
    #    Không giữ nửa câu sai ghép với nửa câu đúng.
    j = 1 if not hoi_thoai else len(W)
    while j < len(W):
        if W[j]["n"] in DEM:
            j += 1
            continue
        best = None   # (độ dài khớp, i)
        for i in range(j - 1, -1, -1):
            if j - i > 14 or W[j]["s"] - W[i]["s"] > 8:
                break
            if W[i]["n"] in DEM or bo[i]:
                continue      # không so với lời đã bỏ (tránh cắt nhầm vào chính lần nói lại)
            L = 0
            while i + L < j and j + L < len(W) and giong(W[i + L]["n"], W[j + L]["n"]):
                L += 1
            if L == 0:
                continue
            if all(W[i + t]["n"] in PHO for t in range(L)):
                continue      # cụm toàn từ phổ biến ("mọi người", "rất là", "đúng không"…) lặp lại là bình thường
            bo_do = j - (i + L)          # số từ nói dở bị bỏ giữa lần nói hỏng và lần nói lại
            ngap = lang(j) >= 0.2 or any(W[k]["n"] in DEM for k in range(i, j))   # có ngập ngừng trước khi nói lại
            if not ngap:
                continue      # nói liền không ngừng ("chiếc ghế em nằm là chiếc ghế…", "tiện ơi là tiện") = câu bình thường
            if L >= 2:
                ok = bo_do <= 6 or (lang(j) >= 0.3 and dau_cau(i) >= i - 2)
            else:                 # khớp 1 từ: chỉ khi bắt đầu lại rõ ràng (ngập ngừng trước), gần, từ đủ dài
                ok = len(W[j]["n"]) >= 3 and lang(j) >= 0.25 and j - i <= 3
            if L >= 2 and j - i == L and lang(j) < 0.12 and not any(W[k]["n"] in DEM for k in range(i, j)):
                ok = False    # lặp liền 1 cụm không ngập ngừng ("đẹp lắm đẹp lắm") = cách nói nhấn mạnh, giữ
            if ok and (best is None or L > best[0]):
                best = (L, i)
        if best:
            L, i = best
            bat = dau_cau(i) if lang(j) >= 0.3 else i    # bắt đầu lại sau 1 nhịp ngừng -> bỏ từ ĐẦU CÂU bị nói hỏng
            sai = " ".join(W[k]["w"].strip() for k in range(bat, j))
            dung = " ".join(W[k]["w"].strip() for k in range(j, min(len(W), j + max(L, 4))))
            danh(bat, j, f"nói sai rồi nói lại — bỏ «{sai[:60]}», giữ «{dung[:40]}…»")
            j += L            # các từ của lần nói lại không phải chỗ nói lại mới
            continue
        j += 1

    # 1b) LẶP 1 TỪ NGAY LIỀN có ngắt ("Đây, đây là…", "Em… em dùng") — góp ý 19/11 NoeSkin. Từ phổ biến cũng tính (luật 1
    #     bỏ qua từ phổ biến). Không đụng láy / nhấn liền mạch ("từ từ", "xinh xinh"): cần dấu ngắt hoặc lặng >= 0,15s.
    if not hoi_thoai:
        for k in range(len(W) - 1):
            if bo[k] or bo[k + 1] or W[k]["n"] in DEM or W[k]["n"] != W[k + 1]["n"]:
                continue
            if re.search(r"[,.…?!-]$", W[k]["w"].strip()) or W[k + 1]["s"] - W[k]["e"] >= 0.15:
                danh(k, k + 1, f"lặp 1 từ — bỏ «{W[k]['w'].strip()}» đầu, giữ lần sau")

    # 1c) CỤM BỎ DỞ: 1–3 từ Whisper ghi "…" (nói dở), đứng sau chỗ ngắt câu, sau đó ngừng rồi nói sang ý khác (không lặp lại
    #     từ nào của cụm trong 6 từ sau) — vd "…tối đa, chuẩn lực 0… không cần chà xát mạnh". Câu nói lại thì luật 1 đã xử.
    if not hoi_thoai:
        for k in range(len(W) - 1):
            if bo[k] or not W[k]["w"].strip().endswith("…") or W[k + 1]["s"] - W[k]["e"] < 0.2:
                continue
            b0 = dau_cau(k)
            if k - b0 + 1 > 3 or (b0 > 0 and not (re.search(r"[.?!…,]$", W[b0 - 1]["w"].strip())
                                                  or W[b0]["s"] - W[b0 - 1]["e"] >= 0.25)):
                continue
            manh = {W[t]["n"] for t in range(b0, k + 1)} - PHO
            sau = {W[t]["n"] for t in range(k + 1, min(len(W), k + 7))}
            if manh and not (manh & sau) and not any(bo[t] for t in range(b0, k + 1)):
                danh(b0, k + 1, f"cụm bỏ dở «{' '.join(W[t]['w'].strip() for t in range(b0, k + 1))}»")

    # 2) tiếng đệm (ừ, ờ, à…): chỉ cắt khi có nhịp ngừng quanh nó (>= 0,35s tính cả tiếng đệm) — tiếng đệm lướt nhanh
    #    giữa câu cắt ra chỉ làm hình giật lắt nhắt, giữ lại. Từ kéo dài: chỉ BÁO (thường Whisper nuốt khoảng lặng).
    nghe = []
    for i, w in enumerate(W):
        if bo[i]:
            continue
        if w["n"] in DEM and not hoi_thoai:
            truoc = w["s"] - W[i - 1]["e"] if i else 9
            sau = W[i + 1]["s"] - w["e"] if i + 1 < len(W) else 9
            if (w["e"] - w["s"]) + truoc + sau >= 0.35:
                danh(i, i + 1, "tiếng đệm")
            else:
                nghe.append(f"  {w['s']:7.2f}s  tiếng đệm \"{w['w'].strip()}\" lướt nhanh giữa câu — giữ (cắt sẽ giật)")
        elif w["e"] - w["s"] > 0.8 and len(w["n"]) <= 6 and not re.search(r"\d", w["n"]):
            nghe.append(f"  {w['s']:7.2f}–{w['e']:6.2f}s  từ \"{w['w'].strip()}\" dài {w['e'] - w['s']:.1f}s"
                        " (ngập ngừng kéo dài tiếng? nghe lại)")

    # 3) câu: Whisper bịa (subscribe / đăng ký kênh / cảm ơn đã xem…), câu lẻ ngắn ngoài kịch bản, câu trùng ý
    SG = []   # (chỉ số từ đầu, cuối, text)
    for gi, sg in enumerate(segs):
        idx = [k for k, w in enumerate(W) if w["g"] == gi]
        if idx:
            SG.append((idx[0], idx[-1], sg["text"].strip()))
    BIA = re.compile(r"subscribe|đăng ký kênh|đăng kí kênh|cảm ơn (các bạn )?đã (xem|theo dõi)|ghiền mì gõ|like và share",
                     re.I)
    for k, (i0, i1, tx) in enumerate(SG):
        if BIA.search(tx):
            danh(i0, i1 + 1, "Whisper bịa / câu ngoài lề")
            continue
        dur = W[i1]["e"] - W[i0]["s"]
        gap_l = W[i0]["s"] - W[i0 - 1]["e"] if i0 else 9
        gap_r = W[i1 + 1]["s"] - W[i1]["e"] if i1 + 1 < len(W) else 9
        if dur < 1.5 and i1 - i0 < 6 and gap_l > 1.0 and gap_r > 1.0:
            danh(i0, i1 + 1, "câu lẻ ngắn giữa 2 khoảng lặng (nói ngoài kịch bản?)")
    trung, lan_sau = [], set()
    for k, (i0, i1, tx) in enumerate(SG):
        for k2 in range(k + 1, len(SG)):
            j0, j1, tx2 = SG[k2]
            a_, b_ = [W[x]["n"] for x in range(i0, i1 + 1)], [W[x]["n"] for x in range(j0, j1 + 1)]
            r = difflib.SequenceMatcher(None, a_, b_).ratio()
            if r >= (0.9 if hoi_thoai else 0.6) and min(len(a_), len(b_)) >= 4:
                # nói lại câu ngay sau, HOẶC nói lại cả 1 ĐOẠN (câu kế tiếp của 2 lần cũng giống nhau) -> bỏ lần TRƯỚC
                ke = k + 1 < len(SG) and k2 + 1 < len(SG) and difflib.SequenceMatcher(
                    None, [W[x]["n"] for x in range(SG[k + 1][0], SG[k + 1][1] + 1)],
                    [W[x]["n"] for x in range(SG[k2 + 1][0], SG[k2 + 1][1] + 1)]).ratio() >= 0.6
                truoc = k > 0 and k2 > 0 and difflib.SequenceMatcher(
                    None, [W[x]["n"] for x in range(SG[k - 1][0], SG[k - 1][1] + 1)],
                    [W[x]["n"] for x in range(SG[k2 - 1][0], SG[k2 - 1][1] + 1)]).ratio() >= 0.6
                if k2 == k + 1 or ke or truoc:
                    danh(i0, i1 + 1, f"nói lại (lần sau lúc {W[j0]['s']:.1f}s giống {r:.0%}) — giữ lần cuối")
                    lan_sau.add(k2)
                else:                # trùng ý cách xa, giữa là nội dung khác -> giữ lần đầu, bỏ lần sau (giữ mạch)
                    danh(j0, j1 + 1, f"câu trùng ý với câu lúc {W[i0]['s']:.1f}s ({r:.0%})")
                trung.append((W[i0]["s"], W[j0]["s"], r))

    # lời chen giữa các lần nói lại ("Rất tốt", "Hả?", "Đợi thích nha"…): chuỗi câu được giữ ngắn (tổng lời < 3,5s) mà 2 bên
    # là câu đã bỏ / lần nói lại -> bỏ luôn
    def bo_cau(k):
        return all(bo[x] for x in range(SG[k][0], SG[k][1] + 1))
    k = 1
    while k < len(SG) - 1:
        if bo_cau(k) or not bo_cau(k - 1):
            k += 1
            continue
        j = k
        while j < len(SG) and not bo_cau(j) and j not in lan_sau:
            j += 1
        noi = sum(W[x]["e"] - W[x]["s"] for y in range(k, j) for x in range(SG[y][0], SG[y][1] + 1))
        if j < len(SG) and noi < 3.5 and (bo_cau(j) or j in lan_sau):
            for x in range(k, j):
                danh(SG[x][0], SG[x][1] + 1, "lời chen giữa các lần nói lại")
        k = j + 1

    # 4) KHÔNG CẮT LẮT NHẮT: mảnh lời còn giữ kẹp giữa 2 chỗ bỏ mà quá ngắn (<= 2 từ, < 0,8s) = mảnh của lần nói hỏng -> bỏ
    k = 0
    while k < len(W):
        if bo[k]:
            k += 1
            continue
        e = k
        while e + 1 < len(W) and not bo[e + 1] and W[e + 1]["s"] - W[e]["e"] < 0.6:
            e += 1
        ke_trai = k > 0 and bo[k - 1]
        ke_phai = e + 1 < len(W) and bo[e + 1]
        if ke_trai and ke_phai and e - k + 1 <= 2 and W[e]["e"] - W[k]["s"] < 0.8:
            danh(k, e + 1, "mảnh lời lẻ giữa 2 chỗ cắt (cắt cho liền mạch)")
        k = e + 1

    print("== CHỖ VẤP TÌM ĐƯỢC (bỏ đi, giữ lần nói cuối):")
    k = 0
    while k < len(W):
        if bo[k]:
            j = k
            while j + 1 < len(W) and bo[j + 1] and ly_do[j + 1] == ly_do[k]:
                j += 1
            txt = " ".join(W[x]["w"].strip() for x in range(k, j + 1))
            print(f"  {W[k]['s']:7.2f}–{W[j]['e']:6.2f}s  [{ly_do[k]}]  \"{txt}\"")
            k = j + 1
        else:
            k += 1
    if nghe:
        print("\n== NGHE LẠI (không tự bỏ):")
        print("\n".join(nghe))
    # 5) đề xuất keeps: gom từ được giữ, tách khi gặp từ bỏ hoặc lặng > 1,2s; mép đoạn để dung.py tự bám ranh giới từ
    keeps, cur = [], None
    for i, w in enumerate(W):
        if bo[i]:
            if cur:
                keeps.append(cur)
                cur = None
            continue
        if cur and w["s"] - cur[1] > 1.2:
            keeps.append(cur)
            cur = None
        lo = W[i - 1]["e"] + 0.01 if i and bo[i - 1] else tu          # không lấn vào từ đã bỏ
        hi = W[i + 1]["s"] - 0.01 if i + 1 < len(W) and bo[i + 1] else 1e9
        if cur is None:
            cur = [round(max(lo, w["s"] - 0.12), 2), round(min(hi, w["e"] + 0.15), 2)]
        else:
            cur[1] = round(min(hi, w["e"] + 0.15), 2)
    if cur:
        keeps.append(cur)
    print(f"\n== ĐỀ XUẤT keeps ({len(keeps)} đoạn, tổng {sum(b - a for a, b in keeps):.1f}s) — dán vào cau-hinh.json:")
    print(json.dumps(keeps))
    print("\nLƯU Ý: Whisper có thể nghe sai — NGHE LẠI các chỗ trên trước khi chốt. Đoạn mở đầu cần ~1,5s hình cho"
          " thumbnail: nới đầu đoạn 1 nếu cần. dung.py tự đặt điểm cắt ở ranh giới từ + đuôi tiếng (không cụt chữ).")
    if "--json" in a:
        (P / "cat-vap.json").write_text(json.dumps({"keeps": keeps, "bo": [
            {"s": W[k]["s"], "e": W[k]["e"], "w": W[k]["w"], "ly_do": ly_do[k]} for k in range(len(W)) if bo[k]]},
            ensure_ascii=False, indent=1), encoding="utf-8")
    if tra_ve:
        return W, bo, ly_do, keeps


if __name__ == "__main__":
    main()
