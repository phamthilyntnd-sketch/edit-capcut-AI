"""KHO MẪU CHỮ TIKTOK — 1.035 mẫu chữ thật (23 nhóm kiểu) lọc từ ~1.950 ảnh bìa video TikTok Việt Nam, 16 ngành (18–20/11/2026).

Dữ liệu: kho/mau-chu-tiktok.json (chỉ nhóm / ngành / loại video + công thức CapCut; KHÔNG lưu ảnh của người khác).
Dùng để chọn KIỂU CHỮ hợp ngành trước khi dựng, và tra công thức dựng lại từng nhóm trong CapCut.

Chạy:  mau_chu.py goi-y <ngành>     -> các nhóm kiểu chữ hay dùng ở ngành đó + bộ kiểu chữ skill nên dùng
       mau_chu.py nhom <số>         -> mô tả + cách làm trong CapCut của 1 nhóm
       mau_chu.py bo                -> các bộ kiểu chữ skill dựng được tự động (bo_chu trong cau-hinh.json)
Trong code: bo_cho_nganh(nganh) -> tên bộ kiểu chữ (chu.BO_CHU) hợp ngành nhất.
"""
import json, sys, unicodedata
from collections import Counter
from pathlib import Path

SK = Path(__file__).resolve().parent.parent
KHO = SK / "kho" / "mau-chu-tiktok.json"

# mã ngành của hồ sơ (thuong-hieu/*.json "nganh", bộ dùng chung nganh.py) -> tên ngành trong kho
MA_NGANH = {"my-pham": "Mỹ phẩm", "am-thuc": "Ẩm thực", "do-uong": "Đồ uống", "gia-dung": "Gia dụng", "thoi-trang": "Thời trang",
            "cong-nghe": "Công nghệ", "cong-nghe-saas": "Công nghệ", "dien-tu": "Công nghệ", "me-va-be": "Mẹ và bé",
            "spa": "Spa – làm đẹp", "spa-tham-my": "Spa – làm đẹp", "du-lich": "Du lịch", "bat-dong-san": "Nhà – bất động sản",
            "noi-that": "Nhà – bất động sản", "quan-cafe": "Quán cafe", "xe": "Xe", "o-to-xe-may": "Xe",
            "thuc-pham-chuc-nang": "Thực phẩm chức năng", "tpcn": "Thực phẩm chức năng", "trang-suc": "Trang sức",
            "giao-duc": "Giáo dục", "tiktok-shop": "TikTok Shop"}
# nhóm kiểu chữ trong kho -> bộ kiểu chữ skill dựng tự động được (chu.BO_CHU)
NHOM_BO = {1: "tiktok", 2: "hop_trang", 3: "tiktok", 4: "toi_gian", 5: "toi_gian", 6: "toi_gian", 7: "vien_den",
           8: "thuong_hieu", 9: "vien_den", 10: "thuong_hieu", 11: "vien_den", 12: "toi_gian", 13: "vien_den",
           14: "hop_trang", 15: "tiktok", 16: "vien_den", 17: "ban_hang_nong", 18: "hop_trang", 19: "thuong_hieu",
           21: "vien_den", 22: "tiktok", 24: "vien_den", 25: "tiktok"}


def _bo_dau(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn").replace("đ", "d")


def kho():
    return json.loads(KHO.read_text(encoding="utf-8"))


def ten_nganh(nganh):
    """'my-pham' / 'Mỹ phẩm' / 'my pham' -> tên ngành trong kho (None nếu không có)."""
    if not nganh:
        return None
    if nganh in MA_NGANH:
        return MA_NGANH[nganh]
    ten = {_bo_dau(m["nganh"]) : m["nganh"] for m in kho()["mau"]}
    k = _bo_dau(nganh).replace("-", " ")
    return ten.get(k) or next((v for kk, v in ten.items() if k in kk or kk.split(" ")[0] == k.split(" ")[0]), None)


def thong_ke(nganh=None):
    d = kho()
    ten = ten_nganh(nganh) if nganh else None
    mau = [m for m in d["mau"] if not ten or m["nganh"] == ten]
    return ten, Counter(m["nhom"] for m in mau), d["nhom"]


def bo_cho_nganh(nganh):
    """Bộ kiểu chữ (chu.BO_CHU) hợp ngành nhất: cộng điểm các nhóm kiểu chữ hay gặp ở ngành đó."""
    ten, c, _ = thong_ke(nganh)
    if not ten or not c:
        return "thuong_hieu"
    diem = Counter()
    for nhom, so in c.items():
        diem[NHOM_BO.get(int(nhom), "thuong_hieu")] += so
    return diem.most_common(1)[0][0]


def _in_goi_y(nganh):
    ten, c, nh = thong_ke(nganh)
    if nganh and not ten:
        print(f"Không có ngành '{nganh}' trong kho. Có: {', '.join(sorted({m['nganh'] for m in kho()['mau']}))}")
        return
    print(f"Ngành: {ten or 'tất cả'} — {sum(c.values())} mẫu")
    for nhom, so in c.most_common(6):
        n = nh[str(nhom)]
        print(f"  nhóm {nhom:>2} ({so} mẫu) {n['ten']} -> bộ skill: {NHOM_BO.get(int(nhom))}\n      CapCut: {n['capcut']}")
    if ten:
        print(f"Bộ kiểu chữ nên dùng: \"bo_chu\": \"{bo_cho_nganh(nganh)}\"  (hoặc \"bo_chu\": \"tu_dong\")")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    a = sys.argv[1:]
    if not a or a[0] not in ("goi-y", "nhom", "bo"):
        print(__doc__)
    elif a[0] == "goi-y":
        _in_goi_y(" ".join(a[1:]) or None)
    elif a[0] == "nhom":
        n = kho()["nhom"].get(a[1]) if len(a) > 1 else None
        print(json.dumps(n, ensure_ascii=False, indent=1) if n else "Nhóm: " + ", ".join(f"{k}. {v['ten']}" for k, v in kho()["nhom"].items()))
    else:
        sys.path.insert(0, str(Path(__file__).parent))
        import chu
        for k, b in chu.BO_CHU.items():
            print(f"  {k:<14} {b['ten']}  (nhóm kho: {', '.join(map(str, b['nhom']))})")
