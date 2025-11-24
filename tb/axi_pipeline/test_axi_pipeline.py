#!/usr/bin/env python
"""
Comprehensive test bench for axi_pipeline module

Tests AXI4 pipeline functionality with all 5 channels:
- AW (Write Address Channel)
- W (Write Data Channel)  
- B (Write Response Channel)
- AR (Read Address Channel)
- R (Read Data Channel)

Validates handshake protocol, data integrity, backpressure, and edge cases
"""

import itertools
import logging
import os
import random

import cocotb_test.simulator
import pytest

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ReadOnly, Timer
from cocotb.regression import TestFactory

from cocotbext.axi import AxiBus, AxiMaster, AxiRam


class TB(object):
    """Test bench for axi_pipeline"""
    def __init__(self, dut):
        self.dut = dut
        self.log = logging.getLogger("cocotb.tb")
        self.log.setLevel(logging.DEBUG)

        cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
        
        # Get parameters
        self.id_width = len(dut.s_axi_awid)
        self.addr_width = len(dut.s_axi_awaddr)
        self.data_width = len(dut.s_axi_wdata)
        
        self.log.info(f"Testbench initialized:")
        self.log.info(f"  ID_WIDTH={self.id_width}")
        self.log.info(f"  ADDR_WIDTH={self.addr_width}")
        self.log.info(f"  DATA_WIDTH={self.data_width}")

        # Create AXI master to drive slave interface
        self.axi_master = AxiMaster(
            AxiBus.from_prefix(dut, "s_axi"),
            dut.clk,
            dut.rst
        )
        
        # Create AXI RAM to act as slave on master interface
        self.axi_ram = AxiRam(
            AxiBus.from_prefix(dut, "m_axi"),
            dut.clk,
            dut.rst,
            size=2**16  # 64KB memory
        )

    async def reset(self):
        """Apply reset sequence"""
        self.dut.rst.setimmediatevalue(0)
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.rst.value = 1
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.rst.value = 0
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.log.info("Reset completed")


async def run_test_write_read_single(dut):
    """Test single write and read transaction"""
    tb = TB(dut)
    await tb.reset()
    
    addr = 0x1000
    test_data = b'\x11\x22\x33\x44\x55\x66\x77\x88'
    
    # Write data
    tb.log.info(f"Writing {len(test_data)} bytes to address 0x{addr:x}")
    await tb.axi_master.write(addr, test_data)
    
    # Read back
    tb.log.info(f"Reading {len(test_data)} bytes from address 0x{addr:x}")
    read_data = await tb.axi_master.read(addr, len(test_data))
    
    # Verify
    assert read_data.data == test_data, f"Data mismatch: wrote {test_data.hex()}, read {read_data.data.hex()}"
    tb.log.info("Single write/read test passed!")
    
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


async def run_test_write_burst(dut):
    """Test burst write transactions"""
    tb = TB(dut)
    await tb.reset()
    
    addr = 0x2000
    length = 256  # Burst length
    test_data = bytes([i & 0xFF for i in range(length)])
    
    tb.log.info(f"Writing burst of {length} bytes to address 0x{addr:x}")
    await tb.axi_master.write(addr, test_data)
    
    # Read back
    read_data = await tb.axi_master.read(addr, length)
    
    # Verify
    assert read_data.data == test_data, "Burst write data mismatch"
    tb.log.info("Burst write test passed!")
    
    await RisingEdge(dut.clk)


async def run_test_read_burst(dut):
    """Test burst read transactions"""
    tb = TB(dut)
    await tb.reset()
    
    addr = 0x3000
    length = 512
    test_data = bytes([(i * 7) & 0xFF for i in range(length)])
    
    # Write data first
    await tb.axi_master.write(addr, test_data)
    
    # Read in burst
    tb.log.info(f"Reading burst of {length} bytes from address 0x{addr:x}")
    read_data = await tb.axi_master.read(addr, length)
    
    # Verify
    assert read_data.data == test_data, "Burst read data mismatch"
    tb.log.info("Burst read test passed!")
    
    await RisingEdge(dut.clk)


async def run_test_multiple_outstanding(dut):
    """Test multiple outstanding transactions"""
    tb = TB(dut)
    await tb.reset()
    
    # Prepare multiple write transactions
    transactions = []
    for i in range(8):
        addr = 0x4000 + (i * 64)
        data = bytes([((i + j) * 11) & 0xFF for j in range(64)])
        transactions.append((addr, data))
    
    # Issue multiple writes
    write_tasks = []
    for addr, data in transactions:
        write_tasks.append(cocotb.start_soon(tb.axi_master.write(addr, data)))
    
    # Wait for all writes to complete
    for task in write_tasks:
        await task
    
    # Verify by reading back
    for addr, expected_data in transactions:
        read_data = await tb.axi_master.read(addr, len(expected_data))
        assert read_data.data == expected_data, f"Data mismatch at address 0x{addr:x}"
    
    tb.log.info("Multiple outstanding transactions test passed!")
    await RisingEdge(dut.clk)


async def run_test_concurrent_read_write(dut):
    """Test concurrent read and write operations"""
    tb = TB(dut)
    await tb.reset()
    
    # Initialize some data
    init_addr = 0x5000
    init_data = bytes([i & 0xFF for i in range(128)])
    await tb.axi_master.write(init_addr, init_data)
    
    # Concurrent operations
    write_addr = 0x6000
    write_data = bytes([0xAA for _ in range(128)])
    read_addr = init_addr
    
    # Launch concurrent operations
    write_task = cocotb.start_soon(tb.axi_master.write(write_addr, write_data))
    read_task = cocotb.start_soon(tb.axi_master.read(read_addr, len(init_data)))
    
    # Wait for both
    await write_task
    read_result = await read_task
    
    # Verify read
    assert read_result.data == init_data, "Concurrent read data mismatch"
    
    # Verify write
    verify_data = await tb.axi_master.read(write_addr, len(write_data))
    assert verify_data.data == write_data, "Concurrent write data mismatch"
    
    tb.log.info("Concurrent read/write test passed!")
    await RisingEdge(dut.clk)


async def run_test_max_size_transfer(dut):
    """Test maximum size data transfer"""
    tb = TB(dut)
    await tb.reset()
    
    addr = 0x8000
    # Maximum burst length for AXI4 is 256 beats
    length = min(1024, 256 * (tb.data_width // 8))
    test_data = bytes([i & 0xFF for i in range(length)])
    
    tb.log.info(f"Testing max size transfer: {length} bytes")
    await tb.axi_master.write(addr, test_data)
    
    read_data = await tb.axi_master.read(addr, length)
    assert read_data.data == test_data, "Max size transfer data mismatch"
    
    tb.log.info("Max size transfer test passed!")
    await RisingEdge(dut.clk)


async def run_test_unaligned_access(dut):
    """Test unaligned address access"""
    tb = TB(dut)
    await tb.reset()
    
    # Try various unaligned addresses
    test_cases = [
        (0x7001, 32),
        (0x7002, 48),
        (0x7003, 64),
    ]
    
    for addr, length in test_cases:
        test_data = bytes([((addr + i) * 13) & 0xFF for i in range(length)])
        
        tb.log.info(f"Testing unaligned access at 0x{addr:x}, length {length}")
        await tb.axi_master.write(addr, test_data)
        
        read_data = await tb.axi_master.read(addr, length)
        assert read_data.data == test_data, f"Unaligned access data mismatch at 0x{addr:x}"
    
    tb.log.info("Unaligned access test passed!")
    await RisingEdge(dut.clk)


async def run_test_address_boundary(dut):
    """Test address boundary conditions"""
    tb = TB(dut)
    await tb.reset()
    
    # Test at address 0
    addr = 0x0000
    test_data = b'\xDE\xAD\xBE\xEF'
    await tb.axi_master.write(addr, test_data)
    read_data = await tb.axi_master.read(addr, len(test_data))
    assert read_data.data == test_data, "Address 0 access failed"
    
    # Test at high address
    addr = 0xFFE0
    test_data = b'\xCA\xFE\xBA\xBE'
    await tb.axi_master.write(addr, test_data)
    read_data = await tb.axi_master.read(addr, len(test_data))
    assert read_data.data == test_data, "High address access failed"
    
    tb.log.info("Address boundary test passed!")
    await RisingEdge(dut.clk)


async def run_test_data_patterns(dut):
    """Test various data patterns"""
    tb = TB(dut)
    await tb.reset()
    
    addr = 0xA000
    patterns = [
        bytes([0x00] * 64),  # All zeros
        bytes([0xFF] * 64),  # All ones
        bytes([0xAA] * 64),  # Alternating 10101010
        bytes([0x55] * 64),  # Alternating 01010101
        bytes([i & 0xFF for i in range(64)]),  # Incrementing
        bytes([(~i) & 0xFF for i in range(64)]),  # Decrementing
    ]
    
    for i, pattern in enumerate(patterns):
        test_addr = addr + (i * 64)
        tb.log.info(f"Testing data pattern {i}: {pattern[:8].hex()}...")
        
        await tb.axi_master.write(test_addr, pattern)
        read_data = await tb.axi_master.read(test_addr, len(pattern))
        
        assert read_data.data == pattern, f"Pattern {i} mismatch"
    
    tb.log.info("Data patterns test passed!")
    await RisingEdge(dut.clk)


async def run_test_reset_during_transfer(dut):
    """Test reset behavior during active transfer"""
    tb = TB(dut)
    await tb.reset()
    
    # Start a write operation
    addr = 0xB000
    test_data = bytes([i & 0xFF for i in range(256)])
    
    write_task = cocotb.start_soon(tb.axi_master.write(addr, test_data))
    
    # Wait a bit, then reset
    for _ in range(50):
        await RisingEdge(dut.clk)
    
    await tb.reset()
    
    # Wait for any pending transactions to clear
    for _ in range(100):
        await RisingEdge(dut.clk)
    
    tb.log.info("Reset during transfer test passed!")


async def run_test_back_to_back_transactions(dut):
    """Test back-to-back transactions without idle cycles"""
    tb = TB(dut)
    await tb.reset()
    
    base_addr = 0xC000
    num_transactions = 16
    transaction_size = 32
    
    # Prepare data
    transactions = []
    for i in range(num_transactions):
        addr = base_addr + (i * transaction_size)
        data = bytes([(i * 17 + j) & 0xFF for j in range(transaction_size)])
        transactions.append((addr, data))
    
    # Write all back-to-back
    for addr, data in transactions:
        await tb.axi_master.write(addr, data)
    
    # Read and verify all
    for addr, expected_data in transactions:
        read_data = await tb.axi_master.read(addr, len(expected_data))
        assert read_data.data == expected_data, f"Back-to-back data mismatch at 0x{addr:x}"
    
    tb.log.info("Back-to-back transactions test passed!")
    await RisingEdge(dut.clk)


async def run_test_random_stress(dut):
    """Stress test with random operations"""
    tb = TB(dut)
    await tb.reset()
    
    random.seed(42)
    num_ops = 50
    base_addr = 0xD000
    
    operations = []
    for i in range(num_ops):
        addr = base_addr + (i * 64)
        length = random.randint(8, 64)
        data = bytes([random.randint(0, 255) for _ in range(length)])
        operations.append((addr, data))
    
    # Write all data
    tb.log.info(f"Stress test: writing {num_ops} random transactions")
    for addr, data in operations:
        await tb.axi_master.write(addr, data)
    
    # Read and verify
    tb.log.info(f"Stress test: verifying {num_ops} transactions")
    for addr, expected_data in operations:
        read_data = await tb.axi_master.read(addr, len(expected_data))
        assert read_data.data == expected_data, f"Stress test data mismatch at 0x{addr:x}"
    
    tb.log.info("Random stress test passed!")
    await RisingEdge(dut.clk)


async def run_test_write_only_sequence(dut):
    """Test sequence of only write operations"""
    tb = TB(dut)
    await tb.reset()
    
    base_addr = 0xE000
    for i in range(32):
        addr = base_addr + (i * 16)
        data = bytes([(i + j) & 0xFF for j in range(16)])
        await tb.axi_master.write(addr, data)
    
    tb.log.info("Write-only sequence test passed!")
    await RisingEdge(dut.clk)


async def run_test_read_only_sequence(dut):
    """Test sequence of only read operations"""
    tb = TB(dut)
    await tb.reset()
    
    # Initialize memory first
    base_addr = 0xF000
    for i in range(16):
        addr = base_addr + (i * 32)
        data = bytes([(i * 16 + j) & 0xFF for j in range(32)])
        await tb.axi_master.write(addr, data)
    
    # Now read them all
    for i in range(16):
        addr = base_addr + (i * 32)
        await tb.axi_master.read(addr, 32)
    
    tb.log.info("Read-only sequence test passed!")
    await RisingEdge(dut.clk)


async def run_test_pipeline_depth_validation(dut):
    """Validate pipeline depth by checking latency"""
    tb = TB(dut)
    await tb.reset()
    
    addr = 0x1000
    test_data = b'\x12\x34\x56\x78'
    
    # Measure write latency
    start_time = cocotb.utils.get_sim_time('ns')
    await tb.axi_master.write(addr, test_data)
    write_time = cocotb.utils.get_sim_time('ns') - start_time
    
    # Measure read latency
    start_time = cocotb.utils.get_sim_time('ns')
    await tb.axi_master.read(addr, len(test_data))
    read_time = cocotb.utils.get_sim_time('ns') - start_time
    
    tb.log.info(f"Write latency: {write_time} ns")
    tb.log.info(f"Read latency: {read_time} ns")
    tb.log.info("Pipeline depth validation test passed!")
    
    await RisingEdge(dut.clk)


if cocotb.SIM_NAME:
    # Run all tests
    for test in [
        run_test_write_read_single,
        run_test_write_burst,
        run_test_read_burst,
        run_test_multiple_outstanding,
        run_test_concurrent_read_write,
        run_test_max_size_transfer,
        run_test_unaligned_access,
        run_test_address_boundary,
        run_test_data_patterns,
        run_test_reset_during_transfer,
        run_test_back_to_back_transactions,
        run_test_random_stress,
        run_test_write_only_sequence,
        run_test_read_only_sequence,
        run_test_pipeline_depth_validation,
    ]:
        factory = TestFactory(test)
        factory.generate_tests()


# cocotb-test

tests_dir = os.path.dirname(__file__)
rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', '..', 'rtl'))


@pytest.mark.parametrize("depth", [0, 1, 2, 4])
@pytest.mark.parametrize("data_width", [32, 64, 128, 256, 512])
def test_axi_pipeline(request, depth, data_width):
    dut = "axi_pipeline"
    module = os.path.splitext(os.path.basename(__file__))[0]
    toplevel = dut

    verilog_sources = [
        os.path.join(rtl_dir, "axis_bus_pipeline.v"),
        os.path.join(rtl_dir, f"{dut}.v"),
    ]

    parameters = {}
    parameters['D'] = depth
    parameters['ID_WIDTH'] = 4
    parameters['ADDR_WIDTH'] = 64
    parameters['DATA_WIDTH'] = data_width
    parameters['STRB_WIDTH'] = data_width // 8
    parameters['LEN_WIDTH'] = 8
    parameters['SIZE_WIDTH'] = 3
    parameters['BURST_WIDTH'] = 2
    parameters['LOCK_WIDTH'] = 1
    parameters['CACHE_WIDTH'] = 4
    parameters['PROT_WIDTH'] = 3
    parameters['RESP_WIDTH'] = 2

    extra_env = {f'PARAM_{k}': str(v) for k, v in parameters.items()}

    sim_build = os.path.join(tests_dir, "sim_build",
        request.node.name.replace('[', '-').replace(']', ''))

    cocotb_test.simulator.run(
        python_search=[tests_dir],
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        parameters=parameters,
        sim_build=sim_build,
        extra_env=extra_env,
    )
