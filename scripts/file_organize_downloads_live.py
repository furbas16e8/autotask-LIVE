"""
file_organize_downloads_live.py
───────────────────────────────
Organizador automático da pasta Downloads (VERSÃO TESTE LIVE).
Utiliza logs centralizados com o nome do usuário ativo e move os arquivos de forma segura.
"""

import sys
import os
import re
import getpass
import time
import shutil
import logging
from pathlib import Path

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────

CATEGORIAS = {
    "Documentos": {".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf"},
    "Imagens": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"},
    "Planilhas": {".csv", ".xls", ".xlsx", ".ods"},
    "Web": {".html", ".htm", ".json", ".xml"},
    "Scripts": {".py", ".sql", ".js", ".css", ".ts", ".jsx", ".tsx", ".pyw", ".sh", ".bat"},
    "Notebooks": {".ipynb"},
    "Aplicativos": {".exe", ".msi", ".apk"},
    "Compactados": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Livros": {".epub", ".mobi", ".azw"},
    "Áudios": {".mp3", ".wav", ".wma", ".flac", ".m4a", ".aac", ".ogg", ".mpeg"},
    "Vídeos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}
}

THRESHOLD_SEGUNDOS = 48 * 3600

DOWNLOADS_DIR = Path.home() / "Downloads"
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
# ──────────────────────────────────────────────────────────────────────────────


def obter_usuario_sanitizado() -> str:
    try:
        username = getpass.getuser()
    except Exception:
        username = "desconhecido"
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", username)


def configurar_logger(username_sufixo: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"file_organize_downloads_live_{username_sufixo}.log"

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


def testar_lock(file_path: Path) -> bool:
    try:
        with open(file_path, "r+b") as f:
            pass
        return True
    except (PermissionError, OSError):
        return False


def obter_nome_unico(destino_pasta: Path, nome_arquivo: str) -> Path:
    path_arquivo = destino_pasta / nome_arquivo
    if not path_arquivo.exists():
        return path_arquivo

    stem = path_arquivo.stem
    suffix = path_arquivo.suffix
    contador = 1

    while True:
        novo_nome = f"{stem}_{contador}{suffix}"
        novo_caminho = destino_pasta / novo_nome
        if not novo_caminho.exists():
            return novo_caminho
        contador += 1


def obter_tamanho_diretorio(caminho: Path) -> int:
    """Calcula recursivamente o tamanho de uma pasta em bytes."""
    tamanho_total = 0
    for root, _, files in os.walk(caminho):
        for f in files:
            fp = os.path.join(root, f)
            try:
                tamanho_total += os.path.getsize(fp)
            except OSError:
                pass
    return tamanho_total


def main() -> None:
    username = obter_usuario_sanitizado()
    configurar_logger(username)

    logging.info(f"=== Execução teste Live iniciada por {username} ===")

    if not DOWNLOADS_DIR.exists():
        logging.error(f"Erro: A pasta de Downloads '{DOWNLOADS_DIR}' não existe.")
        sys.exit(1)

    agora = time.time()
    arquivos_movidos = 0
    arquivos_ignorados = 0
    erros = 0

    for item in DOWNLOADS_DIR.iterdir():
        if not item.is_file():
            continue

        nome_arquivo = item.name
        extensao = item.suffix.lower()

        categoria_alvo = None
        for categoria, extensoes in CATEGORIAS.items():
            if extensao in extensoes:
                categoria_alvo = categoria
                break

        if not categoria_alvo:
            continue

        mtime = item.stat().st_mtime
        idade_segundos = agora - mtime
        if idade_segundos < THRESHOLD_SEGUNDOS:
            arquivos_ignorados += 1
            continue

        if not testar_lock(item):
            arquivos_ignorados += 1
            continue

        try:
            destino_dir = DOWNLOADS_DIR / categoria_alvo
            destino_dir.mkdir(parents=True, exist_ok=True)

            destino_final = obter_nome_unico(destino_dir, nome_arquivo)

            logging.info(f"Sucesso: {nome_arquivo} ➔ {categoria_alvo}")
            shutil.move(str(item), str(destino_final))
            arquivos_movidos += 1

        except Exception as e:
            logging.error(f"Erro ao mover '{nome_arquivo}' para '{categoria_alvo}':", exc_info=True)
            erros += 1

    logging.info(f"Finalizado teste Live. Movidos: {arquivos_movidos} | Ignorados: {arquivos_ignorados} | Erros: {erros}")

    # Exibe o tamanho final de cada pasta de categoria após a execução (recurso da v1.1.3)
    logging.info("Tamanho das pastas de destino:")
    for categoria in CATEGORIAS.keys():
        pasta_categoria = DOWNLOADS_DIR / categoria
        if pasta_categoria.is_dir():
            tamanho_bytes = obter_tamanho_diretorio(pasta_categoria)
            tamanho_mb = tamanho_bytes / (1024 * 1024)
            logging.info(f"  - {categoria}: {tamanho_mb:.2f} MB")


if __name__ == "__main__":
    main()
