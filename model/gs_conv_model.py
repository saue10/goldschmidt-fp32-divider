#!/usr/bin/env python3
"""Golden model of the conventional full-width baseline; writes tb/vectors_conv.mem from tb/vectors.mem inputs."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gs_model import LUT, pack_mant, QNAN

F = 32
def conv_core(MA, MB):
    Y = LUT[(MB >> 16) & 0x7F]
    D0 = (MB * Y) >> 1; N0 = (MA * Y) >> 1
    F1 = (2 << F) - D0
    N1 = (N0 * F1) >> F; D1 = (D0 * F1) >> F
    F2 = (2 << F) - D1
    N2 = (N1 * F2) >> F
    assert 0 <= N2 < (1 << 34)
    return N2

def conv_div(a, b):
    sa, ea, fa = a >> 31, (a >> 23) & 255, a & 0x7FFFFF
    sb, eb, fb = b >> 31, (b >> 23) & 255, b & 0x7FFFFF
    s = sa ^ sb
    a_nan = ea == 255 and fa != 0; b_nan = eb == 255 and fb != 0
    a_inf = ea == 255 and fa == 0; b_inf = eb == 255 and fb == 0
    a_zero = ea == 0; b_zero = eb == 0
    if a_nan or b_nan or (a_zero and b_zero) or (a_inf and b_inf): return QNAN
    if a_inf or b_zero: return (s << 31) | 0x7F800000
    if a_zero or b_inf: return s << 31
    mant, adj = pack_mant(conv_core((1 << 23) | fa, (1 << 23) | fb))
    e = ea - eb + 127 + adj
    if e >= 255: return (s << 31) | 0x7F800000
    if e <= 0: return s << 31
    return (s << 31) | (e << 23) | mant

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    c = [0, 0, 0]; n = 0
    with open(os.path.join(here, "..", "tb", "vectors.mem")) as fi, open(os.path.join(here, "..", "tb", "vectors_conv.mem"), "w") as fo:
        for line in fi:
            a = int(line[0:8], 16); b = int(line[8:16], 16); r = int(line[24:32], 16)
            m = conv_div(a, b); d = abs(m - r); n += 1
            c[0 if d == 0 else 1 if d == 1 else 2] += 1
            fo.write("%08x%08x%08x%08x\n" % (a, b, m, r))
    print("vectors:", n, " conventional vs correctly-rounded [exact, 1ulp, >1ulp]:", c)
