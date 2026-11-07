`timescale 1ns / 1ps
// Pipelined version of the proposed divider: 4 register stages (S0, S1, S2, PACK), 1 result/cycle.
// Same arithmetic as gs_fp32_divider; latency = 4 clock edges (result of vector i visible after the
// 4th rising edge counting the edge that captures it).
module gs_fp32_divider_pipe (
    input         clk,
    input  [31:0] A,
    input  [31:0] B,
    output reg [31:0] RESULT
);
    // stage 0
    wire signed [25:0] E0_c; wire [33:0] N0_c;
    gs_stage0 S0 (.MA({1'b1, A[22:0]}), .MB({1'b1, B[22:0]}), .E0(E0_c), .N0(N0_c));
    reg signed [25:0] E0_r; reg [33:0] N0_r; reg [31:0] A0, B0;
    always @(posedge clk) begin E0_r <= E0_c; N0_r <= N0_c; A0 <= A; B0 <= B; end

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

    // pack / round
    wire [31:0] R_c;
    gs_pack PACK (.N2(N2_r), .A(A2), .B(B2), .RESULT(R_c));
    always @(posedge clk) RESULT <= R_c;
endmodule
