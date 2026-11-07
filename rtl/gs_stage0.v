`timescale 1ns / 1ps
// Stage 0: seed lookup, N0 = A*Y0, eps0 = 1 - B*Y0 (error term kept in signed Q-30 form).
module gs_stage0 (
    input  [23:0]        MA,      // 1.23 mantissa of A (hidden one included)
    input  [23:0]        MB,      // 1.23 mantissa of B
    output signed [25:0] E0,      // eps0, 30 fractional bits, |eps0| < 2^-7
    output [33:0]        N0       // A*Y0, 32 fractional bits
);
    wire [9:0] Y0;
    gs_recip_lut RECIP_LUT (.idx(MB[22:16]), .y0(Y0));

    wire [33:0] PB = MB * Y0;                         // 24x10, 33 fractional bits
    wire [33:0] PA = MA * Y0;                         // 24x10

    wire signed [35:0] e0_full = $signed(36'h2_0000_0000) - $signed({2'b00, PB}); // 1.0 - B*Y0
    wire signed [35:0] e0_sh   = e0_full >>> 3;       // floor to 30 fractional bits
    assign E0 = e0_sh[25:0];
    assign N0 = {1'b0, PA[33:1]};                     // floor to 32 fractional bits
endmodule
