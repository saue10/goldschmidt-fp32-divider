# Truncated multi-precision Goldschmidt FP32 divider (error-term form)

Supplementary material for: *A Truncated Multi-Precision Goldschmidt Divider in Error-Term Form:
Reversible-Logic Cost and FPGA Implementation* (S. Rai, P. Saha, S. Majumdar).

## Contents
| Folder | What it holds |
|---|---|
| `rtl/` | Proposed divider: combinational `gs_fp32_divider.v`, 6-stage pipelined `gs_fp32_divider_pipe2.v` (also the 4-stage `gs_fp32_divider_pipe.v`), stages, seed ROM, rounding/packing |
| `rtl_baseline/` | Conventional full-width Goldschmidt baseline `gs_conv_fp32_divider.v` (uses `rtl/gs_recip_lut.v` and `rtl/gs_pack.v`) |
| `tb/` | Self-checking testbenches and test vectors (`vectors.mem`, `vectors_conv.mem`; 40,230 vectors) |
| `model/` | Bit-accurate Python models (`gs_model.py`, `gs_conv_model.py`); regenerate vectors and the seed ROM |
| `revkit/` | Generator for the reversible blocks (`gen_real.py`), the `.real` circuits (`real/`), and the analytic Clifford+T estimate (`tcount_clifford_t.py`) |
| `scripts/` | Vivado out-of-context flow (`vivado_flow.tcl`, not exercised by the authors; the reported results were obtained in the Vivado GUI) |

## Reproducing the results
**Accuracy (model):** `python3 model/gs_model.py` prints the statistics over 10^6 random mantissa pairs and rewrites `tb/vectors.mem`
and `rtl/gs_recip_lut.v`. `python3 model/gs_conv_model.py` writes `tb/vectors_conv.mem`.

**RTL simulation (Vivado XSim):** add `rtl/*.v` (or `rtl_baseline/*.v` plus `rtl/gs_recip_lut.v`, `rtl/gs_pack.v`) as design sources and a testbench
from `tb/` as the simulation top. Place the vector file in the simulator working directory
(for example `<project>.sim/sim_1/behav/xsim/`). Expected output: `RTL-vs-model mismatches=0` and `PASS`.
Combinational proposed: 39,725 exact / 505 at 1 ULP / 0 above; conventional: 40,171 / 59 / 0.
Pipelined testbenches use `vectors.mem` (4-stage: `tb_gs_fp32_divider_pipe.v`, 6-stage: `tb_gs_fp32_divider_pipe2.v`).

**Reversible costs:** `python3 revkit/gen_real.py` regenerates `revkit/real/*.real`, simulates every circuit against integer arithmetic,
and prints NCV costs. RevKit: `read_real real/<block>.real` then `ps -c` (see `revkit/revkit_commands.txt`).
`python3 revkit/tcount_clifford_t.py` prints the analytic Clifford+T estimate (not a RevKit result).

## Design policy
Round to nearest without a sticky bit; results are within 1 ULP of the correctly rounded quotient. Subnormal inputs are treated as zero and
underflow flushes to zero; NaN, infinity and division by zero follow IEEE 754.

## License
MIT (see `LICENSE`). If you use this work, please cite the paper above.
