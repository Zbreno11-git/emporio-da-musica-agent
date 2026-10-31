# References and skills

## Claude Code skills installed in the project

Installed in `.claude/skills/<name>/` on 2026-10-31. The directory is ignored by Git ([D9](DECISIONS.md)). Integrity was checked by comparing the blob SHA of each local file with the tree of the pinned commit.

| Skill | Source | Commit | Files | License | Intended use | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `frontend-design` | [anthropics/skills](https://github.com/anthropics/skills/tree/ca45fc496a3436251f191354091d557da31c15b5/skills/frontend-design) | `ca45fc4` | `SKILL.md`, `LICENSE.txt` | Apache-2.0 | Implement and review the already approved Ressonância screen, without exploring a new identity | Installed; blobs identical to the commit |
| `webapp-testing` | [anthropics/skills](https://github.com/anthropics/skills/tree/ca45fc496a3436251f191354091d557da31c15b5/skills/webapp-testing) | `ca45fc4` | `SKILL.md`, `LICENSE.txt`, `scripts/with_server.py`, `examples/*.py` (3) | Apache-2.0 | Playwright in Python: Takamine + PIX flow, cross-profile order, profile switch, 320/390 px/desktop | Installed; blobs identical. Playwright not yet installed in `.venv` |
| `qa-response` | [composio-community/support-skills](https://github.com/composio-community/support-skills/tree/83382c4b055fc4e5b055044adb5bfb7585484c9a/qa-response) | `83382c4` | `SKILL.md` | Ambiguous (no LICENSE; README says Apache-2.0 in the badge and MIT in the section) | Review real conversations together with tool results and manual sections. Explicit invocation only (`disable-model-invocation: true`) | Installed; blob `500fb25` checked |

**Pending activation.** Project skills are read from `.claude/skills/`. If they do not show up in the current session, restart Claude Code in the project directory and check `/frontend-design`, `/webapp-testing` and `/qa-response`. Because `qa-response` is explicit-only, it never appears among model-invoked skills.

**Equivalent copies.** Breno's environment already had `frontend-design` and `webapp-testing` in the personal scope, from commit `34040c9`. Their files are identical to `ca45fc4`, and the project copy takes precedence. There is also a `frontend-design` plugin from the official marketplace.

**Reinstall** (only each skill's folder):

```bash
for p in frontend-design webapp-testing; do
  gh api "repos/anthropics/skills/git/trees/ca45fc496a3436251f191354091d557da31c15b5?recursive=1" \
    --jq ".tree[]|select(.type==\"blob\" and (.path|startswith(\"skills/$p/\")))|.path" |
  while read f; do mkdir -p ".claude/$(dirname "${f}")"; gh api "repos/anthropics/skills/contents/$f?ref=ca45fc4" --jq .content | base64 -d > ".claude/$f"; done
done
mkdir -p .claude/skills/qa-response
gh api "repos/composio-community/support-skills/contents/qa-response/SKILL.md?ref=83382c4b055fc4e5b055044adb5bfb7585484c9a" --jq .content | base64 -d > .claude/skills/qa-response/SKILL.md
```

Breno also uses a personal process skill, `software-build`, which organizes continuity documents, sessions with checkpoints and the definition of done. It stays in his personal environment and its content is not distributed in this repository.

## Reference repositories (read, not copied)

Commits pinned by guide 03. These examples teach techniques; the business rules come from the manual and the CSVs.

| Reference | What to take | What to leave out |
| --- | --- | --- |
| [Gemini Cookbook · Function calling](https://github.com/google-gemini/cookbook/blob/b06b824cf2ea29f9543ffa14adcee68b5f934a9b/quickstarts/Function_calling.ipynb) | Declarations, manual dispatch, returning the result | Automatic calling modes |
| [Gemini Cookbook · SQL Agent](https://github.com/google-gemini/cookbook/blob/b06b824cf2ea29f9543ffa14adcee68b5f934a9b/examples/langchain/SQL_Agent_Gemini_LangChain.ipynb) | Schema in the prompt; filters and ordering | LangChain, sample database, Colab |
| [Gemini Cookbook · Embeddings](https://github.com/google-gemini/cookbook/blob/b06b824cf2ea29f9543ffa14adcee68b5f934a9b/quickstarts/Embeddings.ipynb) | Query vs. document task types; index version and hash | — |
| [Pydantic AI · bank_support.py](https://github.com/pydantic/pydantic-ai/blob/2a89126b7a968ae7664348dc055717e0e2bb61f9/examples/pydantic_ai_examples/bank_support.py) | Identity comes from context dependencies, not from a model argument | Banking operations, global cursor, a second orchestration stack |
| [flaviagaia/agente_atendimento](https://github.com/flaviagaia/agente_atendimento/tree/57405d5722cd2230a78862dacbb4e97208b25b57) | Separating customer speech from operational data (`text`, `cards`, `sources`, `next_action`) | Streamlit, ticket categories. No license found: reference only |
| [Renatoelho/atendimento-agentes-ia](https://github.com/Renatoelho/atendimento-agentes-ia/blob/c5400b11b2e1bc215c0a06487222c27a7845e426/docker-compose.yaml) | Summarizing the case for a human | NiFi, MySQL, MinIO, Elasticsearch, Kibana |
| [Bhavik-Jikadara/ai-customer-service-agent](https://github.com/Bhavik-Jikadara/ai-customer-service-agent/blob/4ecde05848eb0e062d378e2ef59dfe169f7790ea/src/customer_service_agent/tools.py) | Readable tool registry | Automatic refund approval |
