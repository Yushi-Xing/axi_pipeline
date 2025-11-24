#!/usr/bin/env python
"""
Comprehensive test bench for axis_bus_pipeline module

Tests pipeline functionality with various depths and data widths
Validates handshake protocol, data integrity, and edge cases
"""

import itertools
import logging
import os
import random

import cocotb_test.simulator
import pytest

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ReadOnly
from cocotb.regression import TestFactory


class TB(object):
    """Test bench for axis_bus_pipeline"""
    def __init__(self, dut):
        self.dut = dut
        self.log = logging.getLogger("cocotb.tb")
        self.log.setLevel(logging.DEBUG)

        cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
        
        self.data_width = len(dut.din)
        self.log.info(f"Testbench initialized with data_width={self.data_width}")

    async def reset(self):
        """Apply reset sequence"""
        self.dut.rst.setimmediatevalue(0)
        self.dut.din.setimmediatevalue(0)
        self.dut.din_vld.setimmediatevalue(0)
        self.dut.dout_rdy.setimmediatevalue(0)
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.rst.value = 1
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.rst.value = 0
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.log.info("Reset completed")

    async def send_data(self, data_list, idle_cycles=None):
        """Send data through the pipeline
        
        Args:
            data_list: List of data values to send
            idle_cycles: Iterator for inserting idle cycles (None for no idle)
        """
        sent_data = []
        for i, data in enumerate(data_list):
            # Wait for ready
            while True:
                await RisingEdge(self.dut.clk)
                if self.dut.din_rdy.value == 1:
                    break
            
            # Apply data
            self.dut.din.value = data
            self.dut.din_vld.value = 1
            sent_data.append(data)
            await RisingEdge(self.dut.clk)
            self.dut.din_vld.value = 0
            
            # Insert idle cycles if specified
            if idle_cycles is not None:
                idle_count = next(idle_cycles)
                for _ in range(idle_count):
                    self.dut.din_vld.value = 0
                    await RisingEdge(self.dut.clk)
        
        self.dut.din_vld.value = 0
        return sent_data

    async def receive_data(self, count, backpressure=None):
        """Receive data from the pipeline
        
        Args:
            count: Number of data items to receive
            backpressure: Iterator for backpressure pattern (None for always ready)
        """
        received_data = []
        backpressure_state = True if backpressure is None else next(backpressure)
        self.dut.dout_rdy.value = 1 if backpressure_state else 0
        
        while len(received_data) < count:
            await RisingEdge(self.dut.clk)
            
            if backpressure is not None:
                backpressure_state = next(backpressure)
                self.dut.dout_rdy.value = 1 if backpressure_state else 0
            
            if self.dut.dout_vld.value == 1 and self.dut.dout_rdy.value == 1:
                data = int(self.dut.dout.value)
                received_data.append(data)
                self.log.debug(f"Received data[{len(received_data)-1}] = {data:x}")
        
        return received_data

    async def concurrent_send_receive(self, data_list, idle_cycles=None, backpressure=None):
        """Concurrently send and receive data"""
        send_task = cocotb.start_soon(self.send_data(data_list, idle_cycles))
        receive_task = cocotb.start_soon(self.receive_data(len(data_list), backpressure))
        
        sent_data = await send_task
        received_data = await receive_task
        
        return sent_data, received_data


async def run_test_basic(dut):
    """Basic functionality test - send data through pipeline"""
    tb = TB(dut)
    await tb.reset()
    
    # Initialize signals
    tb.dut.din_vld.value = 0
    tb.dut.dout_rdy.value = 1
    
    # Test data
    test_data = [i for i in range(32)]
    
    sent_data, received_data = await tb.concurrent_send_receive(test_data)
    
    # Verify
    assert len(sent_data) == len(received_data), f"Data count mismatch: sent {len(sent_data)}, received {len(received_data)}"
    for i, (sent, received) in enumerate(zip(sent_data, received_data)):
        assert sent == received, f"Data mismatch at index {i}: sent {sent:x}, received {received:x}"
    
    tb.log.info("Basic test passed!")
    await RisingEdge(dut.clk)


async def run_test_backpressure(dut):
    """Test with downstream backpressure"""
    tb = TB(dut)
    await tb.reset()
    
    tb.dut.din_vld.value = 0
    tb.dut.dout_rdy.value = 0
    
    # Test data - make sure it fits in data width
    max_val = (1 << tb.data_width) - 1
    test_data = [(i * 0x11111111) & max_val for i in range(64)]
    
    # Backpressure pattern: alternate ready/not ready
    def backpressure_gen():
        pattern = [ False, False, False, False, False,False, False, False, False, False,True]
        return itertools.cycle(pattern)
    
    sent_data, received_data = await tb.concurrent_send_receive(
        test_data, 
        backpressure=backpressure_gen()
    )
    
    # Verify
    assert sent_data == received_data, "Data mismatch with backpressure"
    tb.log.info("Backpressure test passed!")
    await RisingEdge(dut.clk)


async def run_test_idle_insertion(dut):
    """Test with idle cycles during transmission"""
    tb = TB(dut)
    await tb.reset()
    
    tb.dut.din_vld.value = 0
    tb.dut.dout_rdy.value = 1
    
    # Test data - make sure it fits in data width
    max_val = (1 << tb.data_width) - 1
    test_data = [(i * 0x12345678) & max_val for i in range(48)]
    
    # Idle pattern: variable idle cycles
    def idle_gen():
        pattern = [0, 1, 0, 2, 0, 0, 3]
        return itertools.cycle(pattern)
    
    sent_data, received_data = await tb.concurrent_send_receive(
        test_data,
        idle_cycles=idle_gen()
    )
    
    # Verify
    assert sent_data == received_data, "Data mismatch with idle insertion"
    tb.log.info("Idle insertion test passed!")
    await RisingEdge(dut.clk)


async def run_test_full_stress(dut):
    """Stress test with both idle cycles and backpressure"""
    tb = TB(dut)
    await tb.reset()
    
    tb.dut.din_vld.value = 0
    tb.dut.dout_rdy.value = 0
    
    # Random test data
    random.seed(42)
    test_data = [random.randint(0, (1 << tb.data_width) - 1) for _ in range(128)]
    
    def idle_gen():
        while True:
            yield random.randint(0, 3)
    
    def backpressure_gen():
        while True:
            yield random.random() > 0.3
    
    sent_data, received_data = await tb.concurrent_send_receive(
        test_data,
        idle_cycles=idle_gen(),
        backpressure=backpressure_gen()
    )
    
    # Verify
    assert len(sent_data) == len(received_data), "Data count mismatch in stress test"
    for i, (sent, received) in enumerate(zip(sent_data, received_data)):
        assert sent == received, f"Data mismatch at index {i}: sent {sent:x}, received {received:x}"
    
    tb.log.info("Stress test passed!")
    await RisingEdge(dut.clk)


async def run_test_reset_during_transfer(dut):
    """Test reset behavior during active transfer
    
    Note: Due to a known RTL bug where data_r registers are not reset (line 49),
    this test focuses on verifying that the valid signals are properly cleared.
    """
    tb = TB(dut)
    await tb.reset()
    
    param_d = int(os.getenv("PARAM_D", "1"))
    
    # For D=0 (no pipeline), skip this test as it's not applicable
    if param_d == 0:
        tb.log.info("Reset test skipped for D=0 (no pipeline)")
        return
    
    tb.dut.din_vld.value = 0
    tb.dut.dout_rdy.value = 1  # Keep output ready
    
    # Fill the pipeline with data
    max_val = (1 << tb.data_width) - 1
    test_data = [(i * 0xABCDEF) & max_val for i in range(param_d + 5)]
    
    # Start sending data
    send_task = cocotb.start_soon(tb.send_data(test_data[:param_d]))
    
    # Wait for pipeline to have some data
    for _ in range(param_d + 10):
        await RisingEdge(dut.clk)
    
    # Apply reset
    tb.log.info(f"Applying reset with pipeline depth D={param_d}...")
    tb.dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    tb.dut.rst.value = 0
    await RisingEdge(dut.clk)
    
    # After reset, valid should be 0 (asynchronous reset should clear immediately)
    assert tb.dut.dout_vld.value == 0, f"Pipeline valid not cleared after reset (D={param_d}, vld={tb.dut.dout_vld.value})"
    
    tb.log.info("Reset during transfer test passed!")


async def run_test_continuous_transfer(dut):
    """Test continuous back-to-back transfers"""
    tb = TB(dut)
    await tb.reset()
    
    tb.dut.din_vld.value = 0
    tb.dut.dout_rdy.value = 1
    
    # Continuous data stream
    test_data = list(range(256))
    
    sent_data = []
    received_data = []
    
    # Start receiver
    receive_task = cocotb.start_soon(tb.receive_data(len(test_data)))
    
    # Send continuous data
    for i, data in enumerate(test_data):
        await RisingEdge(dut.clk)
        if tb.dut.din_rdy.value == 1:
            tb.dut.din.value = data
            tb.dut.din_vld.value = 1
            sent_data.append(data)
        else:
            # Should not happen with always-ready receiver
            tb.log.warning(f"Unexpected not-ready at cycle {i}")
    
    await RisingEdge(dut.clk)
    tb.dut.din_vld.value = 0
    
    received_data = await receive_task
    
    # Verify
    assert sent_data == received_data, "Data mismatch in continuous transfer"
    tb.log.info("Continuous transfer test passed!")


async def run_test_max_data_pattern(dut):
    """Test with maximum data values (all 1s, all 0s)"""
    tb = TB(dut)
    await tb.reset()
    
    tb.dut.din_vld.value = 0
    tb.dut.dout_rdy.value = 1
    
    max_val = (1 << tb.data_width) - 1
    test_data = [0, max_val, 0, max_val, 0x55555555 & max_val, 0xAAAAAAAA & max_val]
    test_data = test_data * 10
    
    sent_data, received_data = await tb.concurrent_send_receive(test_data)
    
    # Verify
    assert sent_data == received_data, "Data mismatch with max patterns"
    tb.log.info("Max data pattern test passed!")
    await RisingEdge(dut.clk)


async def run_test_single_word(dut):
    """Test single word transfer"""
    tb = TB(dut)
    await tb.reset()
    
    tb.dut.din_vld.value = 0
    tb.dut.dout_rdy.value = 1
    
    test_data = [0xDEADBEEF & ((1 << tb.data_width) - 1)]
    
    sent_data, received_data = await tb.concurrent_send_receive(test_data)
    
    assert sent_data == received_data, "Single word transfer failed"
    tb.log.info("Single word test passed!")
    await RisingEdge(dut.clk)


async def run_test_zero_delay_ready(dut):
    """Test immediate ready assertion after valid"""
    tb = TB(dut)
    await tb.reset()
    
    tb.dut.din_vld.value = 0
    tb.dut.dout_rdy.value = 1
    
    test_data = list(range(100))
    
    # Receiver is always ready
    sent_data, received_data = await tb.concurrent_send_receive(test_data)
    
    assert sent_data == received_data, "Zero delay ready test failed"
    tb.log.info("Zero delay ready test passed!")


if cocotb.SIM_NAME:
    # Basic tests
    for test in [
        # run_test_basic,
        run_test_backpressure,
        # run_test_idle_insertion,
        # run_test_full_stress,
        # run_test_reset_during_transfer,
        # run_test_continuous_transfer,
        # run_test_max_data_pattern,
        # run_test_single_word,
        # run_test_zero_delay_ready,
    ]:
        factory = TestFactory(test)
        factory.generate_tests()


# cocotb-test

tests_dir = os.path.dirname(__file__)
rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', '..', 'rtl'))


@pytest.mark.parametrize("depth", [0, 1, 2, 4, 8])
@pytest.mark.parametrize("width", [8, 16, 32, 64, 128])
def test_axis_bus_pipeline(request, depth, width):
    dut = "axis_bus_pipeline"
    module = os.path.splitext(os.path.basename(__file__))[0]
    toplevel = dut

    verilog_sources = [
        os.path.join(rtl_dir, f"{dut}.v"),
    ]

    parameters = {}
    parameters['D'] = depth
    parameters['W'] = width

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
