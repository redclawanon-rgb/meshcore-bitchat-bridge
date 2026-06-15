# MeshCore bridge daemon launcher for Windows.
# Safe default: dry-run/no serial ports opened unless -OpenRealPorts is supplied.
[CmdletBinding()]
param(
    [string]$RepoPath = "C:\Users\station1\meshcore-bitchat-bridge",
    [string]$PythonExe = "C:\Users\station1\AppData\Local\Programs\Python\Python311\python.exe",
    [string]$Pocket1Port = "COM5",
    [string]$Pocket2Port = "COM8",
    [string]$Pocket3Port = "",
    [string]$LogRoot = "$env:LOCALAPPDATA\MeshCoreBitchatBridge",
    [double]$DurationSeconds = 31536000,
    [double]$PollIntervalSeconds = 0.05,
    [double]$ReconnectIntervalSeconds = 2.0,
    [string[]]$InjectText = @(),
    [switch]$OpenRealPorts
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = "Stop"

function Resolve-FullPath([string]$PathValue) {
    $expanded = [Environment]::ExpandEnvironmentVariables($PathValue)
    return [System.IO.Path]::GetFullPath($expanded)
}

$RepoPath = Resolve-FullPath $RepoPath
$PythonExe = Resolve-FullPath $PythonExe
$LogRoot = Resolve-FullPath $LogRoot
$ToolsDir = Join-Path $RepoPath "tools"
$DaemonPath = Join-Path $ToolsDir "meshcore_bridge_daemon.py"
$RunStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogDir = Join-Path $LogRoot "logs"
$StateDir = Join-Path $LogRoot "state"
$StdoutDir = Join-Path $LogRoot "stdout"
$EventLog = Join-Path $LogDir "meshcore-bridge-$RunStamp.jsonl"
$StateFile = Join-Path $StateDir "meshcore-bridge-state.json"
$StdoutLog = Join-Path $StdoutDir "meshcore-bridge-$RunStamp.out.log"
$StderrLog = Join-Path $StdoutDir "meshcore-bridge-$RunStamp.err.log"

New-Item -ItemType Directory -Force -Path $LogDir, $StateDir, $StdoutDir | Out-Null

if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
    throw "Python executable not found: $PythonExe"
}
if (-not (Test-Path -LiteralPath $DaemonPath -PathType Leaf)) {
    throw "Daemon script not found: $DaemonPath"
}

$daemonArgs = @(
    $DaemonPath,
    "--port", "pocket1=$Pocket1Port",
    "--port", "pocket2=$Pocket2Port",
    "--event-log", $EventLog,
    "--state-file", $StateFile,
    "--duration-seconds", ([string]$DurationSeconds),
    "--poll-interval-seconds", ([string]$PollIntervalSeconds),
    "--reconnect-interval-seconds", ([string]$ReconnectIntervalSeconds)
)
if ($Pocket3Port) {
    $daemonArgs += @("--port", "pocket3=$Pocket3Port")
}

foreach ($item in $InjectText) {
    $daemonArgs += @("--inject-text", $item)
}

if ($OpenRealPorts) {
    $daemonArgs += "--open-real-ports"
}

$ports = [ordered]@{ pocket1 = $Pocket1Port; pocket2 = $Pocket2Port }
if ($Pocket3Port) {
    $ports.pocket3 = $Pocket3Port
}

$plan = [ordered]@{
    type = "meshcore_bridge_windows_launcher_v0"
    mode = $(if ($OpenRealPorts) { "real-ports-requested" } else { "dry-run-no-ports-opened" })
    repo_path = $RepoPath
    python = $PythonExe
    daemon = $DaemonPath
    ports = $ports
    event_log = $EventLog
    state_file = $StateFile
    stdout_log = $StdoutLog
    stderr_log = $StderrLog
    duration_seconds = $DurationSeconds
    poll_interval_seconds = $PollIntervalSeconds
    reconnect_interval_seconds = $ReconnectIntervalSeconds
}
$plan | ConvertTo-Json -Depth 5

Push-Location $RepoPath
try {
    & $PythonExe @daemonArgs 1>> $StdoutLog 2>> $StderrLog
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

$result = [ordered]@{
    type = "meshcore_bridge_windows_launcher_result_v0"
    exit_code = $exitCode
    event_log = $EventLog
    state_file = $StateFile
    stdout_log = $StdoutLog
    stderr_log = $StderrLog
}
$result | ConvertTo-Json -Depth 5
exit $exitCode
