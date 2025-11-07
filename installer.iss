; ============================================
; INNO SETUP SCRIPT - SISTEMA DE AUDIÊNCIAS
; ============================================
; Script para criar instalador Windows profissional
; Inclui todos os arquivos necessários pré-configurados

#define MyAppName "Sistema de Audiências"
#define MyAppVersion "2.0"
#define MyAppPublisher "J. Macedo Advocacia"
#define MyAppExeName "SistemaAudiencias.exe"
#define MyAppDescription "Sistema automatizado de gerenciamento de audiências TRT"

[Setup]
; Informações básicas do aplicativo
AppId={{8A7B9C4D-5E6F-4A1B-8C2D-9E3F4A5B6C7D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://jmacedo.adv.br
AppSupportURL=https://jmacedo.adv.br
AppUpdatesURL=https://jmacedo.adv.br
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; Desabilita seleção de componentes (instalação completa sempre)
DisableProgramGroupPage=yes
; Licença (opcional - comentado por enquanto)
;LicenseFile=LICENSE.txt
; Saída do instalador
OutputDir=.\installer_output
OutputBaseFilename=SistemaAudiencias_Setup_v2.0
; Compressão máxima
Compression=lzma2/max
SolidCompression=yes
; Configurações visuais modernas
WizardStyle=modern
; Privilégios de administrador
PrivilegesRequired=lowest
; Arquitetura
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Informações de versão
VersionInfoVersion={#MyAppVersion}
VersionInfoDescription={#MyAppDescription}
; Desinstalar arquivo de log
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de &Trabalho"; GroupDescription: "Atalhos adicionais:"

[Files]
; Executável principal
Source: "SistemaAudiencias_Windows_v2.0\SistemaAudiencias.exe"; DestDir: "{app}"; Flags: ignoreversion
; Arquivo de configuração com credenciais (PRÉ-CONFIGURADO)
Source: "SistemaAudiencias_Windows_v2.0\.env"; DestDir: "{app}"; Flags: ignoreversion
; Credenciais Google (PRÉ-CONFIGURADO)
Source: "SistemaAudiencias_Windows_v2.0\planilha-de-audiencias-25b5ec50e72f.json"; DestDir: "{app}"; Flags: ignoreversion
; Arquivo batch para execução com UTF-8
Source: "SistemaAudiencias_Windows_v2.0\Executar.bat"; DestDir: "{app}"; Flags: ignoreversion
; Documentação
Source: "SistemaAudiencias_Windows_v2.0\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "SistemaAudiencias_Windows_v2.0\QUICKSTART.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "SistemaAudiencias_Windows_v2.0\LEIA-ME.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "SistemaAudiencias_Windows_v2.0\INSTALACAO_EXECUTAVEL.md"; DestDir: "{app}"; Flags: ignoreversion
; Diretório de logs (criar vazio)
Source: "SistemaAudiencias_Windows_v2.0\logs\*"; DestDir: "{app}\logs"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Atalho no Menu Iniciar (executa o .bat para garantir UTF-8)
Name: "{group}\{#MyAppName}"; Filename: "{app}\Executar.bat"; WorkingDir: "{app}"; Comment: "Executar {#MyAppName}"; IconFilename: "{app}\{#MyAppExeName}"
; Atalho para documentação
Name: "{group}\Guia de Uso"; Filename: "{app}\LEIA-ME.txt"; Comment: "Como usar o sistema"
; Atalho para desinstalar
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"; Comment: "Remover {#MyAppName}"
; Atalho na Área de Trabalho (executa o .bat)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\Executar.bat"; WorkingDir: "{app}"; Tasks: desktopicon; Comment: "Executar {#MyAppName}"; IconFilename: "{app}\{#MyAppExeName}"

[Run]
; Opção de executar após instalação
Filename: "{app}\Executar.bat"; Description: "Executar {#MyAppName} agora"; Flags: postinstall shellexec skipifsilent nowait

[UninstallDelete]
; Limpar arquivos criados durante execução
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\session_tokens.json"

[Code]
// Mensagens customizadas em português
procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel2.Caption := 
    'Este assistente irá instalar o ' + '{#MyAppName}' + ' no seu computador.' + #13#10 + #13#10 +
    'O sistema já está pré-configurado e pronto para uso.' + #13#10 + 
    'Basta clicar em Avançar para continuar.' + #13#10 + #13#10 +
    'IMPORTANTE: Certifique-se de que o Google Chrome está instalado.' + #13#10 + #13#10 +
    'Clique em Avançar para continuar, ou em Cancelar para sair da instalação.';
end;

// Verificar se Chrome está instalado
function IsChromeInstalled(): Boolean;
var
  ChromePath: String;
begin
  // Verifica caminhos comuns do Chrome
  Result := FileExists(ExpandConstant('{pf}\Google\Chrome\Application\chrome.exe')) or
            FileExists(ExpandConstant('{pf32}\Google\Chrome\Application\chrome.exe')) or
            FileExists(ExpandConstant('{localappdata}\Google\Chrome\Application\chrome.exe'));
end;

// Aviso se Chrome não estiver instalado
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  
  if CurPageID = wpWelcome then
  begin
    if not IsChromeInstalled() then
    begin
      if MsgBox('ATENÇÃO: O Google Chrome não foi detectado no seu computador.' + #13#10 + #13#10 +
                'O sistema precisa do Chrome para funcionar.' + #13#10 + #13#10 +
                'Deseja continuar mesmo assim?' + #13#10 +
                '(Você poderá instalar o Chrome depois)', 
                mbConfirmation, MB_YESNO) = IDNO then
        Result := False;
    end;
  end;
end;

// Mensagem final de sucesso
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Criar arquivo de instruções rápidas na área de trabalho
    SaveStringToFile(ExpandConstant('{autodesktop}\COMO USAR - Sistema de Audiências.txt'), 
      '==================================================' + #13#10 +
      'COMO USAR O SISTEMA DE AUDIÊNCIAS' + #13#10 +
      '==================================================' + #13#10 + #13#10 +
      '1. Dê duplo clique no atalho "Sistema de Audiências"' + #13#10 +
      '   na sua Área de Trabalho' + #13#10 + #13#10 +
      '2. O Chrome irá abrir automaticamente' + #13#10 + #13#10 +
      '3. Faça login MANUALMENTE nos sites do TRT2 e TRT15' + #13#10 +
      '   (complete o segundo fator de autenticação)' + #13#10 + #13#10 +
      '4. Aguarde o sistema coletar as audiências' + #13#10 + #13#10 +
      '5. Pronto! As planilhas e calendário serão atualizados' + #13#10 +
      '   automaticamente' + #13#10 + #13#10 +
      '==================================================' + #13#10 +
      'OBSERVAÇÕES IMPORTANTES:' + #13#10 +
      '==================================================' + #13#10 + #13#10 +
      '• O sistema salva seus tokens de login por 24 horas' + #13#10 +
      '• Após 24h, será necessário fazer login novamente' + #13#10 +
      '• O Chrome precisa estar instalado' + #13#10 +
      '• Você receberá emails sobre alterações nas audiências' + #13#10 + #13#10 +
      '==================================================' + #13#10 +
      'SUPORTE:' + #13#10 +
      '==================================================' + #13#10 + #13#10 +
      'Em caso de dúvidas, entre em contato com:' + #13#10 +
      'escritorio.macedoadvocacia@gmail.com' + #13#10 + #13#10,
      False);
  end;
end;
