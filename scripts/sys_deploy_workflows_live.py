"""
sys_deploy_workflows_live.py
────────────────────────────
Sincronização de arquivos de workflows Markdown (.md) locais para a pasta global (VERSÃO TESTE LIVE).
"""

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
    # Mantém apenas caracteres alfanuméricos, hífen e sublinhado
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", username)


def setup_logging() -> None:
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    username = obter_usuario_sanitizado()
    log_file = log_dir / f"sys_deploy_workflows_live_{username}.log"

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


def resolver_caminho_origem() -> Path:
    """Resolve dinamicamente o caminho da pasta de workflows de origem, testando fallbacks (OneDrive)."""
    home = Path.home()
    
    # Caminhos candidatos no Windows
    candidatos = [
        home / "Documents" / "GitHub" / "workflows" / "workflows",
        home / "OneDrive" / "Documentos" / "GitHub" / "workflows" / "workflows",
        home / "OneDrive" / "Documents" / "GitHub" / "workflows" / "workflows",
    ]
    
    for caminho in candidatos:
        if caminho.is_dir():
            return caminho
            
    # Caso padrão se nenhum existir
    return candidatos[0]


def resolver_caminho_destino() -> Path:
    """Resolve dinamicamente o caminho da pasta global de workflows do Gemini."""
    return Path.home() / ".gemini" / "config" / "global_workflows"


def resolver_caminho_skills_origem() -> Path:
    """Resolve dinamicamente o caminho da pasta de skills de origem, testando fallbacks (OneDrive)."""
    home = Path.home()
    
    # Caminhos candidatos no Windows
    candidatos = [
        home / "Documents" / "GitHub" / "workflows" / "skills",
        home / "OneDrive" / "Documentos" / "GitHub" / "workflows" / "skills",
        home / "OneDrive" / "Documents" / "GitHub" / "workflows" / "skills",
    ]
    
    for caminho in candidatos:
        if caminho.is_dir():
            return caminho
            
    # Caso padrão se nenhum existir
    return candidatos[0]


def resolver_caminho_skills_destino() -> Path:
    """Resolve dinamicamente o caminho da pasta global de skills do Gemini."""
    return Path.home() / ".gemini" / "config" / "plugins" / "minhas-skills"


def obter_tamanho_diretorio_mb(diretorio: Path) -> float:
    """Calcula recursivamente o tamanho de todos os arquivos no diretório em MB."""
    total = 0
    if diretorio.is_dir():
        for item in diretorio.rglob("*"):
            if item.is_file():
                try:
                    total += item.stat().st_size
                except Exception:
                    pass
    return total / (1024 * 1024)


def copiar_arquivo_com_lock_check(origem: Path, destino: Path) -> int:
    """Testa se o arquivo está bloqueado e copia, retornando o tamanho em bytes."""
    # Se o destino já existe, testa se não está bloqueado
    if destino.exists():
        try:
            with open(destino, 'r+b') as f:
                pass
        except OSError as e:
            logging.error(f"Erro de travamento (Lock Check) ao acessar o destino '{destino.name}': {e}")
            raise PermissionError(f"Arquivo de destino bloqueado: {destino.name}")

    # Realiza a cópia preservando metadados
    shutil.copy2(origem, destino)
    return origem.stat().st_size


def deploy_workflows():
    # --- Parte 1: Workflows ---
    origem_dir = resolver_caminho_origem()
    destino_dir = resolver_caminho_destino()

    logging.info("Iniciando deploy de workflows globais (Teste Live).")
    logging.info(f"Origem resolvida: {origem_dir}")
    logging.info(f"Destino resolvido: {destino_dir}")

    total_bytes = 0

    if not origem_dir.is_dir():
        logging.error(f"Diretório de origem não encontrado: {origem_dir}")
    else:
        # Garante que a pasta de destino exista
        destino_dir.mkdir(parents=True, exist_ok=True)

        # Varre apenas arquivos .md na raiz da origem
        arquivos_md = list(origem_dir.glob("*.md"))
        
        if not arquivos_md:
            logging.info("Nenhum arquivo Markdown (.md) encontrado para copiar na pasta de origem de workflows.")
        else:
            arquivos_copiados = []
            erros = 0

            for arquivo in arquivos_md:
                destino_arquivo = destino_dir / arquivo.name
                try:
                    bytes_copiados = copiar_arquivo_com_lock_check(arquivo, destino_arquivo)
                    total_bytes += bytes_copiados
                    arquivos_copiados.append(arquivo.name)
                    kb_copiados = bytes_copiados / 1024
                    logging.info(f"Copiado: {arquivo.name} ({kb_copiados:.2f} KB)")
                except Exception as e:
                    logging.error(f"Falha ao copiar '{arquivo.name}': {e}")
                    erros += 1

            if erros > 0:
                logging.warning(f"Total de falhas (arquivos ignorados/bloqueados): {erros}")

    logging.info("Deploy de workflows (Teste Live) concluído.")
    tamanho_dest_workflows_mb = obter_tamanho_diretorio_mb(destino_dir)
    logging.info(f"Tamanho total da pasta de destino global_workflows: {tamanho_dest_workflows_mb:.2f} MB")

    # --- Parte 2: Skills ---
    origem_skills = resolver_caminho_skills_origem()
    destino_skills = resolver_caminho_skills_destino()

    logging.info("Iniciando deploy de skills (Teste Live).")
    logging.info(f"Origem resolvida (Skills): {origem_skills}")
    logging.info(f"Destino resolvido (Skills): {destino_skills}")

    if not origem_skills.is_dir():
        logging.error(f"Diretório de origem de skills não encontrado: {origem_skills}")
    else:
        # Garante que a pasta de destino exista
        destino_skills.mkdir(parents=True, exist_ok=True)

        # Varre todos os arquivos na origem de skills
        arquivos_skills = [p for p in origem_skills.glob("*") if p.is_file()]
        
        if not arquivos_skills:
            logging.info("Nenhum arquivo encontrado para copiar na pasta de origem de skills.")
        else:
            arquivos_copiados_skills = []
            erros_skills = 0

            for arquivo in arquivos_skills:
                destino_arquivo = destino_skills / arquivo.name
                try:
                    bytes_copiados = copiar_arquivo_com_lock_check(arquivo, destino_arquivo)
                    total_bytes += bytes_copiados
                    arquivos_copiados_skills.append(arquivo.name)
                    kb_copiados = bytes_copiados / 1024
                    logging.info(f"Copiado (Skill): {arquivo.name} ({kb_copiados:.2f} KB)")
                except Exception as e:
                    logging.error(f"Falha ao copiar skill '{arquivo.name}': {e}")
                    erros_skills += 1

            if erros_skills > 0:
                logging.warning(f"Total de falhas de skills (arquivos ignorados/bloqueados): {erros_skills}")

    logging.info("Deploy de skills (Teste Live) concluído.")
    tamanho_dest_skills_mb = obter_tamanho_diretorio_mb(destino_skills)
    logging.info(f"Tamanho total da pasta de destino minhas-skills: {tamanho_dest_skills_mb:.2f} MB")

    # Volume total copiado (Regra 5)
    total_copiado_mb = total_bytes / (1024 * 1024)
    logging.info(f"Espaço total copiado: {total_copiado_mb:.2f} MB")



if __name__ == "__main__":
    setup_logging()
    try:
        deploy_workflows()
    except Exception as e:
        logging.exception(f"Erro fatal na execução do deploy: {e}")
