#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Start all Synapse AI Tutor services for development.
.DESCRIPTION
  Launches the FastAPI backend and the Vite frontend dev server in parallel.
  Optionally starts PostgreSQL and Redis via Docker Compose.
#>

param(
  [switch]$WithDocker,   # Start Postgres + Redis with docker-compose
  [switch]$BackendOnly,
  [switch]$FrontendOnly
)

$Root = $PSScriptRoot

Write-Host ""
Write-Host "  ╔═══════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "  ║       Synapse AI Tutor  🚀             ║" -ForegroundColor Magenta
Write-Host "  ╚═══════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

# Start infrastructure
if ($WithDocker) {
  Write-Host "▶ Starting PostgreSQL + Redis..." -ForegroundColor Cyan
  docker compose up -d postgres redis
  Start-Sleep -Seconds 3
}

$jobs = @()

# Start backend
if (-not $FrontendOnly) {
  Write-Host "▶ Starting FastAPI backend on http://localhost:8000 ..." -ForegroundColor Green
  $backendScript = {
    param($Root)
    Set-Location (Join-Path $Root "backend")
    # Activate venv if present
    if (Test-Path "..\venv\Scripts\Activate.ps1") { & "..\venv\Scripts\Activate.ps1" }
    elseif (Test-Path "..\synapse_ai_tutor\.venv\Scripts\Activate.ps1") { & "..\synapse_ai_tutor\.venv\Scripts\Activate.ps1" }
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info
  }
  $jobs += Start-Job -ScriptBlock $backendScript -ArgumentList $Root
}

# Give backend a moment to start
if (-not $BackendOnly -and -not $FrontendOnly) { Start-Sleep -Seconds 2 }

# Start frontend
if (-not $BackendOnly) {
  Write-Host "▶ Starting Vite frontend on http://localhost:5173 ..." -ForegroundColor Blue
  $frontendScript = {
    param($Root)
    Set-Location (Join-Path $Root "frontend")
    npm run dev
  }
  $jobs += Start-Job -ScriptBlock $frontendScript -ArgumentList $Root
}

Write-Host ""
Write-Host "  Services started. Press Ctrl+C to stop all." -ForegroundColor Yellow
Write-Host "  Backend: http://localhost:8000/docs" -ForegroundColor DarkCyan
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor DarkBlue
Write-Host ""

# Stream output from all jobs
try {
  while ($true) {
    foreach ($job in $jobs) {
      $output = Receive-Job -Job $job 2>&1
      if ($output) { Write-Host $output }
    }
    Start-Sleep -Milliseconds 500
  }
} finally {
  Write-Host "`nStopping services..." -ForegroundColor Yellow
  $jobs | Stop-Job
  $jobs | Remove-Job
}
