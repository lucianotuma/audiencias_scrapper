# 📦 GUIA DE CRIAÇÃO DO INSTALADOR WINDOWS

## 🎯 Objetivo

Criar um instalador `.exe` profissional para Windows que inclui **TUDO** pré-configurado:

- ✅ Executável do sistema
- ✅ Arquivo `.env` com credenciais
- ✅ Arquivo JSON do Google
- ✅ Documentação
- ✅ Atalhos automáticos

## 📋 Pré-requisitos

### 1. Inno Setup (Gratuito)

**Download:** https://jrsoftware.org/isdl.php

**Instalação:**

1. Baixe `innosetup-6.x.x.exe`
2. Execute e siga o assistente
3. Aceite todas as opções padrão
4. Pronto! O Inno Setup estará instalado

**Tamanho:** ~5 MB  
**Tempo:** 1-2 minutos

---

## 🚀 Como Criar o Instalador

### Opção 1: Script Automático (RECOMENDADO)

```powershell
.\build_installer.ps1
```

**O que o script faz:**

1. ✅ Verifica se Inno Setup está instalado
2. ✅ Verifica se todos os arquivos necessários existem
3. ✅ Compila o instalador automaticamente
4. ✅ Abre a pasta com o instalador pronto

**Resultado:** `installer_output/SistemaAudiencias_Setup_v2.0.exe`

### Opção 2: Manual

1. Abra o Inno Setup Compiler
2. Abra o arquivo `installer.iss`
3. Clique em "Build" → "Compile"
4. Pronto!

---

## 📦 O que está incluído no instalador

| Item                                         | Descrição                                      |
| -------------------------------------------- | ---------------------------------------------- |
| **SistemaAudiencias.exe**                    | Executável principal (60 MB)                   |
| **.env**                                     | Configurações com credenciais pré-configuradas |
| **planilha-de-audiencias-25b5ec50e72f.json** | Credenciais do Google                          |
| **Executar.bat**                             | Script que garante UTF-8 no console            |
| **Documentação**                             | README, QUICKSTART, LEIA-ME.txt                |
| **logs/**                                    | Diretório para arquivos de log                 |

---

## 🎨 Características do Instalador

### Interface Moderna

- ✅ Interface gráfica moderna do Windows
- ✅ Texto em português brasileiro
- ✅ Logo e ícones personalizados
- ✅ Mensagens claras e diretas

### Instalação Inteligente

- ✅ Verifica se Chrome está instalado (avisa se não estiver)
- ✅ Cria atalhos automáticos (Desktop + Menu Iniciar)
- ✅ Cria arquivo de instruções na área de trabalho
- ✅ Opção de executar após instalação

### Sem Complicações

- ✅ Apenas 3 cliques: Avançar → Avançar → Instalar
- ✅ Todas as configurações já pré-definidas
- ✅ Não pede informações ao usuário
- ✅ **Paradigma: "Não me faça pensar"**

---

## 👥 Para o Usuário Final

### Requisitos

- ⚠️ **Google Chrome** (o instalador avisa se não tiver)
- ✅ Windows 10/11 (64-bit)
- ✅ Nada mais!

### Como Instalar (para usuário leigo)

1. Dê **duplo clique** no instalador
2. Clique em **"Avançar"**
3. Clique em **"Avançar"** novamente
4. Clique em **"Instalar"**
5. Pronto! ✅

### Como Usar

1. Dê **duplo clique** no atalho **"Sistema de Audiências"** na Área de Trabalho
2. O Chrome vai abrir sozinho
3. Faça login **manualmente** nos sites do TRT2 e TRT15
4. Pronto! O sistema coleta tudo automaticamente

---

## 🔧 Personalizações Possíveis

### Ícone Personalizado

No arquivo `installer.iss`, adicione:

```ini
SetupIconFile=icone.ico
```

### Imagem de Fundo

No arquivo `installer.iss`, modifique:

```ini
WizardImageFile=minha_imagem.bmp  ; 164x314 pixels
WizardSmallImageFile=minha_imagem_pequena.bmp  ; 55x58 pixels
```

### Texto de Boas-Vindas

No arquivo `installer.iss`, seção `[Code]`, função `InitializeWizard()`:

```pascal
WizardForm.WelcomeLabel2.Caption := 'Seu texto personalizado aqui';
```

---

## 📊 Tamanho do Instalador

- **Executável compactado:** ~60 MB
- **Após instalação:** ~62 MB
- **Compressão:** LZMA2 (máxima)

---

## 🗑️ Desinstalação

O instalador cria automaticamente:

- ✅ Entrada no Painel de Controle → Programas
- ✅ Atalho no Menu Iniciar → Desinstalar
- ✅ Remove todos os arquivos ao desinstalar
- ✅ Limpa arquivos temporários (logs, tokens)

---

## ⚠️ Segurança

### ⚠️ IMPORTANTE: Credenciais Incluídas

O instalador contém:

- ❗ Usuário e senha do TRT (no arquivo `.env`)
- ❗ Credenciais da conta Google (no arquivo JSON)
- ❗ Senha de email (no arquivo `.env`)

**Recomendações:**

1. ✅ Compartilhe apenas com pessoas autorizadas
2. ✅ Use canal seguro para enviar (não por email comum)
3. ✅ Considere usar senha no instalador (opção abaixo)

### Como Adicionar Senha ao Instalador

No arquivo `installer.iss`, seção `[Setup]`, adicione:

```ini
Password=SuaSenhaAqui123
```

**Resultado:** O usuário precisará digitar a senha para instalar.

---

## 📝 Logs e Troubleshooting

### Logs de Instalação

Localização: `%TEMP%\Setup Log YYYY-MM-DD #001.txt`

### Logs de Execução

Localização: `C:\Program Files\Sistema de Audiências\logs\`

### Problemas Comuns

| Problema                      | Solução                                           |
| ----------------------------- | ------------------------------------------------- |
| "Chrome não encontrado"       | Instalar Google Chrome                            |
| "Erro ao compilar instalador" | Reinstalar Inno Setup                             |
| "Arquivos não encontrados"    | Verificar pasta `SistemaAudiencias_Windows_v2.0/` |

---

## 🎁 Resultado Final

Você terá um instalador profissional que:

1. ✅ **Funciona em qualquer Windows 10/11**
2. ✅ **Instalação com 3 cliques**
3. ✅ **Tudo pré-configurado**
4. ✅ **Atalhos automáticos**
5. ✅ **Instruções incluídas**
6. ✅ **Desinstalação limpa**
7. ✅ **Interface moderna**
8. ✅ **Zero configuração do usuário**

**Paradigma "Não me faça pensar" ✅ IMPLEMENTADO COM SUCESSO!**

---

## 📞 Suporte

Em caso de dúvidas sobre o instalador:

- 📧 escritorio.macedoadvocacia@gmail.com
