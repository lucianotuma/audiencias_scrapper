@echo off
:: ============================================
:: SISTEMA DE AUDIÊNCIAS - LAUNCHER
:: ============================================
:: Este arquivo facilita a execução do sistema
:: 
:: Duplo clique neste arquivo para executar

title Sistema de Audiencias v2.0
color 0B

echo.
echo ============================================
echo   SISTEMA DE AUDIENCIAS v2.0
echo ============================================
echo.
echo Iniciando sistema...
echo.

:: Executa o sistema
SistemaAudiencias.exe

:: Mantém a janela aberta em caso de erro
if errorlevel 1 (
    echo.
    echo ============================================
    echo   ERRO NA EXECUCAO
    echo ============================================
    echo.
    echo Verifique os logs em: logs\audiencias.log
    echo.
    pause
)
