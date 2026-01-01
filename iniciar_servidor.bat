@echo off
echo ================================================
echo  Iniciando Denimax - Dashboard de Producao
echo ================================================
echo.

REM Ativar ambiente virtual se existir
if exist "venv\Scripts\activate.bat" (
    echo Ativando ambiente virtual...
    call venv\Scripts\activate.bat
)

REM Obter endereço IP local
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do set IP=%%a
set IP=%IP:~1%

echo.
echo Servidor iniciando...
echo Voce pode acessar em:
echo   - Local: http://localhost:5000
echo   - Rede: http://%IP%:5000
echo.
echo Pressione Ctrl+C para parar o servidor
echo ================================================
echo.

REM Iniciar aplicação
python -m backend.app

pause
