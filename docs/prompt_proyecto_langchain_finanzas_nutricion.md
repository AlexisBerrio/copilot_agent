# Prompt inicial: copiloto de finanzas personales y nutrición (LangChain/LangGraph)

Prompt autocontenido para entregar a un agente de código que arranque un proyecto nuevo desde
cero. Destila lo que funcionó (y lo que costó aprender) en `personal_assistant_agent`
(asistente de tareas con router propio + MCP), para replicarlo con un stack centrado en
LangChain/LangGraph y un dominio distinto. No es continuación de ese repo — es un proyecto
nuevo, en su propio directorio/repositorio.

---

## Prompt para el agente

Vas a construir **un copiloto conversacional de finanzas personales y nutrición**: un asistente
que, por lenguaje natural, registra gastos/ingresos, responde preguntas sobre el estado
financiero del usuario, registra comidas y sugiere qué comer según restricciones
alimentarias y objetivos nutricionales. Las dos verticales comparten un solo asistente y un solo
historial conversacional — no son dos apps separadas. Ademas, debe ser escalable para llevar en un futuro nuevos dominios si es necesario.

### Stack obligatorio

- Python, `LangChain` y `LangGraph` para la orquestación del agente (no un router de intención
  hecho a mano — ese fue el enfoque del proyecto anterior; acá el objetivo es aprender el
  framework).
- FastAPI para la API HTTP.
- MongoDB para persistencia (tareas/gastos/comidas, memoria de sesión, hechos de perfil).
- `pytest` con tests de integración reales contra Mongo (no todo mockeado).

### Decisiones de arquitectura a tomar vos mismo, con criterio explícito (no las traigas ya
### decididas del proyecto anterior — evalualas para este stack y dominio)

1. **¿Multi-agente o un solo agente con muchas tools?** LangGraph tiene soporte nativo para un
   patrón supervisor/sub-agentes (ej. un agente de finanzas, un agente de nutrición, un
   supervisor que rutea). Evaluá si conviene sobre un único agente con todas las tools
   disponibles — el criterio debería ser complejidad real del dominio, no novedad del patrón.
2. **¿Las tools viven detrás de un protocolo MCP, o son tools nativas de LangChain?** El
   proyecto anterior forzó **todas** las acciones de escritura a pasar por un único cliente MCP
   (una sola vía de ejecución, testeable con el protocolo real, sin mocks del lado del agente).
   Esa separación (proceso de negocio vs. proceso de orquestación del LLM) valió la pena para
   testabilidad y boundaries de seguridad — considerala, pero no la copies mecánicamente si
   LangChain ya te da suficiente aislamiento con sus herramientas nativas.
3. **Memoria:** LangChain trae abstracciones de memoria (buffers, summarizers) — no confíes en
   que "solo funcionan". En el proyecto anterior, un bug real de bridging async/sync entre
   Motor (MongoDB) y el loop de eventos causó pérdida silenciosa de memoria de sesión durante
   semanas, sin que ningún test lo detectara porque todos mockeaban el repositorio. Sea cual sea
   la abstracción de memoria que uses, agregá **al menos un test de integración que escriba con
   una instancia y lea con otra, contra Mongo real** — es la única forma real de detectar esa
   clase de bug.

### Guardrails no negociables (aprendidos del proyecto anterior, aplican más todavía acá por
### tratarse de dinero real)

- **Confirmación humana explícita antes de cualquier operación irreversible o de alto impacto**
  — borrar un registro de gasto, marcar un objetivo financiero como completado, etc. En el
  proyecto anterior esto se limitó a operaciones destructivas específicas (no todo write) tras
  una decisión explícita de scope — replicá ese criterio: pedí confirmación en lo destructivo/
  irreversible, no en cada escritura.
- **Presupuesto de tokens/pasos por interacción** — límite duro para que el agente no entre en
  un loop de tool-calling costoso o infinito.
- **Ningún endpoint público sin autenticación**, ninguna tool sin whitelist explícita de qué
  puede hacer.
- **`tenant_id`/`usuario_id` viaja por todo el flujo desde el primer commit**, aunque al
  principio solo haya un usuario. Agregarlo después obliga a migrar datos.

### Metodología de trabajo (replicar tal cual, funcionó bien)

Desarrollo incremental por fases, cada cambio con su propio ciclo:

1. **Intro** — antes de implementar cualquier ítem, explicá qué es, por qué, y qué beneficio
   trae. Pedí aprobación explícita.
2. **Esperar aprobación explícita** — no asumas luz verde por silencio ni por haber discutido el
   tema; esperá una confirmación clara antes de tocar código.
3. **Implementar.**
4. **Verificar** — lint, type-check, y la suite de tests completa (incluyendo los de
   integración contra Mongo real) antes de dar algo por cerrado.
5. **Documentar** — un documento vivo tipo DoD (Definition of Done) por fases, con una tabla de
   ítems, su estado y evidencia concreta de qué se verificó — no una narración, evidencia
   verificable (qué test corrió, qué comando, qué resultado).
6. **Mensaje de commit** — una sola línea, formato convencional, después de cada ítem cerrado.

Cuando encuentres una inconsistencia real durante la implementación de un ítem (un bug, una
deuda técnica, un supuesto que no se sostiene), no lo escondas ni lo arregles en silencio como
parte de otra cosa: registralo como un ítem propio ("hallazgo") en el documento de DoD, con su
propio estado.

### Reglas de estilo y colaboración

- Comentarios de código: solo cuando el porqué no es obvio (una restricción oculta, un
  workaround, un invariante no evidente). Nunca expliques QUÉ hace el código si el nombre ya lo
  dice. Nunca cites referencias a ítems del documento de DoD (ej. "ver ítem 3.2") dentro de un
  comentario o docstring de código — esas referencias van en el documento de DoD, no en el
  código, porque el código sobrevive a la reorganización del documento y la referencia queda
  obsoleta.
- Sin respuestas conversacionales estáticas: cualquier respuesta que el asistente le da al
  usuario en lenguaje natural (saludos, confirmaciones, aclaraciones) se genera por LLM en cada
  turno, nunca un string fijo hardcodeado.
- No implementes evals costosos (LLM real contra un dataset dorado) de forma automática en cada
  corrida de tests — son opt-in, se corren deliberadamente al tocar un prompt, y su resultado se
  valida de verdad (no se documenta "sin correr" y se sigue adelante).
- Sin sobre-ingeniería: no abstraigas para una hipotética fase futura que todavía no llegó. Tres
  líneas parecidas están bien; una abstracción prematura no.

### Primer entregable esperado

No arranques escribiendo código. Como primer entregable, proponé:

1. Una arquitectura en capas (dominio/aplicación/infraestructura/interfaces, o el equivalente
   que uses) con una breve justificación de las decisiones de la sección "Decisiones de
   arquitectura" de arriba.
2. Un plan de fases (Fase 0: setup y esqueleto, Fase 1: primera vertical end-to-end —
   probablemente finanzas, más simple de modelar que nutrición—, Fase 2: segunda vertical, Fase
   3: orquestación multi-dominio, Fase 4+: lo que corresponda, etc.) con ítems concretos por fase,
   mismo formato de tabla que el DoD descripto arriba.
3. Esperá aprobación de ese plan antes de tocar código.
4. Tienes la potestad de elegir que cosas tomar del proyecto anterior y que se descarta o evoluciona pero siempre pensando en escalabilidad y vanguardia.
5. Vas a tener acceso a la arquietctura y DoD anteriores para entender que se hizo pero no debe ser todo igual, debes mejorar lo mejorable y dar el enfoque a los frameworks.
6. Vale la pena que en etapas paralelas que see implementan de forma distinta en ambos proyectos (como la memoria, nodos, edges, etc.) hagas mayor enfasis para entender las ventajas de trabajar con frameworks y no codigo libre como se trabajo esta implementación.
