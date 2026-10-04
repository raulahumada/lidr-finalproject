# Conventional Commits — front / back

Cómo redactar commits en este monorepo. Spec base: [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

Usar este documento al preparar un commit (humano o agente vía skill `commit-pr-development`).

---

## 1. Formato

```text
<type>[optional scope][optional !]: <description>

[optional body]

[optional footer(s)]
```

- Tras `type` / `scope` / `!` van **siempre** `: ` (dos puntos + espacio) y la descripción.
- Descripción: imperativo, presente, sin punto final. Enfocada en el **porqué** / el cambio de comportamiento, no en listar archivos.
- Body (opcional): una línea en blanco después de la descripción; contexto o detalle.
- Breaking change: `!` en el prefijo y/o footer `BREAKING CHANGE: …`.

---

## 2. Types

| Type | Cuándo |
|------|--------|
| `feat` | Nueva capacidad |
| `fix` | Corrección de bug |
| `docs` | Solo documentación |
| `refactor` | Cambio de estructura sin cambiar comportamiento |
| `perf` | Mejora de rendimiento |
| `test` | Solo tests |
| `build` | Build / dependencias |
| `ci` | CI |
| `chore` | Mantenimiento que no encaja arriba |
| `style` | Solo formato |
| `revert` | Revierte un commit previo |

---

## 3. Scope: front vs back

El **scope** indica en qué app vive el cambio. Usar el nombre de carpeta:

| Scope | Paths típicos |
|-------|----------------|
| `frontend` | `frontend/**` |
| `backend` | `backend/**` |

### Reglas

1. **Solo frontend** → scope `frontend`.
2. **Solo backend** → scope `backend`.
3. **Ambos en el mismo commit** → evitar si se puede. Preferir **dos commits** (uno `frontend`, uno `backend`). Si el cambio es inseparable (contrato compartido + cliente), usar sin scope o scope `repo` y explicar en el body.
4. **Docs / skills / openspec / raíz** (no app) → `docs`, `chore`, o scope omitido / `repo` según el type.
5. No inventar scopes por feature (`auth`, `rag`) **en lugar de** front/back; si hace falta más detalle, va en la descripción:

   ```text
   feat(backend): add RAG retrieval endpoint for omnicanalidad corpus
   feat(frontend): wire chat UI to health and estimate APIs
   ```

### Decisión rápida

```text
¿Los archivos tocados están solo bajo frontend/?  → (frontend)
¿Solo bajo backend/?                             → (backend)
¿Mezcla frontend + backend?                      → partir en 2 commits
¿Solo docs/ .cursor/ openspec/ AGENTS.md?        → docs/chore sin scope app
```

---

## 4. Ejemplos

### Backend

```text
feat(backend): add GET /api/v1/health readiness payload

fix(backend): reject empty title on item create

refactor(backend): extract items store helpers from routes

test(backend): cover items CRUD happy path
```

### Frontend

```text
feat(frontend): replace boilerplate home with Metropol shell

fix(frontend): correct API base URL for local backend

style(frontend): align spacing with Astryx tokens

chore(frontend): bump @astryxdesign/core
```

### Docs / repo

```text
docs: add conventional commits guide for front and back

chore: ignore local .env under backend
```

### Cambio inseparable (excepcional)

```text
feat: align items API contract between backend and frontend

Update ItemUpdate schema and the client form to the same optional fields
so partial updates do not drop description.
```

### Breaking

```text
feat(backend)!: rename items collection path to /api/v1/catalog

BREAKING CHANGE: clients calling /api/v1/items must migrate to /api/v1/catalog.
```

---

## 5. Ramas (opcional, alineado al PR)

Misma idea de type; el sufijo puede mencionar el área:

```text
feat/backend-health-endpoint
fix/frontend-api-base-url
docs/conventional-commits-guide
```

PR base: `development` (ver skill `commit-pr-development`).

---

## 6. Checklist antes de `git commit`

- [ ] Type correcto (`feat` vs `fix` vs `chore`…)
- [ ] Scope `frontend` o `backend` si el diff es de una sola app
- [ ] Si hay front **y** back: ¿se puede partir en dos commits?
- [ ] Descripción en imperativo, sin listar archivos
- [ ] Sin `.env` ni secretos en el stage
- [ ] Un solo propósito por commit
