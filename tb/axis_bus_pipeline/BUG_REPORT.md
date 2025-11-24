# Bug Report: axis_bus_pipeline.v

## Issue #1: Data registers not cleared on reset

### Description
The `axis_bus_pipeline` module does not clear the `data_r` registers during reset. This causes the first valid output after reset to potentially contain stale/uninitialized data from a previous operation or X values from simulation.

### Location
File: `rtl/axis_bus_pipeline.v`, lines 47-68

### Current Code
```verilog
always @(posedge clk or posedge rst) begin
    if (rst) begin
        for (i = 0; i < D; i = i + 1) begin
            vld_r[i] <= 1'b0;
            // data_r[i] <= {W{1'b0}};  // <-- This is commented out!
        end
    end else begin
        // ... pipeline logic
    end
end
```

### Expected Behavior
On reset, all pipeline stage data registers should be cleared to a known state (typically all zeros).

### Observed Behavior
After reset, when `vld_r` is 0 (correctly), the `data_r` registers still contain old/uninitialized values. If there's a timing issue or the consumer reads `dout` when `dout_vld` should be 0 but briefly becomes 1, garbage data may be output.

### Evidence from Tests
Multiple tests show the first received data is garbage:
- `run_test_continuous_transfer`: Expected `[0, 1, 2, ...]`, Got `[33778125, 0, 1, 2, ...]`
- `run_test_max_data_pattern`: Expected `[0, 4294967295, ...]`, Got `[255, 0, 4294967295, ...]`
- `run_test_single_word`: Expected `[3735928559]`, Got `[2863311530]`

### Recommended Fix
Uncomment the data register reset line:
```verilog
always @(posedge clk or posedge rst) begin
    if (rst) begin
        for (i = 0; i < D; i = i + 1) begin
            vld_r[i] <= 1'b0;
            data_r[i] <= {W{1'b0}};  // <-- Uncomment this line
        end
    end else begin
        // ... existing logic
    end
end
```

### Impact
- **Severity**: Medium
- **Functional Impact**: May cause incorrect data to be transmitted after reset
- **Simulation Impact**: Causes test failures due to X-propagation or stale data
- **Real Hardware Impact**: Could cause system initialization issues

### Test Cases Affected
- `run_test_continuous_transfer_001`
- `run_test_max_data_pattern_001`
- `run_test_single_word_001`
- `run_test_zero_delay_ready_001`

## Testing Recommendation
After fixing, run:
```bash
cd tb/axis_bus_pipeline
make PARAM_D=1 PARAM_W=32
make PARAM_D=2 PARAM_W=64
make PARAM_D=4 PARAM_W=128
```

All tests should pass after the fix.
