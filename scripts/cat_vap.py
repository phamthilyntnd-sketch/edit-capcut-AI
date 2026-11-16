"""TÌM CHỖ NÓI VẤP từ phiên âm (transcript.json có mốc từng từ) — chạy được trên MỌI máy (không cần bộ bo-skill-video).

Góp ý 16/11: "cắt vấp KOC chưa cắt được, mình vẫn phải cắt lại". Công cụ này liệt kê:
  - NÓI LẠI / BẮT ĐẦU LẠI: cụm 1–6 từ lặp lại ngay sau đó (giữ LẦN NÓI CUỐI)
  - TIẾNG ĐỆM: ừ, ờ, à, ừm, ơ, um, ah… (đứng riêng)
  - TỪ KÉO DÀI: 1 từ dài > 0,8s (ngập ngừng "ờ…ờ" Whisper gộp vào từ)
  - NGẮT GIỮA CÂU: khoảng lặng > 1,2s rồi nói tiếp câu cũ
rồi ĐỀ XUẤT `keeps` (các đoạn giữ, mốc nguồn) đã bỏ hết các chỗ trên — dán vào cau-hinh.json, rồi NGHE LẠI để chốt.

Chạy:  <python> -I scripts/cat_vap.py projects/<du-an> [--tu 0] [--den 999] [--json]
   --tu/--den: chỉ xét đoạn nguồn [tu, den] (bỏ phần chờ đầu/cuối clip)
"""
import json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
DEM = {"ừ", "ờ", "à", "ừm", "ờm", "ơ", "um", "uhm", "ah", "hừm", "ê", "e", "ư", "hmm", "mm", "ừa"}


def norm(w):
    return re.sub(r"[^\w]", "", w.lower())


def main():
    P = Path(sys.argv[1])
    a = sys.argv[2:]
    tu = float(a[a.index("--tu") + 1]) if "--tu" in a else 0.0
    den = float(a[a.index("--den") + 1]) if "--den" in a else 1e9
    segs = json.loads((P / "transcript.json").read_text(encoding="utf-8"))
    W = [dict(w, n=norm(w["w"]), g=gi) for gi, sg in enumerate(segs) for w in sg.get("words", [])
         if tu <= w["s"] <= den and norm(w["w"])]
    bo = [False] * len(W)
    ly_do = {}

    def danh(i, j, why):   # bỏ từ i..j-1
        for k in range(i, j):
            if not bo[k]:
                bo[k] = True
                ly_do[k] = why

    # 1) tiếng đệm (bỏ) + từ kéo dài (chỉ BÁO: thường do Whisper nuốt khoảng lặng — dung.py tự cắt lặng)
    nghe = []
    for i, w in enumerate(W):
        if w["n"] in DEM:
            danh(i, i + 1, "tiếng đệm")
        elif w["e"] - w["s"] > 0.8 and len(w["n"]) <= 6 and not re.search(r"\d", w["n"]):
            nghe.append(f"  {w['s']:7.2f}–{w['e']:6.2f}s  từ \"{w['w'].strip()}\" dài {w['e'] - w['s']:.1f}s"
                        " (ngập ngừng kéo dài tiếng? nghe lại)")
    # 2) nói lại: cụm n từ (6 -> 1) lặp ngay sau (cho phép chen tiếng đệm) -> bỏ lần TRƯỚC, giữ lần cuối
    i = 0
    while i < len(W):
        hit = False
        for n in range(6, 0, -1):
            a1 = [W[k]["n"] for k in range(i, min(i + n, len(W)))]
            if len(a1) < n:
                continue
            j = i + n
            while j < len(W) and W[j]["n"] in DEM:
                j += 1
            a2 = [W[k]["n"] for k in range(j, min(j + n, len(W)))]
            # n = 1 chỉ tính khi từ lặp là từ có nghĩa dài (tránh "rất rất", "từ từ" là cách nói thật)
            if a1 == a2 and (n >= 2 or (len(a1[0]) >= 3 and W[j]["s"] - W[i + n - 1]["e"] > 0.15)):
                danh(i, j, "nói lại: " + " ".join(W[k]["w"].strip() for k in range(i, i + n)))
                i = j
                hit = True
                break
        if not hit:
            i += 1
    # 3) bắt đầu lại câu: cụm 2–4 từ đầu câu lặp lại trong 6s sau, sau 1 khoảng lặng -> bỏ từ lần đầu tới trước lần sau
    for i in range(len(W)):
        if bo[i] or (i and W[i]["s"] - W[i - 1]["e"] < 0.35):
            continue
        for n in (4, 3, 2):
            if i + n > len(W):
                continue
            a1 = [x["n"] for x in W[i:i + n]]
            for j in range(i + n, len(W)):
                if W[j]["s"] - W[i]["s"] > 6:
                    break
                if [x["n"] for x in W[j:j + n]] == a1 and W[j]["s"] - W[j - 1]["e"] >= 0.3:
                    danh(i, j, "bắt đầu lại câu: " + " ".join(x["w"].strip() for x in W[i:i + n]) + "…")
                    break
            else:
                continue
            break

    # 4) câu: Whisper bịa (subscribe / đăng ký kênh / cảm ơn đã xem…), câu lẻ ngắn ngoài kịch bản, câu trùng ý
    import difflib
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
            if r >= 0.6 and min(len(a_), len(b_)) >= 4:
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


if __name__ == "__main__":
    main()
