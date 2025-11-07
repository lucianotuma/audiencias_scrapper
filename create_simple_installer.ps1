# ============================================
# CRIADOR DE INSTALADOR SIMPLES (SEM INNO SETUP)
# ============================================
# Cria um instalador usando apenas PowerShell
# Resultado: SistemaAudiencias_Setup_v2.0.zip

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "CRIADOR DE INSTALADOR WINDOWS" -ForegroundColor Cyan
Write-Host "Sistema de Audiencias v2.0" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Criar pasta de instalador
$installerFolder = "SistemaAudiencias_Instalador_v2.0"
if (Test-Path $installerFolder) {
    Write-Host "Removendo instalador anterior..." -ForegroundColor Yellow
    Remove-Item $installerFolder -Recurse -Force
}

Write-Host "Criando estrutura do instalador..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $installerFolder | Out-Null

# Copiar todos os arquivos necessarios
Write-Host "Copiando arquivos..." -ForegroundColor Cyan

$filesToCopy = @(
    @{Source="SistemaAudiencias_Windows_v2.0\SistemaAudiencias.exe"; Dest="$installerFolder\SistemaAudiencias.exe"},
    @{Source="SistemaAudiencias_Windows_v2.0\.env"; Dest="$installerFolder\.env"},
    @{Source="SistemaAudiencias_Windows_v2.0\planilha-de-audiencias-25b5ec50e72f.json"; Dest="$installerFolder\planilha-de-audiencias-25b5ec50e72f.json"},
    @{Source="SistemaAudiencias_Windows_v2.0\Executar.bat"; Dest="$installerFolder\Executar.bat"},
    @{Source="SistemaAudiencias_Windows_v2.0\README.md"; Dest="$installerFolder\README.md"},
    @{Source="SistemaAudiencias_Windows_v2.0\QUICKSTART.md"; Dest="$installerFolder\QUICKSTART.md"},
    @{Source="SistemaAudiencias_Windows_v2.0\LEIA-ME.txt"; Dest="$installerFolder\LEIA-ME.txt"},
    @{Source="SistemaAudiencias_Windows_v2.0\INSTALACAO_EXECUTAVEL.md"; Dest="$installerFolder\INSTALACAO_EXECUTAVEL.md"}
)

foreach ($file in $filesToCopy) {
    if (Test-Path $file.Source) {
        Copy-Item $file.Source -Destination $file.Dest -Force
        Write-Host "  Copiado: $($file.Source)" -ForegroundColor Green
    } else {
        Write-Host "  AVISO: Arquivo nao encontrado: $($file.Source)" -ForegroundColor Yellow
    }
}

# Copiar pasta de logs
if (Test-Path "SistemaAudiencias_Windows_v2.0\logs") {
    Copy-Item "SistemaAudiencias_Windows_v2.0\logs" -Destination "$installerFolder\logs" -Recurse -Force
    Write-Host "  Copiado: logs/" -ForegroundColor Green
} else {
    New-Item -ItemType Directory -Path "$installerFolder\logs" | Out-Null
    Write-Host "  Criado: logs/" -ForegroundColor Green
}

# Criar script de instalacao automatica
$installScript = @'
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
'@

$installScript | Out-File -FilePath "$installerFolder\INSTALAR.bat" -Encoding ASCII -Force
Write-Host "  Criado: INSTALAR.bat" -ForegroundColor Green

# Criar arquivo de instrucoes
$instructionsContent = @"
==================================================
  INSTALADOR - SISTEMA DE AUDIENCIAS v2.0
==================================================

IMPORTANTE: Este instalador contem TUDO pre-configurado!
- Executavel
- Credenciais do TRT
- Credenciais do Google
- Configuracoes de email
- Documentacao

==================================================
  COMO INSTALAR:
==================================================

OPCAO 1 - INSTALACAO AUTOMATICA (RECOMENDADO):

1. De duplo clique no arquivo "INSTALAR.bat"
2. Clique em "Sim" se aparecer aviso de seguranca
3. Pressione qualquer tecla para confirmar
4. Aguarde a instalacao
5. Pronto! Use o atalho na Area de Trabalho

OPCAO 2 - INSTALACAO MANUAL:

1. Copie toda esta pasta para:
   C:\Program Files\Sistema de Audiencias\

2. Crie um atalho do arquivo "Executar.bat"
   na sua Area de Trabalho

3. Pronto!

==================================================
  REQUISITOS:
==================================================

- Windows 10 ou 11 (64-bit)
- Google Chrome instalado
- Conexao com internet

==================================================
  COMO USAR:
==================================================

1. De duplo clique no atalho "Sistema de Audiencias"
2. O Chrome ira abrir
3. Faca login manualmente nos sites do TRT
4. Complete o segundo fator de autenticacao (2FA)
5. O sistema coleta tudo automaticamente

Os tokens ficam salvos por 24 horas.

==================================================
  SUPORTE:
==================================================

escritorio.macedoadvocacia@gmail.com

==================================================
  SEGURANCA:
==================================================

ATENCAO: Este instalador contem credenciais sensiveis!
- Nao compartilhe com pessoas nao autorizadas
- Mantenha em local seguro
- Delete apos a instalacao

==================================================
"@

$instructionsContent | Out-File -FilePath "$installerFolder\LEIA-ME PRIMEIRO.txt" -Encoding UTF8 -Force
Write-Host "  Criado: LEIA-ME PRIMEIRO.txt" -ForegroundColor Green

Write-Host ""
Write-Host "Criando arquivo ZIP..." -ForegroundColor Cyan

# Criar arquivo ZIP
$zipPath = "SistemaAudiencias_Instalador_v2.0.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path "$installerFolder\*" -DestinationPath $zipPath -CompressionLevel Optimal

$zipSize = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)

Write-Host ""
Write-Host "=======================================" -ForegroundColor Green
Write-Host "INSTALADOR CRIADO COM SUCESSO!" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Arquivo: $zipPath" -ForegroundColor White
Write-Host "Tamanho: $zipSize MB" -ForegroundColor White
Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "COMO DISTRIBUIR:" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Envie o arquivo ZIP para o usuario" -ForegroundColor White
Write-Host "2. Usuario extrai o ZIP" -ForegroundColor White
Write-Host "3. Usuario executa INSTALAR.bat" -ForegroundColor White
Write-Host "4. Pronto!" -ForegroundColor White
Write-Host ""
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "O QUE ESTA INCLUIDO:" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "- Executavel (60 MB)" -ForegroundColor Green
Write-Host "- Credenciais pre-configuradas" -ForegroundColor Green
Write-Host "- Script de instalacao automatica" -ForegroundColor Green
Write-Host "- Documentacao completa" -ForegroundColor Green
Write-Host "- Criacao automatica de atalhos" -ForegroundColor Green
Write-Host ""
Write-Host "Pressione qualquer tecla para abrir a pasta..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Abrir pasta atual
Invoke-Item .
