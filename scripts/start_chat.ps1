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

function Start-DockerIfNeeded {
    docker info *> $null
    if ($LASTEXITCODE -eq 0) {
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
        docker info *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Docker pronto."
            return
        }
    }

    throw "Docker Desktop nao ficou pronto a tempo. Abra o Docker Desktop e rode o comando novamente."
}

Start-DockerIfNeeded
Invoke-Step "Subindo PostgreSQL" { docker compose up -d postgres }

$env:ENABLE_POSTGRES_PERSISTENCE = "true"
$env:POSTGRES_URL = "postgresql://postgres:postgres@127.0.0.1:55432/lifelineone"

Invoke-Step "Instalando/verificando dependencias" { .\.venv\Scripts\python.exe -m pip install -r requirements.txt }
Invoke-Step "Rodando suite de testes" { .\.venv\Scripts\python.exe -m pytest }
Invoke-Step "Abrindo chat local" { .\.venv\Scripts\python.exe scripts\chat_cli.py }
