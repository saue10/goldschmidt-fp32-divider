`timescale 1ns / 1ps
// Six-stage pipelined divider (1 result/cycle): input regs | S0 | S1 | S2 | pack-1 | pack-2 (output reg).
// Same arithmetic as gs_fp32_divider. Latency: result of a vector appears 6 clock edges after it is presented.
module gs_fp32_divider_pipe2 (
    input         clk,
    input  [31:0] A,
    input  [31:0] B,
    output reg [31:0] RESULT
);
    // stage R: input registers (removes the external input delay from stage 0)
    reg [31:0] Ar, Br;
    always @(posedge clk) begin Ar <= A; Br <= B; end

    // stage 0
    wire signed [25:0] E0_c; wire [33:0] N0_c;
    gs_stage0 S0 (.MA({1'b1, Ar[22:0]}), .MB({1'b1, Br[22:0]}), .E0(E0_c), .N0(N0_c));
    reg signed [25:0] E0_r; reg [33:0] N0_r; reg [31:0] A0, B0;
    always @(posedge clk) begin E0_r <= E0_c; N0_r <= N0_c; A0 <= Ar; B0 <= Br; end

    // stage 1
    wire [33:0] N1_c; wire [17:0] E1_c;
    gs_stage1 S1 (.N0(N0_r), .E0(E0_r), .N1(N1_c), .E1(E1_c));
    reg [33:0] N1_r; reg [17:0] E1_r; reg [31:0] A1, B1;
    always @(posedge clk) begin N1_r <= N1_c; E1_r <= E1_c; A1 <= A0; B1 <= B0; end

    // stage 2
    wire [33:0] N2_c;
    gs_stage2 S2 (.N1(N1_r), .E1(E1_r), .N2(N2_c));
    reg [33:0] N2_r; reg [31:0] A2, B2;
    always @(posedge clk) begin N2_r <= N2_c; A2 <= A1; B2 <= B1; end

    // pack half 1: round, exponent, special-case flags
    wire [22:0] mant_c; wire signed [10:0] e_c; wire sign_c, nan_c, inf_c, zero_c;
    gs_pack_s1 P1 (.N2(N2_r), .A(A2), .B(B2), .mant(mant_c), .e_fin(e_c), .sign(sign_c),
                   .nan_f(nan_c), .inf_f(inf_c), .zero_f(zero_c));
    reg [22:0] mant_r; reg signed [10:0] e_r; reg sign_r, nan_r, inf_r, zero_r;
    always @(posedge clk) begin mant_r <= mant_c; e_r <= e_c; sign_r <= sign_c; nan_r <= nan_c; inf_r <= inf_c; zero_r <= zero_c; end

    // pack half 2: final selection, output register
    wire [31:0] R_c;
    gs_pack_s2 P2 (.mant(mant_r), .e_fin(e_r), .sign(sign_r), .nan_f(nan_r), .inf_f(inf_r), .zero_f(zero_r), .RESULT(R_c));
    always @(posedge clk) RESULT <= R_c;
endmodule
