@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\doccraft-cli.exe" (
    ".venv\Scripts\doccraft-cli.exe" %*
) else (
    uv run doccraft-cli %*
)
