"""KHO TIẾNG NHẤN theo VAI (20/11/2026) — tiếng có sẵn trong THƯ VIỆN CAPCUT (có mã, CapCut tự tải) + tiếng tự tạo dự phòng.

VAI của một tiếng nhấn (dung.py gắn cho từng điểm nhấn):
  chu      chữ nhấn bật lên            tram     vào cảnh trám              chuyen   chuyển cảnh
  san_pham gọi tên sản phẩm            gia      giá / ưu đãi / con số      cta      nút giỏ hàng / kêu gọi
  hoi      câu hỏi                     cao_trao dồn lên trước tên sản phẩm  ket      câu chốt cuối

TIẾNG THƯ VIỆN CAPCUT: không ai công bố cấu trúc JSON của tiếng thư viện, nên skill KHÔNG tự bịa — nó học từ draft thật:
người dùng thả tiếng từ CapCut (Âm thanh › Hiệu ứng âm thanh) vào 1 project bất kỳ (nên đặt tên "-KHO TIENG"), lưu, đóng
CapCut, rồi chạy `kho_tieng.py thu`. Mỗi tiếng có mã thư viện (music_id / effect_id / resource_id) được chép NGUYÊN mẫu
material vào kho/tieng-capcut.json, xếp vai theo tên (sửa tay được khoá "vai"). Khi dựng, tiếng nhấn của vai đó được thay
bằng tiếng thư viện (xoay vòng, không lặp liền nhau); máy khác mở project thì CapCut tự tải theo mã.
Chưa có kho / thiếu vai -> dùng tiếng tự tạo trong sfx/ (tao_sfx.py), cũng xoay vòng theo vai + phong cách.

Chạy:  kho_tieng.py thu [thư mục drafts]   -> quét mọi draft, cập nhật kho/tieng-capcut.json
       kho_tieng.py xem                     -> liệt kê kho theo vai
"""
import copy, glob, hashlib, json, os, re, sys, uuid
from pathlib import Path

SK = Path(__file__).resolve().parent.parent
KHO = SK / "kho" / "tieng-capcut.json"
CT = SK / "kho" / "cong-thuc.json"
VAI = ["chu", "tram", "chuyen", "san_pham", "gia", "cta", "hoi", "cao_trao", "ket"]
# tên tiếng (tiếng Việt / Anh / Trung — CapCut hiển thị theo ngôn ngữ máy) -> vai
VAI_TEN = [
    ("cta", r"cash|money|coin|register|ka-?ching|cha-?ching|tiền|thu ngân|xu|金币|收银|钱"),
    ("gia", r"cash|coin|money|ka-?ching|tiền|xu|price|sale|金币|钱"),
    ("hoi", r"question|hmm|huh|curious|what|hỏi|thắc mắc|疑问|问号|啊\?"),
    ("cao_trao", r"riser|rise|build|tension|drum ?roll|suspense|dồn|cao trào|上升|紧张|鼓点"),
    ("ket", r"chime|bell|success|win|tada|ta-?da|applause|chuông|thành công|vỗ tay|叮|成功|掌声"),
    ("san_pham", r"sparkle|shine|twinkle|glitter|magic|bling|ding|lấp lánh|phép|闪|魔法|叮"),
    ("chuyen", r"whoosh|swoosh|swish|woosh|transition|swipe|whip|wind|vút|chuyển cảnh|嗖|转场|风"),
    ("tram", r"whoosh|swoosh|swipe|slide|pass|camera|shutter|vút|lướt|chụp|嗖|快门|滑"),
    ("chu", r"pop|bubble|click|tick|boing|blip|bloop|plop|snap|type|keyboard|beep|notification|bóp|bụp|tách|gõ|啵|点击|"
            r"弹|叮咚|提示"),
]
# phong cách nghe hợp (để chọn tiếng thư viện hợp ngành)
PC_TEN = {"sang_trong": r"chime|bell|sparkle|shine|soft|swoosh|swish|twinkle|magic|piano|harp|lấp lánh|chuông",
          "nang_dong": r"pop|boing|whip|punch|hit|impact|boom|bass|drum|cash|clap|swoosh|whoosh",
          "de_thuong": r"bubble|boing|pop|cute|kiss|baby|toy|squeak|bloop|plop|xylophone|dễ thương",
          "cong_nghe": r"click|tick|beep|glitch|digital|tech|type|keyboard|robot|scan|zap|electro|blip",
          "co_dien": r"film|camera|shutter|typewriter|vinyl|projector|bell|retro"}


def _ds_draft(goc=None):
    goc = goc or os.environ.get("CAPCUT_DRAFT_DIR") or \
        str(Path.home() / "AppData/Local/CapCut/User Data/Projects/com.lveditor.draft")
    return glob.glob(os.path.join(goc, "*", "draft_content.json")) + \
        glob.glob(os.path.join(goc, "*", "Timelines", "*", "draft_content.json"))


def la_tieng_thu_vien(a):
    """Material audio có mã thư viện CapCut (không phải file người dùng tự nhập)."""
    if a.get("type") in ("extract_music", "record", "video_original_sound", "text_to_audio"):
        return False
    return bool(a.get("music_id") or a.get("effect_id") or a.get("resource_id") or a.get("third_resource_id"))


def vai_cho(ten):
    t = (ten or "").lower()
    return [v for v, r in VAI_TEN if re.search(r, t)]


def thu(goc=None):
    kho_cu = {x["ma"]: x for x in xem_kho()}
    them = 0
    for f in _ds_draft(goc):
        try:
            dc = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception:
            continue
        ten_draft = Path(f).parent.name if Path(f).parent.parent.name != "Timelines" else Path(f).parents[2].name
        mats = dc.get("materials", {})
        dur = {}
        for tr in dc.get("tracks", []):
            for sg in tr.get("segments", []):
                dur.setdefault(sg.get("material_id"), (sg.get("source_timerange") or sg.get("target_timerange") or {})
                               .get("duration"))
        for a in mats.get("audios", []):
            if not la_tieng_thu_vien(a):
                continue
            ma = str(a.get("music_id") or a.get("effect_id") or a.get("resource_id") or a.get("third_resource_id"))
            if ma in kho_cu:
                continue
            d = int(a.get("duration") or dur.get(a["id"]) or 0)
            if d and d > 6_000_000:          # nhạc nền dài, không phải tiếng nhấn
                continue
            mau = copy.deepcopy(a)
            kho_cu[ma] = {"ma": ma, "ten": a.get("name", ""), "loai": a.get("type", ""),
                          "nhom": a.get("category_name", ""), "dur_us": d, "vai": vai_cho(a.get("name")),
                          "phong_cach": [p for p, r in PC_TEN.items() if re.search(r, (a.get("name") or "").lower())],
                          "tu_draft": ten_draft, "mau": mau}
            them += 1
    KHO.parent.mkdir(exist_ok=True)
    KHO.write_text(json.dumps(sorted(kho_cu.values(), key=lambda x: x["ten"]), ensure_ascii=False, indent=1),
                   encoding="utf-8")
    ds = list(kho_cu.values())
    print(f"Kho tiếng CapCut: {len(ds)} tiếng (+{them} mới) -> {KHO}")
    for v in VAI:
        print(f"  {v:9s}", ", ".join(x["ten"] for x in ds if v in x["vai"])[:200] or "-")
    chua = [x["ten"] for x in ds if not x["vai"]]
    if chua:
        print("  chưa rõ vai (sửa khoá \"vai\" trong kho nếu muốn dùng):", ", ".join(chua)[:300])
    return ds


_cache = None


def xem_kho():
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(KHO.read_text(encoding="utf-8")) if KHO.exists() else []
        except Exception:
            _cache = []
    return _cache


def _ct_tieng():
    try:
        return json.loads(CT.read_text(encoding="utf-8")).get("tieng", {})
    except Exception:
        return {}


class BoChon:
    """Chọn tiếng cho từng vai, xoay vòng, ổn định theo dự án (`hat`), không lặp 1 tiếng liền nhau trong cùng vai
    và không 2 lần liền giống nhau trên toàn video."""

    def __init__(self, phong_cach="nang_dong", hat="", sfx_dir=None, thu_vien=True, da_dang="thuong"):
        self.pc, self.hat, self.dir = phong_cach, hat, Path(sfx_dir) if sfx_dir else SK / "sfx"
        ct = _ct_tieng()
        self.tu_tao = ct.get("tu_tao", {})
        self.thu_vien = thu_vien
        self.da_dang = da_dang
        self.dem, self.truoc = {}, None
        kho = xem_kho() if thu_vien else []
        self.tv = {}
        for v in VAI:
            ds = [x for x in kho if v in x.get("vai", [])]
            hop = [x for x in ds if self.pc in x.get("phong_cach", [])]
            # giữ tiếng hợp phong cách lên trước; "da_dang": "cao" -> dùng hết kho của vai
            ds = hop + [x for x in ds if x not in hop] if (da_dang == "cao" or len(hop) < 2) else hop
            ds.sort(key=lambda x: (x not in hop, hashlib.md5((hat + v + x["ma"]).encode()).hexdigest()))
            self.tv[v] = ds

    def _co(self, n):
        return (self.dir / f"{n}.wav").exists()

    def tu_tao_cho(self, vai, goi_y=None):
        """Tên tiếng tự tạo (file .wav trong sfx/) cho vai — xoay vòng trong danh sách theo phong cách."""
        ds = self.tu_tao.get(vai, {})
        pool = ds.get(self.pc) or ds.get("_") or []
        ho = self.tu_tao.get("_ho", {}).get(goi_y) if goi_y else None
        # chữ: tiếng LUÔN cùng họ với kiểu chữ hiện (góp ý 16/11), xoay trong họ; chỗ khác: theo vai, trừ khi đa dạng thấp
        if goi_y and (vai == "chu" or self.da_dang != "cao" or not pool):
            pool = ho or [goi_y]
        pool = [x for x in pool if self._co(x)] or ([goi_y] if goi_y and self._co(goi_y) else ["pop"])
        k = ("t", tuple(pool))
        i = self.dem.get(k, 0)
        n = pool[i % len(pool)]
        if n == self.truoc and len(pool) > 1:
            i += 1
            n = pool[i % len(pool)]
        self.dem[k] = i + 1
        self.truoc = n
        return n

    def thu_vien_cho(self, vai):
        """Mục tiếng thư viện CapCut cho vai (hoặc None)."""
        ds = self.tv.get(vai) or []
        if not ds:
            return None
        i = self.dem.get(("v", vai), 0)
        x = ds[i % len(ds)]
        if x["ma"] == self.truoc and len(ds) > 1:
            i += 1
            x = ds[i % len(ds)]
        self.dem[("v", vai)] = i + 1
        self.truoc = x["ma"]
        return x


def gan_vao_draft(draft_path, doi, total_us=None):
    """Đổi các đoạn tiếng tự tạo trên track SFX thành TIẾNG THƯ VIỆN CapCut.
    doi = [(giây bắt đầu, mục kho)]. Giữ nguyên vị trí + âm lượng; độ dài = tiếng thư viện nhưng không chồng đoạn sau
    trên cùng track. Trả số đoạn đã đổi."""
    p = Path(draft_path) / "draft_content.json"
    dc = json.loads(p.read_text(encoding="utf-8"))
    mats = dc["materials"]
    auds = {a["id"]: a for a in mats.get("audios", [])}
    total_us = total_us or dc.get("duration") or 0
    n = 0
    for tr in dc["tracks"]:
        if tr.get("type") != "audio" or not str(tr.get("name", "")).startswith("SFX"):
            continue
        segs = sorted(tr["segments"], key=lambda s: s["target_timerange"]["start"])
        for k, sg in enumerate(segs):
            st = sg["target_timerange"]["start"]
            muc = next((m for t, m in doi if abs(t * 1e6 - st) < 20_000), None)
            if not muc or sg["material_id"] not in auds:
                continue
            nxt = segs[k + 1]["target_timerange"]["start"] if k + 1 < len(segs) else total_us
            d_tv = int(muc.get("dur_us") or sg["target_timerange"]["duration"])
            d = max(33_333, min(d_tv, nxt - st, (total_us or st + d_tv) - st))
            mat = copy.deepcopy(muc["mau"])
            mat["id"] = sg["material_id"]
            if muc.get("dur_us"):
                mat["duration"] = int(muc["dur_us"])
            mats["audios"][mats["audios"].index(auds[sg["material_id"]])] = mat
            auds[mat["id"]] = mat
            sg["target_timerange"]["duration"] = d
            sg["source_timerange"] = {"start": 0, "duration": d}
            n += 1
    if n:
        p.write_text(json.dumps(dc, ensure_ascii=False), encoding="utf-8")
    return n


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    if a and a[0] == "thu":
        thu(a[1] if len(a) > 1 else None)
    elif a and a[0] == "xem":
        ds = xem_kho()
        print(f"{len(ds)} tiếng thư viện CapCut trong kho")
        for v in VAI:
            print(f"  {v:9s}", ", ".join(x["ten"] for x in ds if v in x["vai"]) or "- (dùng tiếng tự tạo)")
    else:
        print(__doc__)
