module iverilog_dump();
initial begin
    $dumpfile("axi_pipeline.fst");
    $dumpvars(0, axi_pipeline);
end
endmodule
