# 🏛️ Sistema de Gerenciamento de Audiências

Sistema automatizado para escritórios de advocacia que monitora, sincroniza e notifica sobre audiências trabalhistas nos tribunais TRT2 e TRT15.

## ✨ Funcionalidades

- ✅ **Autenticação com 2FA**: Suporte completo para autenticação de dois fatores
- 📥 **Coleta Automatizada**: Extrai audiências dos sistemas PJe dos tribunais
- 📊 **Sincronização Google**: Atualiza automaticamente planilhas Google Sheets
- 📅 **Calendário Integrado**: Cria e gerencia eventos no Google Calendar
- 📧 **Notificações por Email**: Alerta sobre alterações e erros
- 💾 **Cache de Sessão**: Reutiliza tokens de autenticação (válidos por 24h)
- 🔄 **Retry Automático**: Reexecuta operações em caso de falhas temporárias
- 📝 **Logs Detalhados**: Múltiplos níveis de logging (console, arquivo, PaperTrail)

---

## 📋 Pré-requisitos

### Software Necessário

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Google Chrome** (última versão)
- **Conta Google** com acesso às APIs (Sheets, Calendar)

### Credenciais Necessárias

1. **Tribunais (TRT)**:

   - CPF de acesso aos sistemas PJe
   - Senha de acesso
   - Acesso ao segundo fator de autenticação (celular/app)

2. **Google Services**:

   - Arquivo JSON da conta de serviço do Google
   - IDs das planilhas Google Sheets
   - ID do calendário Google

3. **Email (Gmail)**:
   - Endereço de email remetente
   - Senha de aplicativo do Gmail ([Como criar](https://support.google.com/accounts/answer/185833))

---

## 🚀 Instalação

### 1. Clone ou Baixe o Projeto

```bash
cd C:\Users\lucia\OneDrive\Desktop\audiencias
```

### 2. Instale as Dependências

```powershell
# Recomendado: Use um ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instale as bibliotecas
pip install -r requirements.txt
```

### 3. Configure as Variáveis de Ambiente

```powershell
# Copie o template de configuração
Copy-Item .env.example .env

# Edite o arquivo .env com suas credenciais
notepad .env
```

**Preencha todas as variáveis no arquivo `.env`**:

```env
# Credenciais dos Tribunais
TRT_USERNAME=seu_cpf_aqui
TRT_PASSWORD=sua_senha_aqui

# Configuração de Email
EMAIL_SENDER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_aplicativo
EMAIL_RECIPIENTS=email1@exemplo.com, email2@exemplo.com

# Google Services (já configurados, ajuste se necessário)
GOOGLE_SERVICE_ACCOUNT_FILE=./planilha-de-audiencias-25b5ec50e72f.json
ACTUAL_HEARING_SPREADSHEET_ID=1RBUyyexHI3p_nRrD2u84MYoTrLaDddlm7MC838Cvk58
CHANGED_HEARING_SPREADSHEET_ID=1zIYf_0I8g_QgGe6HDy55j2DdhYIlYdYLyBLfSk8MVP4
CALENDAR_ID=c_aae930714cf9b78da155f0a509c1592da4d739c3ff76b758d860797e495661da@group.calendar.google.com

# Logging (opcional)
PAPERTRAIL_HOST=logs5.papertrailapp.com
PAPERTRAIL_PORT=54240
LOG_LEVEL=INFO
```

### 4. Verifique o Arquivo de Credenciais Google

Certifique-se de que o arquivo `planilha-de-audiencias-25b5ec50e72f.json` está no diretório do projeto.

---

## 🎯 Uso

### Execução Manual

```powershell
# Ative o ambiente virtual (se estiver usando)
.\venv\Scripts\Activate.ps1

# Execute o script refatorado (versão 2.0)
python scrapper_refactored.py
```

### Primeira Execução - Autenticação com 2FA

Na primeira execução (ou quando os tokens expirarem), o sistema abrirá o navegador Chrome automaticamente:

1. **Janela do Chrome será aberta** para cada tribunal (TRT2 e TRT15)
2. **Faça login manualmente**:
   - Insira seu CPF
   - Insira sua senha
   - Complete o segundo fator de autenticação (SMS, app, etc.)
3. **Aguarde** - O sistema detectará quando o login for concluído
4. **Tokens salvos** - Os cookies de sessão serão salvos em `session_tokens.json`

⏱️ **Tempo de espera**: O sistema aguarda até 5 minutos para você completar o login.

### Execuções Subsequentes

Após a primeira autenticação, o sistema **reutilizará os tokens salvos** por até **24 horas**, sem necessidade de novo login interativo.

---

## 📁 Estrutura de Arquivos

```
audiencias/
│
├── scrapper.py                              # ❌ Versão antiga (não usar)
├── scrapper_refactored.py                   # ✅ Versão 2.0 (usar esta)
├── requirements.txt                         # 📦 Dependências Python
├── .env                                     # 🔒 Configurações (NÃO COMPARTILHAR)
├── .env.example                             # 📄 Template de configuração
├── .gitignore                               # 🚫 Arquivos ignorados pelo git
├── README.md                                # 📖 Este arquivo
│
├── planilha-de-audiencias-*.json            # 🔑 Credenciais Google (NÃO COMPARTILHAR)
├── session_tokens.json                      # 💾 Cache de tokens (gerado automaticamente)
│
└── logs/                                    # 📝 Logs do sistema (gerado automaticamente)
    └── audiencias.log
```

---

## ⚙️ Configuração Avançada

### Ajustar Tempo de Expiração dos Tokens

No arquivo `.env`:

```env
TOKEN_EXPIRY_HOURS=24    # Padrão: 24 horas
```

### Alterar Nível de Log

No arquivo `.env`:

```env
LOG_LEVEL=DEBUG    # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Desabilitar PaperTrail

Se não quiser usar o PaperTrail, deixe os campos vazios no `.env`:

```env
PAPERTRAIL_HOST=
PAPERTRAIL_PORT=
```

---

## 🔧 Solução de Problemas

### Erro: "Variáveis de ambiente ausentes"

**Solução**: Verifique se o arquivo `.env` existe e está preenchido corretamente.

```powershell
# Verifique se o arquivo existe
Test-Path .env

# Edite o arquivo
notepad .env
```

### Erro: "Tempo esgotado aguardando login"

**Solução**: Você tem 5 minutos para completar o login. Se precisar de mais tempo, edite o código:

```python
# Em scrapper_refactored.py, linha ~771
trt2_success = self.trt2_session.login_interactive(
    'https://pje.trt2.jus.br/primeirograu/login.seam',
    timeout=600  # Aumentar para 10 minutos
)
```

### Erro: "ChromeDriver incompatível"

**Solução**: O sistema baixa automaticamente a versão correta. Se der erro:

```powershell
# Limpe o cache do WebDriver
Remove-Item -Recurse -Force $env:USERPROFILE\.wdm
```

### Erro: "Tokens em cache inválidos"

**Solução**: Remova o arquivo de cache para forçar novo login:

```powershell
Remove-Item session_tokens.json
```

### Erro de Permissão no Google Sheets/Calendar

**Solução**: Verifique se a conta de serviço tem permissão de edição nas planilhas e no calendário.

---

## 📅 Agendamento Automático

### Windows - Agendador de Tarefas

1. Abra o **Agendador de Tarefas** do Windows
2. Crie uma **Nova Tarefa**:
   - **Nome**: Sistema de Audiências
   - **Gatilho**: Diariamente às 08:00
   - **Ação**: Iniciar programa
     - **Programa**: `C:\Users\lucia\OneDrive\Desktop\audiencias\venv\Scripts\python.exe`
     - **Argumentos**: `scrapper_refactored.py`
     - **Iniciar em**: `C:\Users\lucia\OneDrive\Desktop\audiencias`

### Linux/macOS - Cron

```bash
# Edite o crontab
crontab -e

# Adicione a linha (executa às 08:00 todos os dias)
0 8 * * * cd /caminho/para/audiencias && /caminho/para/venv/bin/python scrapper_refactored.py >> /caminho/para/logs/cron.log 2>&1
```

---

## 🔒 Segurança

### ⚠️ IMPORTANTE - Proteção de Credenciais

- **NUNCA** compartilhe o arquivo `.env`
- **NUNCA** compartilhe o arquivo JSON de credenciais Google
- **NUNCA** commit esses arquivos no Git (já estão no `.gitignore`)
- Use **senhas de aplicativo** do Gmail, não sua senha principal
- Mantenha o `session_tokens.json` seguro (contém tokens de autenticação)

### Boas Práticas

1. ✅ Sempre use ambiente virtual Python
2. ✅ Mantenha as dependências atualizadas
3. ✅ Revise os logs regularmente (`logs/audiencias.log`)
4. ✅ Teste notificações de email periodicamente
5. ✅ Faça backup das configurações (exceto credenciais)

---

## 📊 Estrutura dos Dados

### Planilha de Audiências

| Coluna             | Descrição                  | Exemplo                          |
| ------------------ | -------------------------- | -------------------------------- |
| Data da Audiência  | Data no formato DD/MM/AAAA | 15/11/2025                       |
| Hora da Audiência  | Hora no formato HH:MM:SS   | 14:30:00                         |
| Número do Processo | Identificador único        | 1234567-89.2025.5.02.0001        |
| Reclamante         | Nome do autor              | João da Silva                    |
| Reclamado          | Nome do réu                | Empresa XYZ Ltda                 |
| Órgão Julgador     | Vara/localização           | 1ª Vara do Trabalho de São Paulo |
| Tipo               | Tipo de audiência          | Inicial, Instrução, etc.         |
| Status             | Status atual               | Marcada, Realizada, etc.         |

---

## 🆘 Suporte

### Logs

Consulte os logs para diagnóstico:

```powershell
# Ver últimas 50 linhas do log
Get-Content logs\audiencias.log -Tail 50

# Monitorar log em tempo real
Get-Content logs\audiencias.log -Wait
```

### Contato

Para dúvidas ou problemas:

- 📧 Email: escritorio.macedoadvocacia@gmail.com
- 📝 Consulte os logs primeiro: `logs/audiencias.log`

---

## 📝 Changelog

### Versão 2.0 (Novembro 2025)

- ✨ **NOVO**: Suporte completo para autenticação de dois fatores (2FA)
- ✨ **NOVO**: Login interativo via navegador visível
- ✨ **NOVO**: Cache de tokens de sessão (válidos por 24h)
- ✨ **NOVO**: Retry automático em operações críticas
- ✨ **NOVO**: Sistema de logs melhorado (console + arquivo + PaperTrail)
- ✨ **NOVO**: Configuração via variáveis de ambiente (.env)
- ✨ **NOVO**: Validação de configurações na inicialização
- 🔒 **SEGURANÇA**: Credenciais removidas do código-fonte
- 🐛 **CORREÇÃO**: Melhor tratamento de erros e exceções
- 📚 **DOCS**: Documentação completa (README + comentários)

### Versão 1.0 (Original)

- Funcionalidades básicas de scraping
- Login automatizado sem 2FA

---

## 📄 Licença

Este software é de uso interno do escritório. Todos os direitos reservados.

---

## 🙏 Agradecimentos

Desenvolvido para otimizar o gerenciamento de audiências trabalhistas, facilitando o acompanhamento e reduzindo erros manuais.

**Sistema desenvolvido com ❤️ para o Escritório Macedo Advocacia**
