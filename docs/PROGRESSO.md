# Progresso em curso

> Arquivo de trabalho com o estado da sessão **atual**, atualizado a cada etapa.

## ▶️ RETOMAR AQUI — 31/10/2026 (America/Campo_Grande)

**Estado:** Sessão 0 (setup) concluída. O primeiro commit foi publicado no GitHub; o SHA verificado está no diário.

**Próximo passo exato:** fechar a rodada de planejamento com Breno e escrever o plano de dois dias em `docs/SESSOES.md`.

**Não esquecer:**
- O gcloud tem `altivaserra` como configuração `default` ativa, que é de outro projeto. Este repositório usa `CLOUDSDK_ACTIVE_CONFIG_NAME=emporio` e o projeto `emporio-da-musica-agent`.
- O billing do projeto `emporio-da-musica-agent` ainda **não** está vinculado (`billingEnabled=False`). Isso é pré-requisito para o Cloud Run e depende de autorização de Breno.
- `gemini-3.1-flash` não existe na conta. Os candidatos para o benchmark estão em `docs/achados-dos-insumos.md` (M4).
- Os nomes dos arquivos com acento vieram em Unicode decomposto (NFD). O importador deve normalizar os nomes ou localizar os CSVs pelo sufixo.

**Depende do dono:**
- Prazo exato do e-mail.
- Orçamento Gemini e candidatos do benchmark.
- Vincular o billing.
- Critérios que bloqueiam a publicação.
- Registro do uso do ChatGPT em `docs/uso-de-ia.md`.
