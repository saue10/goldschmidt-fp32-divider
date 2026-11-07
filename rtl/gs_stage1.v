`timescale 1ns / 1ps
// Stage 1: N1 = N0 + N0*eps0 (22-bit x 25-bit multiplier), eps1 = eps0^2 (18-bit squarer).
module gs_stage1 (
    input  [33:0]        N0,
    input  signed [25:0] E0,
    output [33:0]        N1,      // 32 fractional bits
    output [17:0]        E1       // eps1 = eps0^2, 30 fractional bits (always >= 0)
);
    wire [23:0] N0h = N0[33:10];                      // top bits of N0 (22 fractional bits)
    wire signed [50:0] p1 = $signed({1'b0, N0h}) * E0;
    wire signed [50:0] p1_sh = p1 >>> 20;
    wire signed [34:0] c1 = p1_sh[34:0];
    wire signed [34:0] n1s = $signed({1'b0, N0}) + c1;
    assign N1 = n1s[33:0];

    wire [25:0] mag = E0[25] ? (~E0 + 26'd1) : E0;    // |eps0|
    wire [17:0] mh  = mag[23:6];                      // 18 significant bits
    wire [35:0] sq  = mh * mh;
    assign E1 = sq[35:18];
endmodule
