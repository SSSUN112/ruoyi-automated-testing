# Jenkins 持续集成说明

## 作用

本项目通过 `Jenkinsfile` 接入 Jenkins 持续集成，用来自动完成环境准备、测试环境检查、接口/UI 自动化测试执行、测试报告归档，以及可选的轻量性能测试。

## 前置条件

Jenkins 节点需要提前准备：

- Python 3.11
- JMeter，并把 `jmeter` 加入系统环境变量 `PATH`
- Allure CLI，或者安装 Jenkins Allure 插件
- RuoYi 后端、前端、MySQL、Redis 服务已启动
- 根据 `.env.test.example` 创建 Jenkins 节点上的 `.env.test`

默认测试环境端口：

| 服务 | 地址 |
| --- | --- |
| 后端服务 | `127.0.0.1:19099` |
| 前端服务 | `127.0.0.1:12580` |
| MySQL | `127.0.0.1:13306` |
| Redis | `127.0.0.1:16379` |

## 参数说明

| 参数 | 说明 |
| --- | --- |
| `TEST_ENV` | 选择环境配置，例如 `test` 会读取 `.env.test` |
| `TEST_SUITE` | 选择执行范围：`smoke`、`api`、`ui`、`full` |
| `RUN_PERFORMANCE` | 是否执行轻量 JMeter 性能测试 |

## 常用执行方式

日常提交代码后，建议先执行：

```powershell
TEST_SUITE=smoke
RUN_PERFORMANCE=false
```

接口改动后，建议执行：

```powershell
TEST_SUITE=api
RUN_PERFORMANCE=false
```

上线前或阶段性验收，建议执行：

```powershell
TEST_SUITE=full
RUN_PERFORMANCE=true
```

## 产物

CI 执行后会归档：

- `logs/**/*.log`
- `reports/**`
- `perf_tests/jmeter/reports/formal/*.md`
- `perf_tests/jmeter/results/jtl/*.jtl`

如果 Jenkins 安装了 Allure 插件，会直接在构建页面展示 Allure 测试报告。
