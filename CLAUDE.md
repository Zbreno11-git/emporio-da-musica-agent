# Empório da Música — instruções para o agente

> Leia isto primeiro, em toda sessão. Este arquivo traz o que não está no código. O roadmap fica em `docs/SESSOES.md` e o estado atual em `docs/PROGRESSO.md`.

## O que é

Agente de atendimento por texto da Empório da Música, loja fictícia de instrumentos em Campo Grande/MS, para o desafio de AI Engineer da Artefact. O dono das decisões é Breno.

O projeto usa:
- Python, FastAPI e Gemini com function calling;
- SQLite;
- busca nas políticas por seção do manual;
- interface HTML com a marca Ressonância;
- demo no Cloud Run.

Estado em 31/10/2026: setup concluído; o agente ainda não foi implementado.

## O requisito que decide empates

> Preço, acesso a pedido e prazo errados reprovam o caso, mesmo com tom cordial. Quando faltar um fato, o agente pergunta ao cliente ou prepara o encaminhamento. Ele nunca inventa.

## Regras invioláveis

- **Segredos e insumos privados não entram no Git:**
  - `.env`;
  - chaves Gemini, GCP e GitHub;
  - `_insumos_privados/` (ZIPs, PDFs, CSVs brutos, guias internos);
  - bancos derivados;
  - nome, e-mail e telefone de clientes dos CSVs.

  Antes de cada commit, conferir `git diff --cached --name-only` e rodar a varredura de segredos e dados pessoais.
- **Dinheiro em centavos inteiros.** Os valores saem de `Decimal` construído a partir da string do CSV, com `ROUND_HALF_UP` uma única vez. O LLM nunca calcula preço: ele recebe os valores confirmados pelo backend.
- **A identidade vem da sessão do servidor.** Um número de pedido digitado no chat identifica o registro procurado, não o cliente. Um pedido de outro perfil recebe a mesma resposta de um pedido inexistente.
- **Execução real é a evidência.** Mocks servem a testes e ficam identificados como mocks. As conversas de `examples/` são capturas reais da versão entregue. Exemplos preparados nos guias não contam como execução.
- **Ações sem integração não são declaradas como feitas.** Um encaminhamento fica `prepared`; não se fala em "registramos" nem se gera protocolo.
- **Consertar primeiro.** Não se constrói sobre defeito conhecido sem autorização de Breno. Deploy, criação de recursos que geram custo e envio de e-mail exigem autorização na hora.

## Autoridade das fontes

| Questão | Fonte (local: `_insumos_privados/`) |
| --- | --- |
| Entregáveis e prazo | PDF da Artefact (`desafio/`) e e-mail do processo |
| Regras da loja | Manual v2.1 (`desafio/.../data/políticas_da_loja.pdf`); lacuna ou conflito decisivo leva a encaminhamento |
| Produto, preço, estoque, pedido | Os 6 CSVs (`desafio/.../data/`) |
| Marca e tela | Guia 01 (`guias/01-branding/`) e o mockup em `referencias-visuais/`, com um único avatar por turno |
| Contratos técnicos | Guia 02 (`guias/02-backend/`), `exemplos/oraculos.json` (valores esperados) e `exemplos/turnos.json` (ilustração do contrato) |
| Aplicação de referências e skills | Guia 03 (`guias/03-visao/`) |

## Fronteiras e gatilhos em vigor

| Fronteira | Regra |
| --- | --- |
| SQL do agente | Só no `catalog.db`, em modo somente leitura, com authorizer de negação por padrão. Pedidos ficam em outra conexão |
| Parcelas | Onde §3 e §3.1 levam a resultados diferentes, retornar `needs_confirmation` e oferecer uma opção inequívoca |
| Skills de terceiros | Ficam instaladas em `.claude/skills/` e ignoradas pelo Git (ver `docs/referencias-e-skills.md`) |
| GCP | **Somente o projeto `emporio-da-musica-agent`. Nunca usar `altivaserra`, que é de outro projeto de Breno e continua como configuração `default` ativa no gcloud.** Todo comando gcloud deste repositório roda com `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio` e `--project emporio-da-musica-agent`, região `southamerica-east1`. Não alterar a configuração global ativa. |

## Onde está o quê

| | |
| --- | --- |
| `docs/SESSOES.md` | Roadmap e "▶️ Começar a próxima sessão por aqui" |
| `docs/PROGRESSO.md` | Estado atual e "retomar aqui" |
| `docs/DECISOES.md` | Decisões, cada uma com o gatilho que a reabre |
| `docs/achados-dos-insumos.md` | Divergências entre dados, manual e guias |
| `docs/arquitetura.md` | Componentes e árvore planejada |
| `docs/DIARIO.md` · `docs/ERROS.md` | Uma entrada por sessão · catálogo de erros por classe |
| `docs/uso-de-ia.md` | Registro real de uso de Claude Code e ChatGPT (entregável) |

## Comandos

```bash
.venv/bin/python --version   # 3.12.3
# portões (testes, lint) entram com o primeiro código
```

## Protocolo

- **Ao abrir uma sessão:** ler este arquivo, depois `docs/PROGRESSO.md`, depois `git status`.
- **Ao fechar:** portões lidos, duas passadas de revisão, atualização dos documentos, commit com o porquê.
- **Ao achar um defeito:** abrir `docs/ERROS.md` antes de consertar.
