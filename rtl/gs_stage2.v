`timescale 1ns / 1ps
// Stage 2 (final): N2 = N1 + N1*eps1 (16-bit x 18-bit multiplier). No D2 / eps2 is formed.
module gs_stage2 (
    input  [33:0] N1,
    input  [17:0] E1,
    output [33:0] N2
);
    wire [15:0] N1h = N1[33:18];                      // 14 fractional bits
    wire [33:0] p2  = N1h * E1;
    assign N2 = N1 + {12'b0, p2[33:12]};
endmodule
