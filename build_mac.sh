#!/bin/bash
# ============================================
# SCRIPT DE BUILD PARA MAC/LINUX
# ============================================
# Este script cria um executável do sistema para Mac/Linux
# 
# COMO USAR:
# 1. Abra o Terminal nesta pasta
# 2. Execute: chmod +x build_mac.sh
# 3. Execute: ./build_mac.sh
# 4. O executável ficará na pasta dist/

echo ""
echo "============================================"
echo "  BUILD DO SISTEMA DE AUDIÊNCIAS - MAC/LINUX"
echo "============================================"
echo ""

# Detecta o sistema operacional
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_NAME="Mac"
else
    OS_NAME="Linux"
fi

echo "🖥️  Sistema detectado: $OS_NAME"
echo ""

# Verifica se está no ambiente virtual
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Ativando ambiente virtual..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "❌ Ambiente virtual não encontrado!"
        echo "   Execute: python3 -m venv .venv"
        exit 1
    fi
fi

# Verifica se PyInstaller está instalado
echo "📦 Verificando PyInstaller..."
if ! pip list | grep -q "pyinstaller"; then
    echo "⚠️  Instalando PyInstaller..."
    pip install pyinstaller==6.3.0
fi

# Limpa builds anteriores
echo ""
echo "🧹 Limpando builds anteriores..."
rm -rf build
rm -rf dist

# Cria o executável
echo ""
echo "🔨 Criando executável..."
echo "   Isso pode levar alguns minutos..."
echo ""

pyinstaller build.spec --clean

# Verifica se foi criado com sucesso
if [ -f "dist/SistemaAudiencias" ]; then
    echo ""
    echo "============================================"
    echo "  ✅ BUILD CONCLUÍDO COM SUCESSO!"
    echo "============================================"
    echo ""
    echo "📁 Executável criado em:"
    echo "   dist/SistemaAudiencias"
    echo ""
    echo "📋 IMPORTANTE - Antes de distribuir:"
    echo "   1. Copie o arquivo .env.example para a pasta dist/"
    echo "   2. O usuário deve criar um .env a partir dele"
    echo "   3. O usuário deve ter o Chrome instalado"
    echo "   4. O arquivo de credenciais Google deve estar na mesma pasta"
    echo ""
    
    # Copia arquivos necessários
    echo "📦 Copiando arquivos necessários..."
    cp .env.example dist/
    cp README.md dist/
    cp QUICKSTART.md dist/
    
    # Torna o executável... executável
    chmod +x dist/SistemaAudiencias
    
    # Cria pasta de distribuição
    DIST_FOLDER="SistemaAudiencias_${OS_NAME}_v2.0"
    rm -rf "$DIST_FOLDER"
    mkdir -p "$DIST_FOLDER"
    
    cp dist/SistemaAudiencias "$DIST_FOLDER"/
    cp .env.example "$DIST_FOLDER"/
    cp README.md "$DIST_FOLDER"/
    cp QUICKSTART.md "$DIST_FOLDER"/
    
    # Cria script de execução
    cat > "$DIST_FOLDER/executar.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./SistemaAudiencias
EOF
    chmod +x "$DIST_FOLDER/executar.sh"
    
    echo ""
    echo "📦 Pasta de distribuição criada:"
    echo "   $DIST_FOLDER/"
    echo ""
    echo "🎉 Pronto para uso!"
    echo ""
    echo "💡 Para executar:"
    echo "   cd $DIST_FOLDER"
    echo "   ./executar.sh"
    echo ""
    
else
    echo ""
    echo "============================================"
    echo "  ❌ ERRO NO BUILD"
    echo "============================================"
    echo ""
    echo "Verifique os erros acima e tente novamente."
    echo ""
fi
