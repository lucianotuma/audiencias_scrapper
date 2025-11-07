# 🚀 Guia de Criação de Executáveis

Este guia explica como criar executáveis do Sistema de Audiências para Windows e Mac.

---

## 📦 Para Windows

### Pré-requisitos

- Python 3.8+ instalado
- Ambiente virtual configurado
- Todas as dependências instaladas

### Passos

1. **Abra o PowerShell** na pasta do projeto

2. **Execute o script de build**:

   ```powershell
   .\build_windows.ps1
   ```

3. **Aguarde o processo** (pode levar 2-5 minutos)

4. **Resultado**:
   - Executável criado em: `dist\SistemaAudiencias.exe`
   - Pasta de distribuição: `SistemaAudiencias_Windows_v2.0\`

### O que é incluído:

- ✅ `SistemaAudiencias.exe` - Executável principal
- ✅ `.env.example` - Template de configuração
- ✅ `README.md` - Documentação completa
- ✅ `QUICKSTART.md` - Guia rápido

### Para distribuir:

1. Compacte a pasta `SistemaAudiencias_Windows_v2.0` em um arquivo .zip
2. Envie para os usuários
3. Usuário deve:
   - Extrair o .zip
   - Copiar `.env.example` para `.env`
   - Preencher o `.env` com suas credenciais
   - Adicionar o arquivo de credenciais Google (`.json`)
   - Executar `SistemaAudiencias.exe`

---

## 🍎 Para Mac

### Pré-requisitos

- Python 3.8+ instalado
- Ambiente virtual configurado
- Todas as dependências instaladas

### Passos

1. **Abra o Terminal** na pasta do projeto

2. **Dê permissão de execução ao script**:

   ```bash
   chmod +x build_mac.sh
   ```

3. **Execute o script de build**:

   ```bash
   ./build_mac.sh
   ```

4. **Aguarde o processo** (pode levar 2-5 minutos)

5. **Resultado**:
   - Executável criado em: `dist/SistemaAudiencias`
   - Pasta de distribuição: `SistemaAudiencias_Mac_v2.0/`

### O que é incluído:

- ✅ `SistemaAudiencias` - Executável principal
- ✅ `executar.sh` - Script facilitador de execução
- ✅ `.env.example` - Template de configuração
- ✅ `README.md` - Documentação completa
- ✅ `QUICKSTART.md` - Guia rápido

### Para distribuir:

1. Compacte a pasta `SistemaAudiencias_Mac_v2.0` em um arquivo .zip
2. Envie para os usuários
3. Usuário deve:
   - Extrair o .zip
   - Abrir o Terminal na pasta extraída
   - Copiar `.env.example` para `.env`
   - Preencher o `.env` com suas credenciais
   - Adicionar o arquivo de credenciais Google (`.json`)
   - Executar: `./executar.sh`

---

## 🐧 Para Linux

Use o mesmo processo do Mac (`build_mac.sh`). O script detecta automaticamente o sistema.

---

## ⚙️ Build Manual (Avançado)

Se preferir fazer o build manualmente:

```bash
# Ative o ambiente virtual
source .venv/bin/activate  # Mac/Linux
.\.venv\Scripts\Activate.ps1  # Windows

# Execute o PyInstaller
pyinstaller build.spec --clean

# O executável estará em dist/
```

---

## 📝 Personalização

### Adicionar Ícone

Edite `build.spec` e altere a linha:

```python
icon=None,  # Coloque o caminho para um .ico (Windows) ou .icns (Mac)
```

Para:

```python
icon='icone.ico',  # Windows
# ou
icon='icone.icns',  # Mac
```

### Reduzir Tamanho do Executável

No `build.spec`, adicione mais bibliotecas em `excludes`:

```python
excludes=[
    'matplotlib',
    'tkinter',
    'PyQt5',
    'PyQt6',
    'jupyter',
    'notebook',
    'IPython',
    'scipy',
    'PIL',
    # ... outras que não são usadas
],
```

### Modo Sem Console (Windows)

No `build.spec`, altere:

```python
console=True,  # Mude para False para esconder o console
```

⚠️ **Aviso**: Sem console, você não verá os logs na tela!

---

## 🔍 Solução de Problemas

### "Módulo não encontrado"

**Solução**: Adicione o módulo em `hiddenimports` no `build.spec`

### "Executável muito grande"

**Solução**: Use UPX para compressão (já habilitado no spec)

### "Erro ao executar"

**Solução**: Execute com console habilitado para ver erros

### "Antivírus bloqueia"

**Solução**: Normal com executáveis Python. Adicione exceção ou assine digitalmente.

---

## 📊 Tamanho Esperado

- **Windows**: ~80-120 MB
- **Mac**: ~70-100 MB
- **Linux**: ~70-100 MB

Inclui Python + todas as bibliotecas + ChromeDriver

---

## 🎯 Checklist de Distribuição

Antes de enviar para usuários, verifique:

- [ ] Executável funciona na sua máquina
- [ ] Testou em uma máquina limpa (sem Python instalado)
- [ ] Incluiu `.env.example`
- [ ] Incluiu documentação (README.md)
- [ ] Instruções sobre arquivo de credenciais Google
- [ ] Informou sobre necessidade do Chrome
- [ ] Criou .zip ou instalador

---

## 📧 Suporte

Para problemas no build, consulte:

- [PyInstaller Docs](https://pyinstaller.org/en/stable/)
- Logs do build em `build/`
- Arquivo de spec: `build.spec`

---

**🎉 Boa sorte com a distribuição!**
