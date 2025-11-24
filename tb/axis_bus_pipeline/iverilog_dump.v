module iverilog_dump();
initial begin
    $dumpfile("axis_bus_pipeline.fst");
    $dumpvars(0, axis_bus_pipeline);
end
endmodule
