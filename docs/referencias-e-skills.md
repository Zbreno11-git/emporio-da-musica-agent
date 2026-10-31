# Referências e skills

## Skills do Claude Code instaladas no projeto

Instaladas em `.claude/skills/<nome>/` em 31/10/2026. O diretório é ignorado pelo Git ([D9](DECISOES.md)). A integridade foi conferida comparando o SHA de blob de cada arquivo local com a árvore do commit fixado.

| Skill | Origem | Commit | Arquivos | Licença | Uso previsto | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `frontend-design` | [anthropics/skills](https://github.com/anthropics/skills/tree/ca45fc496a3436251f191354091d557da31c15b5/skills/frontend-design) | `ca45fc4` | `SKILL.md`, `LICENSE.txt` | Apache-2.0 | Implementar e revisar a tela Ressonância já aprovada, sem explorar uma identidade nova | Instalada; os blobs são idênticos ao commit |
| `webapp-testing` | [anthropics/skills](https://github.com/anthropics/skills/tree/ca45fc496a3436251f191354091d557da31c15b5/skills/webapp-testing) | `ca45fc4` | `SKILL.md`, `LICENSE.txt`, `scripts/with_server.py`, `examples/*.py` (3) | Apache-2.0 | Playwright em Python: fluxo Takamine + PIX, pedido cruzado, troca de perfil, 320/390 px/desktop | Instalada; os blobs são idênticos. Playwright ainda não instalado no `.venv` |
| `qa-response` | [composio-community/support-skills](https://github.com/composio-community/support-skills/tree/83382c4b055fc4e5b055044adb5bfb7585484c9a/qa-response) | `83382c4` | `SKILL.md` | Ambígua (sem LICENSE; o README diz Apache-2.0 no badge e MIT na seção) | Revisar conversas reais junto com os resultados das ferramentas e as seções do manual. Invocação explícita (`disable-model-invocation: true`) | Instalada; blob `500fb25` conferido |

**Ativação pendente.** As skills de projeto são lidas do diretório `.claude/skills/`. Se não aparecerem na sessão atual, reinicie o Claude Code no diretório do projeto e confira com `/frontend-design`, `/webapp-testing` e `/qa-response`. Como a `qa-response` só é chamada explicitamente, ela não aparece entre as skills invocadas automaticamente pelo modelo.

**Cópias equivalentes.** O ambiente de Breno já tinha `frontend-design` e `webapp-testing` no escopo pessoal, vindas do commit `34040c9`. Os arquivos são idênticos aos do `ca45fc4`, e a cópia do projeto tem precedência. Também existe um plugin `frontend-design` do marketplace oficial.

**Reinstalação** (só a pasta de cada skill):

```bash
for p in frontend-design webapp-testing; do
  gh api "repos/anthropics/skills/git/trees/ca45fc496a3436251f191354091d557da31c15b5?recursive=1" \
    --jq ".tree[]|select(.type==\"blob\" and (.path|startswith(\"skills/$p/\")))|.path" |
  while read f; do mkdir -p ".claude/$(dirname "${f}")"; gh api "repos/anthropics/skills/contents/$f?ref=ca45fc4" --jq .content | base64 -d > ".claude/$f"; done
done
mkdir -p .claude/skills/qa-response
gh api "repos/composio-community/support-skills/contents/qa-response/SKILL.md?ref=83382c4b055fc4e5b055044adb5bfb7585484c9a" --jq .content | base64 -d > .claude/skills/qa-response/SKILL.md
```

Além dessas, Breno usa uma skill pessoal de processo, `software-build`, que organiza documentos de continuidade, sessões com checkpoints e a definição de pronto. Ela fica no ambiente pessoal dele e o conteúdo não é distribuído neste repositório.

## Repositórios de referência (lidos, não copiados)

Commits fixados pelo guia 03. Esses exemplos ensinam técnicas; as regras comerciais vêm do manual e dos CSVs.

| Referência | O que aproveitar | O que deixar de fora |
| --- | --- | --- |
| [Gemini Cookbook · Function calling](https://github.com/google-gemini/cookbook/blob/b06b824cf2ea29f9543ffa14adcee68b5f934a9b/quickstarts/Function_calling.ipynb) | Declarações, despacho manual, devolução do resultado | Modos de chamada automática |
| [Gemini Cookbook · SQL Agent](https://github.com/google-gemini/cookbook/blob/b06b824cf2ea29f9543ffa14adcee68b5f934a9b/examples/langchain/SQL_Agent_Gemini_LangChain.ipynb) | Esquema no prompt; filtros e ordenação | LangChain, banco de exemplo, Colab |
| [Gemini Cookbook · Embeddings](https://github.com/google-gemini/cookbook/blob/b06b824cf2ea29f9543ffa14adcee68b5f934a9b/quickstarts/Embeddings.ipynb) | Tipo de tarefa da pergunta × documento; versão e hash do índice | — |
| [Pydantic AI · bank_support.py](https://github.com/pydantic/pydantic-ai/blob/2a89126b7a968ae7664348dc055717e0e2bb61f9/examples/pydantic_ai_examples/bank_support.py) | A identidade vem das dependências do contexto, não do argumento do modelo | Operações bancárias, cursor global, segunda pilha de orquestração |
| [flaviagaia/agente_atendimento](https://github.com/flaviagaia/agente_atendimento/tree/57405d5722cd2230a78862dacbb4e97208b25b57) | Separar a fala da informação operacional (`text`, `cards`, `sources`, `next_action`) | Streamlit, categorias de ticket. Sem licença identificada: só como referência |
| [Renatoelho/atendimento-agentes-ia](https://github.com/Renatoelho/atendimento-agentes-ia/blob/c5400b11b2e1bc215c0a06487222c27a7845e426/docker-compose.yaml) | Ideia de resumir o caso para uma pessoa | NiFi, MySQL, MinIO, Elasticsearch, Kibana |
| [Bhavik-Jikadara/ai-customer-service-agent](https://github.com/Bhavik-Jikadara/ai-customer-service-agent/blob/4ecde05848eb0e062d378e2ef59dfe169f7790ea/src/customer_service_agent/tools.py) | Registro legível de ferramentas | Aprovação automática de reembolso |
