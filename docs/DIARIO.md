# Diário de bordo

> Uma entrada por sessão, com a mais nova no topo. Cada entrada conta o que foi feito, o que foi decidido e por quê, e o que se aprendeu.

## 31/10/2026 — Sessão 0: ambiente pronto, insumos auditados e repositório público

**Feito.**
- Organizei os insumos em `_insumos_privados/` e criei o `.venv` com Python 3.12.3.
- Recalculei `oraculos.json` a partir dos CSVs, sem nenhuma divergência.
- Instalei três skills com os blobs conferidos contra os commits fixados.
- Criei o projeto GCP dedicado e publiquei o primeiro commit.

**Decidido.**
- Breno: usar um projeto GCP novo e nunca o `altivaserra`.
- Agente, com recomendação a Breno: manter as skills de terceiros fora do Git por causa da licença ambígua da `qa-response`; manter os documentos de continuidade em `docs/`.

**Achado.** Encontrei 11 divergências e lacunas nos dados e no manual, e 4 nos materiais de apoio ([achados](achados-dos-insumos.md)). A mais relevante para o código é o conflito de parcelas entre §3 e §3.1, que vai virar `needs_confirmation`.

**Não verificado.** Ainda não chamei o Gemini para gerar conteúdo, só listei os modelos. Também não confirmei se a sessão atual do Claude Code descobriu as skills de projeto.

**Próximo.** Planejamento de dois dias com Breno.
