module signal_pipeline #(
    parameter W = 32, // 信号位宽
    parameter D = 2   // 打几拍（pipeline 深度）
)(
    input wire clk,
    input wire rst,
    input wire [W-1:0] din,
    output wire [W-1:0] dout
);
    // D = 0 自动旁路
    generate
        if (D == 0) begin : NO_DELAY
            assign dout = din;
        end else begin : GEN_DELAY
            reg [W-1:0] pipe_reg [0:D-1];
            integer i;
            always @(posedge clk) begin
                if (rst) begin
                    for (i = 0; i < D; i = i + 1) begin
                        pipe_reg[i] <= {W{1'b0}};
                    end
                end else begin
                    pipe_reg[0] <= din;
                    for (i = 1; i < D; i = i + 1) begin
                        pipe_reg[i] <= pipe_reg[i-1];
                    end
                end
            end
            assign dout = pipe_reg[D-1];
        end
    endgenerate
endmodule