# AXIPIPE 测试工程

本项目为 AXIPIPE 的两个核心 RTL 模块提供完整的 Cocotb 测试平台。

## 项目结构

```
AXIPIPE/
├── rtl/                    # RTL 设计文件
│   ├── axis_bus_pipeline.v    # 通用流水线模块
│   └── axi_pipeline.v          # AXI4 流水线模块
│   └── signal_pipeline.v       # 无握手信号pipeline模块
├── tb/                     # 测试平台
│   ├── axis_bus_pipeline/     # axis_bus_pipeline 测试
│   │   ├── Makefile
│   │   ├── test_axis_bus_pipeline.py
│   │   └── BUG_REPORT.md      # RTL bug 报告
│   └── axi_pipeline/          # axi_pipeline 测试
│       ├── Makefile
│       └── test_axi_pipeline.py
├── README.md               # 项目说明文件
```

## 快速开始

### 环境要求

```bash
pip install cocotb cocotb-test cocotbext-axi pytest
```

需要安装仿真器：Icarus Verilog 或 Verilator

### 运行测试

#### axis_bus_pipeline 测试

```bash
cd tb/axis_bus_pipeline
make PARAM_D=1 PARAM_W=32      # 1级流水线，32位宽
make PARAM_D=2 PARAM_W=64      # 2级流水线，64位宽  
make WAVES=1 PARAM_D=1 PARAM_W=32  # 生成波形
```

#### axi_pipeline 测试

```bash
cd tb/axi_pipeline
make PARAM_D=1 PARAM_DATA_WIDTH=64     # 1级流水线，64位数据
make PARAM_D=2 PARAM_DATA_WIDTH=128    # 2级流水线，128位数据
make PARAM_D=0 PARAM_DATA_WIDTH=256    # 无流水线，256位数据
make WAVES=1 PARAM_D=1 PARAM_DATA_WIDTH=64  # 生成波形
```

## 测试结果

### axis_bus_pipeline - ✅ 9/9 通过

- `run_test_basic` - 基本功能测试
- `run_test_backpressure` - 背压处理测试
- `run_test_idle_insertion` - 空闲周期测试
- `run_test_full_stress` - 随机压力测试
- `run_test_reset_during_transfer` - 复位行为测试
- `run_test_continuous_transfer` - 连续传输测试
- `run_test_max_data_pattern` - 极值数据测试
- `run_test_single_word` - 单字传输测试
- `run_test_zero_delay_ready` - 零延迟就绪测试

**测试配置**:
- D=1, W=32: ✅ PASS 9/9
- D=2, W=64: ✅ PASS 9/9

### axi_pipeline - ✅ 15/15 通过

- `run_test_write_read_single` - 单次写读
- `run_test_write_burst` - 突发写
- `run_test_read_burst` - 突发读
- `run_test_multiple_outstanding` - 多未完成事务
- `run_test_concurrent_read_write` - 并发读写
- `run_test_max_size_transfer` - 最大尺寸传输
- `run_test_unaligned_access` - 非对齐访问
- `run_test_address_boundary` - 地址边界
- `run_test_data_patterns` - 数据模式
- `run_test_reset_during_transfer` - 传输中复位
- `run_test_back_to_back_transactions` - 背靠背事务
- `run_test_random_stress` - 随机压力测试
- `run_test_write_only_sequence` - 纯写序列
- `run_test_read_only_sequence` - 纯读序列
- `run_test_pipeline_depth_validation` - 流水线深度验证

**测试配置**:
- D=0, DATA_WIDTH=256: ✅ PASS 15/15
- D=1, DATA_WIDTH=64: ✅ PASS 15/15
- D=2, DATA_WIDTH=128: ✅ PASS 15/15

## 总结

✅ **测试完成度**: 100%  
✅ **axis_bus_pipeline**: 9个测试，全部通过  
✅ **axi_pipeline**: 15个测试，全部通过  

# axi_pipeline
