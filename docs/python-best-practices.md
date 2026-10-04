# Buenas prácticas Python — backend (`backend/`)

Guía operativa para este monorepo. Prioriza lo que ya hace el código; la arquitectura de capas del curso (`ai-service`, session_16) es **referencia de forma**, no plantilla a copiar ni dominio a reutilizar (aquí el dominio es Metropol Fintech / RAG + multiagente).

Usar este documento al proponer o implementar cambios con surface `backend` o `both`.

---

## 1. Stack y límites

| Pieza | En este repo |
|-------|----------------|
| Framework | FastAPI + Uvicorn |
| Settings | `pydantic-settings` + `.env` (`app/config.py`) |
| Schemas | Pydantic v2 (`app/schemas/`) |
| API | Routers bajo `app/api/routes/`, agregados en `app/api/router.py` |
| Prefijo | `/api/v1` vía `settings.api_prefix` |

- No añadir frameworks paralelos (Flask, Django, otro ASGI app) sin decisión explícita.
- Dependencias nuevas → `backend/requirements.txt` con piso de versión (`>=`), como el resto.
- No commitear `.env`; usar `.env.example` como plantilla.

---

## 2. Layout y factory

Patrón actual (mantenerlo):

```text
backend/app/
├── main.py          # create_app() + instancia `app`
├── config.py        # Settings + get_settings() cacheado
├── api/
│   ├── router.py    # agrega routers
│   └── routes/      # un módulo por recurso/área
└── schemas/         # contratos de request/response
```

- **Factory** `create_app()` en `main.py`: settings, CORS, `include_router`. Exports `app = create_app()` para Uvicorn.
- Routers **finos**: HTTP, status codes, `HTTPException`. Sin lógica de negocio gorda en la ruta.
- Extender routers/schemas existentes antes de inventar carpetas hermanas (`AGENTS.md`).
- Cuando crezca RAG / agentes / orquestación, adoptar capas al estilo del curso **dentro de `backend/app/`** (p. ej. `foundation/`, `domain/`, `generation/`), sin acoplar hermanos entre sí: composición en un conductor/servicio de dominio, no imports cruzados entre pipelines.

### Reglas de dependencia (objetivo al crecer)

De más bajo a más alto:

| Capa | Puede depender de | No debe depender de |
|------|-------------------|---------------------|
| `config` | (nada interno) | resto de `app` |
| foundation / infra | `config` | api, domain conductor, generation hermanos |
| schemas / domain contracts | `config`, foundation | api, generation |
| generation / rag / agents | config, foundation, schemas | api; **otros hermanos de generation** |
| conductor / domain service | generation + foundation + schemas | api (salvo excepciones puntuales) |
| `api` | dependencies, schemas, conductor | lógica de negocio inline |
| `main` | api, config | domain profundo |

Si una pieza no encaja, decidir capa (y documentar) antes de crear una carpeta suelta en la raíz de `app/`.

---

## 3. Settings

- Una sola clase `Settings(BaseSettings)` con `SettingsConfigDict(env_file=".env", extra="ignore")`.
- Acceso vía `get_settings()` con `@lru_cache` — no instanciar `Settings()` suelto en rutas.
- Listas desde env como string + property (ej. `cors_origins` → `cors_origins_list`).
- Tipado explícito; defaults seguros para desarrollo local.
- Secretos solo por env; nunca hardcodear keys/tokens en código.

---

## 4. Schemas (Pydantic v2)

- Separar **Create / Update / response** (como `ItemCreate`, `ItemUpdate`, `Item`).
- `Field(...)` con `min_length` / `max_length` donde aplique.
- Update parcial: campos `T | None = None` + `model_dump(exclude_unset=True)` + `model_copy(update=...)`.
- `ConfigDict(from_attributes=True)` en modelos de salida cuando vengan de ORM/objetos.
- Usar `response_model` en path operations; no devolver dicts crudos en APIs de dominio (la raíz `/` puede ser excepción mínima).

---

## 5. Rutas y HTTP

- `APIRouter(prefix=..., tags=[...])` por recurso; registrar en `api/router.py`.
- Status codes explícitos: `201` create, `204` delete, `404` con `HTTPException` + `status.HTTP_*`.
- Tipar parámetros y retornos (`-> Item`, `-> list[Item]`, `-> None`).
- Preferir `datetime.now(timezone.utc)` (aware) frente a `datetime.utcnow()`.
- Prefijo de versión solo en el include de `main` / settings, no repetirlo en cada router.

---

## 6. Estilo Python

- Python 3.10+ syntax del repo: `str | None`, `list[Item]`, `dict[int, Item]` (no `Optional`/`List`/`Dict` de `typing` salvo necesidad).
- Imports absolutos desde `app.` (`from app.schemas.item import Item`).
- Funciones/módulos pequeños; nombres descriptivos en `snake_case`.
- Sin lógica de negocio en `__init__.py` (paquetes marcadores).
- Evitar `global` salvo stores temporales documentados (hoy: items en memoria); al persistir, sustituir por capa de persistencia.

---

## 7. Persistencia y estado

- Hoy: store en memoria en el módulo de rutas — válido como stub, **no** como patrón definitivo.
- Al introducir DB: repos/adapters en foundation/persistence (o equivalente), schemas de dominio separados del transporte, migraciones acordadas; no SQL crudo en routers.
- No asumir que el estado sobrevive al reload de Uvicorn.

---

## 8. CORS, health y operación

- CORS desde settings; orígenes explícitos en env.
- Health en `GET {api_prefix}/health` — mantenerlo liviano y sin auth pesada.
- Docs OpenAPI en `/docs` (FastAPI default); no romper el contrato público sin bump o nota en la proposal.
- Arranque local: `uvicorn app.main:app --reload` desde `backend/` con venv.

---

## 9. Tests y calidad (mínimo esperado al crecer)

- Tests de API con `TestClient` / httpx AsyncClient cuando haya comportamiento no trivial.
- Nuevos endpoints: al menos happy path + 404/validación relevante.
- No añadir lint/format tooling ad-hoc distinto al del equipo sin pedirlo; si se añade, documentarlo en `AGENTS.md`.

---

## 10. Checklist anti-deriva (para proposals)

Al proponer un cambio backend, contrastar explícitamente:

1. ¿Vive en la capa correcta (api vs schema vs servicio vs foundation)?
2. ¿Extiende routers/schemas existentes o inventa un paralelo injustificado?
3. ¿Routers siguen finos (sin negocio / sin LLM calls directos en la ruta)?
4. ¿Settings solo vía `get_settings()`?
5. ¿Schemas Create/Update/Response claros y tipados?
6. ¿Alineado a capas del curso *como forma*, sin copiar dominio del estimador?
7. ¿Secretos y CORS fuera del código?
8. ¿Impacto en contrato `/api/v1` documentado?

Si hay desviación consciente, nombrarla en la proposal/design (sección **Practices check**) con motivo.
