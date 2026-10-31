# Roadmap

Cada sessão é um pacote de 1 a 2 horas que termina com algo verificável e ganha uma entrada no diário. O estado de cada checkpoint fica em [`PROGRESSO.md`](PROGRESSO.md).

**Progresso: 1 de 10 sessões fechadas** (S0). As próximas são S0b e S1 a S8.

Cada sessão é marcada pelo tipo de verificação que exige:
- **[OFF]** roda offline;
- **[GEM]** exige Gemini real;
- **[URL]** precisa passar na URL hospedada.

> **Notas de ordem.**
> - 31/10/2026: o plano de dois dias foi aprovado por Breno. A execução começou na própria noite de 31/10, adiantando o dia 1.

## ▶️ Começar a próxima sessão por aqui

Ver o bloco "RETOMAR AQUI" em [`PROGRESSO.md`](PROGRESSO.md).

## Respostas de Breno (31/10/2026)

| Pergunta | Resposta | Consequência |
| --- | --- | --- |
| Prazo | Congelar em 02/11 às 23:59 | Meta interna: tudo publicado até 02/11 às 20:00 |
| Modelos no benchmark | `gemini-3.1-flash-lite` × `gemini-3.5-flash` | Duas linhas na S5. Smoke com os dois na S2 |
| Orçamento | US$ 5 no total | Billing em BRL: orçamento equivalente a US$ 5, filtrado nos projetos `emporio-da-musica-agent` e `gen-lang-client-0041725501`, com alertas em 50/90/100%. **O orçamento alerta, não corta**, por isso há limites no código |
| Chave Gemini | Manter a atual em tudo | No deploy, vai para o Secret Manager do projeto Empório. Outros usos da chave contam no teto |
| Bloqueios de entrega | Vazamento entre perfis · preço ou promoção divergente · ação alegada sem execução | Cada um vira um teste automático e um item do veredito final. Latência só é medida |

## Mapa de checkpoints

| C | Fecha quando | Tipo | Depende de |
| --- | --- | --- | --- |
| C0 | Respostas e plano registrados (commit `docs: plano de dois dias`) | OFF | — |
| C1 | `pytest tests/domain` verde: importação + cotação batem com 100% de `oraculos.json` | OFF | C0 |
| C2 | Executor SQL bloqueia as 6 classes de violação | OFF | C1 |
| C3 | Marco 1: Takamine GD20 R$ 2.199,00 → "e no PIX?" R$ 2.089,05 via `/api/chat` | GEM | C2 |
| C4 | Pedidos com identidade da sessão: A vê o 8, cruzado = inexistente | OFF + GEM | C3 |
| C5 | Busca nas políticas: ≥10/12 no top 3, mais as perguntas mistas registradas | OFF | C1 |
| C6 | Primeira revisão no Cloud Run responde o marco 1 em janela anônima | URL | C3, C4 |
| C7 | Benchmark escolhe e fixa `GEMINI_MODEL` | GEM | C4, C5 |
| C8 | Interface Ressonância conferida em 320, 390 px e desktop | OFF + GEM | C3 |
| C9 | Playwright + testes de falha verdes, nova revisão no ar | OFF + URL | C6, C8 |
| C10 | 5 conversas reais na URL, revisadas e sem bloqueio. README final. Clone limpo reproduz | URL | C7, C9 |

---

## ✅ S0 · Setup e primeiro push (31/10/2026)
- [x] Insumos em `_insumos_privados/` (ignorado); `.venv` com Python 3.12.3
- [x] Oráculos × CSVs: 0 divergências; achados registrados
- [x] Três skills de projeto instaladas; projeto GCP dedicado criado (sem billing)
- [x] Repositório público, commit `00e9e7f` verificado

## S0b · Registro do plano (15 min) [OFF]
- [ ] Uso do ChatGPT registrado; decisões D11–D15; este roadmap; varredura pré-commit em `scripts/check_staged.py`
- **✅ C0:** `git log -1` = `docs: plano de dois dias`, e o push confere pelo SHA.

## Dia 1

### S1 · Dados e regras determinísticas (≈2 h) [OFF]
- **1.1 Dependências.**
  - **Faz:** fastapi, uvicorn, pydantic, google-genai, pypdf + pytest, httpx; `requirements*.txt` com versões exatas.
  - **✅** imports OK; `pip install -r requirements.txt` num venv descartável → exit 0.
- **1.2 Importador.**
  - **Faz:** `scripts/import_snapshot.py --source <zip|dir>`. Localiza os CSVs pelo sufixo com normalização NFC, valida cabeçalhos e vínculos, gera `data/build/{catalog.db,orders-demo.db,manifest.json}` em diretório temporário e publica de uma vez.
  - **✅** contagens 9/65/25/50/20/22 e `sellable=61`; uma linha corrompida aborta com linha e motivo.
  - **🐞** Nome NFD ou BOM → `ascii(os.listdir())`.
- **1.3 Cotação.**
  - **Faz:** `app/tools/quote.py` (centavos, `ROUND_HALF_UP`, PIX só sem promoção, parcelas com `needs_confirmation` em §3 × §3.1, combinação de meios acima de R$ 2.000).
  - **✅** `pytest tests/domain` → 9 produtos e 3 pedidos dos oráculos; R$ 600 em 12x recusado.
  - **🐞** Desconto aplicado duas vezes → teste dedicado com o 127.
- **1.4 Executor SQL.**
  - **Faz:** `app/tools/catalog.py` com `mode=ro`, `query_only`, `set_authorizer` negando por padrão, `set_progress_handler`, coluna `product_id` obrigatória e hidratação canônica.
  - **✅ C2:** ATTACH, escrita, PRAGMA, `sqlite_master`, tabela de pedidos e CTE recursiva cara bloqueados (6/6); nylon até R$ 800 → produtos vendáveis abaixo do teto.

### S2 · Primeiro turno com Gemini real (≈2 h) [GEM]
- **2.1** `app/contracts.py` (DTOs `extra='forbid'`); os 3 exemplos do contrato validam.
- **2.2 Loop do agente.**
  - **Faz:** `app/agent.py` com `generate_content`, despacho manual, partes do modelo preservadas (assinaturas), orçamento de 3 rodadas, 6 ferramentas, 25 s e cards hidratados pelo backend.
  - **🐞** Assinatura perdida entre rodadas → registrar as partes cruas.
- **2.3 API mínima.**
  - **Faz:** `app/session.py` (RAM, cookie, TTL, deduplicação); `app/main.py` (`/api/session`, `/api/chat`, `/healthz`); página mínima.
- **2.4 Smoke.**
  - **Faz:** `scripts/smoke_gemini.py --model X` com os 2 candidatos.
  - **✅ C3:** 219900 e depois 208905, mesmo `product_id=95`, via `quote_product(method=pix)`. Registrar modelo, versão do SDK, duração e tokens.
- **Testes offline:** HTTP com Gemini fake identificado (contrato, 409, 410, 503).

### S3 · Pedidos e políticas (≈2 h) [OFF + GEM]
- **3.1 Pedidos.**
  - **Faz:** `app/tools/orders.py` com `WHERE order_id=? AND customer_id=?`; perfis demo-a→2, demo-b→6, demo-c→7; a troca de perfil limpa histórico e cache.
  - **✅ C4:** A/8 `shipped`; B/9 `confirmed`; B/8 == B/999; visitante → `profile_required`.
- **3.2 Manual.**
  - **Faz:** `scripts/build_policy_index.py` → `data/build/policy_sections.json`; revisão manual das seções §3/3.1, §4, §5, §6.2 e §8.
- **3.3 Busca.**
  - **Faz:** BM25 em `app/tools/policies.py`; `evals/policy_retrieval.jsonl` (12 casos-base, 6 paráfrases, 4 mistas).
  - **✅ C5:** top 3 ≥ 10/12.
- **3.4 [GEM]** Pedido 8 com perfil A; frete de exatamente R$ 500 → `contact_store` + handoff `prepared`.

### S4 · Primeiro deploy (≈1,5 h) [URL]
- **Pausa obrigatória:** Breno confirma na hora o vínculo do billing e o orçamento, porque geram custo.
- **4.1 Contas.**
  - **Faz:** com `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio`:
    - vincular o billing;
    - criar o orçamento em BRL com `--filter-projects` nos 2 projetos;
    - habilitar run, cloudbuild, artifactregistry e secretmanager;
    - criar o secret com a chave via stdin, acessível só pela service account do serviço.
- **4.2 Deploy.**
  - **Faz:** `Dockerfile` (python:3.12-slim); `.gcloudignore` auditado com `gcloud meta list-files-for-upload`; `gcloud run deploy --source . --region southamerica-east1 --max-instances 1 --min-instances 0`.
  - **✅ C6:** `/healthz` 200; marco 1 via curl na URL; janela anônima; revisão e commit anotados no README.

## Dia 2

### S5 · Benchmark de custo-benefício (≈1,5 h) [GEM]
- **Faz:** `scripts/benchmark_models.py` com 2 modelos × 2 repetições sobre a bateria fixa:
  - Takamine → PIX;
  - Kalani no PIX;
  - nylon até R$ 800;
  - pedido 8 com A e com B;
  - devolução com fato faltante;
  - fora de escopo;
  - frete de exatamente R$ 500.

  Mede os 3 bloqueios contra oráculos e perfil, a ferramenta e os argumentos, a latência fria e aquecida e os tokens (`usage_metadata`). O custo só entra com preço verificado no dia.
- **Regra de escolha (D14):** o mais barato que passa nos 3 bloqueios em todas as execuções; empate → menor latência mediana.
- **✅ C7:** `evals/benchmark-modelos.md`; `GEMINI_MODEL` fixado; gasto conferido no billing.

### S6 · Interface Ressonância (≈2 h) [OFF + GEM]
- **Faz:** `/frontend-design` com o guia 01. A tela tem:
  - tokens exatos e fontes WOFF2 locais (licença OFL);
  - slogan e 3 sugestões na abertura, recolhidos no primeiro envio;
  - fala antes dos cards e **um avatar por turno**;
  - card com nome, atributo, preço (original, % e vigente) e disponibilidade em texto;
  - seletor de perfil só em `choose_profile`;
  - handoff com resumo copiável;
  - fontes sob demanda, `aria-live`, painel técnico recolhido;
  - "Tentar novamente" que preserva o rascunho.
- **✅ C8:** capturas em 320, 390 e 1280 px; nome e preço legíveis; preço do card == DTO.

### S7 · Navegador, falhas e segunda revisão (≈1,5 h) [OFF + URL]
- **Faz:** `/webapp-testing` com Playwright em Python e 2 contextos isolados:
  - Takamine → PIX;
  - pedido 8 como visitante, com perfil errado e com troca de perfil;
  - erro do provedor via fake identificado;
  - sem `networkidle` nem sleep.

  Falhas: 504, 429, ferramenta vazia, reenvio com o mesmo `request_id`, 409 concorrente, 410.
- **✅ C9:** `pytest` e `pytest tests/e2e` verdes; nova revisão no ar responde o marco 1.

### S8 · Captura real, revisão e entrega (≈2 h, até 20:00) [URL]
- **8.1 Captura.** 5 conversas na URL (descoberta, promoção + PIX, pedido autorizado, devolução, fora de escopo) em `examples/*.md`, com modelo, commit, manifesto, ferramentas, duração e captura de tela.
- **8.2 Revisão.** `/qa-response` em cada uma, com resultados das ferramentas e seções do manual. Um bloqueio leva a corrigir a causa e capturar de novo.
- **8.3 README final.** Setup, decisões, limitações, uso de IA, URL e revisão. Reprodução a partir de clone limpo.
- **✅ C10:** 5/5 sem bloqueio; `scripts/check_staged.py` PASS; `git ls-remote` == HEAD; último commit antes das 23:59 de 02/11. O texto do e-mail fica pronto para Breno enviar.

## Riscos

- **Billing, orçamento e deploy custam dinheiro:** confirmação na hora.
- **O orçamento só alerta:** os limites no código (comprimento, rodadas, 10 turnos/min por sessão, máximo de 1 instância) fazem a contenção.
- **A mesma chave é usada fora do projeto:** conferir o gasto no fim de S2, S5 e S8.
- **Gemini 3.x com function calling:** preservar as partes do conteúdo; o flash-lite pode errar a ferramenta, e o benchmark mede isso.
- **Sessão em RAM:** uma reciclagem da instância perde a sessão. Mitigação: máximo de 1 instância e 410 testado.
- **Ordem de corte se atrasar:** painel técnico → busca semântica → animações → segunda repetição do benchmark. **Nunca cortar:** bloqueios, captura real, README reproduzível.

## Definição de pronto (entrega)

- C0–C10 fechados, cada um com a linha literal do comando citada em `PROGRESSO.md`.
- URL servindo o commit entregue.
- 3–5 conversas reais sem bloqueio.
- README reproduzido a partir de um clone limpo.
- Uso de IA registrado.
- Nada alterado depois de 02/11 às 23:59.
