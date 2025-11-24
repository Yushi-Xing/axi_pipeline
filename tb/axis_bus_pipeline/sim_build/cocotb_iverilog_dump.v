module cocotb_iverilog_dump();
initial begin
    $dumpfile("sim_build/axis_bus_pipeline.fst");
    $dumpvars(0, axis_bus_pipeline);
end
endmodule
