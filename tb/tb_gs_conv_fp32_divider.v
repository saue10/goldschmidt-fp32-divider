`timescale 1ns / 1ps
// Same as tb_gs_fp32_divider but for the conventional baseline; needs vectors_conv.mem renamed/placed as "vectors_conv.mem".
module tb_gs_conv_fp32_divider;
    parameter NVEC = 40230;
    reg  [127:0] mem [0:NVEC-1];
    reg  [31:0]  A, B;
    wire [31:0]  R;
    integer i, model_mismatch, ulp0, ulp1, ulpgt;
    reg [31:0] mdl, rf, d;
    gs_conv_fp32_divider dut (.A(A), .B(B), .RESULT(R));
    initial begin
        $readmemh("vectors_conv.mem", mem);
        $display("loaded: mem[0]=%h  mem[1]=%h  mem[NVEC-1]=%h", mem[0], mem[1], mem[NVEC-1]);
        if ((^mem[0]) === 1'bx || (^mem[NVEC-1]) === 1'bx) begin $display("ERROR: vector file not loaded. Put it in the simulator working directory (e.g. <proj>.sim/sim_1/behav/xsim) or add it as a simulation source."); $finish; end
        model_mismatch = 0; ulp0 = 0; ulp1 = 0; ulpgt = 0;
        for (i = 0; i < NVEC; i = i + 1) begin
            A = mem[i][127:96]; B = mem[i][95:64]; mdl = mem[i][63:32]; rf = mem[i][31:0];
            #5;
            if ((R !== mdl) || (^R === 1'bx)) begin
                model_mismatch = model_mismatch + 1;
                if (model_mismatch < 10) $display("RTL!=MODEL A=%h B=%h rtl=%h model=%h", A, B, R, mdl);
            end
            d = (R > rf) ? (R - rf) : (rf - R);
            if (d == 0) ulp0 = ulp0 + 1; else if (d == 1) ulp1 = ulp1 + 1; else ulpgt = ulpgt + 1;
        end
        $display("vectors=%0d  RTL-vs-model mismatches=%0d", NVEC, model_mismatch);
        $display("vs correctly-rounded: exact=%0d  1ulp=%0d  >1ulp=%0d", ulp0, ulp1, ulpgt);
        if (model_mismatch == 0 && ulpgt == 0) $display("PASS"); else $display("FAIL");
        $finish;
    end
endmodule
