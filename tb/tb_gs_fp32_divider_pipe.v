`timescale 1ns / 1ps
// Pipelined divider testbench: uses vectors.mem (same as the combinational design). Result of vector i
// appears 4 clock edges after it is presented, so it is checked at the negedge when vector i+4 is presented.
module tb_gs_fp32_divider_pipe;
    parameter NVEC = 40230;
    reg  [127:0] mem [0:NVEC-1];
    reg  clk = 0;
    reg  [31:0] A = 0, B = 0;
    wire [31:0] R;
    integer i, mism, ulp0, ulp1, ulpgt;
    reg [31:0] mdl, rf, d;
    gs_fp32_divider_pipe dut (.clk(clk), .A(A), .B(B), .RESULT(R));
    always #5 clk = ~clk;
    initial begin
        $readmemh("vectors.mem", mem);
        $display("loaded: mem[0]=%h  mem[1]=%h  mem[NVEC-1]=%h", mem[0], mem[1], mem[NVEC-1]);
        if ((^mem[0]) === 1'bx || (^mem[NVEC-1]) === 1'bx) begin $display("ERROR: vector file not loaded. Put it in the simulator working directory (e.g. <proj>.sim/sim_1/behav/xsim) or add it as a simulation source."); $finish; end
        mism = 0; ulp0 = 0; ulp1 = 0; ulpgt = 0;
        for (i = 0; i < NVEC + 4; i = i + 1) begin
            @(negedge clk);
            if (i >= 4) begin
                mdl = mem[i-4][63:32]; rf = mem[i-4][31:0];
                if ((R !== mdl) || (^R === 1'bx)) begin
                    mism = mism + 1;
                    if (mism < 10) $display("RTL!=MODEL idx=%0d rtl=%h model=%h", i-4, R, mdl);
                end
                d = (R > rf) ? (R - rf) : (rf - R);
                if (d == 0) ulp0 = ulp0 + 1; else if (d == 1) ulp1 = ulp1 + 1; else ulpgt = ulpgt + 1;
            end
            if (i < NVEC) begin A = mem[i][127:96]; B = mem[i][95:64]; end
        end
        $display("vectors=%0d  RTL-vs-model mismatches=%0d", NVEC, mism);
        $display("vs correctly-rounded: exact=%0d  1ulp=%0d  >1ulp=%0d", ulp0, ulp1, ulpgt);
        if (mism == 0 && ulpgt == 0) $display("PASS"); else $display("FAIL");
        $finish;
    end
endmodule
