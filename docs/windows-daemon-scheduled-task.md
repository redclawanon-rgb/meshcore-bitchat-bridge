# Windows scheduled-task daemon gate

This gate makes the MeshCore-side daemon persistent on Eric's Windows desktop while preserving the existing live-hardware safety gates.

## Scope

- Host: Eric's Windows desktop reached over Tailscale/SSH.
- Repo clone: `C:\Users\station1\meshcore-bitchat-bridge`.
- Python: `C:\Users\station1\AppData\Local\Programs\Python\Python311\python.exe`.
- MeshCore USB Companion ports:
  - `pocket1=COM5` / USB serial `BAE292D6B7431B72`
  - `pocket2=COM8` / USB serial `99EF9E1DC9D17560`

## Safety boundary

The launcher and installer both default to a no-open dry-run mode.

- `Start-MeshCoreBridgeDaemon.ps1` opens no serial ports unless `-OpenRealPorts` is supplied.
- `Install-MeshCoreBridgeScheduledTask.ps1` registers a dry-run task unless `-EnableRealPorts` is supplied.
- The underlying daemon still requires `--open-real-ports` before any serial port is opened.

## Files added

```text
scripts/windows/Start-MeshCoreBridgeDaemon.ps1
scripts/windows/Install-MeshCoreBridgeScheduledTask.ps1
```

## Log and state layout

Default root:

```text
%LOCALAPPDATA%\MeshCoreBitchatBridge
```

Subpaths:

```text
logs\meshcore-bridge-YYYYMMDD-HHMMSS.jsonl
state\meshcore-bridge-state.json
stdout\meshcore-bridge-YYYYMMDD-HHMMSS.out.log
stdout\meshcore-bridge-YYYYMMDD-HHMMSS.err.log
```

The JSONL event log is append-only per daemon run. The state file persists the next bridge message ID so scheduled-task restarts do not reuse IDs.

## Dry-run launcher smoke

From Windows PowerShell:

```powershell
cd C:\Users\station1\meshcore-bitchat-bridge
.\scripts\windows\Start-MeshCoreBridgeDaemon.ps1 -DurationSeconds 1
```

Expected boundaries:

- Prints `meshcore_bridge_windows_launcher_v0` with `mode=dry-run-no-ports-opened`.
- Underlying daemon prints `mode=dry-run-no-ports-opened` in the stdout log.
- No COM port opens occur.

## Register a dry-run scheduled task

```powershell
cd C:\Users\station1\meshcore-bitchat-bridge
.\scripts\windows\Install-MeshCoreBridgeScheduledTask.ps1 -StartNow
```

This verifies task registration/restart plumbing without opening COM ports.

## Register the live scheduled task

Only run after live real-port access is approved for the desktop session:

```powershell
cd C:\Users\station1\meshcore-bitchat-bridge
.\scripts\windows\Install-MeshCoreBridgeScheduledTask.ps1 -EnableRealPorts -StartNow
```

The task action invokes the launcher with `-OpenRealPorts`, which translates to the daemon's `--open-real-ports` gate.

## Inspect task and logs

```powershell
Get-ScheduledTask -TaskName MeshCoreBitchatBridgeDaemon
Get-ScheduledTaskInfo -TaskName MeshCoreBitchatBridgeDaemon
Get-ChildItem "$env:LOCALAPPDATA\MeshCoreBitchatBridge\logs" | Sort-Object LastWriteTime -Descending | Select-Object -First 3
Get-Content "$env:LOCALAPPDATA\MeshCoreBitchatBridge\state\meshcore-bridge-state.json"
```

Useful JSONL event checks:

```powershell
$latest = Get-ChildItem "$env:LOCALAPPDATA\MeshCoreBitchatBridge\logs\*.jsonl" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $latest.FullName -Tail 20
```

Look for:

- `daemon_plan`
- `port_opened` for `COM5` and `COM8` when live mode is enabled
- `state_saved`
- `port_closed` only when the run exits or a device is unplugged/erroring
- no unexpected `parse_error`

## Stop or remove

```powershell
Stop-ScheduledTask -TaskName MeshCoreBitchatBridgeDaemon
Unregister-ScheduledTask -TaskName MeshCoreBitchatBridgeDaemon -Confirm:$false
```

## Verification status

Local repo verification should include:

```bash
python3 -m unittest discover -s tests -v
```

Windows verification should include at least:

1. dry-run launcher smoke;
2. dry-run scheduled-task registration with `-StartNow`;
3. if live access is approved, live scheduled task with `-EnableRealPorts -StartNow` plus latest log/state inspection.

## Non-claims

This gate does not add the real bitchat/mobile side. It only makes the MeshCore-side daemon launchable/persistent/restartable on Windows with JSONL evidence and persisted daemon state.
