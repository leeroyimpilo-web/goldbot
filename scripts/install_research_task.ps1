$ErrorActionPreference = "Stop"

$repo = (Resolve-Path ".").Path
$python = Join-Path $repo ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "GoldBot virtual environment not found. Run scripts\run_goldbot_windows.ps1 first."
}

$action = New-ScheduledTaskAction -Execute $python -Argument "-m app.research_cycle" -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -Daily -At 11:45PM
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName "GoldBotNightlyResearch" -Action $action -Trigger $trigger -Settings $settings -Description "Runs GoldBot research/backtest cycle without promoting strategies automatically." -Force

Write-Host "Installed GoldBotNightlyResearch scheduled task."
