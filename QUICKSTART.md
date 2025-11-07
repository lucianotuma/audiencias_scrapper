# 🚀 Guia Rápido de Início

## Passo 1: Instalar Dependências

```powershell
cd C:\Users\lucia\OneDrive\Desktop\audiencias
pip install -r requirements.txt
```

## Passo 2: Configurar Credenciais

1. Copie o arquivo `.env.example` para `.env`:

```powershell
Copy-Item .env.example .env
```

2. Edite o arquivo `.env` e preencha suas credenciais:

```powershell
notepad .env
```

**Campos obrigatórios:**

- `TRT_USERNAME` - Seu CPF
- `TRT_PASSWORD` - Sua senha dos tribunais
- `EMAIL_SENDER` - Seu email Gmail
- `EMAIL_PASSWORD` - Senha de aplicativo do Gmail
- `EMAIL_RECIPIENTS` - Emails que receberão notificações

## Passo 3: Executar pela Primeira Vez

```powershell
python scrapper_refactored.py
```

### O que vai acontecer:

1. ✅ Sistema valida as configurações
2. 🌐 Abre o Chrome automaticamente para **TRT2**
3. 👤 **VOCÊ FAZ**: Login manual + 2FA no navegador
4. ⏳ Sistema aguarda você terminar o login
5. 💾 Tokens são salvos automaticamente
6. 🌐 Abre o Chrome para **TRT15**
7. 👤 **VOCÊ FAZ**: Login manual + 2FA novamente
8. 💾 Tokens do TRT15 salvos
9. 📊 Sistema coleta audiências automaticamente
10. 📝 Atualiza planilhas e calendário
11. ✅ Pronto!

## Próximas Execuções

Nas próximas 24 horas, o sistema **não pedirá login novamente**!

Os tokens salvos serão reutilizados automaticamente.

## Troubleshooting Rápido

### ❌ Erro: "Variáveis de ambiente ausentes"

**Solução:** Verifique se criou o arquivo `.env` e preencheu todos os campos obrigatórios.

### ❌ Tempo esgotado no login

**Solução:** Você tem 5 minutos. Se precisar de mais tempo, feche e execute novamente.

### ❌ Chrome não abre

**Solução:** Certifique-se de que o Google Chrome está instalado.

### ❌ Erro de credenciais Google

**Solução:** Verifique se o arquivo `planilha-de-audiencias-25b5ec50e72f.json` existe no diretório.

## Ver Logs

```powershell
# Ver log completo
notepad logs\audiencias.log

# Ver últimas linhas
Get-Content logs\audiencias.log -Tail 30
```

## Limpar Cache de Tokens (Forçar Novo Login)

```powershell
Remove-Item session_tokens.json
```

## Testar Notificações de Email

O sistema enviará um email ao final de cada execução se houver alterações ou erros.

Para testar manualmente, você pode adicionar um teste no código ou verificar os logs.

---

**📚 Para mais detalhes, consulte o README.md completo**
