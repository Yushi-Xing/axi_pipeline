# Makefile for axi_pipeline testbench

TOPLEVEL_LANG = verilog

SIM ?= icarus
WAVES ?= 1

COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps

DUT      = axi_pipeline
TOPLEVEL = $(DUT)
MODULE   = test_$(DUT)
VERILOG_SOURCES += ../../rtl/axis_bus_pipeline.v
VERILOG_SOURCES += ../../rtl/$(DUT).v

# module parameters
export PARAM_D ?= 2
export PARAM_ID_WIDTH ?= 4
export PARAM_ADDR_WIDTH ?= 64
export PARAM_DATA_WIDTH ?= 512
export PARAM_STRB_WIDTH ?= $(shell expr $(PARAM_DATA_WIDTH) / 8 )
export PARAM_LEN_WIDTH ?= 8
export PARAM_SIZE_WIDTH ?= 3
export PARAM_BURST_WIDTH ?= 2
export PARAM_LOCK_WIDTH ?= 1
export PARAM_CACHE_WIDTH ?= 4
export PARAM_PROT_WIDTH ?= 3
export PARAM_RESP_WIDTH ?= 2

ifeq ($(SIM), icarus)
	PLUSARGS += -fst

	COMPILE_ARGS += -P $(TOPLEVEL).D=$(PARAM_D)
	COMPILE_ARGS += -P $(TOPLEVEL).ID_WIDTH=$(PARAM_ID_WIDTH)
	COMPILE_ARGS += -P $(TOPLEVEL).ADDR_WIDTH=$(PARAM_ADDR_WIDTH)
	COMPILE_ARGS += -P $(TOPLEVEL).DATA_WIDTH=$(PARAM_DATA_WIDTH)
	COMPILE_ARGS += -P $(TOPLEVEL).STRB_WIDTH=$(PARAM_STRB_WIDTH)
	COMPILE_ARGS += -P $(TOPLEVEL).LEN_WIDTH=$(PARAM_LEN_WIDTH)
	COMPILE_ARGS += -P $(TOPLEVEL).SIZE_WIDTH=$(PARAM_SIZE_WIDTH)
	COMPILE_ARGS += -P $(TOPLEVEL).BURST_WIDTH=$(PARAM_BURST_WIDTH)
	COMPILE_ARGS += -P $(TOPLEVEL).LOCK_WIDTH=$(PARAM_LOCK_WIDTH)
	COMPILE_ARGS += -P $(TOPLEVEL).CACHE_WIDTH=$(PARAM_CACHE_WIDTH)
	COMPILE_ARGS += -P $(TOPLEVEL).PROT_WIDTH=$(PARAM_PROT_WIDTH)
	COMPILE_ARGS += -P $(TOPLEVEL).RESP_WIDTH=$(PARAM_RESP_WIDTH)
	SIM_ARGS += -n   #skip vvp shell when ctrl c assert
	ifeq ($(WAVES), 1)
		VERILOG_SOURCES += iverilog_dump.v
		COMPILE_ARGS += -s iverilog_dump
	endif
else ifeq ($(SIM), verilator)
	COMPILE_ARGS += -Wno-SELRANGE -Wno-WIDTH

	COMPILE_ARGS += -GD=$(PARAM_D)
	COMPILE_ARGS += -GID_WIDTH=$(PARAM_ID_WIDTH)
	COMPILE_ARGS += -GADDR_WIDTH=$(PARAM_ADDR_WIDTH)
	COMPILE_ARGS += -GDATA_WIDTH=$(PARAM_DATA_WIDTH)
	COMPILE_ARGS += -GSTRB_WIDTH=$(PARAM_STRB_WIDTH)
	COMPILE_ARGS += -GLEN_WIDTH=$(PARAM_LEN_WIDTH)
	COMPILE_ARGS += -GSIZE_WIDTH=$(PARAM_SIZE_WIDTH)
	COMPILE_ARGS += -GBURST_WIDTH=$(PARAM_BURST_WIDTH)
	COMPILE_ARGS += -GLOCK_WIDTH=$(PARAM_LOCK_WIDTH)
	COMPILE_ARGS += -GCACHE_WIDTH=$(PARAM_CACHE_WIDTH)
	COMPILE_ARGS += -GPROT_WIDTH=$(PARAM_PROT_WIDTH)
	COMPILE_ARGS += -GRESP_WIDTH=$(PARAM_RESP_WIDTH)

	ifeq ($(WAVES), 1)
		COMPILE_ARGS += --trace-fst
	endif
endif

include $(shell cocotb-config --makefiles)/Makefile.sim

iverilog_dump.v:
	echo 'module iverilog_dump();' > $@
	echo 'initial begin' >> $@
	echo '    $$dumpfile("$(TOPLEVEL).fst");' >> $@
	echo '    $$dumpvars(0, $(TOPLEVEL));' >> $@
	echo 'end' >> $@
	echo 'endmodule' >> $@

clean::
	@rm -rf iverilog_dump.v
	@rm -rf dump.fst $(TOPLEVEL).fst
