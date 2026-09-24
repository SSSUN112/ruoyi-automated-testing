pipeline {
    agent any

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        choice(
            name: 'TEST_ENV',
            choices: ['test', 'dev', 'prod'],
            description: '选择要读取的环境配置文件，例如 .env.test'
        )
        choice(
            name: 'TEST_SUITE',
            choices: ['smoke', 'api', 'ui', 'full'],
            description: '选择本次 CI 要执行的自动化测试范围'
        )
        booleanParam(
            name: 'RUN_PERFORMANCE',
            defaultValue: false,
            description: '是否执行一组轻量 JMeter 性能验证'
        )
    }

    environment {
    BASE_PYTHON = 'D:\\APP\\python311\\python.exe'
    PYTHON = '.venv\\Scripts\\python.exe'
    TEST_ENV = "${params.TEST_ENV}"
    UI_HEADLESS = 'true'
    }

    stages {
        stage('准备 Python 环境') {
            steps {
                powershell '''
                    if (-not (Test-Path ".venv\\Scripts\\python.exe")) {
                        & $env:BASE_PYTHON -m venv .venv
                    }

                    .venv\\Scripts\\python.exe -m pip install --upgrade pip
                    .venv\\Scripts\\python.exe -m pip install -r requirements.txt
                    .venv\\Scripts\\python.exe -m playwright install chromium
                '''
            }
        }

        stage('检查测试环境') {
            steps {
                powershell '''
                    $ports = @(
                        @{ Name = "后端服务"; Host = "127.0.0.1"; Port = 19099 },
                        @{ Name = "前端服务"; Host = "127.0.0.1"; Port = 12580 },
                        @{ Name = "MySQL"; Host = "127.0.0.1"; Port = 13306 },
                        @{ Name = "Redis"; Host = "127.0.0.1"; Port = 16379 }
                    )

                    foreach ($item in $ports) {
                        $result = Test-NetConnection $item.Host -Port $item.Port -InformationLevel Quiet
                        if (-not $result) {
                            throw "$($item.Name) 未连通：$($item.Host):$($item.Port)"
                        }
                    }
                '''
            }
        }

        stage('执行自动化测试') {
            steps {
                script {
                    def testCommand = ''

                    if (params.TEST_SUITE == 'smoke') {
                        testCommand = "${env.PYTHON} -m pytest -m smoke"
                    } else if (params.TEST_SUITE == 'api') {
                        testCommand = "${env.PYTHON} -m pytest api_tests/tests"
                    } else if (params.TEST_SUITE == 'ui') {
                        testCommand = "${env.PYTHON} -m pytest ui_tests/tests"
                    } else {
                        testCommand = "${env.PYTHON} -m pytest"
                    }

                    powershell testCommand
                }
            }
        }

        stage('执行轻量性能测试') {
            when {
                expression { return params.RUN_PERFORMANCE }
            }
            steps {
                powershell '''
                    .\\perf_tests\\jmeter\\run_jmeter.ps1 -Plan 01_login_perf -Threads 1 -RampUp 1 -LoopCount 5 -ReportType formal -ResultName ci_01_login_baseline -NoHtml
                    .\\perf_tests\\jmeter\\run_jmeter.ps1 -Plan 02_read_single_api_perf -Threads 10 -RampUp 5 -LoopCount 3 -ReportType formal -ResultName ci_02_read_single_api_10threads -NoHtml
                    .\\perf_tests\\jmeter\\run_jmeter.ps1 -Plan 03_admin_read_mix_rps_perf -Threads 20 -RampUp 5 -Duration 30 -TargetRps 10 -ReportType formal -ResultName ci_03_read_mix_10rps -NoHtml
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts(
                artifacts: 'logs/**/*.log,reports/**,perf_tests/jmeter/reports/formal/*.md,perf_tests/jmeter/results/jtl/*.jtl',
                allowEmptyArchive: true
            )

            script {
                try {
                    allure includeProperties: false, jdk: '', results: [[path: 'reports/allure-results']]
                } catch (err) {
                    echo "Jenkins 未安装 Allure 插件或 Allure 发布失败，已保留 reports/allure-results 原始结果。"
                }
            }
        }
    }
}
