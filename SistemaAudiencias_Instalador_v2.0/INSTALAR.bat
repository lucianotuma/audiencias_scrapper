@echo off
chcp 65001 > nul
color 0B
cls

echo ===============================================
echo   INSTALADOR - SISTEMA DE AUDIENCIAS v2.0
echo   J. Macedo Advocacia
echo ===============================================
echo.
echo Este instalador ira copiar todos os arquivos
echo para a pasta de Programas e criar atalhos.
echo.
pause

echo.
echo Instalando...
echo.

REM Criar pasta de destino
set "INSTALL_DIR=%ProgramFiles%\Sistema de Audiencias"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copiar todos os arquivos
echo Copiando arquivos...
xcopy /E /I /Y "%~dp0*" "%INSTALL_DIR%" > nul

REM Criar atalho na Area de Trabalho
echo Criando atalho na Area de Trabalho...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut($env:USERPROFILE + '\Desktop\Sistema de Audiencias.lnk'); $s.TargetPath = '%INSTALL_DIR%\Executar.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()"

REM Criar atalho no Menu Iniciar
echo Criando atalho no Menu Iniciar...
set "START_MENU=%AppData%\Microsoft\Windows\Start Menu\Programs"
if not exist "%START_MENU%\Sistema de Audiencias" mkdir "%START_MENU%\Sistema de Audiencias"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%START_MENU%\Sistema de Audiencias\Sistema de Audiencias.lnk'); $s.TargetPath = '%INSTALL_DIR%\Executar.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()"

REM Criar arquivo de instrucoes na Area de Trabalho
echo Criando arquivo de instrucoes...
(
echo ==================================================
echo   COMO USAR O SISTEMA DE AUDIENCIAS
echo ==================================================
echo.
echo 1. De duplo clique no atalho "Sistema de Audiencias"
echo    na sua Area de Trabalho
echo.
echo 2. O Chrome ira abrir automaticamente
echo.
echo 3. Faca login MANUALMENTE nos sites do TRT2 e TRT15
echo    ^(complete o segundo fator de autenticacao^)
echo.
echo 4. Aguarde o sistema coletar as audiencias
echo.
echo 5. Pronto! As planilhas e calendario serao atualizados
echo    automaticamente
echo.
echo ==================================================
echo   OBSERVACOES IMPORTANTES:
echo ==================================================
echo.
echo - O sistema salva seus tokens de login por 24 horas
echo - Apos 24h, sera necessario fazer login novamente
echo - O Chrome precisa estar instalado
echo - Voce recebera emails sobre alteracoes nas audiencias
echo.
echo ==================================================
echo   SUPORTE:
echo ==================================================
echo.
echo escritorio.macedoadvocacia@gmail.com
echo.
) > "%USERPROFILE%\Desktop\COMO USAR - Sistema de Audiencias.txt"

echo.
echo ===============================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo ===============================================
echo.
echo O sistema foi instalado em:
echo %INSTALL_DIR%
echo.
echo Atalhos criados em:
echo - Area de Trabalho
echo - Menu Iniciar
echo.
echo Arquivo de instrucoes criado na Area de Trabalho.
echo.
echo Pressione qualquer tecla para fechar...
pause > nul
