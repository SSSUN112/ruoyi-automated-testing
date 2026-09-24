pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 60, unit: 'MINUTES')
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
    TEST_SUITE = "${params.TEST_SUITE}"
    CI = 'true'
    CI_REPORT_DIR = "reports/ci-${BUILD_NUMBER}"
    RUOYI_API_TEST_LOG_DIR = "reports/ci-${BUILD_NUMBER}/logs"
    }

    stages {
        stage('准备 Python 环境') {
            steps {
                powershell '''
                    $ErrorActionPreference = "Stop"
                    if (-not (Test-Path ".venv\\Scripts\\python.exe")) {
                        & $env:BASE_PYTHON -m venv .venv
                        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
                    }

                    .venv\\Scripts\\python.exe -m pip install -r requirements.txt
                    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
                '''
            }
        }

        stage('准备 UI 浏览器') {
            when { expression { return params.TEST_SUITE in ['ui', 'full'] } }
            steps {
                powershell '& $env:PYTHON -m playwright install chromium; exit $LASTEXITCODE'
            }
        }

        stage('检查测试环境') {
            steps {
                powershell '& $env:PYTHON ci/check_environment.py --suite $env:TEST_SUITE; exit $LASTEXITCODE'
            }
        }

        stage('执行自动化测试') {
            steps {
                script {
                    def testCommand = ''

                    if (params.TEST_SUITE == 'smoke') {
                        testCommand = "${env.PYTHON} -m pytest api_tests/tests -m smoke"
                    } else if (params.TEST_SUITE == 'api') {
                        testCommand = "${env.PYTHON} -m pytest api_tests/tests"
                    } else if (params.TEST_SUITE == 'ui') {
                        testCommand = "${env.PYTHON} -m pytest ui_tests/tests"
                    } else {
                        testCommand = "${env.PYTHON} -m pytest"
                    }

                    powershell "& ${testCommand} --alluredir=${env.CI_REPORT_DIR}/allure-results --junitxml=${env.CI_REPORT_DIR}/junit.xml; exit \$LASTEXITCODE"
                }
            }
        }

        stage('执行轻量性能测试') {
            when {
                expression { return params.RUN_PERFORMANCE }
            }
            steps {
                powershell '''
                    $ErrorActionPreference = "Stop"
                    Get-Command jmeter -ErrorAction Stop | Out-Null
                    .\\perf_tests\\jmeter\\run_jmeter.ps1 -Env $env:TEST_ENV -Plan 01_login_perf -Threads 1 -RampUp 1 -LoopCount 5 -ReportType formal -ResultName "ci_${env:BUILD_NUMBER}_01_login_baseline" -NoHtml
                    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
                    .\\perf_tests\\jmeter\\run_jmeter.ps1 -Env $env:TEST_ENV -Plan 02_read_single_api_perf -Threads 10 -RampUp 5 -LoopCount 3 -ReportType formal -ResultName "ci_${env:BUILD_NUMBER}_02_read_single_api_10threads" -NoHtml
                    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
                    .\\perf_tests\\jmeter\\run_jmeter.ps1 -Env $env:TEST_ENV -Plan 03_admin_read_mix_rps_perf -Threads 20 -RampUp 5 -Duration 30 -TargetRps 10 -ReportType formal -ResultName "ci_${env:BUILD_NUMBER}_03_read_mix_10rps" -NoHtml
                    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
                '''
            }
        }
    }

    post {
        always {
            junit testResults: "${env.CI_REPORT_DIR}/junit.xml", allowEmptyResults: true
            archiveArtifacts(
                artifacts: "${env.CI_REPORT_DIR}/**,perf_tests/jmeter/reports/formal/ci_${env.BUILD_NUMBER}_*.md,perf_tests/jmeter/results/jtl/ci_${env.BUILD_NUMBER}_*.jtl",
                allowEmptyArchive: true
            )

            script {
                try {
                    allure includeProperties: false, jdk: '', results: [[path: "${env.CI_REPORT_DIR}/allure-results"]]
                } catch (err) {
                    echo "Jenkins 未安装 Allure 插件或 Allure 发布失败，已保留 reports/allure-results 原始结果。"
                }
            }
        }
    }
}
