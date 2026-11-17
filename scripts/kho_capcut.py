"""KHO HIỆU ỨNG CAPCUT (V4) — dùng hết tài nguyên có sẵn của CapCut, chọn theo PHONG CÁCH + VAI TRÒ.

Kho = toàn bộ danh mục capcut-cli biết (chuyển cảnh, hiệu ứng cảnh, hiệu ứng nhân vật, kiểu chữ vào/ra/lặp, hoạt ảnh video
vào/ra/kết hợp), lưu ở kho/capcut.json (đi kèm skill -> mọi máy giống nhau). Mỗi mục được gắn PHONG CÁCH theo tên:
  nang_dong (bán hàng, review sôi động) · sang_trong (mỹ phẩm, cao cấp) · de_thuong (mẹ & bé, quà tặng)
  · cong_nghe (đồ điện tử, app) · co_dien (retro, kể chuyện)
và VAI TRÒ cho hiệu ứng cảnh: mo_dau (mở video) · nhan (nhấn 1 khoảnh khắc) · ket (kết video).
Bỏ hẳn các mục không hợp video bán hàng (ma quái, buồn, biến dạng mặt, "The End"…).

Chạy:  kho_capcut.py tao      -> đọc capcut enums, ghi kho/capcut.json (chạy lại khi nâng capcut-cli)
       kho_capcut.py xem [loai] [phong_cach]
Dùng trong code:  chon(loai, phong_cach, so, vai=None, hat=..., tranh=()) -> [slug...]   ·   tieng_cho(ten) -> tên SFX
"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

SK = Path(__file__).resolve().parent.parent
KHO = SK / "kho" / "capcut.json"
LOAI = {"chuyen_canh": "--transitions", "hieu_ung_canh": "--scene-effects", "hieu_ung_nguoi": "--character-effects",
        "chu_vao": "--text-intros", "chu_ra": "--text-outros", "chu_lap": "--text-loop-anims",
        "video_vao": "--image-intros", "video_ra": "--image-outros", "video_ket_hop": "--image-combos"}
PHONG_CACH = {
    "nang_dong": r"shake|zoom|flash|pull|swirl|pulse|strobe|bounce|spin|slide|wipe|pop|jump|burst|explos|spark|lightning|"
                 r"rebound|throb|shockwave|woosh|whoosh|squeeze|stretch|swing|rock|vibrat|enlarge|grow|spring|boing|fly|"
                 r"slingshot|jolt|judder|random bounce|scream|shout|jiggl|wobble",
    "sang_trong": r"dissolve|fade|light|leak|gleam|glow|sparkle|halo|shimmer|blur|mini.?zoom|soft|twinkle|star|beam|sweep|"
                  r"diamond|blink|focus|develop|to color|flare|showing|sunrise|mix|open|haz|angel|magic",
    "de_thuong": r"heart|love|star|butterfl|bubble|cute|like|cloud|snow|rainbow|kiss|sweet|lovestruck|musical|wave|"
                 r"bounce|boing|spring|jiggl|donut|dance|pop.?up",
    "cong_nghe": r"glitch|rgb|scan|neon|pixel|digital|electro|hologram|crt|lines|blocks|cyber|laser|spectrum|chromatic|"
                 r"technology|geometric|mechanical|type|typewriter|code|bullet|flicker|strobe",
    "co_dien": r"film|retro|vintage|old tv|camcorder|vhs|b&w|cinema|grain|tv on|recorder|page|ink|font reel|screening|"
               r"noise|fade",
}
BO = r"spooky|sad|ghost|embarrass|gorilla|big head|big mouth|hellfire|dizzy|trippy|negative|blackout|the end|tv off|" \
     r"mosaic|^woman|^man|struck|electric shock|face glitch|phantom face|crack|fire|flame|black smoke|burn|little devil|" \
     r"wobbly black|stuck frame|scream|emotional|sinking|dopelganger|apparate|consciousness|funhouse|pirate|train|" \
     r"roller|smartphone"
VAI = {"mo_dau": r"fade in|horizontal open|vertical open|portrait open|tv on|camera focus|to color|develop|blurry focus|"
                  r"landscape open|zoom lens|mini zoom",
       "nhan": r"^shake|camera shake|zoom lens|mini zoom|white flash|^flash|pulse|spark|gleam|shockwave|throb|halo|glowburst|"
               r"twinkle|star|rainbow sparkle|heartbeat|collision|light leak|leak",
       "ket": r"fade out|vertical close|horizontal close|white out|landscape close"}
# tiếng nhấn đi theo kiểu hoạt ảnh (kho tiếng tự tổng hợp của skill: bubble cash chime click ding notify pop riser shutter
# sparkle swipe tick whip whoosh)
TIENG = [(r"type|typewriter|reel|ink", "tick"), (r"glitch|rgb|flicker|strobe|scan|pixel|crt|blocks|flash|shutter", "shutter"),
         (r"zoom|pull|woosh|whoosh|fly|slingshot|throw|wind|sweep", "whoosh"),
         (r"slide|wipe|scroll|swipe|showing|open|close|blinds|wiper|split|slice", "swipe"),
         (r"flip|spin|rotat|turn|roll|swirl|whirl|swing|fold|axis|cube", "whip"),
         (r"bounce|boing|spring|jiggl|jump|wobble|bubble|donut", "bubble"),
         (r"sparkle|twinkle|star|gleam|glow|shimmer|light|halo|magic|diamond|leak|beam", "sparkle"),
         (r"heart|love|like|cute|kiss", "chime"), (r"pop|grow|enlarge|mini|punch|pulse|throb|shock", "pop"),
         (r"fade|dissolve|blur|soft|haz|mix", "whoosh")]


def tao():
    kho = {}
    for k, opt in LOAI.items():
        out = subprocess.run(["capcut", "enums", opt], capture_output=True, text=True, encoding="utf-8", shell=True).stdout
        items = json.loads(out.split("\n")[0])
        seen, ds = set(), []
        for x in items:
            ten = x.get("title") or x.get("name") or x["slug"]
            if x["slug"] in seen or re.search(BO, ten.lower()):
                continue
            seen.add(x["slug"])
            t = ten.lower()
            ds.append({"slug": x["slug"], "ten": ten, "pro": bool(x.get("is_vip")),
                       "phong_cach": [p for p, r in PHONG_CACH.items() if re.search(r, t)],
                       "vai": [v for v, r in VAI.items() if re.search(r, t)] if k == "hieu_ung_canh" else [],
                       "tieng": tieng_cho(ten)})
        kho[k] = ds
    KHO.parent.mkdir(exist_ok=True)
    KHO.write_text(json.dumps(kho, ensure_ascii=False, indent=0), encoding="utf-8")
    print("Kho CapCut:", ", ".join(f"{k} {len(v)}" for k, v in kho.items()), "->", KHO)


def tieng_cho(ten):
    t = ten.lower()
    for r, s in TIENG:
        if re.search(r, t):
            return s
    return "whoosh"


_cache = None


def kho():
    global _cache
    if _cache is None:
        _cache = json.loads(KHO.read_text(encoding="utf-8")) if KHO.exists() else {}
    return _cache


def chon(loai, phong_cach="nang_dong", so=1, vai=None, hat="", tranh=(), pro=True):
    """Chọn `so` mục khác nhau, hợp phong cách (+ vai trò), ổn định theo `hat` (cùng dự án -> cùng lựa chọn)."""
    ds = [x for x in kho().get(loai, []) if (pro or not x["pro"]) and x["slug"] not in tranh]
    hop = [x for x in ds if phong_cach in x["phong_cach"] and (not vai or vai in x["vai"])]
    if len(hop) < so:
        hop += [x for x in ds if x not in hop and (not vai or vai in x["vai"])]
    if not hop:
        return []
    hop.sort(key=lambda x: hashlib.md5((hat + x["slug"]).encode()).hexdigest())
    return [x["slug"] for x in hop[:so]]


def thong_tin(loai, slug):
    return next((x for x in kho().get(loai, []) if x["slug"] == slug), {"slug": slug, "ten": slug, "tieng": tieng_cho(slug)})


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    if a and a[0] == "tao":
        tao()
    elif a and a[0] == "xem":
        loai = a[1] if len(a) > 1 else None
        pc = a[2] if len(a) > 2 else None
        for k, v in kho().items():
            if loai and k != loai:
                continue
            ds = [x for x in v if not pc or pc in x["phong_cach"]]
            print(f"== {k} ({len(ds)})", " | ".join(x["ten"] + ("*" if x["pro"] else "") for x in ds)[:1500])
    else:
        print(__doc__)
