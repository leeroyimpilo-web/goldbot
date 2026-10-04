$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    py -3.12 -m venv .venv
}

& ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -e ".[mt5]"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env. Edit broker/database/auth settings before starting GoldBot."
    exit 1
}

python -m app.runner
