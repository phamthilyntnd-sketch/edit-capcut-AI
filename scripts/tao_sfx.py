"""Tạo bộ TIẾNG NHẤN (SFX) riêng của skill bằng tổng hợp âm thanh — không dùng file của ai, không bản quyền.

Chạy:  python scripts/tao_sfx.py            -> sfx/*.wav (48 kHz, stereo, đỉnh ~ -3 dBFS)
Tên tiếng khớp với dung.py: whoosh swipe whip pop bubble click tick notify ding chime sparkle shutter riser cash
(máy có bộ bo-skill-video thì dung.py ưu tiên kho tiếng của bộ đó; xem may.json "sfx").
"""
import sys, wave
from pathlib import Path
import numpy as np

SR = 48000
OUT = Path(__file__).resolve().parent.parent / "sfx"
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(n, a=0.005, r=0.2):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def sweep_noise(d, f0, f1, q=0.35):
    """Tiếng gió quét: ồn trắng lọc dải quanh tần số quét f0 -> f1 (lọc bằng FFT từng khúc)."""
    n = int(SR * d)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    blk = 1024
    for i in range(0, n, blk // 2):
        seg = x[i:i + blk]
        if len(seg) < 8:
            break
        w = np.hanning(len(seg))
        F = np.fft.rfft(seg * w)
        fr = np.fft.rfftfreq(len(seg), 1 / SR)
        fc = f0 * (f1 / f0) ** (i / n)
        F *= np.exp(-((np.log(fr + 1) - np.log(fc)) ** 2) / (2 * q ** 2))
        out[i:i + len(seg)] += np.fft.irfft(F, len(seg))
    return out


def tone(d, f, dec=8.0, harm=((1, 1.0),)):
    tt = t(d)
    return sum(a * np.sin(2 * np.pi * f * k * tt) for k, a in harm) * np.exp(-dec * tt)


def chirp(d, f0, f1, dec=10.0):
    tt = t(d)
    ph = 2 * np.pi * (f0 * tt + (f1 - f0) * tt ** 2 / (2 * d))
    return np.sin(ph) * np.exp(-dec * tt)


def mix(*parts):
    n = max(len(p) for _, p in parts)
    y = np.zeros(n)
    for off, p in parts:
        k = int(off * SR)
        y[k:k + len(p)] += p[:max(0, n - k)]
    return y


def save(name, y, pan=0.0):
    y = y / (np.abs(y).max() + 1e-9) * 10 ** (-3 / 20)
    st = np.stack([y * (1 - pan), y * (1 + pan)], 1)
    OUT.mkdir(exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype("<i2").tobytes())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    w = sweep_noise(0.55, 300, 3200); save("whoosh", w * env(len(w), 0.18, 0.3))
    s = sweep_noise(0.32, 1800, 6000, 0.3); save("swipe", s * env(len(s), 0.05, 0.2))
    p = sweep_noise(0.2, 900, 7000, 0.25); save("whip", p * env(len(p), 0.01, 0.12))
    save("pop", chirp(0.13, 900, 280, 28))
    save("bubble", chirp(0.16, 300, 1300, 18) + 0.3 * chirp(0.16, 600, 2200, 22))
    c = mix((0, rng.standard_normal(int(0.004 * SR))), (0, tone(0.05, 2400, 90))); save("click", c)
    save("tick", mix((0, rng.standard_normal(int(0.002 * SR)) * 0.6), (0, tone(0.035, 3800, 140))))
    save("notify", mix((0, tone(0.18, 880, 12, ((1, 1), (2, .3)))), (0.12, tone(0.3, 1320, 9, ((1, 1), (2, .3))))))
    save("ding", tone(0.9, 1318, 4.5, ((1, 1), (2.76, .35), (5.4, .12))))
    save("chime", mix((0, tone(1.2, 1047, 3.5, ((1, 1), (3, .2)))), (0.09, tone(1.1, 1319, 3.5, ((1, 1), (3, .2)))),
                      (0.18, tone(1.0, 1568, 3.5, ((1, 1), (3, .2))))))
    sp = np.zeros(int(0.7 * SR))
    for i in range(14):
        o, f = rng.uniform(0, 0.5), rng.uniform(2500, 6500)
        b = tone(0.18, f, 30)
        k = int(o * SR); sp[k:k + len(b)] += b[:len(sp) - k] * rng.uniform(.4, 1)
    save("sparkle", sp)
    sh = mix((0, rng.standard_normal(int(0.03 * SR)) * env(int(0.03 * SR), 0.001, 0.025)),
             (0.07, rng.standard_normal(int(0.05 * SR)) * env(int(0.05 * SR), 0.001, 0.04) * 0.8))
    save("shutter", sh)
    r = sweep_noise(1.0, 200, 5000, 0.4) * np.linspace(0.05, 1, int(SR * 1.0)) ** 2 + 0.25 * chirp(1.0, 200, 1200, 0.0)
    save("riser", r * env(len(r), 0.05, 0.08))
    cash = mix((0, tone(0.7, 2093, 5, ((1, 1), (2.4, .4)))), (0.02, rng.standard_normal(int(0.25 * SR)) *
                                                              np.exp(-14 * t(0.25)) * 0.5))
    save("cash", cash)
    # ĐA DẠNG (20/11): biến thể cùng họ để xoay vòng, không nghe 1 tiếng lặp mãi
    w2 = sweep_noise(0.42, 2400, 500, 0.3); save("whoosh-2", w2 * env(len(w2), 0.12, 0.22))
    sw = sweep_noise(0.24, 3000, 9000, 0.22); save("swish", sw * env(len(sw), 0.02, 0.16))
    save("pop-2", mix((0, chirp(0.11, 1400, 420, 34)), (0, 0.25 * chirp(0.08, 2600, 900, 40))))
    save("boing", chirp(0.35, 180, 520, 7) * (1 + 0.4 * np.sin(2 * np.pi * 18 * t(0.35))))
    save("snap", mix((0, rng.standard_normal(int(0.012 * SR)) * env(int(0.012 * SR), 0.0005, 0.01)),
                     (0, tone(0.06, 1700, 70))))
    im = mix((0, chirp(0.45, 150, 45, 7)), (0, rng.standard_normal(int(0.08 * SR)) * np.exp(-40 * t(0.08)) * 0.6))
    save("impact", im)
    save("coin", mix((0, tone(0.12, 1976, 22, ((1, 1), (2, .3)))), (0.07, tone(0.6, 2637, 6, ((1, 1), (2, .25))))))
    save("pluck", tone(0.4, 659, 11, ((1, 1), (2, .5), (3, .25))))
    save("bell", tone(1.3, 784, 3, ((1, 1), (1.5, .6), (2.0, .4), (3.01, .2))))
    z = sweep_noise(0.3, 700, 2600, 0.18) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 60 * t(0.3))))
    save("zip", z * env(len(z), 0.01, 0.08))
    save("blip", mix((0, tone(0.07, 1046, 40)), (0.07, tone(0.09, 1568, 35))))
    rs = sweep_noise(0.6, 300, 3500, 0.35) * np.linspace(0.1, 1, int(SR * 0.6)) ** 2
    save("riser-2", rs * env(len(rs), 0.02, 0.05))
    print("Đã tạo:", ", ".join(sorted(x.stem for x in OUT.glob("*.wav"))), "->", OUT)


if __name__ == "__main__":
    main()
