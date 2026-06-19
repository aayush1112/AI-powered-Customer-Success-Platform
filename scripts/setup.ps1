# ─────────────────────────────────────────────────────────────
#  Project setup script — Windows PowerShell
# ─────────────────────────────────────────────────────────────
$ErrorActionPreference = "Stop"

function Write-Info    ($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Success ($msg) { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn    ($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }

Write-Info "Setting up AI-Powered Customer Success Platform..."

# ── Prerequisites ─────────────────────────────────────────────
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found. Install Docker Desktop first."
    exit 1
}

# ── Environment files ─────────────────────────────────────────
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Warn "Created .env — update secrets before running in production."
}
if (-not (Test-Path "backend\.env")) {
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Warn "Created backend\.env — update secrets before running in production."
}
if (-not (Test-Path "frontend\.env.local")) {
    Copy-Item "frontend\.env.example" "frontend\.env.local"
    Write-Warn "Created frontend\.env.local."
}

# ── Build & start ─────────────────────────────────────────────
Write-Info "Building and starting Docker services..."
docker compose up --build -d

Write-Info "Waiting for services to be healthy (up to 60 s)..."
$healthy = $false
for ($i = 0; $i -lt 12; $i++) {
    try {
        $result = docker compose exec backend curl -sf http://localhost:8000/api/v1/health 2>$null
        if ($LASTEXITCODE -eq 0) { $healthy = $true; break }
    } catch {}
    Start-Sleep -Seconds 5
}

# ── Migrations ────────────────────────────────────────────────
Write-Info "Running database migrations..."
docker compose exec backend alembic upgrade head

Write-Success "Setup complete!"
Write-Host ""
Write-Host "  Frontend: http://localhost:3000"
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  API Docs: http://localhost:8000/api/v1/docs"
Write-Host "  Health:   http://localhost:8000/api/v1/health"
