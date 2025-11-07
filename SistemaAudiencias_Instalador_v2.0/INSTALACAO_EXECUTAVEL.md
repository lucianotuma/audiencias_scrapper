# 📦 Sistema de Audiências - Instalação Rápida

## 🎯 O Que Você Precisa

### Obrigatório
1. ✅ **Google Chrome** instalado ([Download](https://www.google.com/chrome/))
2. ✅ **Credenciais de acesso** aos tribunais (CPF e senha)
3. ✅ **Conta de email Gmail** para notificações
4. ✅ **Arquivo de credenciais Google** (`.json`) - fornecido pela empresa

### Opcional
- Acesso ao PaperTrail (para logs remotos)

---

## 🚀 Instalação (5 minutos)

### Passo 1: Extrair os Arquivos

Extraia o arquivo .zip para uma pasta de sua escolha, por exemplo:
- Windows: `C:\SistemaAudiencias\`
- Mac: `/Applications/SistemaAudiencias/`

### Passo 2: Configurar Credenciais

1. **Copie** o arquivo `.env.example` e **renomeie** para `.env`

2. **Abra** o arquivo `.env` com um editor de texto (Bloco de Notas, TextEdit, etc.)

3. **Preencha** suas credenciais:

```env
# Suas credenciais dos tribunais
TRT_USERNAME=seu_cpf_aqui
TRT_PASSWORD=sua_senha_aqui

# Seu email Gmail
EMAIL_SENDER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_aplicativo_do_gmail

# Quem receberá as notificações
EMAIL_RECIPIENTS=email1@exemplo.com, email2@exemplo.com
```

4. **Salve** o arquivo

### Passo 3: Adicionar Credenciais Google

Coloque o arquivo `.json` de credenciais Google na mesma pasta do executável.

**O nome do arquivo deve ser exatamente:**
- `planilha-de-audiencias-25b5ec50e72f.json`

Ou ajuste o caminho no `.env`:
```env
GOOGLE_SERVICE_ACCOUNT_FILE=./seu-arquivo.json
```

---

## ▶️ Primeira Execução

### Windows

1. **Dê duplo clique** em `SistemaAudiencias.exe`
2. Uma janela preta (console) aparecerá com logs
3. O Chrome abrirá automaticamente

### Mac

1. **Abra o Terminal** na pasta do executável
2. Execute: `./executar.sh`
3. O Chrome abrirá automaticamente

---

## 🔐 Login com 2FA

Quando o Chrome abrir:

### 1️⃣ TRT2
```
================================================================================
🔐 AUTENTICAÇÃO INTERATIVA NECESSÁRIA
================================================================================
📌 Tribunal: TRT2
```

- **Faça login** no site manualmente
- **Complete o 2FA** (SMS, app, etc.)
- **Aguarde** - O sistema detecta quando terminar
- O Chrome fechará automaticamente

### 2️⃣ TRT15
O processo se repete para o TRT15

### ✅ Pronto!
Após ambos os logins, o sistema:
- Coleta audiências automaticamente
- Atualiza planilhas Google
- Atualiza calendário
- Envia notificações se houver alterações

⏱️ **Duração total**: 5-10 minutos (primeira vez)

---

## 🔄 Execuções Seguintes

Nas próximas **24 horas**, o sistema:
- ✅ Usa os tokens salvos
- ✅ NÃO pede login novamente
- ✅ Execução totalmente automática

Após 24h, os tokens expiram e você precisará fazer login novamente.

---

## 📧 Senha de Aplicativo do Gmail

O Gmail exige uma "senha de aplicativo" específica:

1. Acesse: https://myaccount.google.com/security
2. Ative a **verificação em duas etapas**
3. Vá em **Senhas de app**
4. Crie uma senha para "Sistema de Audiências"
5. Use essa senha no `.env`

⚠️ **Não use sua senha normal do Gmail!**

---

## 📅 Agendar Execução Automática

### Windows - Agendador de Tarefas

1. Abra **Agendador de Tarefas**
2. **Criar Tarefa Básica**
3. Nome: "Sistema de Audiências"
4. Gatilho: Diariamente às 08:00
5. Ação: Iniciar programa
   - Programa: `C:\SistemaAudiencias\SistemaAudiencias.exe`
6. Concluir

### Mac - Cron

```bash
# Edite o crontab
crontab -e

# Adicione (executa às 08:00 diariamente)
0 8 * * * /Applications/SistemaAudiencias/executar.sh
```

---

## 📝 Verificar Logs

### Windows
Os logs ficam em:
```
C:\SistemaAudiencias\logs\audiencias.log
```

### Mac/Linux
```
/Applications/SistemaAudiencias/logs/audiencias.log
```

Para ver em tempo real (Windows PowerShell):
```powershell
Get-Content logs\audiencias.log -Wait
```

---

## 🆘 Problemas Comuns

### ❌ "Variáveis de ambiente ausentes"
**Causa**: Arquivo `.env` não existe ou está mal preenchido  
**Solução**: Verifique se criou o `.env` e preencheu todos os campos

### ❌ "Chrome não abre"
**Causa**: Chrome não está instalado  
**Solução**: Instale o Google Chrome

### ❌ "Erro ao acessar planilha"
**Causa**: Arquivo de credenciais Google ausente ou inválido  
**Solução**: Verifique se o arquivo `.json` está na pasta correta

### ❌ "Timeout no login"
**Causa**: Demorou mais de 5 minutos para fazer login  
**Solução**: Execute novamente e faça o login mais rápido

### ❌ "Tokens expirados"
**Causa**: Passaram mais de 24h desde o último login  
**Solução**: Normal! Apenas faça login novamente

---

## 🔒 Segurança

- ✅ **NUNCA** compartilhe seu arquivo `.env`
- ✅ **NUNCA** compartilhe o arquivo `.json` de credenciais
- ✅ Use senhas fortes
- ✅ Mantenha o 2FA ativado
- ✅ Não execute em computadores públicos

---

## 📞 Suporte

Se precisar de ajuda:

1. **Consulte os logs** em `logs/audiencias.log`
2. **Leia o README.md** completo
3. **Entre em contato** com o suporte técnico

---

## ✅ Checklist de Instalação

Antes de executar, confirme:

- [ ] Chrome instalado
- [ ] Arquivo `.env` criado e preenchido
- [ ] Arquivo `.json` de credenciais na pasta
- [ ] Credenciais dos tribunais corretas
- [ ] Senha de aplicativo do Gmail configurada
- [ ] Emails de destinatários configurados

---

**🎉 Pronto! Você está preparado para usar o sistema!**

**▶️ Execute agora e acompanhe os logs na tela.**
