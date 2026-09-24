# RuoYi 自动化测试项目

这是一个面向 [RuoYi-Vue3-FastAPI](https://github.com/insistence/RuoYi-Vue3-FastAPI) 1.9.0 定制测试环境的自动化测试项目，覆盖接口测试、UI 测试、业务流程测试、性能测试和持续集成。

## 项目能力

- 使用 Pytest + Requests 完成接口自动化测试。
- 使用 YAML 管理测试数据，支持 `${variable}` 动态占位符替换。
- 校验 HTTP 状态、业务状态、响应结构以及 MySQL 数据落库结果。
- 通过 Redis 获取图片验证码，并验证登录令牌失效和接口权限。
- 使用 Playwright + Page Object 完成核心 UI 流程测试。
- UI 用例失败时自动采集截图、浏览器日志和 Playwright Trace。
- 使用 Allure 保存测试步骤、请求、响应和测试报告。
- 使用 JMeter 覆盖登录、只读接口、固定 RPS 和低并发写流程。
- 使用 Jenkins 按冒烟、接口、UI 或全量范围执行测试。

当前共收集 **194 条测试**：

- 接口及公共能力测试：176 条
- UI 测试：18 条
- 冒烟测试：47 条

## 被测系统

被测系统采用前后端分离架构：

- 前端：Vue 3、Vite、Element Plus、Pinia、Axios
- 后端：Python、FastAPI、SQLAlchemy、Pydantic、JWT
- 数据存储：MySQL 8.0、Redis
- 默认前端地址：`http://127.0.0.1:12580`
- 默认后端地址：`http://127.0.0.1:19099`

被测系统仓库可以通过 Docker Compose 启动。完整测试依赖前端、后端、MySQL 和 Redis 均处于可访问状态。

## 目录结构

```text
api_automation/
├── api_tests/
│   ├── apis/                 # API 对象封装
│   ├── data/                 # YAML 测试数据和上传文件
│   └── tests/                # 接口和业务流程用例
├── ui_tests/
│   ├── data/                 # UI 测试数据
│   ├── pages/                # Page Object 页面对象
│   └── tests/                # UI 自动化用例
├── common/                   # 请求、断言、数据库、Redis、日志等公共工具
├── perf_tests/jmeter/
│   ├── plans/                # JMeter 测试计划
│   ├── env/                  # 性能测试环境配置模板
│   ├── tools/                # JTL 汇总工具
│   └── run_jmeter.ps1        # JMeter 统一执行入口
├── ci/                       # Jenkins 使用说明
├── config.py                 # 环境配置入口
├── conftest.py               # Pytest fixtures 和测试钩子
├── pytest.ini                # Pytest 配置和 marker 声明
├── Jenkinsfile               # Jenkins Pipeline
└── requirements.txt          # Python 依赖
```

## 环境要求

- Windows 10/11
- Python 3.11
- Chromium（通过 Playwright 安装）
- 可选：Allure CLI，用于生成 HTML 报告
- 可选：JMeter 5.6.3 和 Java 17，用于性能测试
- 已启动的 RuoYi 前端、后端、MySQL 和 Redis

## 安装

在项目根目录执行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

复制测试环境配置模板：

```powershell
Copy-Item .env.test.example .env.test
```

然后按实际测试环境修改 `.env.test`。真实密码、Token 和服务地址只应保存在本地 `.env` 或 `.env.*` 文件中，不要提交到 Git。

主要配置项：

```dotenv
RUOYI_BASE_URL=http://127.0.0.1:19099
RUOYI_FRONTEND_URL=http://127.0.0.1:12580
RUOYI_USERNAME=admin
RUOYI_PASSWORD=change_me

RUOYI_DB_HOST=127.0.0.1
RUOYI_DB_PORT=13306
RUOYI_DB_USER=root
RUOYI_DB_PASSWORD=change_me
RUOYI_DB_NAME=ruoyi-fastapi

RUOYI_REDIS_HOST=127.0.0.1
RUOYI_REDIS_PORT=16379
RUOYI_REDIS_PASSWORD=
RUOYI_REDIS_DB=2
```

## 执行测试

执行全量回归：

```powershell
python -m pytest
```

执行冒烟测试：

```powershell
python -m pytest -m smoke
```

只执行接口测试：

```powershell
python -m pytest api_tests/tests
```

只执行 UI 测试：

```powershell
python -m pytest ui_tests/tests
```

按模块执行，例如用户管理：

```powershell
python -m pytest api_tests/tests/test_user.py
```

执行单个测试方法：

```powershell
python -m pytest api_tests/tests/test_user.py::test_create_user
```

用例默认把 Allure 原始结果写入 `reports/allure-results`。如果本机安装了 Allure CLI，测试结束后会自动生成 `reports/html-report`。

## 测试数据和占位符

YAML 数据可以使用动态占位符：

```yaml
payload:
  username: ${unique_user}
  uuid: ${captcha_uuid}
  code: ${captcha_code}
```

测试执行时，框架会把唯一用户名、验证码 UUID 和从 Redis 读取的验证码答案放入上下文，再通过 `render_case()` 递归替换字典和列表中的占位符。

涉及新增、修改和删除的测试会创建临时数据，并在 fixture teardown 或 `finally` 中清理。请在独立测试环境运行全量测试。

## 性能测试

项目提供 6 个 JMeter 测试计划，覆盖登录、核心只读接口、混合 RPS 和业务写流程。示例：

```powershell
.\perf_tests\jmeter\run_jmeter.ps1 `
  -Plan 02_read_single_api_perf `
  -Threads 10 `
  -RampUp 10 `
  -LoopCount 10
```

更多说明见 [性能测试文档](perf_tests/README.md)。

## Jenkins 持续集成

`Jenkinsfile` 支持以下参数：

- `TEST_ENV`：`test`、`dev`、`prod`
- `TEST_SUITE`：`smoke`、`api`、`ui`、`full`
- `RUN_PERFORMANCE`：是否执行轻量 JMeter 性能验证

流水线按TEST_SUITE检查实际配置：smoke为API冒烟，api/smoke只检查后端、MySQL、Redis；ui/full另检查前端并安装Chromium。服务需提前启动。JUnit、Allure、日志和UI附件按构建号隔离，具体见[使用说明](ci/jenkins_usage.md)。

详细配置见 [Jenkins 持续集成说明](ci/jenkins_usage.md)。

## 使用说明

本项目用于自动化测试学习、框架实践和测试环境回归。仓库中的账号和密码应仅使用测试账号；提交代码前请再次确认 `.env`、日志、报告和本地测试产物未被 Git 跟踪。
