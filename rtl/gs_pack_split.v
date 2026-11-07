`timescale 1ns / 1ps
// gs_pack split into two combinational halves for pipelining. Logic and priority order are identical to gs_pack.
// Half 1: normalise + round + exponent + special-case flags.   Half 2: final selection / packing.
module gs_pack_s1 (
    input  [33:0] N2,
    input  [31:0] A,
    input  [31:0] B,
    output [22:0] mant,
    output signed [10:0] e_fin,
    output        sign,
    output        nan_f,      // result is quiet NaN
    output        inf_f,      // result is infinity  (A inf or B zero)
    output        zero_f      // result is zero      (A zero or B inf)
);
    wire [7:0] ea = A[30:23], eb = B[30:23];
    wire a_nan  = (ea == 8'hFF) && (A[22:0] != 0);
    wire b_nan  = (eb == 8'hFF) && (B[22:0] != 0);
    wire a_inf  = (ea == 8'hFF) && (A[22:0] == 0);
    wire b_inf  = (eb == 8'hFF) && (B[22:0] == 0);
    wire a_zero = (ea == 8'h00);
    wire b_zero = (eb == 8'h00);
    assign sign   = A[31] ^ B[31];
    assign nan_f  = a_nan || b_nan || (a_zero && b_zero) || (a_inf && b_inf);
    assign inf_f  = a_inf || b_zero;
    assign zero_f = a_zero || b_inf;

    wire ge = |N2[33:32];
    wire [34:0] r_ge = {1'b0, N2} + 35'd256;
    wire [34:0] r_lt = {1'b0, N2} + 35'd128;
    wire [24:0] qq   = ge ? r_ge[33:9] : r_lt[32:8];
    wire        ov   = qq[24];
    assign mant = ov ? 23'd0 : qq[22:0];

    wire signed [10:0] e_base = $signed({3'b000, ea}) - $signed({3'b000, eb}) + 11'sd127;
    assign e_fin = e_base - (ge ? 11'sd0 : 11'sd1) + (ov ? 11'sd1 : 11'sd0);
endmodule

module gs_pack_s2 (
    input  [22:0] mant,
    input  signed [10:0] e_fin,
    input         sign, nan_f, inf_f, zero_f,
    output reg [31:0] RESULT
);
    always @(*) begin
        if (nan_f)                    RESULT = 32'h7FC00000;
        else if (inf_f)               RESULT = {sign, 8'hFF, 23'd0};
        else if (zero_f)              RESULT = {sign, 31'd0};
        else if (e_fin >= 11'sd255)   RESULT = {sign, 8'hFF, 23'd0};
        else if (e_fin <= 11'sd0)     RESULT = {sign, 31'd0};
        else                          RESULT = {sign, e_fin[7:0], mant};
    end
endmodule
