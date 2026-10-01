# Plan de fases y Definition of Done

**Fuente de verdad del estado del proyecto.** Se actualiza al cerrar cada ítem, con evidencia verificable
(qué test, qué comando, qué resultado), no con narración. Arquitectura y decisiones: `arquitectura.md`.

## Cómo se trabaja

**Ciclo por ítem:** (1) intro: qué es, por qué y qué beneficio trae → (2) aprobación explícita →
(3) implementar → (4) verificar: `ruff`, `mypy`, suite completa incluida la integración con Mongo real →
(5) documentar aquí con evidencia → (6) commit de una línea en formato convencional.

**Cada fase cierra con cuatro cosas:**

1. **Conceptos:** qué se aprende de LangChain/LangGraph (o del stack).
2. **Entregable funcional:** el sistema queda funcionando.
3. **Contraste:** cómo lo resolvió `personal_assistant_agent` y qué aporta o cobra el framework.
4. **Evidencia DoD.**

**Principio pedagógico:** cuando el framework ofrece una abstracción de alto nivel, primero se construye la
versión explícita, se observa en una traza y luego se sustituye. Se entiende lo que se usa.

**Hallazgos:** cualquier bug, deuda o supuesto que no se sostenga se registra como ítem propio
(*hallazgo*) en la fase en que aparece, con dueño y estado. Nunca se arregla en silencio dentro de otro ítem.

**Leyenda:** ⬜ pendiente · 🔄 en curso · ✅ hecho · ⏸️ bloqueado · ❌ descartado (con motivo).
Niveles: 🟢 higiene inmediata · 🟡 industrialización esperable · 🔴 vanguardia opcional (solo con criterio).

## Resumen

| Fase | Tema | Conceptos principales | Estado |
| --- | --- | --- | --- |
| 0 | Esqueleto | `uv`, `pyproject`, `ruff`/`mypy`, `Settings`, `structlog`, Mongo async, CI | ⬜ |
| 1 | LangChain sin grafo | chat models, mensajes, prompts, salida estructurada, `@tool`, tool calling manual | ⬜ |
| 2 | Primer grafo | `StateGraph`, estado/reducers, nodos, edges, `ToolNode`, ReAct a mano → `create_agent`, streaming, LangSmith, Studio | ⬜ |
| 3 | Memoria y persistencia | checkpointer, `thread_id`, historial de estado, store de largo plazo, resumen | ⬜ |
| 4 | Human-in-the-loop, guardrails y API | `interrupt`, `Command(resume)`, límites, contexto de ejecución, `Principal`, `/chat` | ⬜ |
| 5 | Medir antes de crecer | golden dataset, evals, LLM-as-judge | ⬜ |
| 6 | Segunda vertical: nutrición | contrato de dominio reutilizable, cálculo determinista | ⬜ |
| 7 | Orquestación multidominio | supervisor, subgrafos, `Command`, `Send`, router barato como nodo | ⬜ |
| 8+ | Extensiones | MCP de entrada, despliegue, canales, privacidad | ⬜ |

---

## Fase 0 — Esqueleto

**Conceptos:** gestión de dependencias con `uv`, layout `src/`, tipado estricto, configuración validada,
logging estructurado, Mongo async, CI. Sin LLM.
**Contraste:** en el proyecto anterior todo esto se corrigió sobre la marcha (Fases 0–1 de su anexo); aquí se
nace con ello y se evitan los fallos silenciosos (bridging, drift de dependencias, tests contra Atlas).

| # | Ítem | Nivel | Estado | Evidencia |
| --- | --- | --- | --- | --- |
| 0.1 | `pyproject.toml` + `uv.lock` + layout `src/`; decidir nombre del paquete (propuesta: `copilot`) y versión mínima de Python | 🟢 | ⬜ | |
| 0.2 | `ruff` (lint + format) y `mypy --strict` en todo el repo; configuración de `pytest` con marcadores `integration`/`eval` | 🟢 | ⬜ | |
| 0.3 | `Settings` único (`pydantic-settings`, `SecretStr`), falla ruidosa si falta configuración; `.env.example` con comentario por variable | 🟢 | ⬜ | |
| 0.4 | `structlog` en JSON **a stderr**; `request_id` por contextvars en middleware ASGI puro | 🟢 | ⬜ | |
| 0.5 | `docker-compose.yml` solo con Mongo en `27018`; fixture de test con base de datos aleatoria por sesión que se elimina al final; guard que hace fallar un test si la URI no es local | 🟢 | ⬜ | |
| 0.6 | Cliente Mongo con PyMongo Async API, ciclo de vida ligado al `lifespan`; test de integración de ida y vuelta (escribir con una instancia, leer con otra); verificar compatibilidad con los paquetes de checkpointer/store de LangGraph para Mongo y registrar el resultado | 🟢 | ⬜ | |
| 0.7 | `bootstrap.py` como composition root único; FastAPI con app factory en `interfaces/api/` y `GET /health` (con ping a Mongo) | 🟢 | ⬜ | |
| 0.8 | Test de reglas de dependencia entre capas (`import-linter` o equivalente) | 🟢 | ⬜ | |
| 0.9 | GitHub Actions: `ruff`, `mypy`, unitarios, integración con Mongo como service container, `gitleaks`, caché de `uv` | 🟢 | ⬜ | |
| 0.10 | `README.md`: clone → `uv sync` → `docker compose up -d mongo` → `uv run pytest` | 🟢 | ⬜ | |

**DoD de fase:** en una máquina limpia, `uv sync && uv run pytest` pasa con la integración real incluida;
CI en verde; ningún secreto en el repo; ningún `os.getenv` fuera de `config.py`.

## Fase 1 — LangChain sin grafo + dominio de finanzas

**Conceptos:** `init_chat_model`, tipos de mensaje, plantillas de prompt, salida estructurada
(`with_structured_output`), `@tool` y su esquema, tool calling "a mano" (invocar el modelo, leer
`tool_calls`, ejecutar, devolver `ToolMessage`).
**Contraste:** `_OpenAITextClient` y la cadena de parches de parsing/JSON mode del proyecto anterior
(sus ítems 2.11–2.13) frente al contrato tipado del framework.

| # | Ítem | Nivel | Estado | Evidencia |
| --- | --- | --- | --- | --- |
| 1.1 | Dominio: `Money` (`Decimal` + moneda ISO 4217), `Movimiento`, `Categoria`, `Principal`; reglas de cálculo puras con tests unitarios | 🟢 | ⬜ | |
| 1.2 | Port `MovimientoRepository` + adaptador Mongo (`Decimal128`, índices con `tenant_id` primero, borrado lógico) + test de integración por operación | 🟢 | ⬜ | |
| 1.3 | Servicio de aplicación de finanzas (registrar, listar con filtros, resumen por categoría/periodo, eliminar) | 🟢 | ⬜ | |
| 1.4 | Fábrica de modelos con `init_chat_model`; timeouts y reintentos explícitos; prompts versionados como ficheros | 🟢 | ⬜ | |
| 1.5 | Extracción estructurada: texto libre → `MovimientoPropuesto` validado por Pydantic; script de demostración | 🟢 | ⬜ | |
| 1.6 | Tools de finanzas con `@tool` (envoltorios del servicio); tests de contrato del esquema (sin `tenant_id` expuesto) | 🟢 | ⬜ | |
| 1.7 | Bucle de tool calling manual (sin grafo) para entender el ciclo modelo → tool → modelo | 🟢 | ⬜ | |

**DoD de fase:** un mensaje como "gasté 45.000 en el mercado ayer" queda persistido con monto exacto,
moneda y fecha correctas, verificado contra Mongo real; ninguna cuenta la hace el LLM.

## Fase 2 — Primer grafo

**Conceptos:** `StateGraph`, estado tipado y reducers (`add_messages`), nodos, edges, aristas condicionales,
`ToolNode`, compilación, `invoke` vs. `stream` (modos `values`/`updates`/`messages`), `recursion_limit`.
Luego `create_agent` como versión prefabricada. Trazas en LangSmith y visualización en LangGraph Studio.
**Contraste:** el `agent.py` del proyecto anterior (bucle propio de tool calling, contadores de pasos a mano)
frente a un grafo explícito, inspeccionable y dibujable.

| # | Ítem | Nivel | Estado | Evidencia |
| --- | --- | --- | --- | --- |
| 2.1 | Grafo ReAct de finanzas construido a mano (`StateGraph` + nodo modelo + `ToolNode` + arista condicional) | 🟢 | ⬜ | |
| 2.2 | Tests del grafo con modelo falso (respuestas y `tool_calls` predefinidos), sin red | 🟢 | ⬜ | |
| 2.3 | Streaming de pasos y tokens; CLI mínima de prueba | 🟢 | ⬜ | |
| 2.4 | LangSmith opt-in por configuración; `langgraph.json` + `langgraph dev` para Studio | 🟢 | ⬜ | |
| 2.5 | Sustituir por `create_agent`; documentar qué hace igual, qué agrega (middleware) y qué oculta | 🟢 | ⬜ | |
| 2.6 | Definir el contrato de dominio (tools + prompt + subgrafo) aplicado a finanzas | 🟢 | ⬜ | |

**DoD de fase:** el agente registra y consulta movimientos; la traza de una interacción muestra cada nodo y
tool call; existe la nota comparativa grafo manual vs. `create_agent`.

## Fase 3 — Memoria y persistencia

**Conceptos:** checkpointer (`InMemorySaver` → Mongo), `thread_id`, `get_state`/`get_state_history`,
reanudar y "viajar en el tiempo", store de largo plazo con namespaces, recorte y resumen de mensajes.
**Contraste:** el bug de pérdida silenciosa de memoria y el `ContextBuilder` propio del proyecto anterior.

| # | Ítem | Nivel | Estado | Evidencia |
| --- | --- | --- | --- | --- |
| 3.1 | Checkpointer en memoria; observar el estado por `thread_id` y su historial | 🟢 | ⬜ | |
| 3.2 | Checkpointer sobre Mongo; test: escribir con un grafo compilado, leer con otro nuevo, contra Mongo real | 🟢 | ⬜ | |
| 3.3 | Store de largo plazo con namespace `(tenant_id, user_id)`; extracción de hechos de perfil gated por confianza (moneda por defecto, presupuesto, restricciones) | 🟢 | ⬜ | |
| 3.4 | Presupuesto de contexto: recorte/resumen de mensajes; medir tokens enviados | 🟢 | ⬜ | |
| 3.5 | Política de retención (TTL) de checkpoints y borrado por usuario | 🟡 | ⬜ | |

**DoD de fase:** una conversación sobrevive al reinicio del proceso; los hechos de perfil sobreviven entre
conversaciones; ambos verificados contra Mongo real.

## Fase 4 — Human-in-the-loop, guardrails y API

**Conceptos:** `interrupt()`, `Command(resume=...)`, límites de pasos/llamadas, contexto de ejecución
(`tenant_id`/`user_id` llegan a las tools sin pasar por el LLM), autenticación.
**Contraste:** la confirmación inerte del proyecto anterior (su 4.16) y la autenticación tardía.

| # | Ítem | Nivel | Estado | Evidencia |
| --- | --- | --- | --- | --- |
| 4.1 | `Principal` desde credencial (API key con hash) y propagación como contexto de ejecución del grafo | 🟢 | ⬜ | |
| 4.2 | Confirmación con `interrupt()` para operaciones destructivas; reanudación en otra petición; test de comportamiento real | 🟢 | ⬜ | |
| 4.3 | Guardrails: whitelist de tools, límite de pasos y de llamadas a modelo/tools por interacción, con tests | 🟢 | ⬜ | |
| 4.4 | `POST /chat` autenticado con streaming; errores saneados con `request_id` | 🟢 | ⬜ | |
| 4.5 | Validación de entrada (longitud de mensaje, tipos) y rate limiting básico | 🟡 | ⬜ | |

**DoD de fase:** ningún endpoint que mute datos responde sin autenticación; borrar un movimiento exige
confirmación persistida; los límites del agente están cubiertos por tests.

## Fase 5 — Medir antes de crecer

**Conceptos:** golden dataset, evaluadores, evals opt-in, datasets/experimentos en LangSmith, LLM-as-judge
calibrado.
**Contraste:** se replica lo que funcionó (golden dataset, umbrales en CI) y se corrige lo que no (prompts
cambiados sin volver a evaluar).

| # | Ítem | Nivel | Estado | Evidencia |
| --- | --- | --- | --- | --- |
| 5.1 | Golden dataset de finanzas (≥100 casos: fáciles, ambiguos → `clarify`, adversarios, montos/fechas difíciles) | 🟢 | ⬜ | |
| 5.2 | Runner de evaluación opt-in con métricas (exactitud de tool y argumentos, tasa de `clarify`, tokens, latencia) y umbrales versionados | 🟢 | ⬜ | |
| 5.3 | Job de CI bajo demanda que bloquea regresiones | 🟡 | ⬜ | |
| 5.4 | LLM-as-judge offline para la respuesta final, calibrado contra ~30 juicios humanos | 🟡 | ⬜ | |
| 5.5 | Regla: todo cambio de prompt o de modelo cierra con eval corrido y resultado anotado | 🟢 | ⬜ | |

**DoD de fase:** existe una línea base de calidad y coste del agente de finanzas, reproducible con un comando.

## Fase 6 — Segunda vertical: nutrición

**Conceptos:** reutilizar el contrato de dominio; cálculo nutricional determinista en tools.

| # | Ítem | Nivel | Estado | Evidencia |
| --- | --- | --- | --- | --- |
| 6.1 | Decisión documentada sobre fuente de datos nutricionales (tabla propia vs. USDA / Open Food Facts) | 🟢 | ⬜ | |
| 6.2 | Dominio de nutrición (comida, porción, macros, restricciones, objetivos) + repositorio + tests de integración | 🟢 | ⬜ | |
| 6.3 | Tools y subgrafo de nutrición siguiendo el contrato de dominio, sin tocar finanzas | 🟢 | ⬜ | |
| 6.4 | Golden dataset de nutrición | 🟢 | ⬜ | |
| 6.5 | Tratamiento de datos de salud: qué sale hacia el proveedor LLM, retención, cifrado por campo (criterio) | 🟡 | ⬜ | |

**DoD de fase:** añadir nutrición no modificó código de finanzas (verificable en el diff); evals de ambos
dominios en verde.

## Fase 7 — Orquestación multidominio

**Conceptos:** supervisor, subgrafos, traspasos con `Command(goto=...)`, ejecución paralela con `Send`,
router barato como nodo (reglas → clasificación estructurada → `clarify`).
**Contraste:** el router `if/else` y la ruta `multi_task` del proyecto anterior frente a nodos y aristas.

| # | Ítem | Nivel | Estado | Evidencia |
| --- | --- | --- | --- | --- |
| 7.1 | Nodo de reglas deterministas + nodo de clasificación estructurada + `clarify` | 🟢 | ⬜ | |
| 7.2 | Supervisor que delega en subgrafos de finanzas y nutrición | 🟢 | ⬜ | |
| 7.3 | Mensajes mixtos con `Send` en paralelo y agregación de resultados | 🟡 | ⬜ | |
| 7.4 | Decisión medida: supervisor vs. agente único con todas las tools, comparados con el eval de la Fase 5 | 🟢 | ⬜ | |
| 7.5 | Métrica de % de peticiones resueltas sin LLM | 🟢 | ⬜ | |

**DoD de fase:** un solo asistente atiende ambos dominios y mensajes mixtos; la arquitectura elegida está
justificada con números.

## Fase 8+ — Extensiones (priorizar al llegar)

| # | Ítem | Nivel |
| --- | --- | --- |
| 8.1 | Servidor MCP como adaptador de entrada sobre los mismos servicios | 🟡 |
| 8.2 | Dockerfile multi-stage y despliegue | 🟡 |
| 8.3 | Frontend o canal de voz sobre `/chat` | 🟡 |
| 8.4 | Multi-tenancy activa, cuotas y coste por tenant | 🟡 |
| 8.5 | Derecho al olvido en cascada verificado por test | 🟡 |

## Hallazgos

| # | Fase | Hallazgo | Estado |
| --- | --- | --- | --- |
| — | — | (ninguno todavía) | — |
