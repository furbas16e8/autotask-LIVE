# Changelog

Todos os lançamentos notáveis deste projeto serão documentados neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não publicado]

### Adicionado
- Sincronização automática de pastas de skills (contendo `SKILL.md`) sob a pasta de origem `../GitHub/workflows/skills` para a pasta global de skills do Antigravity `.gemini/config/skills` no script `sys_deploy_agent_resources_live.py`.
- Criação automática da pasta `skills` do Gemini caso ela não exista.
- Cálculo e exibição em MB do tamanho recursivo ocupado pelas pastas de destino (`global_workflows` e `skills`) e do espaço total copiado ao final da execução.
- Deploy seletivo e inteligente baseado em hash SHA-256 de arquivos de workflows e hash consolidado de pastas de skills no script `sys_deploy_agent_resources_live.py`.
- Parsing manual e resiliente de cabeçalho YAML para extrair a versão do workflow ou skill de forma informativa nos logs.
- Mecanismo de sincronização automática via Git (`git fetch` + `git pull`) do repositório de workflows de origem antes de iniciar o deploy.

### Modificado
- Renomeado o script utilitário `sys_deploy_workflows_live.py` para `sys_deploy_agent_resources_live.py` para refletir a cobertura de múltiplos recursos do agente, mantendo um wrapper legado para compatibilidade.
- Lógica de deploy: agora evita cópias desnecessárias e registra se o recurso é `[NOVO]`, `[ATUALIZADO]` ou `[INALTERADO]` nos logs, detalhando as versões.
- Relatório de volume de deploy: exibe a soma de bytes gravados fisicamente na execução corrente em vez do tamanho total de todos os recursos da origem.
