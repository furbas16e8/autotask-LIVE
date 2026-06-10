"""
sys_clean_temp_live.py
──────────────────────
Limpeza de diretório Windows Temp (VERSÃO TESTE LIVE).
"""

import os
import sys
import shutil
import logging
import getpass
import re
from pathlib import Path

def obter_usuario_sanitizado() -> str:
    try:
        username = getpass.getuser()
    except Exception:
        username = "desconhecido"
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", username)


def setup_logging() -> None:
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    username = obter_usuario_sanitizado()
    log_file = log_dir / f"sys_clean_temp_live_{username}.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def obter_tamanho_diretorio(caminho) -> int:
    tamanho_total = 0
    for root, dirs, files in os.walk(caminho):
        for f in files:
            fp = os.path.join(root, f)
            if not os.path.islink(fp):
                try:
                    tamanho_total += os.path.getsize(fp)
                except OSError:
                    pass
    return tamanho_total


def limpar_temp(caminho):
    logging.info(f"Iniciando limpeza em: {caminho}")
    arquivos_removidos = 0
    erros = 0
    bytes_liberados = 0

    for item in os.listdir(caminho):
        item_caminho = os.path.join(caminho, item)
        
        try:
            tamanho_item = 0
            if os.path.isfile(item_caminho) or os.path.islink(item_caminho):
                if not os.path.islink(item_caminho):
                    tamanho_item = os.path.getsize(item_caminho)
                os.unlink(item_caminho)
                arquivos_removidos += 1
                bytes_liberados += tamanho_item
            elif os.path.isdir(item_caminho):
                tamanho_item = obter_tamanho_diretorio(item_caminho)
                shutil.rmtree(item_caminho)
                arquivos_removidos += 1
                bytes_liberados += tamanho_item
        except Exception:
            erros += 1
            continue

    mb_liberados = bytes_liberados / (1024 * 1024)
    logging.info(f"Limpeza concluída.")
    logging.info(f"Itens removidos: {arquivos_removidos}")
    logging.info(f"Espaço liberado: {mb_liberados:.2f} MB")
    logging.info(f"Itens ignorados (em uso): {erros}")


if __name__ == "__main__":
    setup_logging()
    caminho_temp = r"C:\Windows\Temp"
    
    try:
        limpar_temp(caminho_temp)
    except PermissionError:
        logging.error("ERRO: Este script precisa de privilégios de Administrador para limpar C:\\Windows\\Temp.")
