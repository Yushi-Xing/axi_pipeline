module axi_pipeline #(
    parameter integer D = 1,              // pipeline depth
    parameter integer ID_WIDTH = 4,       // AXI ID width
    parameter integer ADDR_WIDTH = 64,    // Address width
    parameter integer DATA_WIDTH = 512,   // Data width
    parameter integer STRB_WIDTH = DATA_WIDTH / 8,  // Strobe width
    parameter integer LEN_WIDTH = 8,      // Burst length width
    parameter integer SIZE_WIDTH = 3,     // Burst size width
    parameter integer BURST_WIDTH = 2,    // Burst type width
    parameter integer LOCK_WIDTH = 1,     // Lock width
    parameter integer CACHE_WIDTH = 4,    // Cache width
    parameter integer PROT_WIDTH = 3,     // Protection width
    parameter integer RESP_WIDTH = 2      // Response width
)(
    input wire clk,
    input wire rst,

    // Slave interface (connect to upstream master)
    input wire [ID_WIDTH-1:0] s_axi_awid,
    input wire [ADDR_WIDTH-1:0] s_axi_awaddr,
    input wire [LEN_WIDTH-1:0] s_axi_awlen,
    input wire [SIZE_WIDTH-1:0] s_axi_awsize,
    input wire [BURST_WIDTH-1:0] s_axi_awburst,
    input wire [LOCK_WIDTH-1:0] s_axi_awlock,
    input wire [CACHE_WIDTH-1:0] s_axi_awcache,
    input wire [PROT_WIDTH-1:0] s_axi_awprot,
    input wire s_axi_awvalid,
    output wire s_axi_awready,

    input wire [DATA_WIDTH-1:0] s_axi_wdata,
    input wire [STRB_WIDTH-1:0] s_axi_wstrb,
    input wire s_axi_wlast,
    input wire s_axi_wvalid,
    output wire s_axi_wready,

    output wire [ID_WIDTH-1:0] s_axi_bid,
    output wire [RESP_WIDTH-1:0] s_axi_bresp,
    output wire s_axi_bvalid,
    input wire s_axi_bready,

    input wire [ID_WIDTH-1:0] s_axi_arid,
    input wire [ADDR_WIDTH-1:0] s_axi_araddr,
    input wire [LEN_WIDTH-1:0] s_axi_arlen,
    input wire [SIZE_WIDTH-1:0] s_axi_arsize,
    input wire [BURST_WIDTH-1:0] s_axi_arburst,
    input wire [LOCK_WIDTH-1:0] s_axi_arlock,
    input wire [CACHE_WIDTH-1:0] s_axi_arcache,
    input wire [PROT_WIDTH-1:0] s_axi_arprot,
    input wire s_axi_arvalid,
    output wire s_axi_arready,

    output wire [ID_WIDTH-1:0] s_axi_rid,
    output wire [DATA_WIDTH-1:0] s_axi_rdata,
    output wire [RESP_WIDTH-1:0] s_axi_rresp,
    output wire s_axi_rlast,
    output wire s_axi_rvalid,
    input wire s_axi_rready,

    // Master interface (connect to downstream slave)
    output wire [ID_WIDTH-1:0] m_axi_awid,
    output wire [ADDR_WIDTH-1:0] m_axi_awaddr,
    output wire [LEN_WIDTH-1:0] m_axi_awlen,
    output wire [SIZE_WIDTH-1:0] m_axi_awsize,
    output wire [BURST_WIDTH-1:0] m_axi_awburst,
    output wire [LOCK_WIDTH-1:0] m_axi_awlock,
    output wire [CACHE_WIDTH-1:0] m_axi_awcache,
    output wire [PROT_WIDTH-1:0] m_axi_awprot,
    output wire m_axi_awvalid,
    input wire m_axi_awready,

    output wire [DATA_WIDTH-1:0] m_axi_wdata,
    output wire [STRB_WIDTH-1:0] m_axi_wstrb,
    output wire m_axi_wlast,
    output wire m_axi_wvalid,
    input wire m_axi_wready,

    input wire [ID_WIDTH-1:0] m_axi_bid,
    input wire [RESP_WIDTH-1:0] m_axi_bresp,
    input wire m_axi_bvalid,
    output wire m_axi_bready,

    output wire [ID_WIDTH-1:0] m_axi_arid,
    output wire [ADDR_WIDTH-1:0] m_axi_araddr,
    output wire [LEN_WIDTH-1:0] m_axi_arlen,
    output wire [SIZE_WIDTH-1:0] m_axi_arsize,
    output wire [BURST_WIDTH-1:0] m_axi_arburst,
    output wire [LOCK_WIDTH-1:0] m_axi_arlock,
    output wire [CACHE_WIDTH-1:0] m_axi_arcache,
    output wire [PROT_WIDTH-1:0] m_axi_arprot,
    output wire m_axi_arvalid,
    input wire m_axi_arready,

    input wire [ID_WIDTH-1:0] m_axi_rid,
    input wire [DATA_WIDTH-1:0] m_axi_rdata,
    input wire [RESP_WIDTH-1:0] m_axi_rresp,
    input wire m_axi_rlast,
    input wire m_axi_rvalid,
    output wire m_axi_rready
);

// AW channel pipeline
localparam AW_WIDTH = ID_WIDTH + ADDR_WIDTH + LEN_WIDTH + SIZE_WIDTH + BURST_WIDTH + LOCK_WIDTH + CACHE_WIDTH + PROT_WIDTH;
wire [AW_WIDTH-1:0] aw_din  = {s_axi_awid, s_axi_awaddr, s_axi_awlen, s_axi_awsize, s_axi_awburst, s_axi_awlock, s_axi_awcache, s_axi_awprot};
wire [AW_WIDTH-1:0] aw_dout;
assign {m_axi_awid, m_axi_awaddr, m_axi_awlen, m_axi_awsize, m_axi_awburst, m_axi_awlock, m_axi_awcache, m_axi_awprot} = aw_dout;

axis_bus_pipeline #(
    .D(D),
    .W(AW_WIDTH)
) inst_aw (
    .clk(clk),
    .rst(rst),
    .din(aw_din),
    .din_vld(s_axi_awvalid),
    .din_rdy(s_axi_awready),
    .dout(aw_dout),
    .dout_vld(m_axi_awvalid),
    .dout_rdy(m_axi_awready)
);

// AR channel pipeline
localparam AR_WIDTH = ID_WIDTH + ADDR_WIDTH + LEN_WIDTH + SIZE_WIDTH + BURST_WIDTH + LOCK_WIDTH + CACHE_WIDTH + PROT_WIDTH;
wire [AR_WIDTH-1:0] ar_din  = {s_axi_arid, s_axi_araddr, s_axi_arlen, s_axi_arsize, s_axi_arburst, s_axi_arlock, s_axi_arcache, s_axi_arprot};
wire [AR_WIDTH-1:0] ar_dout;
assign {m_axi_arid, m_axi_araddr, m_axi_arlen, m_axi_arsize, m_axi_arburst, m_axi_arlock, m_axi_arcache, m_axi_arprot} = ar_dout;

axis_bus_pipeline #(
    .D(D),
    .W(AR_WIDTH)
) inst_ar (
    .clk(clk),
    .rst(rst),
    .din(ar_din),
    .din_vld(s_axi_arvalid),
    .din_rdy(s_axi_arready),
    .dout(ar_dout),
    .dout_vld(m_axi_arvalid),
    .dout_rdy(m_axi_arready)
);

// W channel pipeline
localparam W_WIDTH = DATA_WIDTH + STRB_WIDTH + 1;
wire [W_WIDTH-1:0] w_din  = {s_axi_wdata, s_axi_wstrb, s_axi_wlast};
wire [W_WIDTH-1:0] w_dout;
assign {m_axi_wdata, m_axi_wstrb, m_axi_wlast} = w_dout;

axis_bus_pipeline #(
    .D(D),
    .W(W_WIDTH)
) inst_w (
    .clk(clk),
    .rst(rst),
    .din(w_din),
    .din_vld(s_axi_wvalid),
    .din_rdy(s_axi_wready),
    .dout(w_dout),
    .dout_vld(m_axi_wvalid),
    .dout_rdy(m_axi_wready)
);

// B channel pipeline (reverse direction)
localparam B_WIDTH = ID_WIDTH + RESP_WIDTH;
wire [B_WIDTH-1:0] b_din  = {m_axi_bid, m_axi_bresp};
wire [B_WIDTH-1:0] b_dout;
assign {s_axi_bid, s_axi_bresp} = b_dout;

axis_bus_pipeline #(
    .D(D),
    .W(B_WIDTH)
) inst_b (
    .clk(clk),
    .rst(rst),
    .din(b_din),
    .din_vld(m_axi_bvalid),
    .din_rdy(m_axi_bready),
    .dout(b_dout),
    .dout_vld(s_axi_bvalid),
    .dout_rdy(s_axi_bready)
);

// R channel pipeline (reverse direction)
localparam R_WIDTH = ID_WIDTH + DATA_WIDTH + RESP_WIDTH + 1;
wire [R_WIDTH-1:0] r_din  = {m_axi_rid, m_axi_rdata, m_axi_rresp, m_axi_rlast};
wire [R_WIDTH-1:0] r_dout;
assign {s_axi_rid, s_axi_rdata, s_axi_rresp, s_axi_rlast} = r_dout;

axis_bus_pipeline #(
    .D(D),
    .W(R_WIDTH)
) inst_r (
    .clk(clk),
    .rst(rst),
    .din(r_din),
    .din_vld(m_axi_rvalid),
    .din_rdy(m_axi_rready),
    .dout(r_dout),
    .dout_vld(s_axi_rvalid),
    .dout_rdy(s_axi_rready)
);

endmodule