# finanzas_agent

Copiloto conversacional de finanzas personales y nutrición, construido con LangChain y LangGraph como
proyecto de aprendizaje incremental.

## Arranque

Requiere [`uv`](https://docs.astral.sh/uv/). El intérprete (Python 3.12.3) lo fija `.python-version`.

```bash
uv sync          # crea .venv e instala dependencias exactas de uv.lock
uv run pytest
```

## Documentación

- [`docs/arquitectura.md`](docs/arquitectura.md) — arquitectura y decisiones (ADR).
- [`docs/plan_fases.md`](docs/plan_fases.md) — plan por fases y Definition of Done (fuente de verdad del estado).
- [`docs/prompt_proyecto_langchain_finanzas_nutricion.md`](docs/prompt_proyecto_langchain_finanzas_nutricion.md) — encargo original.
- `docs/arquitectura_solucion.md`, `docs/anexo_arquitectura_objetivo.md` — referencia del proyecto anterior
  (`personal_assistant_agent`); no describen este repositorio.
