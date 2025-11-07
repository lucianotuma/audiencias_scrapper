"""
Script de teste para validar a configuração do sistema.
Execute este script antes de usar o sistema principal.
"""

import os
import sys
from pathlib import Path

def print_header(text):
    """Imprime cabeçalho formatado."""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def print_status(item, status, details=""):
    """Imprime status de um item."""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {item}", end="")
    if details:
        print(f" - {details}")
    else:
        print()

def check_python_version():
    """Verifica versão do Python."""
    print_header("VERIFICANDO PYTHON")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    is_ok = version.major >= 3 and version.minor >= 8
    print_status(f"Python {version_str}", is_ok, "Mínimo: 3.8")
    return is_ok

def check_dependencies():
    """Verifica se as dependências estão instaladas."""
    print_header("VERIFICANDO DEPENDÊNCIAS")
    
    required_packages = [
        'pandas',
        'requests',
        'dotenv',
        'google',
        'selenium',
        'tenacity',
        'webdriver_manager'
    ]
    
    all_ok = True
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_status(package, True)
        except ImportError:
            print_status(package, False, "NÃO INSTALADO")
            all_ok = False
    
    if not all_ok:
        print("\n⚠️  Execute: pip install -r requirements.txt")
    
    return all_ok

def check_env_file():
    """Verifica se o arquivo .env existe e está configurado."""
    print_header("VERIFICANDO ARQUIVO .ENV")
    
    env_file = Path('.env')
    
    if not env_file.exists():
        print_status("Arquivo .env", False, "NÃO ENCONTRADO")
        print("\n⚠️  Execute: Copy-Item .env.example .env")
        return False
    
    print_status("Arquivo .env", True, "ENCONTRADO")
    
    # Carrega e verifica variáveis
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        'TRT_USERNAME': 'CPF de acesso aos tribunais',
        'TRT_PASSWORD': 'Senha de acesso aos tribunais',
        'EMAIL_SENDER': 'Email remetente (Gmail)',
        'EMAIL_PASSWORD': 'Senha de aplicativo do Gmail',
        'EMAIL_RECIPIENTS': 'Destinatários de notificações'
    }
    
    all_ok = True
    for var, description in required_vars.items():
        value = os.getenv(var, '').strip()
        is_set = bool(value)
        print_status(f"  {var}", is_set, description if not is_set else "")
        if not is_set:
            all_ok = False
    
    if not all_ok:
        print("\n⚠️  Edite o arquivo .env e preencha as variáveis obrigatórias")
    
    return all_ok

def check_google_credentials():
    """Verifica arquivo de credenciais do Google."""
    print_header("VERIFICANDO CREDENCIAIS GOOGLE")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    cred_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', './planilha-de-audiencias-25b5ec50e72f.json')
    file_path = Path(cred_file)
    
    exists = file_path.exists()
    print_status(f"Arquivo: {cred_file}", exists)
    
    if exists:
        print_status("  Tamanho do arquivo", file_path.stat().st_size > 100, 
                    f"{file_path.stat().st_size} bytes")
    else:
        print("\n⚠️  Certifique-se de que o arquivo de credenciais está no diretório")
    
    return exists

def check_chrome():
    """Verifica se o Chrome está instalado."""
    print_header("VERIFICANDO GOOGLE CHROME")
    
    # Locais comuns do Chrome no Windows
    chrome_paths = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]
    
    chrome_found = any(p.exists() for p in chrome_paths)
    print_status("Google Chrome", chrome_found)
    
    if not chrome_found:
        print("\n⚠️  Instale o Google Chrome: https://www.google.com/chrome/")
    
    return chrome_found

def main():
    """Executa todos os testes."""
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "TESTE DE CONFIGURAÇÃO DO SISTEMA" + " "*26 + "║")
    print("╚" + "="*78 + "╝")
    
    results = {
        'Python': check_python_version(),
        'Dependências': check_dependencies(),
        'Arquivo .env': check_env_file(),
        'Credenciais Google': check_google_credentials(),
        'Google Chrome': check_chrome()
    }
    
    print_header("RESUMO FINAL")
    
    all_passed = all(results.values())
    
    for item, status in results.items():
        print_status(item, status)
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ✅ ✅  CONFIGURAÇÃO COMPLETA - PRONTO PARA USAR!  ✅ ✅ ✅")
        print("\n▶️  Execute agora: python scrapper_refactored.py")
    else:
        print("❌ ❌ ❌  CONFIGURAÇÃO INCOMPLETA  ❌ ❌ ❌")
        print("\n🔧 Corrija os problemas acima antes de continuar")
    print("="*80 + "\n")
    
    return all_passed

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        sys.exit(1)
