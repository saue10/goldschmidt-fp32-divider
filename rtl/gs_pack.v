`timescale 1ns / 1ps
// Normalise, round-to-nearest, pack IEEE-754 binary32. Special cases: NaN, Inf, zero handled;
// subnormal inputs are treated as zero (DAZ) and underflow flushes to zero (FTZ).
module gs_pack (
    input  [33:0] N2,
    input  [31:0] A,
    input  [31:0] B,
    output reg [31:0] RESULT
);
    wire [7:0] ea = A[30:23], eb = B[30:23];
    wire a_nan  = (ea == 8'hFF) && (A[22:0] != 0);
    wire b_nan  = (eb == 8'hFF) && (B[22:0] != 0);
    wire a_inf  = (ea == 8'hFF) && (A[22:0] == 0);
    wire b_inf  = (eb == 8'hFF) && (B[22:0] == 0);
    wire a_zero = (ea == 8'h00);
    wire b_zero = (eb == 8'h00);
    wire sign   = A[31] ^ B[31];

    wire ge = |N2[33:32];                              // N2 >= 1.0
    wire [34:0] r_ge = {1'b0, N2} + 35'd256;           // round at bit 9
    wire [34:0] r_lt = {1'b0, N2} + 35'd128;           // round at bit 8
    wire [24:0] qq   = ge ? r_ge[33:9] : r_lt[32:8];
    wire        ov   = qq[24];                         // rounded up to 2.0
    wire [22:0] mant = ov ? 23'd0 : qq[22:0];

    wire signed [10:0] e_base = $signed({3'b000, ea}) - $signed({3'b000, eb}) + 11'sd127;
    wire signed [10:0] e_fin  = e_base - (ge ? 11'sd0 : 11'sd1) + (ov ? 11'sd1 : 11'sd0);

    always @(*) begin
        if (a_nan || b_nan || (a_zero && b_zero) || (a_inf && b_inf))
            RESULT = 32'h7FC00000;
        else if (a_inf || b_zero)
            RESULT = {sign, 8'hFF, 23'd0};
        else if (a_zero || b_inf)
            RESULT = {sign, 31'd0};
        else if (e_fin >= 11'sd255)
            RESULT = {sign, 8'hFF, 23'd0};
        else if (e_fin <= 11'sd0)
            RESULT = {sign, 31'd0};
        else
            RESULT = {sign, e_fin[7:0], mant};
    end
endmodule
