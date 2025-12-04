<#!
setup.ps1

One-click Windows setup for Agent Council:
- Creates a local venv (.venv)
- Installs dependencies
- Prompts for and writes OPENAI_API_KEY to .env
- Optionally launches agentcouncil.py

Usage (PowerShell):
  powershell -ExecutionPolicy Bypass -File setup.ps1
  # Optional: skip auto-run prompt
  powershell -ExecutionPolicy Bypass -File setup.ps1 -NoRun

#>

param(
    [switch]$NoRun
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Error "Required command '$Name' not found. Please install it and re-run." -ErrorAction Stop
    }
}

function Get-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) { return 'python' }
    if (Get-Command py -ErrorAction SilentlyContinue) { return 'py -3' }
    Write-Error "Python 3.x not found. Install from https://www.python.org/downloads/ and re-run." -ErrorAction Stop
}

function Read-ApiKey {
    param([string]$Existing)
    $prompt = 'Enter your OpenAI API key (sk-...):'
    if ($Existing) { $prompt = "Existing key detected. Press Enter to keep or enter a new one:" }
    $secure = Read-Host $prompt -AsSecureString
    if (-not $secure || ($secure.Length -eq 0 -and $Existing)) {
        return $Existing
    }
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto($ptr)
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    return $plain
}

Push-Location $PSScriptRoot
try {
    Write-Host "[1/5] Checking prerequisites..." -ForegroundColor Cyan
    $python = Get-Python
    Assert-Command ($python.Split(' ')[0])

    Write-Host "[2/5] Creating virtual environment (.venv) if needed..." -ForegroundColor Cyan
    if (-not (Test-Path ".venv")) {
        & $python -m venv .venv
    }

    $activate = Join-Path ".venv" "Scripts/Activate.ps1"
    if (-not (Test-Path $activate)) {
        Write-Error "Activation script not found at $activate" -ErrorAction Stop
    }

    Write-Host "[3/5] Activating venv and installing dependencies..." -ForegroundColor Cyan
    . $activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    python -m pip install -e .

    Write-Host "[4/5] Setting OPENAI_API_KEY in .env..." -ForegroundColor Cyan
    $envPath = Join-Path $PSScriptRoot ".env"
    $existingKey = $null
    if (Test-Path $envPath) {
        $envLines = Get-Content $envPath
        foreach ($line in $envLines) {
            if ($line -match '^OPENAI_API_KEY\s*=') {
                $existingKey = $line -replace '^OPENAI_API_KEY\s*=\s*', ''
                break
            }
        }
    } else {
        $envLines = @()
    }

    $apiKey = Read-ApiKey -Existing $existingKey
    if (-not $apiKey) { Write-Error "No API key provided." -ErrorAction Stop }

    $newLines = @()
    $replaced = $false
    foreach ($line in $envLines) {
        if ($line -match '^OPENAI_API_KEY\s*=') {
            $newLines += "OPENAI_API_KEY=$apiKey"
            $replaced = $true
        } else {
            $newLines += $line
        }
    }
    if (-not $replaced) {
        $newLines += "OPENAI_API_KEY=$apiKey"
    }
    $newLines | Set-Content -Encoding UTF8 $envPath
    Write-Host "API key saved to .env" -ForegroundColor Green

    Write-Host "[5/5] Setup complete." -ForegroundColor Cyan
    if (-not $NoRun) {
        $run = Read-Host "Run Agent Council now? (y/n)"
        if ($run -match '^[Yy]') {
            Write-Host "Launching agentcouncil.py..." -ForegroundColor Green
            python agentcouncil.py
        }
    }
}
finally {
    Pop-Location
}
