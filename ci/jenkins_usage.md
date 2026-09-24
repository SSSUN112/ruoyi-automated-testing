# Jenkins执行说明

流水线在Windows节点、仓库根目录运行，节点需Python 3.11；BASE_PYTHON默认D:\APP\python311\python.exe，按安装路径调整。保持被测服务手动启动，Jenkins不会启动或停止前后端。

| TEST_SUITE | 执行范围 | 连接检查 | Chromium |
| --- | --- | --- | --- |
| smoke | api_tests/tests中smoke标记 | 后端、MySQL、Redis | 不安装 |
| api | 全部API测试 | 后端、MySQL、Redis | 不安装 |
| ui | UI测试 | 后端、MySQL、Redis、前端 | 安装 |
| full | API与UI | 全部 | 安装 |

检查脚本ci/check_environment.py加载项目config.py，遵循TEST_ENV与.env配置，不硬编码端口。三次TCP连接尝试；端口可连接不等于应用健康，认证及业务功能仍由测试验证。输出服务名和结果，不输出密码。localhost指Jenkins执行节点，需与服务所在主机一致。

Jenkins节点需自行提供.env.test等文件，不能提交真实密码。现有config.py的环境文件会覆盖同名环境变量，使用Jenkins Credentials时须留意这一优先级。流水线不打印配置文件。

同一任务禁止并发，总超时60分钟；Python安装、pytest、浏览器安装失败退出，不把未收集到用例当通过。不在每轮强制升级pip。

报告保存在reports/ci-构建号/，含JUnit、Allure原始结果、日志和UI失败附件。Jenkins应安装JUnit插件，Allure插件可选；CI不再自动生成本地固定路径的Allure HTML。测试失败仍进入归档阶段，环境检查失败可能没有JUnit记录，允许空报告并保持原构建失败状态。

RUN_PERFORMANCE默认false。开启后检查jmeter命令，三套计划使用TEST_ENV对应的perf_tests/jmeter/env配置和独立构建号名称；注意JMeter属性文件与Python配置是独立来源，必须指向同一环境。性能测试按脚本执行结果判定，不新增响应时间/错误率门槛；如需性能门禁应另行定义阈值。

首次验证建议TEST_ENV=test、TEST_SUITE=api、RUN_PERFORMANCE=false。启动后端、MySQL、Redis即可，前端可以不启动。任务若采用SCM加载Jenkinsfile，先提交并推送修改，再构建；若在任务配置中粘贴脚本，则同步更新脚本及仓库辅助文件。不要把测试运行在未经确认的生产环境。

离线验证（不连接被测服务）：

```powershell
python -m unittest discover -s ci -p "test_*.py" -v
```
