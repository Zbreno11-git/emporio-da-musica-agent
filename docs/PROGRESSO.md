# Progresso em curso

> Arquivo de trabalho com o estado da sessão **atual**, atualizado a cada etapa.

## ▶️ RETOMAR AQUI — 31/10/2026 (America/Campo_Grande)

**Estado:** o plano de dois dias foi aprovado ([SESSOES.md](SESSOES.md)). Em curso: S0b, depois S1.

**Próximo passo exato:** S1.1, que instala as dependências no `.venv` e gera os `requirements*.txt`.

**Checkpoints:**

| C | Fecha quando | Estado |
| --- | --- | --- |
| C0 | Plano registrado (commit `docs: plano de dois dias`) | 🔵 |
| C1 | Importação + cotação = oráculos | ⬜ |
| C2 | Executor SQL bloqueia 6/6 | ⬜ |
| C3 | Marco 1 com Gemini real | ⬜ |
| C4 | Pedidos com identidade da sessão | ⬜ |
| C5 | Busca nas políticas ≥10/12 | ⬜ |
| C6 | Primeira revisão no Cloud Run | ⬜ |
| C7 | Benchmark fixa `GEMINI_MODEL` | ⬜ |
| C8 | Interface em 320/390/desktop | ⬜ |
| C9 | Playwright + falhas, segunda revisão | ⬜ |
| C10 | 5 conversas reais, README, clone limpo | ⬜ |

**Não esquecer:**
- **GCP:** o gcloud tem `altivaserra` como configuração `default` ativa. Este repositório usa `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio` e o projeto `emporio-da-musica-agent`.
- **Billing:** ainda **não** vinculado (`billingEnabled=False`). O vínculo e o orçamento (BRL ≈ US$ 5) exigem confirmação de Breno na S4.
- **Chave Gemini:** pertence a `gen-lang-client-0041725501`, com billing ativo na mesma conta.
- **Nomes com acento:** os arquivos vieram em Unicode decomposto (NFD). O importador localiza os CSVs pelo sufixo.
- **Antes de cada commit:** `git add` e depois `.venv/bin/python scripts/check_staged.py`, que precisa dar PASS.

## Provas desta sessão

| Prova | Comando | Resultado (literal) | Quando |
| --- | --- | --- | --- |
| Commit inicial publicado | `git ls-remote origin refs/heads/main` | `00e9e7f665d89e783febedafd7d7908382d82c05` (== HEAD == API) | 31/10/2026 |
