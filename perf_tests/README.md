# 性能测试

本目录用于存放性能测试资产，和接口自动化、UI 自动化分开管理。

## 目录结构

```text
perf_tests/
  data/        # 性能测试公共参数化数据，JMeter/Locust 都放这里
  jmeter/
    plans/       # JMeter .jmx 脚本
    env/         # JMeter 环境参数模板
    results/
      jtl/       # 命令行运行生成的 .jtl 原始结果
      html/      # JMeter HTML 性能报告
    reports/
      debug/      # 调试报告
      formal/     # 正式报告
      templates/  # 报告模板
    tools/       # JMeter 辅助脚本，比如 JTL 汇总工具
    run_jmeter.ps1
    performance_test_plan.md
  locust/
    locustfile.py
    scenarios/
```

## JMeter 推荐流程

1. 先在 JMeter GUI 里创建和调试脚本。
2. 调通后把 `.jmx` 保存到 `perf_tests/jmeter/plans/`。
3. 参数化数据放到 `perf_tests/data/`。
4. 环境参数参考 `perf_tests/jmeter/env/test.properties.example`。
5. 正式执行时用命令行跑，不建议用 GUI 压测。

完整性能测试规划见：

```text
perf_tests/jmeter/performance_test_plan.md
```

## JMeter 框架入口

推荐使用封装好的运行脚本，不需要每次手写很长的 JMeter 命令：

```powershell
cd D:\PythonProject\ruoyi-api-test\api_automation

.\perf_tests\jmeter\run_jmeter.ps1 `
  -Plan 02_read_single_api_perf `
  -Threads 10 `
  -RampUp 10 `
  -LoopCount 10
```

运行后会自动生成：

```text
perf_tests/jmeter/results/jtl/      # JMeter 原始结果
perf_tests/jmeter/results/html/     # JMeter HTML 报告
perf_tests/jmeter/reports/debug/    # 默认 Markdown 调试报告
```

可以指定结果名称，便于对比多轮压测：

```powershell
.\perf_tests\jmeter\run_jmeter.ps1 `
  -Plan 02_read_single_api_perf `
  -Threads 20 `
  -RampUp 20 `
  -LoopCount 10 `
  -ResultName read_single_api_20threads
```

正式压测报告使用 `-ReportType formal`：

```powershell
.\perf_tests\jmeter\run_jmeter.ps1 `
  -Plan 03_admin_read_mix_rps_perf `
  -Threads 100 `
  -RampUp 5 `
  -Duration 30 `
  -TargetRps 100 `
  -ReportType formal `
  -ResultName admin_read_mix_100rps_30s
```

如果需要直接使用 JMeter 命令，也可以这样执行：

```powershell
jmeter -n `
  -t perf_tests/jmeter/plans/01_login_perf.jmx `
  -q perf_tests/jmeter/env/test.properties `
  -l perf_tests/jmeter/results/jtl/01_login_perf.jtl `
  -e -o perf_tests/jmeter/results/html/01_login_perf
```

常用命令行覆盖参数：

```powershell
jmeter -n `
  -t perf_tests/jmeter/plans/02_read_single_api_perf.jmx `
  -Jprotocol=http `
  -Jserver=127.0.0.1 `
  -Jport=19099 `
  -Jthreads=10 `
  -Jramp_up=10 `
  -Jloop_count=10 `
  -l perf_tests/jmeter/results/jtl/02_read_single_api_perf.jtl `
  -e -o perf_tests/jmeter/results/html/02_read_single_api_perf
```

## JMeter 场景脚本

建议先做登录认证和只读接口压测，风险低、容易稳定复现。

当前已有这些 JMeter 脚本：

```text
perf_tests/jmeter/plans/01_login_perf.jmx                 # 登录认证压测：验证码 -> 登录
perf_tests/jmeter/plans/02_read_single_api_perf.jmx       # 核心只读接口单接口压测：用户、角色、菜单、部门、岗位列表
perf_tests/jmeter/plans/03_admin_read_mix_rps_perf.jmx    # 后台只读混合业务固定 RPS 压测
perf_tests/jmeter/plans/04_user_write_flow_perf.jmx       # 用户生命周期读写流程低并发压测
perf_tests/jmeter/plans/05_role_menu_write_flow_perf.jmx  # 角色菜单权限读写流程低并发压测
perf_tests/jmeter/plans/06_org_user_write_flow_perf.jmx   # 部门岗位用户关联读写流程低并发压测
```

`01_login_perf.jmx` 用于登录认证链路：

```text
获取验证码 -> 登录 -> 提取 token
```

`02_read_single_api_perf.jmx` 用于核心只读接口单接口压测：

```text
单线程登录准备 token -> 依次执行用户、角色、菜单、部门、岗位列表线程组
```

登录认证压测示例：

```powershell
.\perf_tests\jmeter\run_jmeter.ps1 `
  -Plan 01_login_perf `
  -Threads 10 `
  -RampUp 10 `
  -LoopCount 10
```

核心只读接口压测示例：

```powershell
.\perf_tests\jmeter\run_jmeter.ps1 `
  -Plan 02_read_single_api_perf `
  -Threads 10 `
  -RampUp 10 `
  -LoopCount 10
```

固定 RPS 混合场景用于模拟管理员在系统管理模块内按业务比例访问多个只读接口。

```text
登录准备 token -> 按比例查询用户列表、用户详情、角色列表、角色详情、菜单列表、部门列表、岗位列表
```

```powershell
.\perf_tests\jmeter\run_jmeter.ps1 `
  -Plan 03_admin_read_mix_rps_perf `
  -Threads 100 `
  -RampUp 5 `
  -Duration 30 `
  -TargetRps 100
```

比如高峰期 30 秒，平均每秒 100 个请求，七类只读业务占比为：

```text
用户列表：30%，约 30 req/s
用户详情：15%，约 15 req/s
角色列表：20%，约 20 req/s
角色详情：10%，约 10 req/s
菜单列表：5%，约 5 req/s
部门列表：10%，约 10 req/s
岗位列表：10%，约 10 req/s
```

用户生命周期写流程用于低并发验证写入链路和清理能力：

```powershell
.\perf_tests\jmeter\run_jmeter.ps1 `
  -Plan 04_user_write_flow_perf `
  -Threads 1 `
  -RampUp 1 `
  -LoopCount 1
```

角色菜单权限流程用于低并发验证权限变更链路：

```powershell
.\perf_tests\jmeter\run_jmeter.ps1 `
  -Plan 05_role_menu_write_flow_perf `
  -Threads 1 `
  -RampUp 1 `
  -LoopCount 1
```

部门岗位用户关联流程用于低并发验证组织关系链路：

```powershell
.\perf_tests\jmeter\run_jmeter.ps1 `
  -Plan 06_org_user_write_flow_perf `
  -Threads 1 `
  -RampUp 1 `
  -LoopCount 1
```

`TargetRps` 会自动换算为 JMeter 的每分钟吞吐量：

```text
100 req/s = 6000 req/min
用户列表：1800 req/min
用户详情：900 req/min
角色列表：1200 req/min
角色详情：600 req/min
菜单列表：300 req/min
部门列表：600 req/min
岗位列表：600 req/min
```

高并发场景主要看同时有多少虚拟用户在线，比如 100 个线程同时循环请求。固定 RPS 场景主要看单位时间内产生多少请求，比如稳定产生 100 req/s。真实压测经常两者结合：用足够线程支撑目标 RPS，再观察响应时间、错误率和服务器资源。

如果报告里的实际 `Throughput/s` 明显低于 `TargetRps`，通常说明线程数不够、接口响应太慢、服务端资源不足或本地机器资源不足。可以逐步提高 `-Threads`，比如 100、300、500，对比观察是否能接近目标 RPS。

写接口可以后面低并发补充：

```text
新增用户 -> 删除用户
新增角色 -> 删除角色
```

## Locust 示例

```powershell
locust -f perf_tests/locust/locustfile.py --host http://127.0.0.1:19099
```

打开 Locust Web UI 后配置并发用户数、启动速率和运行时长。
