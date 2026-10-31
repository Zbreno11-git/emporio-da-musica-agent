# Roadmap

Cada sessão é um pacote de 1 a 2 horas que termina com algo verificável e ganha uma entrada no diário.

**Progresso: 1 de N sessões fechadas.** O valor de N será definido quando o plano de dois dias for aprovado.

> **Notas de ordem.** Toda inversão, divisão ou fusão de sessão fica registrada aqui, com data e motivo.

## ▶️ Começar a próxima sessão por aqui

- **Sessão:** 1, a ser detalhada no plano de dois dias.
- **Primeiro passo:** o plano aprovado por Breno.
- **Ler antes:** `CLAUDE.md`, `docs/PROGRESSO.md`, guia 02 §3–5 e `exemplos/oraculos.json`.
- **Depende do dono:** sim. Prazo, modelo/orçamento Gemini, billing do projeto GCP e critérios que bloqueiam a publicação.

---

## Bloco 0 — Preparação

### ✅ Sessão 0 — Setup e primeiro push (31/10/2026)
- [x] Insumos organizados em `_insumos_privados/` (ignorado) e lidos
- [x] `.venv` com Python 3.12.3
- [x] Valores de referência conferidos contra os CSVs (0 divergências) e achados registrados
- [x] Skills `frontend-design`, `webapp-testing` e `qa-response` instaladas no projeto
- [x] Projeto GCP `emporio-da-musica-agent` criado (billing ainda não vinculado)
- [x] Repositório público com o primeiro commit

## Blocos seguintes — a preencher com o plano aprovado

Marcos já acordados nos guias, na ordem de dependência:
1. Importação + cotação determinística (offline)
2. Gemini real + catálogo + cotação: Takamine GD20 por R$ 2.199,00 e depois "e no PIX?" por R$ 2.089,05
3. Benchmark de custo-benefício dos modelos Gemini
4. Pedidos com identidade na sessão + primeiro deploy
5. Políticas (busca por seção) + interface Ressonância
6. Testes de sessão, falhas e UI; captura de 5 conversas reais; README final
