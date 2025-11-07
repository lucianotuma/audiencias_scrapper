"""
Sistema de gerenciamento de audiências para escritório de advocacia.
Responsável por:
1. Autenticar nos sistemas de tribunais (TRT2 e TRT15)
2. Extrair informações de audiências agendadas
3. Sincronizar com planilhas Google
4. Atualizar eventos no Google Calendar
5. Enviar notificações por email quando houver alterações
"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
import logging
import re
import smtplib
from email.mime.text import MIMEText
from logging.handlers import SysLogHandler
from typing import Dict, Final, List, Optional, Tuple, Union

import pandas as pd
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Constantes para acesso a serviços Google
SCOPES: Final[List[str]] = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

SERVICE_ACCOUNT_FILE: Final[str] = './planilha-de-audiencias-25b5ec50e72f.json'
ACTUAL_HEARING_SPREADSHEET_ID: Final[str] = '1RBUyyexHI3p_nRrD2u84MYoTrLaDddlm7MC838Cvk58'
CHANGED_HEARING_SPREADSHEET_ID: Final[str] = '1zIYf_0I8g_QgGe6HDy55j2DdhYIlYdYLyBLfSk8MVP4'
CALENDAR_ID: Final[str] = 'c_aae930714cf9b78da155f0a509c1592da4d739c3ff76b758d860797e495661da@group.calendar.google.com'

# Configuração de logging
PAPERTRAIL_HOST: Final[str] = "logs5.papertrailapp.com"
PAPERTRAIL_PORT: Final[int] = 54240


class HearingLogger:
    """Gerenciador de logs do sistema."""
    
    def __init__(self, logger_name: str = "Hearing Scrapper") -> None:
        """Inicializa o logger com configuração para PaperTrail."""
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        handler = SysLogHandler(address=(PAPERTRAIL_HOST, PAPERTRAIL_PORT))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def info(self, message: str) -> None:
        """Registra uma mensagem informativa."""
        self.logger.info(message)
        
    def error(self, message: str, exc_info: bool = True) -> None:
        """Registra uma mensagem de erro."""
        self.logger.error(message, exc_info=exc_info)


class EmailNotifier:
    """Gerenciador de notificações por email."""
    
    def __init__(
        self, 
        sender: str = 'escritorio.macedoadvocacia@gmail.com',
        recipients: str = 'jessica@jmacedo.adv.br, lucianotuma@gmail.com, lorena.almeida@jmacedo.adv.br, pamela.almeida@jmacedo.adv.br',
        password: str = 'xxzbevnctkhqhnwl',
        logger: Optional[HearingLogger] = None
    ) -> None:
        """Inicializa o notificador de email com credenciais e destinatários."""
        self.sender = sender
        self.recipients = recipients
        self.password = password
        self.logger = logger or HearingLogger()
        
    def send(self, message: str, subject: str = 'Aviso do Sistema Automatizado') -> None:
        """Envia uma notificação por email."""
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = self.sender
            msg['To'] = self.recipients
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.send_message(msg)
                
            self.logger.info(f"Email enviado com sucesso: {subject}")
        except Exception as e:
            self.logger.error(f'Falha ao enviar email: {e}')


class GoogleServicesManager:
    """Gerenciador de serviços Google (Sheets e Calendar)."""
    
    def __init__(
        self, 
        service_account_file: str = SERVICE_ACCOUNT_FILE,
        logger: Optional[HearingLogger] = None
    ) -> None:
        """Inicializa o gerenciador com credenciais de serviço."""
        self.service_account_file = service_account_file
        self.logger = logger or HearingLogger()
        self.credentials = self._get_credentials()
        self.sheet_service = self._build_sheets_service()
        self.calendar_service = self._build_calendar_service()
    
    def _get_credentials(self) -> service_account.Credentials:
        """Obtém as credenciais da conta de serviço."""
        try:
            return service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=SCOPES
            )
        except Exception as e:
            self.logger.error(f"Falha ao obter credenciais: {e}")
            raise
    
    def _build_sheets_service(self):
        """Constrói o serviço de Google Sheets."""
        try:
            return build('sheets', 'v4', credentials=self.credentials)
        except Exception as e:
            self.logger.error(f"Falha ao construir serviço Sheets: {e}")
            raise
    
    def _build_calendar_service(self):
        """Constrói o serviço de Google Calendar."""
        try:
            return build('calendar', 'v3', credentials=self.credentials)
        except Exception as e:
            self.logger.error(f"Falha ao construir serviço Calendar: {e}")
            raise


class GoogleSheetsManager:
    """Gerenciador específico para operações com Google Sheets."""
    
    def __init__(
        self, 
        services_manager: GoogleServicesManager,
        notifier: EmailNotifier,
        logger: Optional[HearingLogger] = None
    ) -> None:
        """Inicializa o gerenciador de Sheets com serviços Google."""
        self.sheet_service = services_manager.sheet_service
        self.notifier = notifier
        self.logger = logger or HearingLogger()
    
    def read_from_sheet(self, spreadsheet_id: str) -> pd.DataFrame:
        """Lê dados de uma planilha Google e retorna como DataFrame."""
        try:
            range_name = 'A1:I1502'
            sheet = self.sheet_service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            data = result.get('values', [])
            if not data:
                return pd.DataFrame()
            
            headers = data[0]
            values = data[1:] if len(data) > 1 else []
            return pd.DataFrame(values, columns=headers)
        
        except Exception as e:
            self.logger.error(f"Falha ao ler planilha {spreadsheet_id}: {e}")
            self.notifier.send(f"O sistema não conseguiu ler a planilha. Erro: {e}")
            return pd.DataFrame()
    
    def clear_sheet(self, spreadsheet_id: str) -> None:
        """Limpa todos os valores de uma planilha."""
        request = {
            'requests': {
                'updateCells': {
                    'range': {
                        'sheetId': 0
                    },
                    'fields': 'userEnteredValue'
                }
            }
        }
        
        try:
            self.sheet_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, 
                body=request
            ).execute()
            self.logger.info(f"Planilha {spreadsheet_id} limpa com sucesso")
        except Exception as e:
            self.logger.error(f"Falha ao limpar planilha {spreadsheet_id}: {e}")
            self.notifier.send(f"O sistema não conseguiu limpar a planilha. Erro: {e}")
    
    def write_to_sheet(self, dataframe: pd.DataFrame, spreadsheet_id: str) -> None:
        """Escreve um DataFrame em uma planilha Google."""
        if dataframe.empty:
            self.logger.error("Tentativa de escrever DataFrame vazio na planilha")
            self.notifier.send("Tentativa de escrever dados vazios na planilha. Verifique o código.")
            return
        
        try:
            # Cria range dinâmico com base no tamanho do dataframe
            range_name = f'A1:I{len(dataframe) + 1}'
            
            # Prepara valores com cabeçalhos
            values = dataframe.values.tolist()
            values.insert(0, dataframe.columns.tolist())
            
            data = {'values': values}
            
            # Limpa e atualiza a planilha
            self.clear_sheet(spreadsheet_id)
            self.sheet_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                body=data,
                range=range_name,
                valueInputOption='RAW'
            ).execute()
            
            self.logger.info(f"Dados escritos com sucesso na planilha {spreadsheet_id}")
        
        except Exception as e:
            self.logger.error(f"Falha ao escrever na planilha {spreadsheet_id}: {e}")
            self.notifier.send(
                f"O sistema não conseguiu gravar as datas de audiências na planilha. Erro: {e}"
            )
    
    def append_to_sheet(self, dataframe: pd.DataFrame, spreadsheet_id: str) -> None:
        """Adiciona dados de um DataFrame ao final de uma planilha Google."""
        if dataframe.empty:
            return
        
        try:
            range_name = f'A1:I{len(dataframe) + 1}'
            values = dataframe.values.tolist()
            data = {'values': values}
            
            self.sheet_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                body=data,
                range=range_name,
                valueInputOption='RAW'
            ).execute()
            
            self.logger.info(f"Dados adicionados com sucesso à planilha {spreadsheet_id}")
        
        except Exception as e:
            self.logger.error(f"Falha ao adicionar dados à planilha {spreadsheet_id}: {e}")
            self.notifier.send(
                f"O sistema não conseguiu adicionar novos dados à planilha. Erro: {e}"
            )


class GoogleCalendarManager:
    """Gerenciador específico para operações com Google Calendar."""
    
    def __init__(
        self, 
        services_manager: GoogleServicesManager,
        notifier: EmailNotifier,
        logger: Optional[HearingLogger] = None
    ) -> None:
        """Inicializa o gerenciador de Calendar com serviços Google."""
        self.calendar_service = services_manager.calendar_service
        self.notifier = notifier
        self.logger = logger or HearingLogger()
    
    def get_event_summaries(self, calendar_id: str) -> List[str]:
        """Recupera uma lista de resumos de eventos do calendário."""
        try:
            # Período para busca: de ontem até o futuro
            current_datetime = datetime.utcnow()
            one_day = timedelta(days=1)
            previous_datetime = current_datetime - one_day
            previous_datetime_str = previous_datetime.isoformat() + 'Z'
            
            events_result = self.calendar_service.events().list(
                calendarId=calendar_id,
                timeMin=previous_datetime_str,
                singleEvents=True
            ).execute()
            
            events = events_result.get('items', [])
            return [event['summary'] for event in events]
        
        except Exception as e:
            self.logger.error(f"Falha ao listar eventos do calendário {calendar_id}: {e}")
            self.notifier.send(f"O sistema não conseguiu listar os eventos do calendário. Erro: {e}")
            return []
    
    def create_event(self, row_values: List[str], calendar_id: str) -> None:
        """Cria um evento de audiência no calendário."""
        try:
            date_str = f'{row_values[0]} {row_values[1]}'
            start_date_obj = datetime.strptime(date_str, '%d/%m/%Y %H:%M:%S')
            end_date_obj = start_date_obj + timedelta(hours=1)
            
            event = {
                'summary': f'{row_values[6]} - {row_values[3]} x {row_values[4]} {row_values[0]} às {row_values[1]} - {row_values[5]}',
                'location': row_values[5],
                'description': (
                    f'Audiência Trabalhista do Tipo {row_values[6]} nos Autos do Processo {row_values[2]} '
                    f'do(a) {row_values[5]}, marcada para {row_values[0]} às {row_values[1]}. '
                    f'Reclamante: {row_values[3]} x Reclamado: {row_values[4]}. '
                    f'O Status da Audiência é {row_values[7]}'
                ),
                'start': {
                    'dateTime': start_date_obj.strftime('%Y-%m-%dT%H:%M:%S'),
                    'timeZone': 'America/Sao_Paulo',
                },
                'end': {
                    'dateTime': end_date_obj.strftime('%Y-%m-%dT%H:%M:%S'),
                    'timeZone': 'America/Sao_Paulo',
                },
                'colorId': '3'
            }
            
            self.calendar_service.events().insert(
                calendarId=calendar_id, 
                body=event
            ).execute()
            
            self.logger.info(f"Evento criado com sucesso: {event['summary']}")
        
        except Exception as e:
            self.logger.error(f"Falha ao criar evento no calendário: {e}")
            self.notifier.send(f"O sistema não conseguiu criar um evento no calendário. Erro: {e}")
    
    def update_event_date(self, new_date: str, new_time: str, event_id: str, calendar_id: str) -> None:
        """Atualiza a data e hora de um evento no calendário."""
        try:
            date_str = f'{new_date} {new_time}'
            start_date_obj = datetime.strptime(date_str, '%d/%m/%Y %H:%M:%S')
            end_date_obj = start_date_obj + timedelta(hours=1)
            
            event = {
                'start': {
                    'dateTime': start_date_obj.strftime('%Y-%m-%dT%H:%M:%S'),
                    'timeZone': 'America/Sao_Paulo'
                },
                'end': {
                    'dateTime': end_date_obj.strftime('%Y-%m-%dT%H:%M:%S'),
                    'timeZone': 'America/Sao_Paulo'
                }
            }
            
            self.calendar_service.events().patch(
                calendarId=calendar_id, 
                eventId=event_id, 
                body=event
            ).execute()
            
            self.logger.info(f"Evento {event_id} atualizado com sucesso")
        
        except Exception as e:
            self.logger.error(f"Falha ao atualizar evento {event_id}: {e}")
            self.notifier.send(f"O sistema não conseguiu atualizar um evento no calendário. Erro: {e}")
    
    def delete_event(self, event_id: str, calendar_id: str) -> None:
        """Remove um evento do calendário."""
        try:
            self.calendar_service.events().delete(
                calendarId=calendar_id, 
                eventId=event_id
            ).execute()
            self.logger.info(f"Evento {event_id} removido com sucesso")
        
        except Exception as e:
            self.logger.error(f"Falha ao remover evento {event_id}: {e}")
            self.notifier.send(f"O sistema não conseguiu remover um evento do calendário. Erro: {e}")
    
    def find_events_by_summary(self, summary: str, calendar_id: str) -> List[Dict]:
        """Busca eventos no calendário pelo resumo/título."""
        try:
            events_result = self.calendar_service.events().list(
                calendarId=calendar_id,
                q=summary
            ).execute()
            
            return events_result.get('items', [])
        
        except Exception as e:
            self.logger.error(f"Falha ao buscar eventos com resumo '{summary}': {e}")
            self.notifier.send(f"O sistema não conseguiu buscar eventos no calendário. Erro: {e}")
            return []
    
    def populate_calendar(self, dataframe: pd.DataFrame, calendar_id: str) -> None:
        """Popula o calendário com eventos baseados nos dados do DataFrame."""
        if dataframe.empty:
            self.logger.error("Tentativa de popular calendário com DataFrame vazio")
            self.notifier.send("Tentativa de popular calendário com dados vazios. Verifique o código.")
            return
        
        event_summaries = self.get_event_summaries(calendar_id)
        
        for _, row in dataframe.iterrows():
            row_values = row.values
            event_summary = f'{row_values[6]} - {row_values[3]} x {row_values[4]} {row_values[0]} às {row_values[1]} - {row_values[5]}'
            
            if event_summary not in event_summaries:
                self.create_event(row_values, calendar_id)
    
    def handle_changed_events(self, diff_dataframe: pd.DataFrame, calendar_id: str) -> None:
        """Gerencia eventos que tiveram alterações (exclusão de antigos, criação de novos)."""
        if diff_dataframe.empty:
            return
        
        for _, row in diff_dataframe.iterrows():
            row_values = row.values
            event_summary = f'{row_values[6]} - {row_values[3]} x {row_values[4]} {row_values[0]} às {row_values[1]} - {row_values[5]}'
            
            events = self.find_events_by_summary(event_summary, calendar_id)
            
            if not events:
                self.logger.error(f"Evento não encontrado para exclusão: '{event_summary}'")
                self.notifier.send(
                    f'O sistema não conseguiu encontrar e deletar o evento: "{event_summary}". '
                    f'Verifique manualmente se o evento existe.'
                )
            else:
                for event in events:
                    event_id = event['id']
                    self.delete_event(event_id, calendar_id)
                    self.notifier.send(
                        f'ATENÇÃO: O evento de título "{event_summary}" sofreu uma alteração. '
                        f'Favor comunicar ao cliente.'
                    )


class CourtSession:
    """Gerenciador de sessão para acesso aos tribunais."""
    
    def __init__(
        self,
        logger: Optional[HearingLogger] = None,
        notifier: Optional[EmailNotifier] = None
    ) -> None:
        """Inicializa o gerenciador de sessão com headers padrão."""
        self.session = requests.Session()
        self.logger = logger or HearingLogger()
        self.notifier = notifier or EmailNotifier()
        self._set_headers()
        
    def _set_headers(self) -> None:
        """Define headers padrão para a sessão."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        self.session.headers.update(headers)
    
    def login(self, login_url: str, username: str, password: str, timeout: int = 30) -> bool:
        """
        Realiza login no sistema do tribunal usando Selenium.
        
        1. Abre `login_url`.
        2. Clica no botão //*[@id="btnSsoPdpj"]/img (SSO-PJ).
        3. Aguarda carregamento da tela OpenID.
        4. Preenche <input id|name='username'> e 'password'.
        5. Clica <button id='kc-login'>.
        """
        try:
            # Configuração do Chrome em modo headless
            chrome_opts = ChromeOptions()
            chrome_opts.add_argument("--headless=new")  # Versão moderna do headless
            chrome_opts.add_argument("--disable-gpu")
            chrome_opts.add_argument("--no-sandbox")
            chrome_opts.add_argument("--window-size=1920,1080")
            chrome_opts.add_experimental_option("excludeSwitches", ["enable-logging"])
            
            # Adiciona argumentos para persistir cookies para a sessão requests
            chrome_opts.add_argument("--user-data-dir=/tmp/chrome-profile")
            chrome_opts.add_argument(
                                    "--user-agent="
                                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                                    "Chrome/125.0.0.0 Safari/537.36"
            )

# 2) Ocultar a flag de automação
            chrome_opts.add_argument("--disable-blink-features=AutomationControlled")
            
            # Configura o serviço Chrome
            service = ChromeService(ChromeDriverManager().install())
            
            with webdriver.Chrome(service=service, options=chrome_opts) as driver:
                wait = WebDriverWait(driver, timeout)
                
                # 1) Acessa página inicial
                driver.get(login_url)
                self.logger.info(f"Acessando {login_url}")
                
                # 2) Clica no botão SSO-PJ
                sso_btn = wait.until(
                    EC.element_to_be_clickable((By.ID, "btnSsoPdpj"))
                )
                sso_btn.click()
                self.logger.info("Botão SSO-PJ clicado")
                
                # 3) Aguarda redirecionamento para a tela OpenID
                wait.until(EC.url_contains("openid"))
                self.logger.info("Redirecionado para tela OpenID")
                
                # 4) Localiza inputs e preenche credenciais
                username_input = wait.until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                password_input = wait.until(
                    EC.presence_of_element_located((By.ID, "password"))
                )
                login_button = wait.until(
                    EC.element_to_be_clickable((By.ID, "kc-login"))
                )
                
                username_input.clear()
                username_input.send_keys(username)
                password_input.clear()
                password_input.send_keys(password)
                login_button.click()
                self.logger.info("Credenciais inseridas e botão de login clicado")
                
                # 5) Confirma que saiu da tela de login
                wait.until(lambda d: "openid" not in d.current_url.lower())
                self.logger.info("Autenticação concluída com sucesso")
                
                # 6) Captura cookies para usar na sessão requests
                cookies = driver.get_cookies()
                for cookie in cookies:
                    self.session.cookies.set(
                        cookie['name'], 
                        cookie['value'], 
                        domain=cookie.get('domain', '')
                    )
                
                self.logger.info(f"Capturados {len(cookies)} cookies para a sessão")
                return True
                
        except TimeoutException as te:
            msg = f"Timeout ao tentar autenticar em {login_url}: {te}"
            self.notifier.send(msg)
            self.logger.error(msg)
            return False
            
        except Exception as e:
            msg = f"O sistema não conseguiu autenticar as credenciais na URL {login_url} (erro: {e})"
            self.notifier.send(msg)
            self.logger.error(msg)
            return False
    
    def search_hearings(
        self, 
        api_url: str,
        search_start_date: str,
        search_end_date: str,
        situation_code: str = 'M',
        page_number: str = '1',
        results_per_page: str = '1500',
        order: str = 'asc'
    ) -> Dict:
        """Realiza busca de audiências na API do tribunal."""
        params = {
            'dataFim': search_end_date,
            'dataInicio': search_start_date,
            'codigoSituacao': situation_code,
            'numeroPagina': page_number,
            'tamanhoPagina': results_per_page,
            'ordenacao': order
        }
        
        try:
            response = self.session.get(api_url, params=params)
            response.raise_for_status()  # Levanta exceção para códigos de erro HTTP
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na requisição à API {api_url}: {e}")
            self.notifier.send(f"Falha ao buscar audiências na API {api_url}. Erro: {e}")
            return {}


class HearingDataProcessor:
    """Processador de dados de audiências."""
    
    @staticmethod
    def json_to_dataframe(json_data: Union[Dict, List[Dict]]) -> pd.DataFrame:
        """Converte dados JSON de audiências para DataFrame."""
        if not json_data or 'resultado' not in json_data:
            return pd.DataFrame()
        
        try:
            # Cria DataFrame a partir dos dados normalizados
            dataframe = pd.DataFrame(pd.json_normalize(json_data['resultado']))
            
            # Seleciona apenas as colunas desejadas
            columns = [
                'dataInicio',
                'pautaAudienciaHorario.horaInicial',
                'processo.numero',
                'poloAtivo.nome',
                'poloPassivo.nome',
                'processo.orgaoJulgador.descricao',
                'tipo.descricao',
                'statusDescricao'
            ]
            
            # Verifica se todas as colunas existem
            if not all(col in dataframe.columns for col in columns):
                missing = [col for col in columns if col not in dataframe.columns]
                # Cria colunas vazias para as que estão faltando
                for col in missing:
                    dataframe[col] = None
            
            dataframe = dataframe[columns]
            
            # Formata a data para o padrão brasileiro
            if 'dataInicio' in dataframe.columns:
                dataframe['dataInicio'] = pd.to_datetime(dataframe['dataInicio'])
                dataframe['dataInicio'] = dataframe['dataInicio'].dt.strftime('%d/%m/%Y')
            
            # Renomeia as colunas para melhor legibilidade
            dataframe.rename(columns={
                'dataInicio': 'Data da Audiência',
                'pautaAudienciaHorario.horaInicial': 'Hora da Audiência',
                'processo.numero': 'Número do Processo',
                'poloAtivo.nome': 'Reclamante',
                'poloPassivo.nome': 'Reclamado',
                'processo.orgaoJulgador.descricao': 'Órgão Julgador',
                'tipo.descricao': 'Tipo',
                'statusDescricao': 'Status'
            }, inplace=True)
            
            return dataframe
            
        except Exception as e:
            logger = HearingLogger()
            logger.error(f"Erro ao processar dados JSON: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def find_changed_hearings(new_df: pd.DataFrame, old_df: pd.DataFrame) -> pd.DataFrame:
        """Identifica audiências que tiveram alterações."""
        if new_df.empty or old_df.empty:
            return pd.DataFrame()
        
        result = pd.DataFrame()
        
        for _, row in new_df.iterrows():
            # Extrai dados da linha atual
            court_case_number = row['Número do Processo']
            hearing_date = row['Data da Audiência']
            hearing_type = row['Tipo']
            hearing_hour = row['Hora da Audiência']
            hearing_place = row['Órgão Julgador']
            
            # Busca por diferenças no dataframe antigo
            matching_rows = old_df[
                (old_df['Número do Processo'] == court_case_number) &
                (old_df['Órgão Julgador'] == hearing_place)
            ]
            
            # Filtra apenas as linhas com alterações em data, tipo ou hora
            changed_rows = matching_rows[
                (matching_rows['Data da Audiência'] != hearing_date) |
                (matching_rows['Tipo'] != hearing_type) |
                (matching_rows['Hora da Audiência'] != hearing_hour)
            ]
            
            # Adiciona as linhas alteradas ao resultado
            if not changed_rows.empty:
                result = pd.concat([result, changed_rows], ignore_index=True)
        
        return result
    
    @staticmethod
    def combine_and_sort_dataframes(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """Combina dois DataFrames e ordena por data de audiência."""
        if df1.empty:
            return df2
        if df2.empty:
            return df1
        
        # Converte datas para datetime para ordenação correta
        df1_copy = df1.copy()
        df2_copy = df2.copy()
        
        df1_copy['Data da Audiência'] = pd.to_datetime(df1_copy['Data da Audiência'], format='%d/%m/%Y')
        df2_copy['Data da Audiência'] = pd.to_datetime(df2_copy['Data da Audiência'], format='%d/%m/%Y')
        
        # Concatena os DataFrames
        combined_df = pd.concat([df1_copy, df2_copy], ignore_index=True)
        
        # Remove duplicatas (mesmo processo, local, data e hora)
        combined_df = combined_df.drop_duplicates(
            subset=['Número do Processo', 'Órgão Julgador', 'Data da Audiência', 'Hora da Audiência'],
            keep='first'
        )
        
        # Ordena por data
        combined_df = combined_df.sort_values(by='Data da Audiência')
        
        # Converte data de volta para string no formato brasileiro
        combined_df['Data da Audiência'] = combined_df['Data da Audiência'].dt.strftime('%d/%m/%Y')
        
        return combined_df


class HearingManager:
    """Gerenciador principal do sistema de audiências."""
    
    def __init__(self) -> None:
        """Inicializa o gerenciador com todos os componentes necessários."""
        self.logger = HearingLogger()
        self.notifier = EmailNotifier(logger=self.logger)
        self.services = GoogleServicesManager(logger=self.logger)
        self.sheets = GoogleSheetsManager(self.services, self.notifier, self.logger)
        self.calendar = GoogleCalendarManager(self.services, self.notifier, self.logger)
        self.trt2_session = CourtSession(self.logger, self.notifier)
        self.trt15_session = CourtSession(self.logger, self.notifier)
    
    def _authenticate_with_courts(self) -> bool:
        """Autentica com os sistemas dos tribunais."""
        self.logger.info("Iniciando autenticação nos tribunais")
        
        trt2_success = self.trt2_session.login(
            'https://pje.trt2.jus.br/primeirograu/login.seam',
            '39248808832', 
            'M@cedoadv02030405'
        )
        
        trt15_success = self.trt15_session.login(
            'https://pje.trt15.jus.br/primeirograu/login.seam',
            '39248808832', 
            'M@cedoadv02030405'
        )
        
        if trt2_success and trt15_success:
            self.logger.info("Autenticação concluída com sucesso em ambos os tribunais")
            return True
        else:
            self.logger.error("Falha na autenticação em um ou mais tribunais")
            return False
    
    def _get_current_hearings(self, court_domain: str, session: CourtSession) -> pd.DataFrame:
        """Obtém audiências atuais de um tribunal específico."""
        try:
            self.logger.info(f"Buscando audiências atuais no {court_domain}")
            
            year = datetime.now().year
            today = datetime.now().strftime("%Y-%m-%d")
            
            api_url = f'https://{court_domain}/pje-comum-api/api/pauta-usuarios-externos'
            
            response_json = session.search_hearings(
                api_url=api_url,
                search_start_date=today,
                search_end_date=f'{year}-12-31'
            )
            
            return HearingDataProcessor.json_to_dataframe(response_json)
            
        except Exception as e:
            self.logger.error(f"Erro ao obter audiências atuais de {court_domain}: {e}")
            self.notifier.send(
                f"Falha ao obter audiências atuais de {court_domain}. Erro: {e}"
            )
            return pd.DataFrame()
    
    def _get_future_hearings(self, court_domain: str, session: CourtSession, year: int) -> pd.DataFrame:
        """Obtém audiências futuras de um tribunal específico para um ano específico."""
        try:
            self.logger.info(f"Buscando audiências futuras no {court_domain} para o ano {year}")
            
            api_url = f'https://{court_domain}/pje-comum-api/api/pauta-usuarios-externos'
            
            response_json = session.search_hearings(
                api_url=api_url,
                search_start_date=f'{year}-01-01',
                search_end_date=f'{year}-12-31'
            )
            
            return HearingDataProcessor.json_to_dataframe(response_json)
            
        except Exception as e:
            self.logger.error(f"Erro ao obter audiências futuras de {court_domain} para {year}: {e}")
            self.notifier.send(
                f"Falha ao obter audiências futuras de {court_domain} para {year}. Erro: {e}"
            )
            return pd.DataFrame()
    
    def process_hearings(self) -> None:
        """Processo principal de obtenção e processamento de audiências."""
        self.logger.info("Iniciando rotina de processamento de audiências")
        
        # 1. Autenticação com os tribunais
        if not self._authenticate_with_courts():
            self.logger.error("Falha na autenticação. Encerrando processamento.")
            return
        
        # 2. Obtenção de audiências atuais
        trt2_hearings = self._get_current_hearings('pje.trt2.jus.br', self.trt2_session)
        trt15_hearings = self._get_current_hearings('pje.trt15.jus.br', self.trt15_session)
        
        # 3. Combinação das audiências atuais
        current_hearings = HearingDataProcessor.combine_and_sort_dataframes(
            trt2_hearings, trt15_hearings
        )
        
        # 4. Obtenção de audiências futuras
        current_year = datetime.now().year
        all_hearings = current_hearings.copy()
        
        # Busca audiências para os próximos 3 anos
        for year in range(current_year + 1, current_year + 4):
            # TRT2
            future_trt2 = self._get_future_hearings('pje.trt2.jus.br', self.trt2_session, year)
            all_hearings = HearingDataProcessor.combine_and_sort_dataframes(
                all_hearings, future_trt2
            )
            
            # TRT15
            future_trt15 = self._get_future_hearings('pje.trt15.jus.br', self.trt15_session, year)
            all_hearings = HearingDataProcessor.combine_and_sort_dataframes(
                all_hearings, future_trt15
            )
        
        # 5. Identificação de audiências com alterações
        old_hearings = self.sheets.read_from_sheet(ACTUAL_HEARING_SPREADSHEET_ID)
        changed_hearings = HearingDataProcessor.find_changed_hearings(all_hearings, old_hearings)
        
        if not changed_hearings.empty:
            self.logger.info(f"Detectadas {len(changed_hearings)} audiências com alterações")
            self.sheets.append_to_sheet(changed_hearings, CHANGED_HEARING_SPREADSHEET_ID)
            self.calendar.handle_changed_events(changed_hearings, CALENDAR_ID)
        
        # 6. Atualização da planilha principal
        self.sheets.write_to_sheet(all_hearings, ACTUAL_HEARING_SPREADSHEET_ID)
        
        # 7. Atualização do calendário
        self.calendar.populate_calendar(all_hearings, CALENDAR_ID)
        
        self.logger.info("Rotina de processamento de audiências concluída com sucesso")


def main() -> None:
    """Função principal de execução do programa."""
    try:
        manager = HearingManager()
        manager.process_hearings()
    except Exception as e:
        logger = HearingLogger()
        notifier = EmailNotifier()
        error_message = f"Erro crítico na execução do programa: {e}"
        logger.error(error_message)
        notifier.send(error_message)


if __name__ == '__main__':
    main()