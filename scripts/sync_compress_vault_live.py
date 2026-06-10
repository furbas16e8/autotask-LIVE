"""
sync_compress_vault_live.py
───────────────────────────
Backup automatizado do Obsidian Vault com criptografia AES-256 (7z) (VERSÃO TESTE LIVE).
"""

import sys
import logging
import getpass
import re
from datetime import date
from pathlib import Path

try:
    import py7zr
except ImportError:
    print("\n[!] Erro: A biblioteca 'py7zr' nao esta instalada.")
    print("Por favor, execute o comando abaixo para instalar as dependencias:")
    print("    pip install -r requirements.txt\n")
    sys.exit(1)


# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────

VAULT_PATH  = Path.home() / "Documents" / "ObsidianMD" / "life-and-thoughts"
BACKUP_DIR  = Path.home() / "Documents" / "backups" / "obsidian"

BASE_PASSWORD = "Gillettemouse3#"
ANCHOR_DATE   = date(2021, 6, 12)

MAX_BACKUPS = 50
# ──────────────────────────────────────────────────────────────────────────────


def build_password(backup_date: date) -> str:
    delta = (backup_date - ANCHOR_DATE).days
    if delta < 0:
        raise ValueError(
            f"A data âncora ({ANCHOR_DATE}) é posterior à data do backup ({backup_date})."
        )
    return f"{BASE_PASSWORD}{delta}"


def backup_filename(backup_date: date) -> str:
    return f"vault_{backup_date.strftime('%Y%m%d')}.7z"


def create_archive(archive_path: Path, password: str) -> None:
    with py7zr.SevenZipFile(
        archive_path,
        mode="w",
        password=password,
        header_encryption=True,
    ) as archive:
        archive.writeall(VAULT_PATH, arcname=VAULT_PATH.name)


def rotate_backups() -> None:
    existing = sorted(BACKUP_DIR.glob("vault_????????.7z"))
    excess = len(existing) - MAX_BACKUPS

    if excess <= 0:
        return

    for old_file in existing[:excess]:
        old_file.unlink()
        log(f"rotação     → removido: {old_file.name}")


def validate_config() -> None:
    errors = []

    if "caminho" in str(VAULT_PATH) or "caminho" in str(BACKUP_DIR):
        errors.append("VAULT_PATH e BACKUP_DIR não foram configurados.")
    if BASE_PASSWORD == "sua_senha_aqui":
        errors.append("BASE_PASSWORD não foi definida.")
    if ANCHOR_DATE == date(2020, 1, 1):
        errors.append("ANCHOR_DATE ainda está com o valor de exemplo — defina sua data âncora.")
    if not VAULT_PATH.exists():
        errors.append(f"VAULT_PATH não encontrado: {VAULT_PATH}")

    if errors:
        print("Erros de configuração encontrados:\n")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)


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
    log_file = log_dir / f"sync_compress_vault_live_{username}.log"

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


def log(message: str) -> None:
    logging.info(message)


def main() -> None:
    validate_config()
    setup_logging()

    today         = date.today()
    filename      = backup_filename(today)
    archive_path  = BACKUP_DIR / filename
    password      = build_password(today)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if archive_path.exists():
        size_mb = archive_path.stat().st_size / (1024 ** 2)
        log(f"aviso       → arquivo do dia já existe: {filename} ({size_mb:.2f} MB)")
        log("             O backup não será sobrescrito. Delete o arquivo manualmente se necessário.")
        sys.exit(0)

    log(f"iniciando   → {filename}")
    log(f"origem      → {VAULT_PATH}")
    log(f"destino     → {archive_path}")

    try:
        create_archive(archive_path, password)
    except Exception as exc:
        if archive_path.exists():
            archive_path.unlink()
        log(f"erro        → falha ao criar o arquivo: {exc}")
        sys.exit(1)

    size_mb = archive_path.stat().st_size / (1024 ** 2)
    log(f"concluído   → Tamanho do arquivo comprimido: {size_mb:.2f} MB")

    rotate_backups()

    existing_count = len(list(BACKUP_DIR.glob("vault_????????.7z")))
    log(f"backups     → {existing_count}/{MAX_BACKUPS} arquivos mantidos")


if __name__ == "__main__":
    main()
