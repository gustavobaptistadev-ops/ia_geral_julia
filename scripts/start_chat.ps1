$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location -LiteralPath $projectRoot

function Invoke-Step {
    param(
        [string]$Description,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Description"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Falha na etapa: $Description"
    }
}

function Test-DockerReady {
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    docker info > $null 2>&1
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference
    return $exitCode -eq 0
}

function Start-DockerIfNeeded {
    if (Test-DockerReady) {
        return
    }

    $dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path -LiteralPath $dockerDesktop) {
        Write-Host "Docker Desktop nao esta rodando. Iniciando Docker Desktop..."
        Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
    } else {
        throw "Docker Desktop nao foi encontrado. Abra o Docker Desktop manualmente e rode o comando novamente."
    }

    for ($attempt = 1; $attempt -le 60; $attempt++) {
        Start-Sleep -Seconds 2
        if (Test-DockerReady) {
            Write-Host "Docker pronto."
            return
        }
    }

    throw "Docker Desktop nao ficou pronto a tempo. Abra o Docker Desktop e rode o comando novamente."
}

function Invoke-TestSuite {
    $settingsEnvNames = @(
        "APP_NAME",
        "APP_VERSION",
        "ENVIRONMENT",
        "DEBUG",
        "POSTGRES_URL",
        "ENABLE_POSTGRES_PERSISTENCE",
        "REDIS_URL",
        "GOOGLE_CALENDAR_API_KEY",
        "GOOGLE_CALENDAR_SCOPE",
        "API_SECRET_KEY",
        "ALLOWED_ORIGINS"
    )
    $savedValues = @{}

    foreach ($name in $settingsEnvNames) {
        $item = Get-Item -LiteralPath "Env:$name" -ErrorAction SilentlyContinue
        if ($null -ne $item) {
            $savedValues[$name] = $item.Value
            Remove-Item -LiteralPath "Env:$name" -ErrorAction SilentlyContinue
        }
    }

    try {
        .\.venv\Scripts\python.exe -m pytest
        if ($LASTEXITCODE -ne 0) {
            throw "pytest falhou"
        }
    } finally {
        foreach ($name in $savedValues.Keys) {
            Set-Item -LiteralPath "Env:$name" -Value $savedValues[$name]
        }
    }
}

Start-DockerIfNeeded
Invoke-Step "Subindo PostgreSQL" { docker compose up -d postgres }

Invoke-Step "Instalando/verificando dependencias" { .\.venv\Scripts\python.exe -m pip install -r requirements.txt }
Invoke-Step "Rodando suite de testes" { Invoke-TestSuite }

$env:ENABLE_POSTGRES_PERSISTENCE = "true"
$env:POSTGRES_URL = "postgresql://postgres:postgres@127.0.0.1:55432/lifelineone"

Invoke-Step "Abrindo chat local" { .\.venv\Scripts\python.exe scripts\chat_cli.py }
