# ============================================
# SCRIPT DE BUILD PARA WINDOWS
# ============================================
# Este script cria um executável do sistema para Windows
# 
# COMO USAR:
# 1. Abra o PowerShell nesta pasta
# 2. Execute: .\build_windows.ps1
# 3. O executável ficará na pasta dist\

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  BUILD DO SISTEMA DE AUDIÊNCIAS - WINDOWS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verifica se está no ambiente virtual
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Ativando ambiente virtual..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
}

# Verifica se PyInstaller está instalado
Write-Host "📦 Verificando PyInstaller..." -ForegroundColor Green
$pyinstaller = pip list | Select-String "pyinstaller"
if (-not $pyinstaller) {
    Write-Host "⚠️  Instalando PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller==6.3.0
}

# Limpa builds anteriores
Write-Host ""
Write-Host "🧹 Limpando builds anteriores..." -ForegroundColor Green
if (Test-Path "build") {
    Remove-Item -Recurse -Force build
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force dist
}

# Cria o executável
Write-Host ""
Write-Host "🔨 Criando executável..." -ForegroundColor Green
Write-Host "   Isso pode levar alguns minutos..." -ForegroundColor Yellow
Write-Host ""

pyinstaller build.spec --clean

# Verifica se foi criado com sucesso
if (Test-Path "dist\SistemaAudiencias.exe") {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  ✅ BUILD CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📁 Executável criado em:" -ForegroundColor Cyan
    Write-Host "   dist\SistemaAudiencias.exe" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 IMPORTANTE - Antes de distribuir:" -ForegroundColor Yellow
    Write-Host "   1. Copie o arquivo .env.example para a pasta dist\" -ForegroundColor White
    Write-Host "   2. O usuário deve criar um .env a partir dele" -ForegroundColor White
    Write-Host "   3. O usuário deve ter o Chrome instalado" -ForegroundColor White
    Write-Host "   4. O arquivo de credenciais Google deve estar na mesma pasta" -ForegroundColor White
    Write-Host ""
    
    # Copia arquivos necessários
    Write-Host "📦 Copiando arquivos necessários..." -ForegroundColor Green
    Copy-Item .env.example dist\
    Copy-Item README.md dist\
    Copy-Item QUICKSTART.md dist\
    
    # Cria pasta de distribuição
    $distFolder = "SistemaAudiencias_Windows_v2.0"
    if (Test-Path $distFolder) {
        Remove-Item -Recurse -Force $distFolder
    }
    New-Item -ItemType Directory -Path $distFolder | Out-Null
    
    Copy-Item dist\SistemaAudiencias.exe $distFolder\
    Copy-Item .env.example $distFolder\
    Copy-Item README.md $distFolder\
    Copy-Item QUICKSTART.md $distFolder\
    
    Write-Host ""
    Write-Host "📦 Pasta de distribuição criada:" -ForegroundColor Cyan
    Write-Host "   $distFolder\" -ForegroundColor White
    Write-Host ""
    Write-Host "🎉 Pronto para uso!" -ForegroundColor Green
    Write-Host ""
    
} else {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "  ❌ ERRO NO BUILD" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Verifique os erros acima e tente novamente." -ForegroundColor Yellow
    Write-Host ""
}
