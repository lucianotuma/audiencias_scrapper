"""
Sistema de gerenciamento de audiências para escritório de advocacia.

Responsável por:
1. Autenticar nos sistemas de tribunais (TRT2 e TRT15) com suporte a 2FA
2. Extrair informações de audiências agendadas
3. Sincronizar com planilhas Google
4. Atualizar eventos no Google Calendar
5. Enviar notificações por email quando houver alterações

Autor: Sistema Automatizado
Versão: 2.0
Data: Novembro 2025
"""

from __future__ import annotations
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union
import json
import logging
import os
import smtplib
import sys
import time
from email.mime.text import MIMEText
from logging.handlers import RotatingFileHandler, SysLogHandler

import pandas as pd
import requests
from dotenv import load_dotenv
from google.api_core import retry
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException
from tenacity import retry as tenacity_retry
from tenacity import stop_after_attempt, wait_exponential, retry_if_exception_type
import chromedriver_autoinstaller

# Carrega variáveis de ambiente
load_dotenv()

# Constantes para acesso a serviços Google
SCOPES: List[str] = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]


class Config:
    """Gerenciador centralizado de configurações do sistema."""
    
    # Credenciais TRT
    TRT_USERNAME: str = os.getenv('TRT_USERNAME', '')
    TRT_PASSWORD: str = os.getenv('TRT_PASSWORD', '')
    
    # Configurações de Email
    EMAIL_SENDER: str = os.getenv('EMAIL_SENDER', '')
    EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_RECIPIENTS: str = os.getenv('EMAIL_RECIPIENTS', '')
    
    # Google Services
    SERVICE_ACCOUNT_FILE: str = os.getenv(
        'GOOGLE_SERVICE_ACCOUNT_FILE', 
        './planilha-de-audiencias-25b5ec50e72f.json'
    )
    ACTUAL_HEARING_SPREADSHEET_ID: str = os.getenv(
        'ACTUAL_HEARING_SPREADSHEET_ID',
        '1RBUyyexHI3p_nRrD2u84MYoTrLaDddlm7MC838Cvk58'
    )
    CHANGED_HEARING_SPREADSHEET_ID: str = os.getenv(
        'CHANGED_HEARING_SPREADSHEET_ID',
        '1zIYf_0I8g_QgGe6HDy55j2DdhYIlYdYLyBLfSk8MVP4'
    )
    CALENDAR_ID: str = os.getenv(
        'CALENDAR_ID',
        'c_aae930714cf9b78da155f0a509c1592da4d739c3ff76b758d860797e495661da@group.calendar.google.com'
    )
    
    # Logging
    PAPERTRAIL_HOST: str = os.getenv('PAPERTRAIL_HOST', '')
    PAPERTRAIL_PORT: int = int(os.getenv('PAPERTRAIL_PORT', '0'))
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Cache de Tokens
    TOKEN_CACHE_FILE: str = os.getenv('TOKEN_CACHE_FILE', './session_tokens.json')
    TOKEN_EXPIRY_HOURS: int = int(os.getenv('TOKEN_EXPIRY_HOURS', '24'))
    
    @classmethod
    def validate(cls) -> bool:
        """Valida se todas as configurações obrigatórias estão presentes."""
        required_fields = {
            'TRT_USERNAME': cls.TRT_USERNAME,
            'TRT_PASSWORD': cls.TRT_PASSWORD,
            'EMAIL_SENDER': cls.EMAIL_SENDER,
            'EMAIL_PASSWORD': cls.EMAIL_PASSWORD,
            'EMAIL_RECIPIENTS': cls.EMAIL_RECIPIENTS,
        }
        
        missing = [field for field, value in required_fields.items() if not value]
        
        if missing:
            print(f"❌ ERRO: Variáveis de ambiente ausentes: {', '.join(missing)}")
            print("📝 Por favor, crie um arquivo .env baseado em .env.example")
            return False
        
        return True


class HearingLogger:
    """Gerenciador avançado de logs do sistema."""
    
    def __init__(self, logger_name: str = "HearingScrapper") -> None:
        """Inicializa o logger com múltiplos handlers."""
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
        
        # Remove handlers existentes para evitar duplicação
        self.logger.handlers.clear()
        
        # Formato detalhado de log
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 1. Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 2. Handler para arquivo local (rotativo)
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / 'audiencias.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 3. Handler para PaperTrail (se configurado)
        if Config.PAPERTRAIL_HOST and Config.PAPERTRAIL_PORT:
            try:
                papertrail_handler = SysLogHandler(
                    address=(Config.PAPERTRAIL_HOST, Config.PAPERTRAIL_PORT)
                )
                papertrail_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                papertrail_handler.setFormatter(papertrail_formatter)
                self.logger.addHandler(papertrail_handler)
            except Exception as e:
                self.logger.warning(f"Não foi possível conectar ao PaperTrail: {e}")
        
    def debug(self, message: str) -> None:
        """Registra uma mensagem de debug."""
        self.logger.debug(message)
        
    def info(self, message: str) -> None:
        """Registra uma mensagem informativa."""
        self.logger.info(message)
        
    def warning(self, message: str) -> None:
        """Registra um aviso."""
        self.logger.warning(message)
        
    def error(self, message: str, exc_info: bool = True) -> None:
        """Registra uma mensagem de erro."""
        self.logger.error(message, exc_info=exc_info)
        
    def critical(self, message: str, exc_info: bool = True) -> None:
        """Registra uma mensagem crítica."""
        self.logger.critical(message, exc_info=exc_info)


class EmailNotifier:
    """Gerenciador de notificações por email."""
    
    def __init__(self, logger: Optional[HearingLogger] = None) -> None:
        """Inicializa o notificador de email com credenciais do .env."""
        self.sender = Config.EMAIL_SENDER
        self.recipients = Config.EMAIL_RECIPIENTS
        self.password = Config.EMAIL_PASSWORD
        self.logger = logger or HearingLogger()
        
    @tenacity_retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    def send(self, message: str, subject: str = 'Aviso do Sistema Automatizado') -> None:
        """Envia uma notificação por email com retry automático."""
        try:
            msg = MIMEText(message, 'plain', 'utf-8')
            msg['Subject'] = subject
            msg['From'] = self.sender
            msg['To'] = self.recipients
            
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.send_message(msg)
                
            self.logger.info(f"✉️ Email enviado com sucesso: {subject}")
        except Exception as e:
            self.logger.error(f'❌ Falha ao enviar email: {e}')
            raise


class TokenCache:
    """Gerenciador de cache de tokens de autenticação."""
    
    def __init__(self, cache_file: str = None, logger: Optional[HearingLogger] = None):
        """Inicializa o gerenciador de cache."""
        self.cache_file = Path(cache_file or Config.TOKEN_CACHE_FILE)
        self.logger = logger or HearingLogger()
        
    def save_tokens(self, tribunal: str, cookies: List[Dict]) -> None:
        """Salva tokens de um tribunal no cache."""
        try:
            cache_data = self._load_cache()
            
            cache_data[tribunal] = {
                'cookies': cookies,
                'timestamp': datetime.now().isoformat(),
                'expires_at': (
                    datetime.now() + timedelta(hours=Config.TOKEN_EXPIRY_HOURS)
                ).isoformat()
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"💾 Tokens salvos em cache para {tribunal}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar tokens: {e}")
            
    def load_tokens(self, tribunal: str) -> Optional[List[Dict]]:
        """Carrega tokens de um tribunal do cache se ainda válidos."""
        try:
            cache_data = self._load_cache()
            
            if tribunal not in cache_data:
                self.logger.debug(f"Nenhum token em cache para {tribunal}")
                return None
                
            token_data = cache_data[tribunal]
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            
            if datetime.now() > expires_at:
                self.logger.info(f"⏰ Tokens expirados para {tribunal}")
                return None
                
            self.logger.info(f"✅ Tokens carregados do cache para {tribunal}")
            return token_data['cookies']
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar tokens: {e}")
            return None
            
    def _load_cache(self) -> Dict:
        """Carrega o arquivo de cache."""
        if not self.cache_file.exists():
            return {}
            
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Erro ao ler cache: {e}")
            return {}
            
    def clear_tokens(self, tribunal: str = None) -> None:
        """Limpa tokens do cache (tribunal específico ou todos)."""
        try:
            if tribunal:
                cache_data = self._load_cache()
                if tribunal in cache_data:
                    del cache_data[tribunal]
                    with open(self.cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, indent=2, ensure_ascii=False)
                    self.logger.info(f"🗑️ Tokens removidos para {tribunal}")
            else:
                if self.cache_file.exists():
                    self.cache_file.unlink()
                    self.logger.info("🗑️ Cache de tokens completamente limpo")
        except Exception as e:
            self.logger.error(f"Erro ao limpar cache: {e}")


class GoogleServicesManager:
    """Gerenciador de serviços Google (Sheets e Calendar)."""
    
    def __init__(self, logger: Optional[HearingLogger] = None) -> None:
        """Inicializa o gerenciador com credenciais de serviço."""
        self.service_account_file = Config.SERVICE_ACCOUNT_FILE
        self.logger = logger or HearingLogger()
        self.credentials = self._get_credentials()
        self.sheet_service = self._build_sheets_service()
        self.calendar_service = self._build_calendar_service()
    
    @tenacity_retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _get_credentials(self) -> service_account.Credentials:
        """Obtém as credenciais da conta de serviço com retry."""
        try:
            self.logger.info("🔐 Obtendo credenciais do Google...")
            creds = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=SCOPES
            )
            self.logger.info("✅ Credenciais obtidas com sucesso")
            return creds
        except FileNotFoundError:
            self.logger.critical(f"Arquivo de credenciais não encontrado: {self.service_account_file}")
            raise
        except Exception as e:
            self.logger.error(f"Falha ao obter credenciais: {e}")
            raise
    
    @tenacity_retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _build_sheets_service(self):
        """Constrói o serviço de Google Sheets com retry."""
        try:
            self.logger.debug("Construindo serviço Google Sheets...")
            return build('sheets', 'v4', credentials=self.credentials)
        except Exception as e:
            self.logger.error(f"Falha ao construir serviço Sheets: {e}")
            raise
    
    @tenacity_retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _build_calendar_service(self):
        """Constrói o serviço de Google Calendar com retry."""
        try:
            self.logger.debug("Construindo serviço Google Calendar...")
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
    
    @tenacity_retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=20),
        retry=retry_if_exception_type((HttpError, TimeoutError))
    )
    def read_from_sheet(self, spreadsheet_id: str) -> pd.DataFrame:
        """Lê dados de uma planilha Google e retorna como DataFrame."""
        try:
            self.logger.info(f"📖 Lendo planilha {spreadsheet_id[:15]}...")
            range_name = 'A1:I1502'
            sheet = self.sheet_service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            data = result.get('values', [])
            if not data:
                self.logger.warning("Planilha vazia")
                return pd.DataFrame()
            
            headers = data[0]
            values = data[1:] if len(data) > 1 else []
            df = pd.DataFrame(values, columns=headers)
            self.logger.info(f"✅ {len(df)} registros lidos da planilha")
            return df
        
        except HttpError as e:
            self.logger.error(f"Erro HTTP ao ler planilha: {e}")
            self.notifier.send(f"Erro ao acessar planilha Google. Verifique permissões. Erro: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Falha ao ler planilha {spreadsheet_id}: {e}")
            self.notifier.send(f"O sistema não conseguiu ler a planilha. Erro: {e}")
            return pd.DataFrame()
    
    @tenacity_retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=20)
    )
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
            self.logger.debug(f"🧹 Limpando planilha {spreadsheet_id[:15]}...")
            self.sheet_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, 
                body=request
            ).execute()
            self.logger.debug("✅ Planilha limpa")
        except Exception as e:
            self.logger.error(f"Falha ao limpar planilha {spreadsheet_id}: {e}")
            self.notifier.send(f"O sistema não conseguiu limpar a planilha. Erro: {e}")
            raise
    
    @tenacity_retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    def write_to_sheet(self, dataframe: pd.DataFrame, spreadsheet_id: str) -> None:
        """Escreve um DataFrame em uma planilha Google."""
        if dataframe.empty:
            self.logger.error("Tentativa de escrever DataFrame vazio na planilha")
            self.notifier.send("Tentativa de escrever dados vazios na planilha. Verifique o código.")
            return
        
        try:
            self.logger.info(f"✍️ Escrevendo {len(dataframe)} registros na planilha...")
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
            
            self.logger.info(f"✅ Dados escritos com sucesso na planilha")
        
        except Exception as e:
            self.logger.error(f"Falha ao escrever na planilha {spreadsheet_id}: {e}")
            self.notifier.send(
                f"O sistema não conseguiu gravar as datas de audiências na planilha. Erro: {e}"
            )
            raise
    
    @tenacity_retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    def append_to_sheet(self, dataframe: pd.DataFrame, spreadsheet_id: str) -> None:
        """Adiciona dados de um DataFrame ao final de uma planilha Google."""
        if dataframe.empty:
            return
        
        try:
            self.logger.info(f"➕ Adicionando {len(dataframe)} registros à planilha...")
            range_name = f'A1:I{len(dataframe) + 1}'
            values = dataframe.values.tolist()
            data = {'values': values}
            
            self.sheet_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                body=data,
                range=range_name,
                valueInputOption='RAW'
            ).execute()
            
            self.logger.info(f"✅ Dados adicionados com sucesso")
        
        except Exception as e:
            self.logger.error(f"Falha ao adicionar dados à planilha {spreadsheet_id}: {e}")
            self.notifier.send(
                f"O sistema não conseguiu adicionar novos dados à planilha. Erro: {e}"
            )
            raise


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
    
    @tenacity_retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    def get_event_summaries(self, calendar_id: str) -> List[str]:
        """Recupera uma lista de resumos de eventos do calendário."""
        try:
            self.logger.debug("📅 Listando eventos do calendário...")
            # Período para busca: de ontem até o futuro
            current_datetime = datetime.utcnow()
            one_day = timedelta(days=1)
            previous_datetime = current_datetime - one_day
            previous_datetime_str = previous_datetime.isoformat() + 'Z'
            
            events_result = self.calendar_service.events().list(
                calendarId=calendar_id,
                timeMin=previous_datetime_str,
                singleEvents=True,
                maxResults=2500
            ).execute()
            
            events = events_result.get('items', [])
            self.logger.debug(f"✅ {len(events)} eventos encontrados no calendário")
            return [event['summary'] for event in events]
        
        except Exception as e:
            self.logger.error(f"Falha ao listar eventos do calendário: {e}")
            self.notifier.send(f"O sistema não conseguiu listar os eventos do calendário. Erro: {e}")
            return []
    
    @tenacity_retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    def create_event(self, row_values: List[str], calendar_id: str) -> None:
        """Cria um evento de audiência no calendário."""
        try:
            date_str = f'{row_values[0]} {row_values[1]}'
            start_date_obj = datetime.strptime(date_str, '%d/%m/%Y %H:%M:%S')
            end_date_obj = start_date_obj + timedelta(hours=1)
            
            event_summary = f'{row_values[6]} - {row_values[3]} x {row_values[4]} {row_values[0]} às {row_values[1]} - {row_values[5]}'
            
            event = {
                'summary': event_summary,
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
            
            self.logger.debug(f"📅 Evento criado: {event_summary[:60]}...")
        
        except Exception as e:
            self.logger.error(f"Falha ao criar evento no calendário: {e}")
            raise
    
    @tenacity_retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    def delete_event(self, event_id: str, calendar_id: str) -> None:
        """Remove um evento do calendário."""
        try:
            self.calendar_service.events().delete(
                calendarId=calendar_id, 
                eventId=event_id
            ).execute()
            self.logger.debug(f"🗑️ Evento {event_id} removido")
        
        except HttpError as e:
            if e.resp.status == 404:
                self.logger.warning(f"Evento {event_id} já foi removido")
            else:
                self.logger.error(f"Falha ao remover evento {event_id}: {e}")
                raise
    
    @tenacity_retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    def find_events_by_summary(self, summary: str, calendar_id: str) -> List[Dict]:
        """Busca eventos no calendário pelo resumo/título."""
        try:
            events_result = self.calendar_service.events().list(
                calendarId=calendar_id,
                q=summary,
                maxResults=50
            ).execute()
            
            return events_result.get('items', [])
        
        except Exception as e:
            self.logger.error(f"Falha ao buscar eventos com resumo '{summary}': {e}")
            return []
    
    def populate_calendar(self, dataframe: pd.DataFrame, calendar_id: str) -> None:
        """Popula o calendário com eventos baseados nos dados do DataFrame."""
        if dataframe.empty:
            self.logger.error("Tentativa de popular calendário com DataFrame vazio")
            self.notifier.send("Tentativa de popular calendário com dados vazios. Verifique o código.")
            return
        
        self.logger.info(f"📅 Sincronizando {len(dataframe)} audiências com o calendário...")
        event_summaries = self.get_event_summaries(calendar_id)
        created_count = 0
        
        for _, row in dataframe.iterrows():
            row_values = row.values
            event_summary = f'{row_values[6]} - {row_values[3]} x {row_values[4]} {row_values[0]} às {row_values[1]} - {row_values[5]}'
            
            if event_summary not in event_summaries:
                self.create_event(row_values, calendar_id)
                created_count += 1
        
        self.logger.info(f"✅ {created_count} novos eventos criados no calendário")
    
    def handle_changed_events(self, diff_dataframe: pd.DataFrame, calendar_id: str) -> None:
        """Gerencia eventos que tiveram alterações (exclusão de antigos, criação de novos)."""
        if diff_dataframe.empty:
            return
        
        self.logger.info(f"🔄 Processando {len(diff_dataframe)} audiências alteradas...")
        
        for _, row in diff_dataframe.iterrows():
            row_values = row.values
            event_summary = f'{row_values[6]} - {row_values[3]} x {row_values[4]} {row_values[0]} às {row_values[1]} - {row_values[5]}'
            
            events = self.find_events_by_summary(event_summary, calendar_id)
            
            if not events:
                self.logger.warning(f"⚠️ Evento não encontrado para exclusão: '{event_summary[:60]}...'")
                self.notifier.send(
                    f'O sistema não conseguiu encontrar e deletar o evento: "{event_summary}". '
                    f'Verifique manualmente se o evento existe.'
                )
            else:
                for event in events:
                    event_id = event['id']
                    self.delete_event(event_id, calendar_id)
                    self.notifier.send(
                        f'⚠️ ATENÇÃO: O evento de título "{event_summary}" sofreu uma alteração. '
                        f'Favor comunicar ao cliente.'
                    )


class CourtSession:
    """Gerenciador de sessão para acesso aos tribunais com suporte a 2FA."""
    
    def __init__(
        self,
        tribunal_name: str,
        logger: Optional[HearingLogger] = None,
        notifier: Optional[EmailNotifier] = None
    ) -> None:
        """Inicializa o gerenciador de sessão com headers padrão."""
        self.tribunal_name = tribunal_name
        self.session = requests.Session()
        self.logger = logger or HearingLogger()
        self.notifier = notifier or EmailNotifier()
        self.token_cache = TokenCache(logger=self.logger)
        self._set_headers()
        
    def _set_headers(self) -> None:
        """Define headers padrão para a sessão."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session.headers.update(headers)
    
    def login_interactive(self, login_url: str, timeout: int = 300) -> bool:
        """
        Realiza login interativo no sistema do tribunal com suporte a 2FA.
        
        Abre o navegador Chrome de forma visível para que o usuário possa:
        1. Inserir credenciais manualmente
        2. Completar o segundo fator de autenticação (2FA)
        3. Aguarda até que o login seja concluído
        4. Captura e salva os cookies/tokens para uso posterior
        
        Args:
            login_url: URL da página de login do tribunal
            timeout: Tempo máximo em segundos para aguardar o login (padrão: 300s = 5 minutos)
            
        Returns:
            bool: True se o login foi bem-sucedido, False caso contrário
        """
        # Tenta carregar tokens do cache primeiro
        cached_cookies = self.token_cache.load_tokens(self.tribunal_name)
        if cached_cookies:
            self.logger.info(f"🔑 Usando tokens em cache para {self.tribunal_name}")
            for cookie in cached_cookies:
                self.session.cookies.set(
                    cookie['name'],
                    cookie['value'],
                    domain=cookie.get('domain', '')
                )
            # Valida se os tokens ainda funcionam
            if self._validate_session():
                return True
            else:
                self.logger.warning("⚠️ Tokens em cache inválidos, realizando novo login")
                self.token_cache.clear_tokens(self.tribunal_name)
        
        try:
            self.logger.info(f"🌐 Iniciando login interativo para {self.tribunal_name}")
            self.logger.info(f"🔗 URL: {login_url}")
            
            # Configuração do Chrome - MODO VISÍVEL para interação manual
            chrome_opts = ChromeOptions()
            # Removido --headless para permitir interação visual
            chrome_opts.add_argument("--start-maximized")
            chrome_opts.add_argument("--disable-blink-features=AutomationControlled")
            chrome_opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_opts.add_experimental_option('useAutomationExtension', False)
            
            # User agent realista
            chrome_opts.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Instala e configura o ChromeDriver automaticamente
            chromedriver_autoinstaller.install()
            
            driver = webdriver.Chrome(options=chrome_opts)
            
            try:
                # Abre a página de login
                driver.get(login_url)
                self.logger.info(f"✅ Página de login carregada: {login_url}")
                
                # Instruções para o usuário
                print("\n" + "="*80)
                print("🔐 AUTENTICAÇÃO INTERATIVA NECESSÁRIA")
                print("="*80)
                print(f"📌 Tribunal: {self.tribunal_name}")
                print(f"🌐 URL: {login_url}")
                print("\n📋 INSTRUÇÕES:")
                print("  1. Uma janela do Chrome foi aberta")
                print("  2. Faça login MANUALMENTE no sistema do tribunal")
                print("  3. Complete o segundo fator de autenticação (2FA) se solicitado")
                print("  4. Aguarde até estar completamente logado")
                print("  5. O sistema detectará automaticamente quando o login for concluído")
                print(f"\n⏱️  Tempo máximo: {timeout} segundos")
                print("="*80 + "\n")
                
                # Aguarda o usuário completar o login
                # Detecta quando sai da página de login/openid
                start_time = time.time()
                logged_in = False
                
                while time.time() - start_time < timeout:
                    current_url = driver.current_url.lower()
                    
                    # Verifica se saiu das páginas de login
                    if 'login' not in current_url and 'openid' not in current_url and 'auth' not in current_url:
                        # Verifica se tem cookies de sessão
                        cookies = driver.get_cookies()
                        if cookies and len(cookies) > 0:
                            self.logger.info("✅ Login detectado com sucesso!")
                            logged_in = True
                            break
                    
                    time.sleep(2)  # Verifica a cada 2 segundos
                
                if not logged_in:
                    raise TimeoutException(f"Tempo esgotado aguardando login ({timeout}s)")
                
                # Captura todos os cookies
                cookies = driver.get_cookies()
                self.logger.info(f"🍪 Capturados {len(cookies)} cookies")
                
                # Adiciona cookies à sessão requests
                for cookie in cookies:
                    self.session.cookies.set(
                        cookie['name'],
                        cookie['value'],
                        domain=cookie.get('domain', '')
                    )
                
                # Salva tokens no cache para uso futuro
                self.token_cache.save_tokens(self.tribunal_name, cookies)
                
                print("\n✅ Login concluído com sucesso!")
                print("💾 Tokens salvos para uso futuro\n")
                
                return True
                
            finally:
                # Fecha o navegador
                driver.quit()
                
        except TimeoutException:
            msg = f"⏱️ Tempo esgotado aguardando login em {self.tribunal_name}"
            self.logger.error(msg, exc_info=False)
            self.notifier.send(f"Timeout no login de {self.tribunal_name}. O usuário não completou o login a tempo.")
            return False
            
        except WebDriverException as e:
            msg = f"❌ Erro no WebDriver ao autenticar em {self.tribunal_name}: {e}"
            self.logger.error(msg)
            self.notifier.send(f"Erro no navegador ao tentar login em {self.tribunal_name}. Verifique se o Chrome está instalado.")
            return False
            
        except Exception as e:
            msg = f"❌ Erro inesperado ao autenticar em {self.tribunal_name}: {e}"
            self.logger.error(msg)
            self.notifier.send(f"Falha no login de {self.tribunal_name}. Erro: {e}")
            return False
    
    def _validate_session(self) -> bool:
        """Valida se a sessão atual ainda está ativa."""
        try:
            # Tenta fazer uma requisição simples para verificar se está autenticado
            # Ajuste a URL conforme necessário para o seu caso
            test_url = f"https://pje.{self.tribunal_name.lower()}.jus.br/primeirograu/"
            response = self.session.get(test_url, timeout=10, allow_redirects=False)
            
            # Se retornar 200 ou 302 (não 401/403), considera válido
            if response.status_code in [200, 302]:
                self.logger.debug(f"✅ Sessão válida para {self.tribunal_name}")
                return True
            else:
                self.logger.debug(f"❌ Sessão inválida (status {response.status_code})")
                return False
        except Exception as e:
            self.logger.debug(f"❌ Erro ao validar sessão: {e}")
            return False
    
    @tenacity_retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=20),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
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
        """Realiza busca de audiências na API do tribunal com retry automático."""
        params = {
            'dataFim': search_end_date,
            'dataInicio': search_start_date,
            'codigoSituacao': situation_code,
            'numeroPagina': page_number,
            'tamanhoPagina': results_per_page,
            'ordenacao': order
        }
        
        try:
            self.logger.debug(f"🔍 Buscando audiências: {search_start_date} a {search_end_date}")
            response = self.session.get(api_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            total = len(data.get('resultado', []))
            self.logger.debug(f"✅ {total} audiências encontradas")
            
            return data
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [401, 403]:
                self.logger.error(f"❌ Não autenticado. Limpando tokens...")
                self.token_cache.clear_tokens(self.tribunal_name)
            self.logger.error(f"Erro HTTP na API {api_url}: {e}")
            raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na requisição à API {api_url}: {e}")
            raise


class HearingDataProcessor:
    """Processador de dados de audiências."""
    
    def __init__(self, logger: Optional[HearingLogger] = None):
        """Inicializa o processador."""
        self.logger = logger or HearingLogger()
    
    def json_to_dataframe(self, json_data: Union[Dict, List[Dict]]) -> pd.DataFrame:
        """Converte dados JSON de audiências para DataFrame."""
        if not json_data or 'resultado' not in json_data:
            self.logger.warning("JSON vazio ou sem campo 'resultado'")
            return pd.DataFrame()
        
        try:
            # Cria DataFrame a partir dos dados normalizados
            dataframe = pd.DataFrame(pd.json_normalize(json_data['resultado']))
            
            if dataframe.empty:
                self.logger.debug("DataFrame vazio após normalização")
                return pd.DataFrame()
            
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
            missing_cols = [col for col in columns if col not in dataframe.columns]
            if missing_cols:
                self.logger.warning(f"Colunas ausentes: {missing_cols}")
                # Cria colunas vazias para as que estão faltando
                for col in missing_cols:
                    dataframe[col] = None
            
            dataframe = dataframe[columns]
            
            # Formata a data para o padrão brasileiro
            if 'dataInicio' in dataframe.columns:
                dataframe['dataInicio'] = pd.to_datetime(dataframe['dataInicio'], errors='coerce')
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
            
            # Remove linhas com valores nulos em campos críticos
            dataframe = dataframe.dropna(subset=['Data da Audiência', 'Número do Processo'])
            
            self.logger.debug(f"✅ DataFrame processado: {len(dataframe)} registros válidos")
            return dataframe
            
        except Exception as e:
            self.logger.error(f"Erro ao processar dados JSON: {e}")
            return pd.DataFrame()
    
    def find_changed_hearings(self, new_df: pd.DataFrame, old_df: pd.DataFrame) -> pd.DataFrame:
        """Identifica audiências que tiveram alterações."""
        if new_df.empty or old_df.empty:
            self.logger.debug("DataFrames vazios - sem alterações para detectar")
            return pd.DataFrame()
        
        self.logger.info("🔍 Procurando audiências alteradas...")
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
        
        if not result.empty:
            self.logger.info(f"⚠️ Encontradas {len(result)} audiências alteradas")
        else:
            self.logger.info("✅ Nenhuma alteração detectada")
            
        return result
    
    def combine_and_sort_dataframes(self, df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """Combina dois DataFrames e ordena por data de audiência."""
        if df1.empty:
            return df2.copy() if not df2.empty else pd.DataFrame()
        if df2.empty:
            return df1.copy()
        
        try:
            # Converte datas para datetime para ordenação correta
            df1_copy = df1.copy()
            df2_copy = df2.copy()
            
            df1_copy['Data da Audiência'] = pd.to_datetime(
                df1_copy['Data da Audiência'], 
                format='%d/%m/%Y',
                errors='coerce'
            )
            df2_copy['Data da Audiência'] = pd.to_datetime(
                df2_copy['Data da Audiência'], 
                format='%d/%m/%Y',
                errors='coerce'
            )
            
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
            
            self.logger.debug(f"✅ DataFrames combinados: {len(combined_df)} registros únicos")
            return combined_df
            
        except Exception as e:
            self.logger.error(f"Erro ao combinar DataFrames: {e}")
            return pd.DataFrame()


class HearingManager:
    """Gerenciador principal do sistema de audiências."""
    
    def __init__(self) -> None:
        """Inicializa o gerenciador com todos os componentes necessários."""
        self.logger = HearingLogger()
        self.logger.info("="*80)
        self.logger.info("🚀 INICIANDO SISTEMA DE GERENCIAMENTO DE AUDIÊNCIAS v2.0")
        self.logger.info("="*80)
        
        # Valida configurações
        if not Config.validate():
            raise ValueError("Configurações inválidas. Verifique o arquivo .env")
        
        self.notifier = EmailNotifier(logger=self.logger)
        self.services = GoogleServicesManager(logger=self.logger)
        self.sheets = GoogleSheetsManager(self.services, self.notifier, self.logger)
        self.calendar = GoogleCalendarManager(self.services, self.notifier, self.logger)
        self.processor = HearingDataProcessor(self.logger)
        
        # Sessões dos tribunais
        self.trt2_session = CourtSession('TRT2', self.logger, self.notifier)
        self.trt15_session = CourtSession('TRT15', self.logger, self.notifier)
    
    def _authenticate_with_courts(self) -> bool:
        """Autentica com os sistemas dos tribunais usando login interativo."""
        self.logger.info("🔐 Iniciando autenticação nos tribunais...")
        
        # TRT2
        self.logger.info("\n" + "="*80)
        self.logger.info("📍 AUTENTICAÇÃO TRT2")
        self.logger.info("="*80)
        trt2_success = self.trt2_session.login_interactive(
            'https://pje.trt2.jus.br/primeirograu/login.seam'
        )
        
        if not trt2_success:
            self.logger.error("❌ Falha na autenticação do TRT2")
            return False
        
        # TRT15
        self.logger.info("\n" + "="*80)
        self.logger.info("📍 AUTENTICAÇÃO TRT15")
        self.logger.info("="*80)
        trt15_success = self.trt15_session.login_interactive(
            'https://pje.trt15.jus.br/primeirograu/login.seam'
        )
        
        if not trt15_success:
            self.logger.error("❌ Falha na autenticação do TRT15")
            return False
        
        self.logger.info("\n✅ Autenticação concluída com sucesso em ambos os tribunais")
        return True
    
    def _get_current_hearings(self, court_domain: str, session: CourtSession) -> pd.DataFrame:
        """Obtém audiências atuais de um tribunal específico."""
        try:
            self.logger.info(f"📥 Buscando audiências atuais no {court_domain}...")
            
            year = datetime.now().year
            today = datetime.now().strftime("%Y-%m-%d")
            
            api_url = f'https://{court_domain}/pje-comum-api/api/pauta-usuarios-externos'
            
            response_json = session.search_hearings(
                api_url=api_url,
                search_start_date=today,
                search_end_date=f'{year}-12-31'
            )
            
            df = self.processor.json_to_dataframe(response_json)
            self.logger.info(f"✅ {len(df)} audiências obtidas de {court_domain}")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter audiências de {court_domain}: {e}")
            self.notifier.send(
                f"Falha ao obter audiências atuais de {court_domain}. Erro: {e}"
            )
            return pd.DataFrame()
    
    def _get_future_hearings(self, court_domain: str, session: CourtSession, year: int) -> pd.DataFrame:
        """Obtém audiências futuras de um tribunal específico para um ano específico."""
        try:
            self.logger.info(f"📥 Buscando audiências de {year} no {court_domain}...")
            
            api_url = f'https://{court_domain}/pje-comum-api/api/pauta-usuarios-externos'
            
            response_json = session.search_hearings(
                api_url=api_url,
                search_start_date=f'{year}-01-01',
                search_end_date=f'{year}-12-31'
            )
            
            df = self.processor.json_to_dataframe(response_json)
            self.logger.info(f"✅ {len(df)} audiências obtidas de {court_domain} ({year})")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter audiências futuras de {court_domain}/{year}: {e}")
            self.notifier.send(
                f"Falha ao obter audiências futuras de {court_domain} para {year}. Erro: {e}"
            )
            return pd.DataFrame()
    
    def process_hearings(self) -> None:
        """Processo principal de obtenção e processamento de audiências."""
        start_time = time.time()
        self.logger.info("🏁 Iniciando rotina de processamento de audiências...")
        
        try:
            # 1. Autenticação com os tribunais
            if not self._authenticate_with_courts():
                self.logger.critical("❌ Falha na autenticação. Encerrando processamento.")
                return
            
            # 2. Obtenção de audiências atuais
            self.logger.info("\n" + "="*80)
            self.logger.info("📊 FASE 1: COLETA DE AUDIÊNCIAS ATUAIS")
            self.logger.info("="*80)
            
            trt2_hearings = self._get_current_hearings('pje.trt2.jus.br', self.trt2_session)
            trt15_hearings = self._get_current_hearings('pje.trt15.jus.br', self.trt15_session)
            
            # 3. Combinação das audiências atuais
            current_hearings = self.processor.combine_and_sort_dataframes(
                trt2_hearings, trt15_hearings
            )
            self.logger.info(f"📊 Total de audiências atuais: {len(current_hearings)}")
            
            # 4. Obtenção de audiências futuras
            self.logger.info("\n" + "="*80)
            self.logger.info("📊 FASE 2: COLETA DE AUDIÊNCIAS FUTURAS")
            self.logger.info("="*80)
            
            current_year = datetime.now().year
            all_hearings = current_hearings.copy()
            
            # Busca audiências para os próximos 3 anos
            for year in range(current_year + 1, current_year + 4):
                self.logger.info(f"\n📅 Processando ano: {year}")
                
                # TRT2
                future_trt2 = self._get_future_hearings('pje.trt2.jus.br', self.trt2_session, year)
                all_hearings = self.processor.combine_and_sort_dataframes(
                    all_hearings, future_trt2
                )
                
                # TRT15
                future_trt15 = self._get_future_hearings('pje.trt15.jus.br', self.trt15_session, year)
                all_hearings = self.processor.combine_and_sort_dataframes(
                    all_hearings, future_trt15
                )
            
            self.logger.info(f"\n📊 Total geral de audiências: {len(all_hearings)}")
            
            # 5. Identificação de audiências com alterações
            self.logger.info("\n" + "="*80)
            self.logger.info("📊 FASE 3: DETECÇÃO DE ALTERAÇÕES")
            self.logger.info("="*80)
            
            old_hearings = self.sheets.read_from_sheet(Config.ACTUAL_HEARING_SPREADSHEET_ID)
            changed_hearings = self.processor.find_changed_hearings(all_hearings, old_hearings)
            
            if not changed_hearings.empty:
                self.logger.info(f"⚠️ Detectadas {len(changed_hearings)} audiências com alterações")
                self.sheets.append_to_sheet(changed_hearings, Config.CHANGED_HEARING_SPREADSHEET_ID)
                self.calendar.handle_changed_events(changed_hearings, Config.CALENDAR_ID)
            else:
                self.logger.info("✅ Nenhuma alteração detectada")
            
            # 6. Atualização da planilha principal
            self.logger.info("\n" + "="*80)
            self.logger.info("📊 FASE 4: ATUALIZAÇÃO DE PLANILHAS E CALENDÁRIO")
            self.logger.info("="*80)
            
            self.sheets.write_to_sheet(all_hearings, Config.ACTUAL_HEARING_SPREADSHEET_ID)
            
            # 7. Atualização do calendário
            self.calendar.populate_calendar(all_hearings, Config.CALENDAR_ID)
            
            # Finalização
            elapsed_time = time.time() - start_time
            self.logger.info("\n" + "="*80)
            self.logger.info(f"✅ ROTINA CONCLUÍDA COM SUCESSO")
            self.logger.info(f"⏱️  Tempo total: {elapsed_time:.2f} segundos")
            self.logger.info("="*80 + "\n")
            
        except Exception as e:
            self.logger.critical(f"❌ Erro crítico no processamento: {e}")
            self.notifier.send(f"ERRO CRÍTICO no processamento de audiências: {e}")
            raise


def main() -> None:
    """Função principal de execução do programa."""
    try:
        manager = HearingManager()
        manager.process_hearings()
    except Exception as e:
        logger = HearingLogger()
        notifier = EmailNotifier()
        error_message = f"❌ Erro crítico na execução do programa: {e}"
        logger.critical(error_message)
        notifier.send(error_message)
        sys.exit(1)


if __name__ == '__main__':
    main()
