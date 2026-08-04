$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location -LiteralPath $projectRoot

if (-not (Test-Path -LiteralPath ".\.venv\Scripts\python.exe")) {
    throw "Ambiente virtual nao encontrado em .\.venv. Crie ou restaure a venv antes de rodar a simulacao."
}

.\.venv\Scripts\python.exe scripts\simulate_patients.py
