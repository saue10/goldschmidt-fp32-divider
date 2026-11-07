#!/usr/bin/env python3
"""Analytic T-count / T-depth estimate of the arithmetic blocks in the Clifford+T model used by Gayathri et al. (2021):
logical-AND = 4 T (T-depth 2, uncompute free), n-bit Gidney adder = 4n T (T-depth 2n); CNOT/NOT/copy free.
Multiplier m x n = row 0: m ANDs into the product; rows 1..n-1: m ANDs into a temp register + (m+1)-bit adder.
This is an ANALYTIC estimate for the same circuit structure as gen_real.py, not a RevKit result."""
def mult_T(m, n):  return 4*m + (n-1)*(4*m + 4*(m+1))
def mult_D(m, n):  return 2 + (n-1)*(2 + 2*(m+1))
def add_T(w): return 4*w
def add_D(w): return 2*w
blocks = {
 "mult24x10": (mult_T(24,10), mult_D(24,10)),
 "mult23x24": (mult_T(23,24), mult_D(23,24)),
 "square18x18": (mult_T(18,18), mult_D(18,18)),
 "mult16x18": (mult_T(16,18), mult_D(16,18)),
 "mult34x34": (mult_T(34,34), mult_D(34,34)),
 "constsub36": (add_T(36), add_D(36)), "constsub34": (add_T(34), add_D(34)),
 "abs36": (add_T(35), add_D(35)), "addsub34": (add_T(34), add_D(34)), "add34": (add_T(34), add_D(34)),
}
B = {k: v[0] for k, v in blocks.items()}; D = {k: v[1] for k, v in blocks.items()}
prop = 2*B["mult24x10"] + B["mult23x24"] + B["square18x18"] + B["mult16x18"] + B["constsub36"] + B["abs36"] + B["addsub34"] + B["add34"]
conv = 2*B["mult24x10"] + 3*B["mult34x34"] + 2*B["constsub34"]
# T-depth: stage chain with independent products in parallel (optimistic) and fully serialized (pessimistic)
d_prop_par = D["mult24x10"] + D["constsub36"] + D["abs36"] + D["mult23x24"] + D["addsub34"] + D["mult16x18"] + D["add34"]
d_prop_ser = 2*D["mult24x10"] + D["constsub36"] + D["abs36"] + D["mult23x24"] + D["square18x18"] + D["addsub34"] + D["mult16x18"] + D["add34"]
d_conv_par = D["mult24x10"] + D["constsub34"] + D["mult34x34"] + D["constsub34"] + D["mult34x34"]
d_conv_ser = 2*D["mult24x10"] + 2*D["constsub34"] + 3*D["mult34x34"]
for k, v in blocks.items(): print("%-12s T=%6d  Tdepth=%5d" % (k, v[0], v[1]))
print("proposed   T=%d  (%.1f%% below conventional)  T-depth ~%d (parallel) / %d (serial)" % (prop, 100*(1-prop/conv), d_prop_par, d_prop_ser))
print("conventional T=%d  T-depth ~%d (parallel) / %d (serial)" % (conv, d_conv_par, d_conv_ser))
# published mantissa-only figures from Gayathri et al. 2021 components
print("published mantissa-only: restoring %d, non-restoring %d, Goldschmidt (mult+sub) %d" % (9936+2208, 2208+2208, 95232+19825))
print("proposed vs published Goldschmidt mantissa: %.1f%% lower" % (100*(1-prop/(95232+19825))))
