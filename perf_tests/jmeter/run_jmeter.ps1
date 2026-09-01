param(
    [string]$Plan = "02_read_single_api_perf",
    [string]$Env = "test",
    [int]$Threads = 10,
    [int]$RampUp = 10,
    [int]$LoopCount = 10,
    [int]$Duration = 0,
    [double]$TargetRps = 0,
    [ValidateSet("debug", "formal")]
    [string]$ReportType = "debug",
    [string]$ResultName = "",
    [switch]$NoHtml
)

$ErrorActionPreference = "Stop"

$JMeterDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PerfDir = Split-Path -Parent $JMeterDir
$ProjectDir = Split-Path -Parent $PerfDir

$PlanPath = Join-Path $JMeterDir "plans\$Plan.jmx"
$EnvPath = Join-Path $JMeterDir "env\$Env.properties"

if (-not (Test-Path -LiteralPath $PlanPath)) {
    throw "JMeter plan not found: $PlanPath"
}

if (-not (Test-Path -LiteralPath $EnvPath)) {
    throw "JMeter env file not found: $EnvPath"
}

if ([string]::IsNullOrWhiteSpace($ResultName)) {
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $ResultName = "${Plan}_${Timestamp}"
}

$JtlDir = Join-Path $JMeterDir "results\jtl"
$HtmlRootDir = Join-Path $JMeterDir "results\html"
$ReportDir = Join-Path $JMeterDir "reports\$ReportType"

New-Item -ItemType Directory -Force -Path $JtlDir, $HtmlRootDir, $ReportDir | Out-Null

$JtlPath = Join-Path $JtlDir "$ResultName.jtl"
$HtmlDir = Join-Path $HtmlRootDir $ResultName
$MarkdownPath = Join-Path $ReportDir "$ResultName.md"

if (Test-Path -LiteralPath $JtlPath) {
    Remove-Item -LiteralPath $JtlPath -Force
}

if (Test-Path -LiteralPath $HtmlDir) {
    [System.IO.Directory]::Delete($HtmlDir, $true)
}

$Args = @(
    "-n",
    "-t", $PlanPath,
    "-q", $EnvPath,
    "-Jthreads=$Threads",
    "-Jramp_up=$RampUp",
    "-Jloop_count=$LoopCount",
    "-Jwrite_threads=$Threads",
    "-Jwrite_ramp_up=$RampUp",
    "-Jwrite_loop_count=$LoopCount",
    "-l", $JtlPath
)

$SummaryThreads = $Threads
$ThreadSplits = [ordered]@{}

if ($Duration -gt 0) {
    $Args += "-Jduration_seconds=$Duration"
}

if ($TargetRps -gt 0) {
    $Culture = [System.Globalization.CultureInfo]::InvariantCulture

    $ReadMixWeights = [ordered]@{
        user_list = 0.30
        user_detail = 0.15
        role_list = 0.20
        role_detail = 0.10
        menu_list = 0.05
        dept_list = 0.10
        post_list = 0.10
    }

    $SummaryThreads = 0

    $Args += "-Jtarget_rps=$($TargetRps.ToString('0.###', $Culture))"

    foreach ($Name in $ReadMixWeights.Keys) {
        $Weight = $ReadMixWeights[$Name]
        $Rps = $TargetRps * $Weight
        $ThreadCount = [Math]::Max(1, [int][Math]::Ceiling($Threads * $Weight))
        $SummaryThreads += $ThreadCount
        $ThreadSplits[$Name] = $ThreadCount

        $Args += "-J${Name}_rpm=$(($Rps * 60).ToString('0.###', $Culture))"
        $Args += "-J${Name}_threads=$ThreadCount"
    }

    $Args += "-Juser_rpm=$(($TargetRps * 0.45 * 60).ToString('0.###', $Culture))"
    $Args += "-Jrole_rpm=$(($TargetRps * 0.30 * 60).ToString('0.###', $Culture))"
    $Args += "-Jmenu_rpm=$(($TargetRps * 0.05 * 60).ToString('0.###', $Culture))"
    $Args += "-Jdept_rpm=$(($TargetRps * 0.20 * 60).ToString('0.###', $Culture))"
    $Args += "-Juser_threads=$([Math]::Max(1, [int][Math]::Ceiling($Threads * 0.45)))"
    $Args += "-Jrole_threads=$([Math]::Max(1, [int][Math]::Ceiling($Threads * 0.30)))"
    $Args += "-Jmenu_threads=$([Math]::Max(1, [int][Math]::Ceiling($Threads * 0.05)))"
    $Args += "-Jdept_threads=$([Math]::Max(1, [int][Math]::Ceiling($Threads * 0.20)))"
}

if (-not $NoHtml) {
    $Args += @("-e", "-o", $HtmlDir)
}

Write-Host "Running JMeter plan: $Plan"
if ($TargetRps -gt 0) {
    Write-Host "TotalThreads=$SummaryThreads RampUp=$RampUp"
    Write-Host "Thread split: UserList=$($ThreadSplits['user_list']) UserDetail=$($ThreadSplits['user_detail']) RoleList=$($ThreadSplits['role_list']) RoleDetail=$($ThreadSplits['role_detail']) MenuList=$($ThreadSplits['menu_list']) DeptList=$($ThreadSplits['dept_list']) PostList=$($ThreadSplits['post_list'])"
} else {
    Write-Host "Threads=$Threads RampUp=$RampUp LoopCount=$LoopCount"
}
if ($Duration -gt 0) {
    Write-Host "Duration=$Duration seconds"
}
if ($TargetRps -gt 0) {
    Write-Host "TargetRps=$TargetRps UserList=30% UserDetail=15% RoleList=20% RoleDetail=10% MenuList=5% DeptList=10% PostList=10%"
}
Write-Host "JTL: $JtlPath"
if (-not $NoHtml) {
    Write-Host "HTML: $HtmlDir"
}

& jmeter @Args
if ($LASTEXITCODE -ne 0) {
    throw "JMeter exited with code $LASTEXITCODE"
}

if (-not (Test-Path -LiteralPath $JtlPath)) {
    throw "JMeter did not generate JTL result file: $JtlPath"
}

$Python = Join-Path $ProjectDir "..\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}

$SummaryScript = Join-Path $JMeterDir "tools\summarize_jtl.py"
$SummaryArgs = @(
    $SummaryScript,
    "--jtl", $JtlPath,
    "--output", $MarkdownPath,
    "--plan", $Plan,
    "--threads", $SummaryThreads,
    "--ramp-up", $RampUp,
    "--loop-count", $LoopCount
)
if ($Duration -gt 0) {
    $SummaryArgs += @("--duration", $Duration)
}
if ($TargetRps -gt 0) {
    $SummaryArgs += @("--target-rps", $TargetRps)
}

& $Python @SummaryArgs
if ($LASTEXITCODE -ne 0) {
    throw "JTL summary failed with code $LASTEXITCODE"
}

Write-Host "Markdown summary: $MarkdownPath"
