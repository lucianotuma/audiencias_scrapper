# Script de compilacao do instalador Windows
# Sistema de Audiencias v2.0

Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "COMPILADOR DE INSTALADOR WINDOWS" -ForegroundColor Cyan
Write-Host "Sistema de Audiencias v2.0" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Inno Setup esta instalado
$InnoSetupPaths = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 5\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 5\ISCC.exe"
)

$InnoSetupExe = $null
foreach ($path in $InnoSetupPaths) {
    if (Test-Path $path) {
        $InnoSetupExe = $path
        break
    }
}

if (-not $InnoSetupExe) {
    Write-Host "ERRO: Inno Setup nao encontrado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Para instalar o Inno Setup:" -ForegroundColor Yellow
    Write-Host "  1. Acesse: https://jrsoftware.org/isdl.php" -ForegroundColor White
    Write-Host "  2. Baixe: innosetup-6.x.x.exe" -ForegroundColor White
    Write-Host "  3. Instale com as opcoes padrao" -ForegroundColor White
    Write-Host "  4. Execute este script novamente" -ForegroundColor White
    Write-Host ""
    Write-Host "Pressione qualquer tecla para abrir a pagina de download..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Start-Process "https://jrsoftware.org/isdl.php"
    exit 1
}

Write-Host "Inno Setup encontrado: $InnoSetupExe" -ForegroundColor Green
Write-Host ""

# Verificar se o executavel existe
if (-not (Test-Path "SistemaAudiencias_Windows_v2.0\SistemaAudiencias.exe")) {
    Write-Host "ERRO: Executavel nao encontrado!" -ForegroundColor Red
    Write-Host "Execute build_windows.ps1 primeiro para criar o executavel." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "Executavel encontrado" -ForegroundColor Green
Write-Host ""

# Verificar se arquivos de configuracao existem
$requiredFiles = @(
    "SistemaAudiencias_Windows_v2.0\.env",
    "SistemaAudiencias_Windows_v2.0\planilha-de-audiencias-25b5ec50e72f.json",
    "SistemaAudiencias_Windows_v2.0\Executar.bat"
)

$allFilesExist = $true
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "ERRO: Arquivo nao encontrado: $file" -ForegroundColor Red
        $allFilesExist = $false
    } else {
        Write-Host "Arquivo encontrado: $file" -ForegroundColor Green
    }
}

if (-not $allFilesExist) {
    Write-Host ""
    Write-Host "Alguns arquivos necessarios nao foram encontrados." -ForegroundColor Red
    Write-Host "Certifique-se de que todos os arquivos estao na pasta SistemaAudiencias_Windows_v2.0/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host ""
Write-Host "Compilando instalador..." -ForegroundColor Cyan
Write-Host ""

# Criar diretorio de saida se nao existir
if (-not (Test-Path "installer_output")) {
    New-Item -ItemType Directory -Path "installer_output" | Out-Null
}

# Compilar o instalador
try {
    & $InnoSetupExe "installer.iss"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=======================================" -ForegroundColor Green
        Write-Host "INSTALADOR CRIADO COM SUCESSO!" -ForegroundColor Green
        Write-Host "=======================================" -ForegroundColor Green
        Write-Host ""
        
        $installerPath = "installer_output\SistemaAudiencias_Setup_v2.0.exe"
        if (Test-Path $installerPath) {
            $fileInfo = Get-Item $installerPath
            $fileSize = [math]::Round($fileInfo.Length / 1MB, 2)
            
            Write-Host "Arquivo: $installerPath" -ForegroundColor White
            Write-Host "Tamanho: $fileSize MB" -ForegroundColor White
            Write-Host ""
            Write-Host "=======================================" -ForegroundColor Cyan
            Write-Host "COMO USAR O INSTALADOR:" -ForegroundColor Cyan
            Write-Host "=======================================" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "1. Copie o arquivo para outro computador" -ForegroundColor White
            Write-Host "2. De duplo clique no instalador" -ForegroundColor White
            Write-Host "3. Clique em Avancar -> Avancar -> Instalar" -ForegroundColor White
            Write-Host "4. Use o atalho na Area de Trabalho" -ForegroundColor White
            Write-Host ""
            Write-Host "=======================================" -ForegroundColor Cyan
            Write-Host "O QUE ESTA INCLUIDO:" -ForegroundColor Cyan
            Write-Host "=======================================" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "- Executavel (60 MB)" -ForegroundColor Green
            Write-Host "- Configuracoes (.env com credenciais)" -ForegroundColor Green
            Write-Host "- Credenciais Google (JSON)" -ForegroundColor Green
            Write-Host "- Script de execucao (UTF-8)" -ForegroundColor Green
            Write-Host "- Documentacao completa" -ForegroundColor Green
            Write-Host "- Atalhos automaticos" -ForegroundColor Green
            Write-Host ""
            Write-Host "=======================================" -ForegroundColor Yellow
            Write-Host "REQUISITO DO USUARIO FINAL:" -ForegroundColor Yellow
            Write-Host "=======================================" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Apenas Google Chrome precisa estar instalado" -ForegroundColor Yellow
            Write-Host "(o instalador avisa se nao estiver)" -ForegroundColor White
            Write-Host ""
            Write-Host "Pressione qualquer tecla para abrir a pasta do instalador..." -ForegroundColor Cyan
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            
            # Abrir pasta do instalador
            Invoke-Item "installer_output"
        }
    } else {
        Write-Host ""
        Write-Host "ERRO: Falha ao compilar o instalador" -ForegroundColor Red
        Write-Host "Codigo de saida: $LASTEXITCODE" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "ERRO CRITICO: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}
