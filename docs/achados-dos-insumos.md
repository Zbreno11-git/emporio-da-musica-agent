# Achados nos insumos

> Auditoria feita em 31/10/2026 sobre o enunciado da Artefact, o manual v2.1, os 6 CSVs e os guias 01/02/03. As referências apontam para seção do manual, ID de produto ou de pedido, ou arquivo, sem reproduzir dados pessoais. Os scripts de conferência rodaram localmente sobre os arquivos originais.

## Conferência dos valores de referência

`oraculos.json` (guia 02) foi recalculado a partir dos CSVs, com `Decimal` e `ROUND_HALF_UP`:

- **contagens:** 9 categorias, 65 produtos, 25 promoções, 50 clientes, 20 pedidos e 22 itens;
- **produtos vendáveis:** 61, contando os que têm `status = active` e estoque maior que zero;
- **detalhe:** 9 produtos (81, 90, 94, 95, 96, 121, 127, 130, 136) e 3 pedidos (8, 9, 20).

**Resultado: 0 divergências.** As relações também foram verificadas:
- não há produto sem categoria;
- não há promoção nem item que aponte para produto inexistente;
- não há pedido sem cliente nem pedido sem item;
- todos os campos `specs` são JSON válido;
- nenhum produto tem duas promoções ativas.

## Divergências e lacunas que mudam a implementação

| # | Onde | Achado | Tratamento proposto |
| --- | --- | --- | --- |
| A1 | Manual §3 × §3.1 | A tabela do §3 fixa a parcela mínima do crédito em R$ 100. O §3.1 fixa R$ 80 para 4–6x. A regra até 3x ("exceto abaixo de R$ 50") admite mais de uma leitura | `quote_product` retorna `needs_confirmation` quando as leituras divergem e oferece uma opção inequívoca |
| A2 | `orders.csv` × §3/§3.1 | Os pedidos 9, 16 e 18 têm parcelas abaixo do mínimo do §3.1 (6x de R$ 58,32; 6x de R$ 71,65; 12x de R$ 38,32). O pedido 7 (3x de R$ 53,30) fica abaixo dos R$ 100 do §3 | O agente apresenta o registro histórico tal como está e não o "corrige" nem o julga |
| A3 | Manual, capa e §1.2 × §7 | Telefone geral (67) 3341-4444; WhatsApp principal (67) 3321-4500 | Exibir cada contato por finalidade, citando a seção. No handoff, usar o canal do §7 |
| A4 | Manual, capa × §1.2 | O e-mail aparece sem acento na capa e com acento (`empório`) no §1.2 | Preferir outro canal documentado; não exibir o e-mail divergente como certo |
| A5 | Manual §5.1 | Frete na região metropolitana: R$ 35 abaixo de R$ 500, grátis acima. **Exatamente R$ 500** não está coberto | Explicar as faixas e preparar handoff `policy_gap` |
| A6 | Manual §1 × `categories`/`products` | O manual fala em mais de 300 instrumentos e cita sopros e cordas orquestrais, mas as categorias 6, 7 e 8 não têm produtos no snapshot (65 produtos) | Responder "não temos no catálogo consultado" sem inferir um catálogo maior |
| A7 | `promotions` | O produto 95 (Takamine GD20) tem promoção **inativa**. Quatro promoções estão ativas, nos produtos 90, 94, 121 e 127. A fonte não traz datas de vigência | Caso de demonstração de "promoção expirada" (§7.3): informar o preço atual sem prometer desconto |
| A8 | `orders.total_brl` | Os totais dos pedidos 3 e 20 diferem da soma dos preços atuais dos itens | O total histórico do pedido prevalece; `order_items` não tem preço unitário |
| A9 | `orders` | Só o pedido 8 está `shipped`. A previsão de entrega dele (28/02/2026) já passou em relação a hoje (31/10/2026). Os 8 códigos de rastreio seguem o formato do §5.3 | Apresentar a data como previsão registrada no snapshot, sem afirmar o estado atual da entrega |
| A10 | `customers` | Há um e-mail repetido entre clientes. Campos opcionais vazios em `orders`: `tracking_code` (12), `estimated_delivery` (12), `notes` (16) | O e-mail não identifica um cliente. Campos vazios viram `null` |
| A11 | Produtos 96, 130, 136 | 96 está ativo com estoque 0; 130 está `coming_soon` com 2 unidades; 136 está `discontinued` com 13 unidades | Nenhum aparece como disponível; cada estado é informado por escrito |

## Divergências entre materiais de apoio

| # | Onde | Achado | Tratamento |
| --- | --- | --- | --- |
| M1 | Nomes dos ZIPs | `01_Guia_Visao_e_Aplicacao.zip` contém o guia **03**; `03_Ressonancia_Branding.zip` contém o guia **01** | Organizados por conteúdo em `_insumos_privados/guias/{01-branding,02-backend,03-visao}` |
| M2 | Mockup da opção 1 × decisão aprovada | O mockup repete o avatar da loja em cada card e omite o atributo do produto | Segue a decisão: um avatar por turno, com atributo no card (D7) |
| M3 | Guia 02 §10 | Cita `ARTEFACT_REQUIREMENTS_V1.md` e `ARTEFACT_REFERENCIAS_REPOS_SKILLS.md` | Os dois arquivos não estavam entre os materiais recebidos; as decisões do guia 02 e do prompt da sessão prevalecem |
| M4 | Modelo Gemini | A preferência inicial era "3.1 Flash", mas a conta não lista esse ID. Existem `gemini-3.1-flash-lite`, `gemini-3-flash-preview`, `gemini-3.5-flash`, `3.6`, `3.7` e `3.8-flash` | Escolha por benchmark (D2) |
