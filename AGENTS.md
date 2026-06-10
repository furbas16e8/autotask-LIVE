# Guidelines and Specifications for LLM/AI Agents (AUTOTASK LIVE)

Este repositório contém os scripts do **AUTOTASK LIVE**, que são executados remotamente a partir de um Launcher. As regras abaixo são **especificações técnicas de arquitetura mandatórias** para garantir a compatibilidade e portabilidade universal de todos os scripts e utilitários.

---

## ⚡ 1. Portabilidade e Resolução Dinâmica de Caminhos

Os scripts nunca devem conter caminhos absolutos hardcoded vinculados ao usuário (como `C:\Users\FULANO\...`). As rotas devem ser resolvidas dinamicamente da seguinte forma:

### A. Pastas do Sistema Operacional (Downloads, Documentos, etc.)
* **Python**: Utilizar a biblioteca padrão `pathlib.Path.home()` para referenciar o diretório do usuário:
  ```python
  DOWNLOADS_DIR = Path.home() / "Downloads"
  ```
* **PowerShell**: Utilizar a variável nativa `$HOME` para localizar a pasta do usuário:
  ```powershell
  $path = Join-Path $HOME "Documents\GitHub\autotask-LIVE\setup"
  ```

### B. Pasta do Repositório (Logs, Scripts locais, etc.)
No **AUTOTASK LIVE**, a execução ocorre a partir de uma pasta efêmera no desktop da máquina de execução (`Desktop\AUTOTASK\`). 
Para encontrar subpastas internas (como a pasta de logs em `Desktop\AUTOTASK\logs`), os scripts Python não devem assumir onde a pasta inicial está. Eles devem localizar o diretório do próprio script (`__file__`) e subir os níveis necessários:
```python
# Como o script reside em "Desktop/AUTOTASK/scripts/script.py", o diretório raiz é o segundo nível acima (parent.parent)
# Isso resolve dinamicamente para "Desktop/AUTOTASK/logs"
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
```

---

## 👤 2. Identificação Dinâmica de Usuários e Máquinas

Para a criação de arquivos de logs específicos por máquina e usuário em ambientes de execução, os logs devem ser nomeados com o sufixo `_live_{username}` da máquina Windows ativa.

### A. Obtenção e Sanitização de Usuário
O nome do usuário do Windows deve ser consultado dinamicamente e sanitizado contra caracteres especiais usando Regex para evitar problemas de criação de arquivos no sistema de arquivos do Windows:
```python
import getpass
import re

def obter_usuario_sanitizado() -> str:
    try:
        username = getpass.getuser()
    except Exception:
        username = "desconhecido"
    # Mantém apenas caracteres alfanuméricos, hífen e sublinhado
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", username)
```

### B. Comitando Logs no Git (Repositório)
Ao contrário do repositório AUTOTASK local, os arquivos `.log` gerados na máquina cliente do AUTOTASK LIVE ficam apenas no Desktop (`Desktop\AUTOTASK\logs\`).
No entanto, caso logs de homologação sejam gerados localmente na pasta `branch/logs/`, eles devem ser ignorados no `.gitignore` geral caso não sejam necessários, exceto se especificamente desejado pelo desenvolvedor.

---

## 🐍 3. Resolução do Executável Python no PowerShell

O Windows 10/11 possui aliases de execução sob `AppData\Local\Microsoft\WindowsApps\python.exe`. Esse atalho é problemático quando o interpretador do Python é instalado a partir do instalador oficial do python.org, causando erros na interceptação de argumentos (`Invalid argument`).

**Regra para Scripts PowerShell**:
Nunca execute chamadas genéricas como `python script.py` no console ou no launcher. Em vez disso, busque dinamicamente o interpretador real no sistema que não esteja na subpasta do WindowsApps:
```powershell
# Detecta o caminho real
$pythonCmd = (Get-Command -All python | Where-Object { $_.Path -notlike "*WindowsApps*" } | Select-Object -First 1).Path
if (-not $pythonCmd) {
    $pythonCmd = "python"
}

# Invoca o script usando o interpretador correto
& $pythonCmd $item.FullName
```

---

## 🔒 4. Integridade e Segurança do Sistema de Arquivos

* **Operação entre Dispositivos**: Sempre utilize `shutil.move()` para transferências de arquivos em vez de `pathlib.Path.rename()`. Se um usuário mover a pasta `Downloads` para um HD secundário (como `D:\Downloads`), o método `rename()` falhará com erro de link cruzado de dispositivos (`EXDEV`).
* **Lock Checking**: Em automações de arquivo (ex: triagem de downloads), sempre realize um teste de abertura em leitura e escrita rápida (`open(file, 'r+b')`) dentro de um bloco `try/except` para garantir que o arquivo não está sendo baixado pelo navegador ou aberto exclusivamente por outro processo no Windows.

---

## 📊 5. Padronização de Logs e Exibição de Tamanhos (MB)

Todos os scripts que manipulam arquivos ou diretórios devem reportar os volumes finais de dados em Megabytes (MB):
* **Limpezas de Diretório**: Devem reportar o espaço total removido/liberado em MB (ex: `Espaço liberado: X.XX MB`).
* **Compressão/Backup**: Devem informar o tamanho final do arquivo compactado em MB (ex: `Tamanho do arquivo comprimido: X.XX MB`), inclusive exibindo a cubagem atual se o arquivo já existir e a cópia for ignorada.
* **Triagem/Organização de Arquivos**: Ao final de cada execução, devem calcular e registrar recursivamente o tamanho ocupado por cada pasta de destino utilizada na classificação.

---

## 📝 6. Compatibilidade de Scripts PowerShell e Codificação de Arquivos

Para garantir que os scripts do PowerShell sejam executados sem erros de compilação ou sintaxe em qualquer instalação do Windows (inclusive no Windows PowerShell 5.1 padrão rodando sob encoding ANSI/CP-1252):

### A. Codificação de Arquivos (.ps1)
Todos os arquivos de script do PowerShell (`.ps1`) contendo caracteres especiais ou Unicode devem ser salvos na codificação **UTF-8 com BOM** (Byte Order Mark).
* **Por quê**: Sem o BOM, o PowerShell 5.1 tentará ler o arquivo usando a codificação de página ativa da máquina (tipicamente CP-1252 no Brasil). Caracteres Unicode como `✔` (checkmark) e `─` (linha divisória) possuem em sua codificação UTF-8 o byte `0x94`, que sob CP-1252 é interpretado como o caractere de aspa dupla inteligente (`”`). Isso faz com que o parser do PowerShell feche strings prematuramente e interprete o código subsequente como texto literal, quebrando a sintaxe do script.

### B. Evitar Here-Strings (`@" ... "@`)
Para a construção de blocos de texto multilinha dinâmicos, dê preferência ao uso de junção de array de strings (`-join "`r`n"`) em vez de *here-strings* literais.

### C. Estrutura de Try-Catch
Sempre mantenha a palavra-chave `catch` na mesma linha da chave de fechamento do bloco `try`:
```powershell
try {
    # código
} catch {
    # tratamento de erro
}
```
