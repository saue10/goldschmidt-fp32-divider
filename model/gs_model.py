#!/usr/bin/env python3
"""Bit-accurate golden model of gs_fp32_divider (epsilon-form truncated Goldschmidt).
Mirrors the Verilog in rtl/ line by line. Run:  python3 gs_model.py
Writes tb/vectors.mem and prints accuracy statistics."""
import random, math, os, sys
import numpy as np

K, W, F, E0F, N0F, Q, E1F, M = 7, 10, 32, 30, 22, 18, 30, 14   # design parameters
FR = 23 + W                                                      # frac bits of A*Y0, B*Y0

def lut():
    t = []
    for i in range(1 << K):
        lo = 1 + i / 2**K; hi = 1 + (i + 1) / 2**K
        t.append(min(int(round(2 / (lo + hi) * 2**W)), (1 << W) - 1))
    return t
LUT = lut()

def mant_core(MA, MB):
    """MA, MB: 24-bit mantissas with hidden one. Returns N2 (34-bit, 32 frac bits)."""
    idx = (MB >> 16) & 0x7F
    Y = LUT[idx]
    PB = MB * Y; PA = MA * Y
    e0 = (1 << FR) - PB
    e0t = e0 >> 3                              # arithmetic shift, 30 frac bits, signed
    assert -(1 << 24) < e0t < (1 << 24)
    N0 = PA >> 1                               # 32 frac bits
    N0h = N0 >> 10                             # 22 frac bits
    c1 = (N0h * e0t) >> 20
    N1 = N0 + c1
    mag = abs(e0t); mh = mag >> 6              # 18-bit
    assert mh < (1 << 18)
    e1 = (mh * mh) >> 18                       # eps1 = eps0^2, 30 frac bits
    N1h = N1 >> 18                             # 14 frac bits
    c2 = (N1h * e1) >> 12
    N2 = N1 + c2
    assert 0 <= N2 < (1 << 34)
    return N2

def pack_mant(N2):
    ge = N2 >= (1 << 32)
    q = ((N2 + 256) >> 9) if ge else ((N2 + 128) >> 8)
    ov = (q >> 24) & 1
    mant = 0 if ov else (q & 0x7FFFFF)
    return mant, (0 if ge else -1) + ov

QNAN = 0x7FC00000
def div_fp32(a, b):
    sa, ea, fa = a >> 31, (a >> 23) & 255, a & 0x7FFFFF
    sb, eb, fb = b >> 31, (b >> 23) & 255, b & 0x7FFFFF
    s = sa ^ sb
    a_nan = ea == 255 and fa != 0; b_nan = eb == 255 and fb != 0
    a_inf = ea == 255 and fa == 0; b_inf = eb == 255 and fb == 0
    a_zero = ea == 0; b_zero = eb == 0                # subnormals flushed (DAZ)
    if a_nan or b_nan or (a_zero and b_zero) or (a_inf and b_inf): return QNAN
    if a_inf or b_zero: return (s << 31) | 0x7F800000
    if a_zero or b_inf: return s << 31
    mant, adj = pack_mant(mant_core((1 << 23) | fa, (1 << 23) | fb))
    e = ea - eb + 127 + adj
    if e >= 255: return (s << 31) | 0x7F800000
    if e <= 0: return s << 31                          # FTZ
    return (s << 31) | (e << 23) | mant

def ref_div(a, b):
    """Correctly rounded (RNE) reference with the same special-case policy (normal operands only)."""
    ea, fa = (a >> 23) & 255, a & 0x7FFFFF; eb, fb = (b >> 23) & 255, b & 0x7FFFFF
    s = (a >> 31) ^ (b >> 31)
    A = (1 << 23) | fa; B = (1 << 23) | fb
    ge = A >= B; sh = 23 if ge else 24
    num = A << sh; q, r = divmod(num, B)
    if 2 * r > B or (2 * r == B and q & 1): q += 1
    e = ea - eb + 127 + (0 if ge else -1)
    if q >> 24: q >>= 1; e += 1
    if e >= 255: return (s << 31) | 0x7F800000
    if e <= 0: return s << 31
    return (s << 31) | (e << 23) | (q & 0x7FFFFF)

def stats(n=1_000_000, seed=11):
    rng = np.random.default_rng(seed)
    A = (1 << 23) | rng.integers(0, 1 << 23, n, dtype=np.int64)
    B = (1 << 23) | rng.integers(0, 1 << 23, n, dtype=np.int64)
    L = np.array(LUT, dtype=np.int64)
    Y = L[(B >> 16) & 0x7F]
    PB = B * Y; PA = A * Y
    e0t = ((1 << FR) - PB) >> 3
    N0 = PA >> 1
    N1 = N0 + (((N0 >> 10) * e0t) >> 20)
    mh = np.abs(e0t) >> 6
    e1 = (mh * mh) >> 18
    N2 = N1 + (((N1 >> 18) * e1) >> 12)
    ge = N2 >= (1 << 32)
    Qv = np.where(ge, (N2 + 256) >> 9, (N2 + 128) >> 8)
    ov = Qv >> 24
    Qv = np.where(ov == 1, Qv >> 1, Qv); E = np.where(ge, 0, -1) + ov
    sh = np.where(A >= B, 23, 24); num = A << sh; qq = num // B; r = num - qq * B
    up = (2 * r > B) | ((2 * r == B) & ((qq & 1) == 1)); qq = qq + up
    ovr = qq >> 24; qq = np.where(ovr == 1, qq >> 1, qq); Er = np.where(A >= B, 0, -1) + ovr
    d = np.abs(Qv - qq); bad = E != Er
    return dict(n=n, exact=float(np.mean((d == 0) & ~bad)), one_ulp=float(np.mean((d == 1) & ~bad)),
                gt1=float(np.mean((d > 1) | bad)), max_ulp=int(d.max()), seed_worst_eps0=float(np.abs(e0t).max() / 2**30))

def make_vectors(path, nrand=20000, seed=5):
    rnd = random.Random(seed); vs = []
    def f(s, e, m): return (s << 31) | (e << 23) | m
    sp = [0x00000000, 0x80000000, 0x7F800000, 0xFF800000, 0x7FC00000, 0x3F800000, 0xBF800000, 0x00000001,
          0x007FFFFF, 0x7F7FFFFF, 0x00800000, 0x40000000, 0x3F000000, 0x7F000000, 0x01000000]
    for a in sp:
        for b in sp: vs.append((a, b))
    vs += [(0x41200000, 0x40000000), (0x3F800000, 0x3F800000), (0x41CC0000, 0x3FC00000), (0x42C80000, 0x40800000), (0x40F00000, 0x40200000)]
    for _ in range(nrand):
        a = f(rnd.getrandbits(1), rnd.randint(1, 254), rnd.getrandbits(23))
        b = f(rnd.getrandbits(1), rnd.randint(1, 254), rnd.getrandbits(23)); vs.append((a, b))
    for _ in range(nrand):   # moderate exponents (no over/underflow)
        a = f(rnd.getrandbits(1), rnd.randint(100, 150), rnd.getrandbits(23))
        b = f(rnd.getrandbits(1), rnd.randint(100, 150), rnd.getrandbits(23)); vs.append((a, b))
    with open(path, "w") as fh:
        for a, b in vs:
            ea, eb = (a >> 23) & 255, (b >> 23) & 255
            normal = 0 < ea < 255 and 0 < eb < 255
            m = div_fp32(a, b); r = ref_div(a, b) if normal else m
            fh.write("%08x%08x%08x%08x\n" % (a, b, m, r))
    return len(vs)

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    n = make_vectors(os.path.join(here, "..", "tb", "vectors.mem"))
    print("vectors written:", n)
    st = stats(); print(st)
    # emit LUT for Verilog
    with open(os.path.join(here, "..", "rtl", "gs_recip_lut.v"), "w") as fh:
        fh.write("`timescale 1ns / 1ps\n// 128-entry reciprocal seed ROM, index = B mantissa fraction [22:16].\n"
                 "// y0 = round(1024 * 2/(b_lo+b_hi)), Q0.10 (minimax relative error over each interval).\n"
                 "module gs_recip_lut (\n    input      [6:0] idx,\n    output reg [9:0] y0\n);\n    always @(*) begin\n        case (idx)\n")
        for i, v in enumerate(LUT): fh.write("            7'd%d: y0 = 10'd%d;\n" % (i, v))
        fh.write("            default: y0 = 10'd512;\n        endcase\n    end\nendmodule\n")
