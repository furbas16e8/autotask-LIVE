"""
sys_deploy_agent_resources_live.py
──────────────────────────────────
Sincronização de workflows globais e pastas de skills locais para as pastas globais do Gemini (VERSÃO TESTE LIVE).
"""

import sys
import shutil
import logging
import getpass
import re
import hashlib
from pathlib import Path

def obter_usuario_sanitizado() -> str:
    try:
        username = getpass.getuser()
    except Exception:
        username = "desconhecido"
    # Mantém apenas caracteres alfanuméricos, hífen e sublinhado
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", username)


def extrair_metadados_yaml(caminho_arquivo: Path) -> dict:
    """
    Abre o arquivo Markdown e lê as linhas iniciais delimitadas por '---'.
    Extrai chaves e valores estruturados.
    """
    metadados = {}
    if not caminho_arquivo.is_file():
        return metadados
    try:
        lines = []
        with open(caminho_arquivo, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(100):  # Limite de segurança para evitar arquivos muito longos
                line = f.readline()
                if not line:
                    break
                lines.append(line.strip())
        
        if not lines or lines[0] != "---":
            return metadados
            
        for line in lines[1:]:
            if line == "---":
                break
            if ":" in line:
                parts = line.split(":", 1)
                chave = parts[0].strip().lower()
                valor = parts[1].strip()
                if valor.startswith('"') and valor.endswith('"'):
                    valor = valor[1:-1]
                elif valor.startswith("'") and valor.endswith("'"):
                    valor = valor[1:-1]
                metadados[chave] = valor
    except Exception as e:
        logging.debug(f"Erro ao extrair metadados YAML de {caminho_arquivo.name}: {e}")
    return metadados


def calcular_hash_arquivo(caminho: Path) -> str:
    """Calcula o hash SHA-256 de um arquivo."""
    sha256 = hashlib.sha256()
    try:
        with open(caminho, "rb") as f:
            for bloco in iter(lambda: f.read(65536), b""):
                sha256.update(bloco)
        return sha256.hexdigest()
    except Exception as e:
        logging.error(f"Erro ao calcular hash de {caminho}: {e}")
        return ""


def calcular_hash_diretorio(caminho: Path) -> str:
    """Calcula recursivamente o hash SHA-256 consolidado de um diretório."""
    sha256 = hashlib.sha256()
    if not caminho.is_dir():
        return ""
    try:
        arquivos = []
        for item in caminho.rglob("*"):
            if item.is_file():
                arquivos.append(item)
        arquivos.sort(key=lambda p: p.relative_to(caminho))

        for arquivo in arquivos:
            rel_path = str(arquivo.relative_to(caminho)).replace("\\", "/")
            sha256.update(rel_path.encode("utf-8"))
            with open(arquivo, "rb") as f:
                for bloco in iter(lambda: f.read(65536), b""):
                    sha256.update(bloco)
        return sha256.hexdigest()
    except Exception as e:
        logging.error(f"Erro ao calcular hash do diretório {caminho}: {e}")
        return ""



def setup_logging() -> None:
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    username = obter_usuario_sanitizado()
    log_file = log_dir / f"sys_deploy_agent_resources_live_{username}.log"

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
    return Path.home() / ".gemini" / "config" / "skills"


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


def copiar_diretorio_com_lock_check(origem: Path, destino: Path) -> int:
    """Copia recursivamente um diretório para o destino, verificando locks de arquivos e retornando o tamanho em bytes."""
    destino.mkdir(parents=True, exist_ok=True)
    total_bytes = 0
    for item in origem.iterdir():
        destino_item = destino / item.name
        if item.is_dir():
            total_bytes += copiar_diretorio_com_lock_check(item, destino_item)
        elif item.is_file():
            total_bytes += copiar_arquivo_com_lock_check(item, destino_item)
    return total_bytes


def sincronizar_repositorio_git(caminho_repo: Path) -> None:
    """Verifica se o repositório Git de origem está atualizado e realiza sincronização se necessário."""
    import subprocess
    
    # Verifica se a pasta existe e se é um repositório git
    if not (caminho_repo / ".git").is_dir():
        logging.info("O diretório de origem não é um repositório Git ou o .git não está acessível. Pulando sincronização git.")
        return

    logging.info("Verificando se o repositório de workflows está atualizado com o remoto...")
    try:
        # Executa git fetch para atualizar as informações do remoto
        subprocess.run(
            ["git", "fetch"],
            cwd=caminho_repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=15
        )
        
        # Compara HEAD com a branch upstream correspondente
        local_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=caminho_repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        ).stdout.strip()
        
        upstream_sha_cmd = subprocess.run(
            ["git", "rev-parse", "@{u}"],
            cwd=caminho_repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if upstream_sha_cmd.returncode != 0:
            logging.info("Nenhum branch upstream configurado. Pulando pull automático.")
            return
            
        upstream_sha = upstream_sha_cmd.stdout.strip()
        
        if local_sha != upstream_sha:
            # Verifica se está atrás (behind)
            base_sha = subprocess.run(
                ["git", "merge-base", "HEAD", "@{u}"],
                cwd=caminho_repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            ).stdout.strip()
            
            if local_sha == base_sha:
                logging.info("O repositório local está desatualizado (atrás do remoto). Executando 'git pull'...")
                pull_res = subprocess.run(
                    ["git", "pull"],
                    cwd=caminho_repo,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if pull_res.returncode == 0:
                    logging.info("Repositório de workflows sincronizado com sucesso via git pull.")
                else:
                    logging.warning(f"Falha ao executar 'git pull' (pode haver conflitos locais): {pull_res.stderr.strip()}")
            elif upstream_sha == base_sha:
                logging.info("O repositório local está à frente do remoto (ahead). Nenhuma sincronização necessária.")
            else:
                logging.warning("Os repositórios local e remoto divergiram. Recomenda-se resolução manual. Pulando pull automático.")
        else:
            logging.info("O repositório de workflows já está atualizado com o remoto.")
            
    except subprocess.TimeoutExpired:
        logging.warning("Timeout ao tentar se comunicar com o remoto do Git. Pulando sincronização git.")
    except Exception as e:
        logging.warning(f"Não foi possível sincronizar o repositório via Git: {e}. Prosseguindo com deploy local.")


def deploy_agent_resources():
    # --- Parte 1: Workflows ---
    origem_dir = resolver_caminho_origem()
    destino_dir = resolver_caminho_destino()

    # Sincroniza a origem (repositório workflows) antes de prosseguir
    sincronizar_repositorio_git(origem_dir.parent)

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
                
                # Extrai metadados para auditoria/logs
                meta_orig = extrair_metadados_yaml(arquivo)
                meta_dest = extrair_metadados_yaml(destino_arquivo) if destino_arquivo.exists() else {}
                
                versao_orig = meta_orig.get("version", "desconhecida")
                versao_dest = meta_dest.get("version", "desconhecida")
                
                status_recurso = "INALTERADO"
                precisa_copiar = False
                
                if not destino_arquivo.exists():
                    status_recurso = "NOVO"
                    precisa_copiar = True
                else:
                    hash_orig = calcular_hash_arquivo(arquivo)
                    hash_dest = calcular_hash_arquivo(destino_arquivo)
                    if hash_orig != hash_dest:
                        status_recurso = "ATUALIZADO"
                        precisa_copiar = True

                if precisa_copiar:
                    try:
                        bytes_copiados = copiar_arquivo_com_lock_check(arquivo, destino_arquivo)
                        total_bytes += bytes_copiados
                        arquivos_copiados.append(arquivo.name)
                        kb_copiados = bytes_copiados / 1024
                        if status_recurso == "NOVO":
                            logging.info(f"[NOVO] Copiado: {arquivo.name} ({kb_copiados:.2f} KB) - Versão: {versao_orig}")
                        else:
                            logging.info(f"[ATUALIZADO] Atualizado: {arquivo.name} ({kb_copiados:.2f} KB) - Versão antiga: {versao_dest} -> Nova: {versao_orig}")
                    except Exception as e:
                        logging.error(f"Falha ao copiar '{arquivo.name}': {e}")
                        erros += 1
                else:
                    logging.info(f"[INALTERADO] Ignorado (já atualizado): {arquivo.name} - Versão: {versao_dest}")

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

        # Varre todos os subdiretórios na origem de skills
        pastas_skills = [p for p in origem_skills.glob("*") if p.is_dir()]
        
        if not pastas_skills:
            logging.info("Nenhuma pasta de skill encontrada para copiar na pasta de origem de skills.")
        else:
            pastas_copiadas = []
            erros_skills = 0

            for pasta in pastas_skills:
                destino_pasta = destino_skills / pasta.name
                
                # Extrai metadados do arquivo SKILL.md se ele existir
                skill_md_orig = pasta / "SKILL.md"
                skill_md_dest = destino_pasta / "SKILL.md"
                
                meta_orig = extrair_metadados_yaml(skill_md_orig) if skill_md_orig.exists() else {}
                meta_dest = extrair_metadados_yaml(skill_md_dest) if skill_md_dest.exists() else {}
                
                versao_orig = meta_orig.get("version", "desconhecida")
                versao_dest = meta_dest.get("version", "desconhecida")
                
                status_recurso = "INALTERADO"
                precisa_copiar = False
                
                if not destino_pasta.exists():
                    status_recurso = "NOVO"
                    precisa_copiar = True
                else:
                    hash_orig = calcular_hash_diretorio(pasta)
                    hash_dest = calcular_hash_diretorio(destino_pasta)
                    if hash_orig != hash_dest:
                        status_recurso = "ATUALIZADO"
                        precisa_copiar = True

                if precisa_copiar:
                    try:
                        # Limpeza atômica da pasta destino (se existia)
                        if destino_pasta.exists():
                            try:
                                shutil.rmtree(destino_pasta)
                            except Exception as e:
                                logging.warning(f"Não foi possível remover completamente a pasta de destino '{destino_pasta.name}' antes de recriar: {e}. Sobrescrevendo arquivos existentes.")
                        
                        bytes_copiados = copiar_diretorio_com_lock_check(pasta, destino_pasta)
                        total_bytes += bytes_copiados
                        pastas_copiadas.append(pasta.name)
                        kb_copiados = bytes_copiados / 1024
                        if status_recurso == "NOVO":
                            logging.info(f"[NOVO] Copiada pasta de skill: {pasta.name} ({kb_copiados:.2f} KB) - Versão: {versao_orig}")
                        else:
                            logging.info(f"[ATUALIZADO] Atualizada pasta de skill: {pasta.name} ({kb_copiados:.2f} KB) - Versão antiga: {versao_dest} -> Nova: {versao_orig}")
                    except Exception as e:
                        logging.error(f"Falha ao copiar pasta de skill '{pasta.name}': {e}")
                        erros_skills += 1
                else:
                    logging.info(f"[INALTERADO] Ignorada pasta de skill (já atualizada): {pasta.name} - Versão: {versao_dest}")

            if erros_skills > 0:
                logging.warning(f"Total de falhas de skills (pastas ignoradas/bloqueados): {erros_skills}")

    logging.info("Deploy de skills (Teste Live) concluído.")
    tamanho_dest_skills_mb = obter_tamanho_diretorio_mb(destino_skills)
    logging.info(f"Tamanho total da pasta de destino skills: {tamanho_dest_skills_mb:.2f} MB")

    # Volume total copiado (Regra 5)
    total_copiado_mb = total_bytes / (1024 * 1024)
    logging.info(f"Espaço total copiado: {total_copiado_mb:.2f} MB")


if __name__ == "__main__":
    setup_logging()
    try:
        deploy_agent_resources()
    except Exception as e:
        logging.exception(f"Erro fatal na execução do deploy: {e}")
