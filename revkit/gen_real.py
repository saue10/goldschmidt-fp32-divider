#!/usr/bin/env python3
"""Generates RevLib .real files for the arithmetic blocks of the proposed and conventional dividers,
verifies each circuit by simulation against integer arithmetic, and totals NCV quantum cost.
NCV cost model: t1 (NOT)=1, t2 (CNOT)=1, t3 (Toffoli)=5.   Usage: python3 gen_real.py"""
import random, os, json
random.seed(1)

class Circ:
    def __init__(s, name): s.name = name; s.lines = []; s.idx = {}; s.gates = []; s.kind = {}
    def line(s, nm, kind):          # kind: 'in' (primary input), 'out' (primary output), 'anc' (constant 0, garbage)
        s.idx[nm] = len(s.lines); s.lines.append(nm); s.kind[nm] = kind; return nm
    def reg(s, p, n, kind): return [s.line("%s%d" % (p, i), kind) for i in range(n)]
    def x(s, t): s.gates.append((t,))
    def cx(s, c, t): s.gates.append((c, t))
    def ccx(s, c1, c2, t):
        if c1 == c2: s.cx(c1, t)
        else: s.gates.append((c1, c2, t))
    def qc(s): return sum({1: 1, 2: 1, 3: 5}[len(g)] for g in s.gates)
    def counts(s): return {k: sum(1 for g in s.gates if len(g) == k) for k in (1, 2, 3)}
    def sim(s, init):               # init: dict name->bit ; others 0
        st = [0] * len(s.lines)
        for k, v in init.items(): st[s.idx[k]] = v
        for g in s.gates:
            i = [s.idx[n] for n in g]
            if len(g) == 1: st[i[0]] ^= 1
            elif len(g) == 2: st[i[1]] ^= st[i[0]]
            else: st[i[2]] ^= st[i[0]] & st[i[1]]
        return {n: st[s.idx[n]] for n in s.lines}
    def write(s, path):
        n = len(s.lines); names = " ".join(s.lines)
        const = "".join("0" if s.kind[l] in ("anc", "out") else "-" for l in s.lines)
        garb = "".join("-" if s.kind[l] == "out" else "1" for l in s.lines)
        with open(path, "w") as f:
            f.write(".version 2.0\n.numvars %d\n.variables %s\n.inputs %s\n.outputs %s\n.constants %s\n.garbage %s\n.begin\n"
                    % (n, names, names, names, const, garb))
            for g in s.gates: f.write("t%d %s\n" % (len(g), " ".join(g)))
            f.write(".end\n")

def emit_add(c, X, Y, cin):
    """Cuccaro ripple-carry adder: Y = (X + Y) mod 2^w, X restored, cin (|0>) restored. 2(w-1) Toffolis."""
    w = len(X)
    def maj(a, b, z): c.cx(z, b); c.cx(z, a); c.ccx(a, b, z)
    def uma(a, b, z): c.ccx(a, b, z); c.cx(z, a); c.cx(a, b)
    ch = [cin] + X[:-1]
    for i in range(w - 1): maj(ch[i], Y[i], X[i])
    c.cx(X[w - 1], Y[w - 1]); c.cx(X[w - 2], Y[w - 1]) if w > 1 else None
    for i in range(w - 2, -1, -1): uma(ch[i], Y[i], X[i])

def build_mult(m, n, square=False):
    c = Circ(("square%dx%d" if square else "mult%dx%d") % (m, n))
    A = c.reg("a", m, "in"); B = A if square else c.reg("b", n, "in")
    P = c.reg("p", m + n, "out"); T = c.reg("q", m + 1, "anc"); cin = c.line("cin", "anc")
    for i in range(m): c.ccx(A[i], B[0], P[i])
    for j in range(1, n):
        for i in range(m): c.ccx(A[i], B[j], T[i])
        emit_add(c, T, P[j:j + m + 1], cin)
        for i in range(m): c.ccx(A[i], B[j], T[i])
    return c

def build_add(w):
    c = Circ("add%d" % w); X = c.reg("x", w, "in"); Y = c.reg("y", w, "out"); ci = c.line("cin", "anc")
    for i in range(w): pass
    emit_add(c, X, Y, ci); return c

def build_addsub(w):        # N = s ? N - p : N + p
    c = Circ("addsub%d" % w); s = c.line("s", "in"); X = c.reg("p", w, "in"); Y = c.reg("n", w, "out"); ci = c.line("cin", "anc")
    for y in Y: c.cx(s, y)
    emit_add(c, X, Y, ci)
    for y in Y: c.cx(s, y)
    return c

def build_constsub(w, K):   # y = (K - y) mod 2^w, in place
    c = Circ("constsub%d" % w); Y = c.reg("y", w, "out"); Kr = c.reg("k", w, "anc"); ci = c.line("cin", "anc")
    for y in Y: c.x(y)
    Kp = (K + 1) % (1 << w)
    ones = [Kr[i] for i in range(w) if (Kp >> i) & 1]
    for k in ones: c.x(k)
    emit_add(c, Kr, Y, ci)
    for k in ones: c.x(k)
    return c

def build_abs(w):           # sign-magnitude: low w-1 bits <- |x|, sign bit kept
    c = Circ("abs%d" % w); X = c.reg("x", w, "out"); Z = c.reg("z", w - 1, "anc"); ci = c.line("cin", "anc")
    for i in range(w - 1): c.cx(X[w - 1], X[i])
    c.cx(X[w - 1], Z[0]); emit_add(c, Z, X[:w - 1], ci); c.cx(X[w - 1], Z[0])
    return c

def build_copy(w):
    c = Circ("copy%d" % w); X = c.reg("x", w, "in"); Y = c.reg("y", w, "out")
    for i in range(w): c.cx(X[i], Y[i])
    return c

def bits(v, w): return [(v >> i) & 1 for i in range(w)]
def val(r, pre, w): return sum(r["%s%d" % (pre, i)] << i for i in range(w))
def check(c, kind, a, b):
    for _ in range(300):
        if kind == "mult":
            x = random.getrandbits(a); y = x if c.name.startswith("square") else random.getrandbits(b)
            ini = {"a%d" % i: v for i, v in enumerate(bits(x, a))}
            if not c.name.startswith("square"): ini.update({"b%d" % i: v for i, v in enumerate(bits(y, b))})
            r = c.sim(ini); assert val(r, "p", a + b) == x * y and val(r, "a", a) == x and r["cin"] == 0
        elif kind == "add":
            x = random.getrandbits(a); y = random.getrandbits(a)
            ini = {"x%d" % i: v for i, v in enumerate(bits(x, a))}; ini.update({"y%d" % i: v for i, v in enumerate(bits(y, a))})
            r = c.sim(ini); assert val(r, "y", a) == (x + y) % (1 << a) and val(r, "x", a) == x and r["cin"] == 0
        elif kind == "addsub":
            p = random.getrandbits(a - 8); n = random.getrandbits(a); s = random.getrandbits(1)
            ini = {"p%d" % i: v for i, v in enumerate(bits(p, a))}; ini.update({"n%d" % i: v for i, v in enumerate(bits(n, a))}); ini["s"] = s
            r = c.sim(ini); assert val(r, "n", a) == ((n - p) if s else (n + p)) % (1 << a) and r["cin"] == 0
        elif kind == "constsub":
            K = b; y = random.getrandbits(a)
            ini = {"y%d" % i: v for i, v in enumerate(bits(y, a))}
            r = c.sim(ini); assert val(r, "y", a) == (K - y) % (1 << a) and val(r, "k", a) == 0 and r["cin"] == 0
        elif kind == "abs":
            x = random.randint(-(1 << (a - 2)), (1 << (a - 2))); xs = x % (1 << a)
            ini = {"x%d" % i: v for i, v in enumerate(bits(xs, a))}
            r = c.sim(ini); assert val(r, "x", a - 1) == abs(x) and r["x%d" % (a - 1)] == (1 if x < 0 else 0) and r["cin"] == 0 and val(r, "z", a - 1) == 0
        elif kind == "copy":
            x = random.getrandbits(a); ini = {"x%d" % i: v for i, v in enumerate(bits(x, a))}
            r = c.sim(ini); assert val(r, "y", a) == x

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__)); out = os.path.join(here, "real"); os.makedirs(out, exist_ok=True)
    blocks = {}
    def reg_block(c, kind, a=0, b=0):
        check(c, kind, a, b); c.write(os.path.join(out, c.name + ".real"))
        blocks[c.name] = dict(lines=len(c.lines), gates=len(c.gates), t3=c.counts()[3], qc=c.qc())
    reg_block(build_mult(24, 10), "mult", 24, 10)
    reg_block(build_mult(23, 24), "mult", 23, 24)
    reg_block(build_mult(18, 18, square=True), "mult", 18, 18)
    reg_block(build_mult(16, 18), "mult", 16, 18)
    reg_block(build_mult(34, 34), "mult", 34, 34)
    reg_block(build_constsub(36, 1 << 33), "constsub", 36, 1 << 33)
    reg_block(build_constsub(34, 1 << 33), "constsub", 34, 1 << 33)
    reg_block(build_abs(36), "abs", 36)
    reg_block(build_addsub(34), "addsub", 34)
    reg_block(build_add(34), "add", 34)
    reg_block(build_copy(34), "copy", 34)
    designs = {
      "proposed (eps-form, truncated multipliers)": {"mult24x10": 2, "mult23x24": 1, "square18x18": 1, "mult16x18": 1,
                                                    "constsub36": 1, "abs36": 1, "addsub34": 1, "add34": 1},
      "conventional full-width": {"mult24x10": 2, "mult34x34": 3, "copy34": 1, "constsub34": 2},
    }
    res = {}
    for d, inst in designs.items():
        tot = dict(qc=0, t3=0, gates=0, lines=0)
        for b, k in inst.items():
            for key in tot: tot[key] += k * blocks[b][key]
        res[d] = tot
    print("%-14s %6s %7s %7s %9s" % ("block", "lines", "gates", "T3", "NCV-QC"))
    for b, v in blocks.items(): print("%-14s %6d %7d %7d %9d" % (b, v["lines"], v["gates"], v["t3"], v["qc"]))
    print()
    for d, v in res.items(): print("%-46s QC=%d  T3=%d  gates=%d  lines(sum, no reuse)=%d" % (d, v["qc"], v["t3"], v["gates"], v["lines"]))
    p = res["proposed (eps-form, truncated multipliers)"]["qc"]; q = res["conventional full-width"]["qc"]
    print("QC reduction vs conventional: %.2f%%" % (100 * (1 - p / q)))
    json.dump(dict(blocks=blocks, designs=res), open(os.path.join(here, "cost_summary.json"), "w"), indent=1)
    print("all circuits verified by simulation")
