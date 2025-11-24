module axis_bus_pipeline #(
    parameter integer D = 1,  // pipeline depth
    parameter integer W = 32  // bus width
)(
    input  wire         clk,
    input  wire         rst,

    // upstream
    input  wire [W-1:0] din,
    input  wire         din_vld,
    output wire         din_rdy,

    // downstream
    output wire [W-1:0] dout,
    output wire         dout_vld,
    input  wire         dout_rdy
);

    // D = 0 → direct pass
    generate 
        if (D == 0) begin : NO_PIPE
            assign dout     = din;
            assign dout_vld = din_vld;
            assign din_rdy  = dout_rdy;

        end else begin : PIPE

            reg [W-1:0] data_r [0:D-1];
            reg         vld_r  [0:D-1];

            integer i;

            // ready 信号链条，从后向前
            wire [D:0] rdy_chain;
            assign rdy_chain[D] = dout_rdy;

            genvar gi;
            for (gi = 0; gi < D; gi = gi + 1) begin : RDY_GEN
                assign rdy_chain[gi] = (!vld_r[gi]) || rdy_chain[gi+1]; //挤气泡
            end

            assign din_rdy = rdy_chain[0];

            // pipeline stage 更新
            always @(posedge clk or posedge rst) begin
                if (rst) begin
                    for (i = 0; i < D; i = i + 1) begin
                        vld_r[i] <= 1'b0;
                        data_r[i] <= {W{1'b0}};  // 可选：reset 清 data
                    end
                end else begin
                    // stage0
                    if (din_rdy) begin
                        vld_r[0] <= din_vld;
                        data_r[0] <= din;
                    end

                    // stage 中间
                    for (i = 1; i < D; i = i + 1) begin
                        if (rdy_chain[i]) begin
                            vld_r[i] <= vld_r[i-1];
                            data_r[i] <= data_r[i-1];
                        end
                    end
                end
            end

            assign dout     = data_r[D-1];
            assign dout_vld = vld_r[D-1];

        end 
    endgenerate

endmodule
