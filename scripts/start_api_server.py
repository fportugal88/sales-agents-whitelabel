"""Script para iniciar o servidor FastAPI."""

import os
import socket
import sys
from typing import Tuple
import uvicorn

from src.config.settings import get_settings
from src.utils.logger import configure_logging


def get_port_from_process(port: int) -> str:
    """Try to identify which process is using the port (Windows)."""
    try:
        import subprocess
        # Try to find process using netstat (Windows)
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=2
        )
        for line in result.stdout.split('\n'):
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) > 4:
                    pid = parts[-1]
                    try:
                        # Try to get process name
                        task_result = subprocess.run(
                            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        if task_result.stdout:
                            proc_name = task_result.stdout.split(',')[0].strip('"')
                            return f"PID {pid} ({proc_name})"
                    except:
                        pass
                    return f"PID {pid}"
    except Exception:
        pass
    return "processo desconhecido"


def is_port_available(port: int) -> Tuple[bool, str]:
    """Check if port is available and return status with process info if occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True, ""
        except OSError as e:
            process_info = get_port_from_process(port)
            return False, process_info


def find_available_port(start_port: int, max_attempts: int = 5) -> Tuple[int, str]:
    """Find an available port starting from start_port."""
    for i in range(max_attempts):
        port = start_port + i
        available, process_info = is_port_available(port)
        if available:
            return port, ""
        if i == 0:
            # Only show process info for the first port
            return port, process_info
    return None, ""


if __name__ == "__main__":
    configure_logging()
    
    try:
        settings = get_settings()
    except Exception as e:
        print("=" * 60)
        print("❌ ERRO DE CONFIGURAÇÃO")
        print("=" * 60)
        print(f"Erro: {str(e)}")
        print("\nPor favor, verifique:")
        print("1. O arquivo .env existe e está configurado corretamente")
        print("2. A variável OPENAI_API_KEY está definida")
        print("3. As outras configurações estão corretas")
        print("=" * 60)
        sys.exit(1)

    print("=" * 60)
    print("Sales Agents API Server")
    print("=" * 60)

    # Determine port - check environment variable first, then settings, then default
    default_port = 8000
    if settings.server_port:
        default_port = settings.server_port
    elif os.getenv("SERVER_PORT"):
        try:
            default_port = int(os.getenv("SERVER_PORT"))
        except ValueError:
            print(f"⚠️  SERVER_PORT inválido, usando porta padrão {default_port}")

    # Check if default port is available
    available, process_info = is_port_available(default_port)
    
    if not available:
        print(f"⚠️  Porta {default_port} está ocupada", end="")
        if process_info:
            print(f" por {process_info}")
        else:
            print()
        
        # Try to find alternative port
        alt_port, _ = find_available_port(8004, max_attempts=3)
        if alt_port and is_port_available(alt_port)[0]:
            print(f"✅ Usando porta alternativa: {alt_port}")
            port = alt_port
        else:
            print("❌ Não foi possível encontrar uma porta disponível.")
            print(f"\nSugestões:")
            print(f"1. Encerre o processo usando a porta {default_port}")
            if process_info:
                print(f"   Processo: {process_info}")
            print(f"2. Ou defina SERVER_PORT no .env para usar outra porta")
            print(f"   Exemplo: SERVER_PORT=8005")
            sys.exit(1)
    else:
        port = default_port
        print(f"✅ Usando porta {port}")

    print(f"📡 Servidor iniciando em http://localhost:{port}")
    print(f"📚 Documentação disponível em http://localhost:{port}/docs")
    print("=" * 60)
    
    try:
        uvicorn.run(
            "src.api.server:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor encerrado pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro ao iniciar servidor: {str(e)}")
        sys.exit(1)

