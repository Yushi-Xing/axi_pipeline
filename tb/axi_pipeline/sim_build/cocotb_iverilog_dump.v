module cocotb_iverilog_dump();
initial begin
    $dumpfile("sim_build/axi_pipeline.fst");
    $dumpvars(0, axi_pipeline);
end
endmodule
