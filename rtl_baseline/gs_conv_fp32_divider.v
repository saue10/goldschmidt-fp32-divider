`timescale 1ns / 1ps
// Conventional full-width Goldschmidt FP32 divider (baseline for iso-accuracy comparison).
// Same seed ROM, same Q2.32 internal precision, same packing as the proposed design;
// D2 is also omitted (so the baseline is not penalised for it). Three full 34x34 multiplications.
module gs_conv_fp32_divider (
    input  [31:0] A,
    input  [31:0] B,
    output [31:0] RESULT
);
    wire [23:0] MA = {1'b1, A[22:0]};
    wire [23:0] MB = {1'b1, B[22:0]};
    wire [9:0]  Y0;
    gs_recip_lut RECIP_LUT (.idx(MB[22:16]), .y0(Y0));

    wire [33:0] PB = MB * Y0;
    wire [33:0] PA = MA * Y0;
    wire [33:0] D0 = {1'b0, PB[33:1]};                // Q2.32
    wire [33:0] N0 = {1'b0, PA[33:1]};

    wire [33:0] F1 = 34'h2_0000_0000 - D0;            // 2.0 - D0
    wire [67:0] pn1 = N0 * F1;
    wire [67:0] pd1 = D0 * F1;
    wire [33:0] N1 = pn1[65:32];
    wire [33:0] D1 = pd1[65:32];

    wire [33:0] F2 = 34'h2_0000_0000 - D1;            // 2.0 - D1
    wire [67:0] pn2 = N1 * F2;
    wire [33:0] N2 = pn2[65:32];

    gs_pack PACK (.N2(N2), .A(A), .B(B), .RESULT(RESULT));
endmodule
