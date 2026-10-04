# Entrega LiDR — Plataforma multiagente con RAG

Entrega del [Máster en AI Engineering de LIDR](https://www.lidr.co/ai-engineering/): una **plataforma multiagente con RAG**.

El **cliente** de la entrega es **Metropol Fintech**. Su documentación de negocio y sistemas (omnicanalidad, ventas, cobranzas, Tenela, etc.) es el **corpus del RAG** — conocimiento indexado para que los agentes respondan y razonen con contexto real. Esa documentación **no** es el software que se entrega en este repo.

---

## Qué se entrega aquí

| Se entrega | No se entrega |
|------------|---------------|
| Plataforma multiagente + RAG (este monorepo: API + UI) | Chatwoot, Rasa, Mautic ni el stack omnicanal del cliente |
| Orquestación de agentes, retrieval, experiencia de uso | Reimplementar la solución productiva de Metropol |
| AI Engineering aplicado a un cliente real | Solo demos sin dominio |

En una frase: *agentes + RAG sobre el conocimiento de Metropol Fintech*.

---

## Cliente: Metropol Fintech

Financiera de préstamos (MooviTech / Grupo Metropol). Dominios relevantes para el producto:

- **Ventas** — captación, recurrentes, ofertas, dictamen, solicitudes.
- **Cobranzas** — avisos de pago, medios, planes, promesas, quitas.
- **Operación omnicanal** — WhatsApp, campañas, handoff a humanos.
- **Core Tenela** — identidad, dictamen, simulación de préstamo, gestiones.

Problema que ataca la plataforma: el saber del cliente está en muchos documentos; hace falta un sistema que lo **recupere** (RAG), lo use con **agentes especializados** y dé respuestas alineadas al negocio, con camino a evaluación, citas y handoff.

> El cliente es Metropol **Fintech**, no una empresa de transporte.

---

## Documentación del cliente = corpus RAG

Fuente de conocimiento (no código de esta entrega):

- Carpeta de proyecto del cliente: *Metropol Fintech - Omnicanalidad (Agentes)*
- Notebook: [Metropol Fintech (NotebookLM)](https://notebooklm.google.com/notebook/15d6ea8b-2036-4548-8f8a-cf7aefb81d59)

Ahí viven cosas como flujos de ventas/cobranzas, documento funcional, propuesta, levantamientos, diagramas, integraciones Tenela, y docs de sus sistemas actuales (p. ej. referencias a inbox, bot, campañas). Todo eso **alimenta el índice RAG**. Mencionar Chatwoot, Rasa o Mautic en el corpus es hablar del **mundo del cliente**, no de dependencias de este monorepo.

### Dominios que el RAG debe cubrir

1. Ventas  
2. Cobranzas  
3. Arquitectura / operación omnicanal del cliente  
4. APIs y reglas Tenela  
5. Campañas y handoff humano  

---

## Visión de la plataforma

```text
Usuario / API / UI
        │
        ▼
   Orquestador  ──► agentes especializados (Ventas, Cobranzas, Docs, Operación, …)
        │
        ▼
      RAG  ◄── corpus Metropol Fintech (docs del cliente)
        │
        ▼
   LLM + tools / políticas / handoff
```

| Pieza | Rol |
|-------|-----|
| **Orquestador** | Enruta a agentes, estado, políticas |
| **Agentes** | Especializados por dominio del cliente |
| **RAG** | Recupera y cita el corpus Metropol |
| **Guardrails** | No inventar política; escalar si no hay evidencia |

Alineado al máster: producto con IA, RAG, multiagente, evaluación y operación — no “entrenar un modelo” como eje.

---

## Este monorepo

```text
entrega-lidr/
├── README.md     ← producto, cliente, corpus (este archivo)
├── AGENTS.md     ← cómo trabajar el código del repo
├── backend/      ← FastAPI
└── frontend/     ← Next.js + Astryx
```

Cómo correr API/UI: `AGENTS.md` y `frontend/AGENTS.md`.

---

## Fuentes

- [Máster AI Engineering — LIDR](https://www.lidr.co/ai-engineering/)
- Docs del cliente + [NotebookLM Metropol Fintech](https://notebooklm.google.com/notebook/15d6ea8b-2036-4548-8f8a-cf7aefb81d59)
