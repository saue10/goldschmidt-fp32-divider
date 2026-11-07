`timescale 1ns / 1ps
// Truncated multi-precision Goldschmidt FP32 divider (epsilon formulation).
// Two iterations; only error terms are multiplied, so later multipliers are narrow:
//   seed  : 24x10 (x2)   N0 = A*Y0, D0 = B*Y0  (eps0 = 1 - D0)
//   iter 1: 22x25        N1 = N0 + N0*eps0 ;  18x18 squarer eps1 = eps0^2
//   iter 2: 16x18        N2 = N1 + N1*eps1   (no D2, no eps2)
module gs_fp32_divider (
    input  [31:0] A,
    input  [31:0] B,
    output [31:0] RESULT
);
    wire [23:0] MA = {1'b1, A[22:0]};
    wire [23:0] MB = {1'b1, B[22:0]};

    wire signed [25:0] E0;
    wire [33:0] N0, N1, N2;
    wire [17:0] E1;

    gs_stage0 STAGE0 (.MA(MA), .MB(MB), .E0(E0), .N0(N0));
    gs_stage1 STAGE1 (.N0(N0), .E0(E0), .N1(N1), .E1(E1));
    gs_stage2 STAGE2 (.N1(N1), .E1(E1), .N2(N2));
    gs_pack   PACK   (.N2(N2), .A(A), .B(B), .RESULT(RESULT));
endmodule
