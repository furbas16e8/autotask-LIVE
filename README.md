```text
  ╔═╗ ║ ║ ═╦═ ╔═╗ ═╦═ ╔═╗ ╔═╗ ║╗
  ╠═╣ ║ ║  ║  ║ ║  ║  ╠═╣ ╚═╗ ╠╝   L I V E
  ╩ ╩ ╚═╝  ╩  ╚═╝  ╩  ╩ ╩ ══╝ ║╚
```

O **AUTOTASK LIVE** é um ambiente de execução efêmera e remota para utilitários Python no Windows, projetado para rodar em qualquer máquina conectada à internet sem a necessidade de clonar permanentemente o repositório ou configurar atalhos persistentes no sistema de arquivos.

Ele utiliza uma arquitetura baseada em um script **Launcher** em PowerShell executado diretamente em memória via *one-liner* HTTPS.

---

## 📂 Estrutura do Repositório

```text
autotask-LIVE/
├── setup/
│   └── AUTOTASK_live.ps1                    # Console CLI interativo local
├── scripts/
│   ├── file_organize_downloads_live.py      # Organizador automático de Downloads
│   ├── sync_compress_vault_live.py          # Backup do Obsidian Vault (AES-256)
│   ├── sys_clean_temp_live.py               # Limpeza de arquivos temporários
│   └── sys_deploy_agent_resources_live.py   # Sincronização de recursos do agente (workflows e skills)
├── blueprints/
│   └── blueprint_20260526_AUTOTASK-Live.html # Documento técnico de arquitetura
├── README.md                                # Documentação do projeto
└── AGENTS.md                                # Regras e diretrizes para Agentes de IA
```

---

## ⚙️ Arquitetura & Como Funciona

O AUTOTASK LIVE separa o repositório de código privado da máquina cliente através do seguinte fluxo:

1. **Launcher**: Um script PowerShell `launcher.ps1` é hospedado em um **Gist Secreto** no GitHub do desenvolvedor.
2. **Execução em Memória**: O usuário inicia o console usando uma chamada *one-liner* no PowerShell:
   ```powershell
   irm https://gist.githubusercontent.com/furbas16e8/GIST_ID/raw/launcher.ps1 | iex
   ```
3. **Autenticação**: O Launcher autentica na API do GitHub usando um **PAT (Personal Access Token) Fine-grained** configurado com acesso `Contents: Read-only` ao repositório privado `autotask-LIVE`.
4. **Downloads Efêmeros**: Os scripts Python (`.py`) são baixados em formato Base64 diretamente para `Desktop\AUTOTASK\scripts\`. Em execuções subsequentes, esses arquivos são automaticamente sobrescritos para assegurar que a versão mais recente seja sempre executada.
5. **Logs**: Os logs de execução de cada utilitário são gerados dinamicamente em `Desktop\AUTOTASK\logs\` com identificação de usuário do Windows ativo.

---

## 🚀 Como Configurar e Instalar

### 1. Criar o Personal Access Token (PAT)
1. Vá em seu GitHub ➔ **Settings** ➔ **Developer Settings** ➔ **Personal Access Tokens** ➔ **Fine-grained tokens**.
2. Clique em **Generate new token**.
3. Configure:
   - **Repository access**: Select repositories ➔ `autotask-LIVE`.
   - **Permissions**: Repository permissions ➔ **Contents: Read-only**.
   - **Expiration**: 90 dias (recomendado por segurança).
4. Copie o token gerado.

### 2. Criar o launcher.ps1 e Hospedar no Gist
1. Crie um script `launcher.ps1` localmente contendo o seu token e repositório:
   ```powershell
   $token   = "ghp_SEU_TOKEN_AQUI"
   $repo    = "furbas16e8/autotask-LIVE"
   $branch  = "main"
   $headers = @{ Authorization = "token $token"; "User-Agent" = "PowerShell" }

   $desktop = [Environment]::GetFolderPath('Desktop')
   $runDir  = Join-Path $desktop "AUTOTASK"
   $scripts = Join-Path $runDir "scripts"
   $logs    = Join-Path $runDir "logs"

   New-Item -ItemType Directory -Force -Path $scripts | Out-Null
   New-Item -ItemType Directory -Force -Path $logs    | Out-Null

   $menu = [ordered]@{
       "1" = @{ file = "file_organize_downloads_live.py"; label = "Organizar Downloads" }
       "2" = @{ file = "sync_compress_vault_live.py";    label = "Backup do Vault (Obsidian)" }
       "3" = @{ file = "sys_clean_temp_live.py";         label = "Limpar Temp do Sistema" }
       "4" = @{ file = "sys_deploy_agent_resources_live.py"; label = "Deploy de Recursos do Agente" }
   }

   Clear-Host
   Write-Host ""
   Write-Host "  AUTOTASK LIVE"                -ForegroundColor White
   Write-Host "  ──────────────────────────────" -ForegroundColor DarkGray
   $menu.GetEnumerator() | ForEach-Object {
       Write-Host "  [$($_.Key)]  $($_.Value.label)" -ForegroundColor Gray
   }
   Write-Host "  ──────────────────────────────" -ForegroundColor DarkGray
   $choice = Read-Host "  Escolha"

   if (-not $menu.Contains($choice)) {
       Write-Host "  Opção inválida." -ForegroundColor Red
       exit 1
   }

   $selected = $menu[$choice]
   $apiUrl   = "https://api.github.com/repos/$repo/contents/scripts/$($selected.file)?ref=$branch"
   $outFile  = Join-Path $scripts $selected.file

   try {
       Write-Host "  Baixando $($selected.file)..." -ForegroundColor DarkGray
       $content = Invoke-RestMethod -Uri $apiUrl -Headers $headers
       $bytes   = [Convert]::FromBase64String($content.content)
       [System.IO.File]::WriteAllBytes($outFile, $bytes)
   } catch {
       Write-Host "  Erro ao baixar script: $_" -ForegroundColor Red
       exit 1
   }

   $pythonCmd = (Get-Command -All python | Where-Object { $_.Path -notlike "*WindowsApps*" } | Select-Object -First 1).Path
   if (-not $pythonCmd) { $pythonCmd = "python" }

   Write-Host "  Executando $($selected.label)..." -ForegroundColor White
   Write-Host ""
   & $pythonCmd $outFile
   ```
2. Acesse [gist.github.com](https://gist.github.com) e crie um **Secret Gist** nomeado `launcher.ps1` com o conteúdo acima.
3. Clique em **Raw** na página do Gist e copie o endereço URL obtido.

### 3. Execução
No terminal do Windows PowerShell, execute o seguinte comando utilizando a URL raw obtida:
```powershell
irm URL_DO_GIST_RAW | iex
```

---

## 🛠️ Requisitos de Execução
- **Python 3.10+** instalado (fora da pasta `WindowsApps`).
- **py7zr** instalada para o script de backup (o script avisa e instrui caso falte).
- Direitos de **Administrador** no terminal se desejar executar a limpeza de temporários do sistema (`sys_clean_temp_live.py`).
- Política de execução de scripts habilitada no PowerShell do usuário:
  ```powershell
  Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
  ```