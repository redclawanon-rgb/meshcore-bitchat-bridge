# Register/start a Windows Scheduled Task for the MeshCore bridge daemon.
# Safe default: registers a dry-run task unless -EnableRealPorts is supplied.
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$TaskName = "MeshCoreBitchatBridgeDaemon",
    [string]$RepoPath = "C:\Users\station1\meshcore-bitchat-bridge",
    [string]$PythonExe = "C:\Users\station1\AppData\Local\Programs\Python\Python311\python.exe",
    [string]$Pocket1Port = "COM5",
    [string]$Pocket2Port = "COM8",
    [string]$Pocket3Port = "",
    [string]$LogRoot = "$env:LOCALAPPDATA\MeshCoreBitchatBridge",
    [double]$DurationSeconds = 31536000,
    [double]$ReconnectIntervalSeconds = 2.0,
    [string[]]$InjectText = @(),
    [switch]$EnableRealPorts,
    [switch]$StartNow
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = "Stop"

function Quote-TaskArg([string]$Value) {
    return '"' + ($Value -replace '"', '\"') + '"'
}

$LauncherPath = Join-Path $RepoPath "scripts\windows\Start-MeshCoreBridgeDaemon.ps1"
if (-not (Test-Path -LiteralPath $LauncherPath -PathType Leaf)) {
    throw "Launcher script not found: $LauncherPath"
}
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
    throw "Python executable not found: $PythonExe"
}

$pwshCommand = Get-Command pwsh.exe -ErrorAction SilentlyContinue
if ($pwshCommand) {
    $pwsh = $pwshCommand.Source
}
else {
    $pwsh = (Get-Command powershell.exe -ErrorAction Stop).Source
}

$argumentList = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", (Quote-TaskArg $LauncherPath),
    "-RepoPath", (Quote-TaskArg $RepoPath),
    "-PythonExe", (Quote-TaskArg $PythonExe),
    "-Pocket1Port", (Quote-TaskArg $Pocket1Port),
    "-Pocket2Port", (Quote-TaskArg $Pocket2Port),
    "-LogRoot", (Quote-TaskArg $LogRoot),
    "-DurationSeconds", ([string]$DurationSeconds),
    "-ReconnectIntervalSeconds", ([string]$ReconnectIntervalSeconds)
)
if ($Pocket3Port) {
    $argumentList += @("-Pocket3Port", (Quote-TaskArg $Pocket3Port))
}
foreach ($item in $InjectText) {
    $argumentList += @("-InjectText", (Quote-TaskArg $item))
}
if ($EnableRealPorts) {
    $argumentList += "-OpenRealPorts"
}
$taskArguments = $argumentList -join " "

$action = New-ScheduledTaskAction -Execute $pwsh -Argument $taskArguments -WorkingDirectory $RepoPath
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Days 365) `
    -MultipleInstances IgnoreNew `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

$summaryPorts = [ordered]@{ pocket1 = $Pocket1Port; pocket2 = $Pocket2Port }
if ($Pocket3Port) {
    $summaryPorts.pocket3 = $Pocket3Port
}

$summary = [ordered]@{
    type = "meshcore_bridge_scheduled_task_plan_v0"
    task_name = $TaskName
    mode = $(if ($EnableRealPorts) { "real-ports-enabled" } else { "dry-run-no-ports-opened" })
    execute = $pwsh
    arguments = $taskArguments
    working_directory = $RepoPath
    trigger = "AtLogOn"
    restart_interval = "PT1M"
    restart_count = 999
    ports = $summaryPorts
    log_root = $LogRoot
    inject_count = $InjectText.Count
    start_now = [bool]$StartNow
}
$summary | ConvertTo-Json -Depth 5

if ($PSCmdlet.ShouldProcess($TaskName, "Register scheduled task")) {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    $registered = Get-ScheduledTask -TaskName $TaskName
    if ($StartNow) {
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 2
    }
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    [ordered]@{
        type = "meshcore_bridge_scheduled_task_result_v0"
        task_name = $registered.TaskName
        state = [string]$registered.State
        last_run_time = $info.LastRunTime
        last_task_result = $info.LastTaskResult
        next_run_time = $info.NextRunTime
    } | ConvertTo-Json -Depth 5
}
