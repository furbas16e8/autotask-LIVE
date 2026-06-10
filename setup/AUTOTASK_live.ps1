# =========================================================
# AUTOTASK - Automation Control Center (LIVE VERSION TEST)
# =========================================================

$Host.UI.RawUI.WindowTitle = "AUTOTASK LIVE (TEST)"

# Verifica se o script está sendo executado como Administrador
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host ""
    Write-Host " [AVISO] Execute o PowerShell como Administrador para gerenciar tarefas e limpeza do sistema!" -ForegroundColor Yellow
    Write-Host ""
    Start-Sleep -Seconds 3
}

# Sobe dois níveis do diretório atual e entra na pasta de scripts (nesta versão de teste, a pasta branch/)
$currentDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Obtém a pasta raiz do projeto:
$rootPath = (Get-Item $currentDir).Parent.FullName

# Aponta direto para a pasta 'scripts' dentro de branch/
$scriptsPath = "$rootPath\scripts\*"

# Resolve o executável real do Python (evitando o alias do WindowsApps)
$pythonCmd = (Get-Command -All python | Where-Object { $_.Path -notlike "*WindowsApps*" } | Select-Object -First 1).Path
if (-not $pythonCmd) {
    $pythonCmd = "python"
}

# =========================================================
# FUNÇÕES
# =========================================================

function Obter-ScriptsPython {
    return Get-ChildItem -Path $scriptsPath -Include *.py |
    Where-Object { $_.Name -ne "AUTOTASK_live.ps1" }
}


function Filtrar-Tarefas {

    return Get-ScheduledTask | Where-Object {

        $_.TaskName -like "sys_*" -or
        $_.TaskName -like "sync_*" -or
        $_.TaskName -like "tool_*" -or
        $_.TaskName -like "file_*"
    }
}

function Linha {

    param(
        [string]$Cor = "Gray"
    )

    Write-Host (" " + ("─" * 82)) -ForegroundColor $Cor
}

function Banner {

    Clear-Host

    Write-Host ""
    Write-Host "  ╔═╗ ║ ║ ═╦═ ╔═╗ ═╦═ ╔═╗ ╔═╗ ║╗" -ForegroundColor Cyan
    Write-Host "  ╠═╣ ║ ║  ║  ║ ║  ║  ╠═╣ ╚═╗ ╠╝" -ForegroundColor Cyan
    Write-Host "  ╩ ╩ ╚═╝  ╩  ╚═╝  ╩  ╩ ╩ ══╝ ║╚" -ForegroundColor Cyan -NoNewline
    Write-Host "                                by: Douglas Furbino" -ForegroundColor DarkGray

    Linha

    Write-Host ""
}

function Secao {

    param(
        [string]$Titulo
    )

    Write-Host ""
    Write-Host "  $Titulo" -ForegroundColor White
    Linha "Gray"
    Write-Host ""
}

function Pausa {

    Write-Host ""
    Read-Host " Pressione ENTER para continuar"
}

function Mostrar-UltimosLogs {
    Banner
    Secao "ÚLTIMOS LOGS DA MÁQUINA"

    $rawUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name.Split("\")[-1]
    $sanitizedUser = $rawUser -replace '[^a-zA-Z0-9_\-]', '_'

    $logFolder = "$rootPath\logs"
    if (-not (Test-Path $logFolder)) {
        Write-Host " [!] Pasta de logs não encontrada." -ForegroundColor Red
        Pausa
        return
    }

    $logFiles = Get-ChildItem -Path "$logFolder\*_$sanitizedUser.log"

    if ($logFiles.Count -eq 0) {
        Write-Host " Nenhum log encontrado para esta máquina ($sanitizedUser)." -ForegroundColor Gray
        Pausa
        return
    }

    foreach ($file in $logFiles) {
        $lines = Get-Content -Path $file.FullName
        if ($lines.Count -eq 0) {
            continue
        }

        # Encontra o início da última execução
        $startIndex = -1
        for ($i = $lines.Count - 1; $i -ge 0; $i--) {
            if ($lines[$i] -match "Execução iniciada|iniciando|Iniciando limpeza") {
                $startIndex = $i
                break
            }
        }

        # Se não achar, pega do início ou das últimas 5 linhas
        if ($startIndex -eq -1) {
            $startIndex = [Math]::Max(0, $lines.Count - 5)
        }

        $lastRunLines = $lines[$startIndex..($lines.Count - 1)]

        # Extrai data e hora da primeira linha da última execução
        $dateTime = "Desconhecida"
        if ($lastRunLines[0] -match '^\[([^\]]+)\]') {
            $dateTime = $Matches[1]
        }

        # Verifica se houve erros
        $hasErrors = $false
        $errorMsg = ""
        foreach ($line in $lastRunLines) {
            if ($line -match "\[ERROR\]|ERRO:|failed|failure|falha") {
                $hasErrors = $true
                $errorMsg = $line -replace '^\[[^\]]+\]\s*', ''
                break
            }
        }

        Write-Host ""
        Linha "Gray"

        Write-Host " Script    : " -ForegroundColor White -NoNewline
        Write-Host $file.BaseName.Replace("_$sanitizedUser", "") -ForegroundColor Cyan

        Write-Host " Data/Hora : " -ForegroundColor White -NoNewline
        Write-Host $dateTime -ForegroundColor Cyan

        Write-Host " Status    : " -ForegroundColor White -NoNewline
        if ($hasErrors) {
            Write-Host "ERRO ✖" -ForegroundColor Red
            Write-Host " Detalhe   : " -ForegroundColor White -NoNewline
            Write-Host $errorMsg -ForegroundColor Gray
        }
        else {
            Write-Host "SUCESSO ✔" -ForegroundColor Green
        }
    }

    Write-Host ""
    Linha

    Pausa
}

function Mostrar-Menu {

    Banner

    Write-Host "   [1]" -ForegroundColor Cyan -NoNewline
    Write-Host "  Executar Script"

    Write-Host "   [2]" -ForegroundColor Cyan -NoNewline
    Write-Host "  Agendar Script"

    Write-Host "   [3]" -ForegroundColor Cyan -NoNewline
    Write-Host "  Ver Agendamentos"

    Write-Host "   [4]" -ForegroundColor Cyan -NoNewline
    Write-Host "  Excluir Agendamento"

    Write-Host "   [5]" -ForegroundColor Cyan -NoNewline
    Write-Host "  Ver Últimos Logs"

    Write-Host ""

    Write-Host "   [Q]" -ForegroundColor Gray -NoNewline
    Write-Host "  Sair"

    Write-Host ""

    Linha

    Write-Host ""
    Write-Host ""

    return Read-Host " ➜ Escolha uma opção"
}

# =========================================================
# LOOP PRINCIPAL
# =========================================================

while ($true) {

    $opcaoMenu = Mostrar-Menu

    switch (($opcaoMenu + "").ToUpper()) {

        # =================================================
        # EXECUTAR SCRIPT
        # =================================================

        "1" {

            Banner
            Secao "EXECUTAR SCRIPT"

            $scripts = Obter-ScriptsPython

            if ($scripts.Count -eq 0) {

                Write-Host " [!] Nenhum script encontrado." -ForegroundColor Red
                Start-Sleep -Seconds 2

                continue
            }

            for ($i = 0; $i -lt $scripts.Count; $i++) {

                Write-Host " [$($i + 1)] " -ForegroundColor Cyan -NoNewline
                Write-Host $scripts[$i].BaseName -ForegroundColor White
            }

            Write-Host ""

            $escolha = Read-Host " ➜ Digite o número"

            if (
                [int]::TryParse($escolha, [ref]$null) -and
                [int]$escolha -gt 0 -and
                [int]$escolha -le $scripts.Count
            ) {

                $item = $scripts[[int]$escolha - 1]

                Write-Host ""
                Linha

                Write-Host ""
                Write-Host " [ Running ] " -ForegroundColor Cyan -NoNewline
                Write-Host "$($item.Name)" -ForegroundColor White
                Write-Host ""

                & $pythonCmd $item.FullName
            }

            Pausa
        }

        # =================================================
        # AGENDAR SCRIPT
        # =================================================

        "2" {

            Banner
            Secao "AGENDAR SCRIPT"

            $scripts = Obter-ScriptsPython

            if ($scripts.Count -eq 0) {

                Write-Host " [!] Nenhum script encontrado." -ForegroundColor Red
                Start-Sleep -Seconds 2

                continue
            }

            for ($i = 0; $i -lt $scripts.Count; $i++) {

                Write-Host " [$($i + 1)] " -ForegroundColor Cyan -NoNewline
                Write-Host $scripts[$i].BaseName -ForegroundColor White
            }

            Write-Host ""

            $escolha = Read-Host " ➜ Digite o número do script"

            if (
                [int]::TryParse($escolha, [ref]$null) -and
                [int]$escolha -gt 0 -and
                [int]$escolha -le $scripts.Count
            ) {

                $item = $scripts[[int]$escolha - 1]

                Write-Host ""
                Secao "PREFIXOS DISPONÍVEIS"

                Write-Host " [1] " -ForegroundColor Cyan -NoNewline
                Write-Host "sys_"

                Write-Host " [2] " -ForegroundColor Cyan -NoNewline
                Write-Host "sync_"

                Write-Host " [3] " -ForegroundColor Cyan -NoNewline
                Write-Host "tool_"

                Write-Host " [4] " -ForegroundColor Cyan -NoNewline
                Write-Host "file_"

                Write-Host ""

                $p = Read-Host " ➜ Escolha"

                $pref = switch ($p) {

                    "1" { "sys_" }
                    "2" { "sync_" }
                    "3" { "tool_" }
                    "4" { "file_" }

                    Default { "auto_" }
                }

                Write-Host ""

                $nomeCustomizado = (
                    Read-Host " ➜ Nome do agendamento"
                ).Replace(" ", "_").ToLower()

                $horario = Read-Host " ➜ Horário (HH:MM)"

                $opcaoFreq = (
                    Read-Host " ➜ Frequência [D] Diário [S] Semanal [M] Mensal"
                ).ToUpper()

                $descricao = Read-Host " ➜ Descrição"

                $action = New-ScheduledTaskAction `
                    -Execute $pythonCmd `
                    -Argument """$($item.FullName)"" #origem:$($item.Name)"

                $trigger = switch ($opcaoFreq) {

                    "D" {
                        New-ScheduledTaskTrigger -Daily -At $horario
                    }

                    "S" {
                        New-ScheduledTaskTrigger `
                            -Weekly `
                            -At $horario `
                            -DaysOfWeek Monday
                    }

                    "M" {
                        New-ScheduledTaskTrigger `
                            -Once `
                            -At (Get-Date -Format "yyyy-MM-01 $horario")
                    }

                    Default {
                        $null
                    }
                }

                if ($null -ne $trigger) {

                    Register-ScheduledTask `
                        -TaskName "$pref$nomeCustomizado" `
                        -Action $action `
                        -Trigger $trigger `
                        -Description $descricao `
                        -Force | Out-Null

                    Write-Host ""
                    Linha

                    Write-Host ""
                    Write-Host " [ OK ] " -ForegroundColor Green -NoNewline
                    Write-Host "Agendamento criado com sucesso." -ForegroundColor Green
                }
                else {

                    Write-Host ""
                    Write-Host " [!] Frequência inválida." -ForegroundColor Red
                }
            }

            Start-Sleep -Seconds 2
        }

        # =================================================
        # VER AGENDAMENTOS
        # =================================================

        "3" {

            Banner
            Secao "AGENDAMENTOS ATIVOS"

            $tarefasPainel = Filtrar-Tarefas

            if ($tarefasPainel.Count -eq 0) {

                Write-Host " Nenhum agendamento encontrado." -ForegroundColor Gray
            }
            else {
                for ($i = 0; $i -lt $tarefasPainel.Count; $i++) {
                    $tarefa = $tarefasPainel[$i]

                    $horario = [datetime]$tarefa.Triggers[0].StartBoundary |
                    Get-Date -Format "HH:mm"

                    $triggerClass = $null
                    if ($null -ne $tarefa.Triggers -and $tarefa.Triggers.Count -gt 0 -and $null -ne $tarefa.Triggers[0].CimClass) {
                        $triggerClass = $tarefa.Triggers[0].CimClass.CimClassName
                    }

                    $frequencia = switch ($triggerClass) {
                        "MSFT_TaskDailyTrigger" { "Diário" }
                        "MSFT_TaskWeeklyTrigger" { "Semanal" }
                        "MSFT_TaskMonthlyTrigger" { "Mensal" }
                        "MSFT_TaskMonthlyDOWTrigger" { "Mensal" }
                        "MSFT_TaskTimeTrigger" { "Mensal" }
                        Default { "Outro" }
                    }

                    $proxExecStr = "N/A"
                    try {
                        $info = Get-ScheduledTaskInfo -TaskName $tarefa.TaskName
                        $nextRun = $info.NextRunTime
                        if ($null -ne $nextRun -and $nextRun -ne "" -and $nextRun -ne [DateTime]::MinValue) {
                            $diff = $nextRun - (Get-Date)
                            $days = [Math]::Ceiling($diff.TotalDays)
                            if ($days -le 0) {
                                $proxExecStr = "Hoje"
                            } elseif ($days -eq 1) {
                                $proxExecStr = "Amanhã"
                            } else {
                                $proxExecStr = "Em $days dias"
                            }
                        }
                    }
                    catch {}

                    $origem = if (
                        $tarefa.Actions[0].Arguments -match '#origem:(.*)$'
                    ) {
                        $Matches[1]
                    }
                    else {
                        "Desconhecido"
                    }

                    Write-Host ""
                    Linha "Gray"

                    Write-Host " [$($i + 1)] " -ForegroundColor Cyan -NoNewline
                    Write-Host "Script    : " -ForegroundColor White -NoNewline
                    Write-Host $origem -ForegroundColor Cyan

                    Write-Host "     Task ID   : " -ForegroundColor White -NoNewline
                    Write-Host $tarefa.TaskName -ForegroundColor Gray
                    
                    Write-Host "     Frequência: " -ForegroundColor White -NoNewline
                    Write-Host $frequencia -ForegroundColor Cyan -NoNewline
                    Write-Host " às " -ForegroundColor Gray -NoNewline
                    Write-Host $horario -ForegroundColor Cyan

                    Write-Host "     Próxima Ex: " -ForegroundColor White -NoNewline
                    Write-Host $proxExecStr -ForegroundColor Cyan

                    Write-Host "     Descrição : " -ForegroundColor White -NoNewline
                    Write-Host $tarefa.Description -ForegroundColor Gray
                }
            }

            Write-Host ""
            Linha

            if ($tarefasPainel.Count -gt 0) {
                Write-Host ""
                $escolha = Read-Host " ➜ Escolha o número para disparar/testar a tarefa (ou ENTER para voltar)"

                if (
                    [int]::TryParse($escolha, [ref]$null) -and
                    [int]$escolha -gt 0 -and
                    [int]$escolha -le $tarefasPainel.Count
                ) {
                    $tarefaAlvo = $tarefasPainel[[int]$escolha - 1]

                    Write-Host ""
                    Write-Host " [ Running ] " -ForegroundColor Cyan -NoNewline
                    Write-Host "Disparando agendamento: $($tarefaAlvo.TaskName)..." -ForegroundColor White

                    try {
                        Start-ScheduledTask -TaskName $tarefaAlvo.TaskName
                        Write-Host ""
                        Write-Host " [ OK ] " -ForegroundColor Green -NoNewline
                        Write-Host "Tarefa iniciada com sucesso no Agendador de Tarefas." -ForegroundColor Green
                    }
                    catch {
                        Write-Host ""
                        Write-Host " [!] Erro ao iniciar tarefa: $_" -ForegroundColor Red
                    }
                    Start-Sleep -Seconds 3
                }
            }
            else {
                Pausa
            }
        }

        # =================================================
        # EXCLUIR AGENDAMENTO
        # =================================================

        "4" {

            Banner
            Secao "EXCLUIR AGENDAMENTO"

            $tarefas = Filtrar-Tarefas

            if ($tarefas.Count -eq 0) {

                Write-Host " [!] Nenhum agendamento encontrado." -ForegroundColor Red
                Start-Sleep -Seconds 2
            }
            else {

                for ($i = 0; $i -lt $tarefas.Count; $i++) {

                    Write-Host " [$($i + 1)] " -ForegroundColor Cyan -NoNewline
                    Write-Host $tarefas[$i].TaskName -ForegroundColor White
                }

                Write-Host ""

                $del = Read-Host " ➜ Escolha o número para excluir"

                if (
                    [int]::TryParse($del, [ref]$null) -and
                    [int]$del -gt 0 -and
                    [int]$del -le $tarefas.Count
                ) {

                    Unregister-ScheduledTask `
                        -TaskName $tarefas[[int]$del - 1].TaskName `
                        -Confirm:$false

                    Write-Host ""
                    Linha

                    Write-Host ""
                    Write-Host " [ OK ] " -ForegroundColor Green -NoNewline
                    Write-Host "Agendamento removido." -ForegroundColor Green

                    Start-Sleep -Seconds 2
                }
            }
        }

        # =================================================
        # VER ÚLTIMOS LOGS
        # =================================================

        "5" {

            Mostrar-UltimosLogs
        }

        # =================================================
        # SAIR
        # =================================================

        "Q" {

            Clear-Host
            exit
        }

        # =================================================
        # OPÇÃO INVÁLIDA
        # =================================================

        Default {

            Write-Host ""
            Write-Host " [!] Opção inválida." -ForegroundColor Red

            Start-Sleep -Seconds 1
        }
    }
}
