# Uso de assistentes de IA

> Este é um entregável do enunciado. Registro só o que de fato aconteceu, com data, e atualizo ao longo do projeto. Para cada uso, separo o que a ferramenta fez, o que eu (Breno) decidi e como o resultado foi verificado.

## Ferramentas

| Ferramenta | Papel |
| --- | --- |
| Claude Code (Opus) | Implementação, auditoria dos insumos, testes e documentação, guiado por skills de processo e de técnica |
| ChatGPT | *A preencher por Breno: uso na pesquisa e na redação dos guias de visão, backend e branding* |
| GPT Images | Prancha da marca Ressonância e miniatura universal do catálogo (registrado no guia de branding) |

## Registro por sessão

### 31/10/2026 · Sessão 0, setup (Claude Code)

- **O que o Claude Code fez:**
  - leu o enunciado, o manual, os CSVs e os três guias;
  - recalculou os valores de referência a partir dos CSVs (0 divergências) e listou as inconsistências do manual em [`achados-dos-insumos.md`](achados-dos-insumos.md);
  - criou o `.venv`, o `.gitignore` e a documentação inicial;
  - instalou três skills fixadas por commit, conferindo os blobs;
  - criou o projeto GCP dedicado e o repositório público.
- **O que eu decidi:** a stack, a marca, o fluxo de políticas e o uso de um projeto GCP separado. Essas decisões vieram antes desta sessão, nos guias, e foram reafirmadas no prompt de abertura.
- **Como verifiquei:** os scripts de conferência rodaram sobre os arquivos originais; antes do push, revisei o diff e rodei a varredura de segredos e dados pessoais.
