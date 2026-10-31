# Empório da Música · agente de atendimento

Protótipo em Python de um agente de atendimento por texto para a **Empório da Música**, loja fictícia de instrumentos musicais em Campo Grande/MS. Este projeto foi desenvolvido para o desafio técnico de AI Engineer da Artefact.

O agente vai responder perguntas sobre catálogo, preços, formas de pagamento, pedidos e políticas da loja. Ele consulta os dados quando precisa de um fato e o manual quando precisa de uma regra. Quando falta informação, prepara um encaminhamento para a equipe.

## Estado atual (31/10/2026)

**Setup concluído. A implementação do agente ainda não começou.**

| Pronto | Próximo |
| --- | --- |
| Repositório, `.gitignore` e ambiente Python 3.12.3 em `.venv` | Importador dos CSVs para SQLite e funções de preço testadas contra os valores de referência |
| Arquitetura, decisões e inventário de referências e skills em [`docs/`](docs/) | Primeiro marco: o Gemini real responde o preço do Takamine GD20 (R$ 2.199,00) e, no turno seguinte, "e no PIX?" (R$ 2.089,05) |
| Auditoria dos dados e do manual em [`docs/achados-dos-insumos.md`](docs/achados-dos-insumos.md) | Pedidos com identidade na sessão, busca no manual, interface e deploy no Cloud Run |

O roadmap está em [`docs/SESSOES.md`](docs/SESSOES.md) e o estado da sessão em curso está em [`docs/PROGRESSO.md`](docs/PROGRESSO.md).

## Stack escolhida

| Peça | Escolha | Detalhe |
| --- | --- | --- |
| Linguagem e API | Python 3.12, FastAPI, Pydantic v2 | [arquitetura](docs/arquitetura.md) |
| Modelo | Gemini com function calling (SDK `google-genai`) | O modelo exato será decidido por medição de custo-benefício ([D2](docs/DECISOES.md)) |
| Dados | SQLite somente leitura para o catálogo e banco separado para pedidos | O dinheiro é tratado em centavos, com cálculo determinístico |
| Políticas | Recuperação por seção do manual | Começa com busca lexical; a busca semântica só entra se a avaliação mostrar ganho |
| Interface | HTML, CSS e JS servidos pelo FastAPI, com a identidade "Ressonância" | |
| Demo | Um serviço no GCP Cloud Run | A mesma aplicação roda localmente |

As justificativas completas estão em [`docs/DECISOES.md`](docs/DECISOES.md).

## Setup local

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
cp .env.example .env    # preencha GEMINI_API_KEY localmente; nunca faça commit do .env
```

O arquivo de dependências e os comandos de importação, execução e testes entram com a primeira implementação. Os dados originais do desafio (CSVs e manual) não são versionados. O importador vai ler o ZIP fornecido pela Artefact a partir de um diretório local ignorado pelo Git.

## Estrutura

A árvore atual contém só a documentação. A estrutura planejada para o código está em [`docs/arquitetura.md`](docs/arquitetura.md#árvore-planejada).

```text
README.md            este arquivo
CLAUDE.md            instruções do projeto para o agente de código
.env.example         nomes das variáveis de ambiente, sem valores
docs/                arquitetura, decisões, achados, roadmap, progresso e uso de IA
```

## Uso de assistentes de IA

O registro está em [`docs/uso-de-ia.md`](docs/uso-de-ia.md) e é atualizado ao longo do projeto. Ele separa o que cada ferramenta fez das decisões que tomei e da forma como os resultados foram verificados.
