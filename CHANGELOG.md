# Changelog

Todos os lançamentos notáveis deste projeto serão documentados neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não publicado]

### Adicionado
- Sincronização automática de skills da pasta de origem `../GitHub/workflows/skills` para a pasta global de plugins do Gemini `.gemini/config/plugins/minhas-skills` no script `sys_deploy_workflows_live.py`.
- Criação automática da pasta `minhas-skills` caso ela não exista.
- Cálculo e exibição em MB do tamanho recursivo ocupado pelas pastas de destino (`global_workflows` e `minhas-skills`) e do espaço total copiado ao final da execução.
