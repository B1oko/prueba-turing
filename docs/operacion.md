# Operacion y desarrollo

## Requisitos

- Python `>=3.12`.
- `uv` para gestionar entorno y comandos.
- Archivo `.env` con `GEMINI_API_KEY`.
- PDF de reglas en `data/MagicCompRules 20260417.pdf`.

## Variables de entorno

Ejemplo minimo:

```env
GEMINI_API_KEY=tu_clave
```

Opcionales:

```env
SERVE_FRONTEND=true
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0
CHROMA_DB_PATH=./.chroma_db
CHROMA_COLLECTION_NAME=mtg_rules
LANGSMITH_TRACING=false
```

## Instalacion local

```bash
uv sync
```

## Ingesta de reglas

La ingesta reconstruye `.chroma_db/` desde el PDF oficial.

```bash
uv run python ingestion/run_ingestion.py
```

Proceso:

1. Comprueba que existe el PDF.
2. Elimina la base vectorial anterior.
3. Parsea reglas y secciones con PyMuPDF.
4. Crea documentos con `rule_id`, `page` y `source`.
5. Inserta documentos en ChromaDB en lotes de 200.

## Ejecutar la API

```bash
uv run uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Con `SERVE_FRONTEND=True`, el frontend queda disponible en:

```text
http://127.0.0.1:8000/
```

## Ejecutar con Docker

```bash
docker compose up api
```

El compose expone:

- `8000:8000`
- `8501:8000`

Ambos puertos apuntan al mismo servicio FastAPI.

## Tests

```bash
uv run pytest tests/
```

Los tests actuales cubren:

- Ejecucion basica del grafo del agente con LLM mockeado.
- Busqueda de reglas con vector store mockeado.
- Busqueda de cartas con cliente MTG mockeado.
- Flujo de herramienta de creacion de carta con grafo mockeado.

## Datos persistidos

### `.chroma_db/`

Contiene la base vectorial local. Se puede regenerar con la ingesta.

### `custom_cards/`

Contiene subcarpetas por carta custom. Cada subcarpeta puede incluir:

- `<nombre>.png`: imagen renderizada de la carta.
- `<nombre>.json`: metadata serializada del modelo `Card`.

## Observabilidad

Si `LANGSMITH_TRACING=True` y `LANGSMITH_API_KEY` esta configurada, el arranque activa:

- `LANGSMITH_TRACING=true`
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`
- `LANGSMITH_ENDPOINT`

## Problemas comunes

### Falta `GEMINI_API_KEY`

`Settings` requiere `GEMINI_API_KEY` o `GOOGLE_API_KEY`. Si no esta presente, la aplicacion puede fallar durante el arranque.

### ChromaDB no inicializado

Ejecuta la ingesta antes de usar preguntas de reglas:

```bash
uv run python ingestion/run_ingestion.py
```

### PDF no encontrado

Comprueba que existe:

```text
data/MagicCompRules 20260417.pdf
```

### README menciona Streamlit

El codigo actual sirve frontend estatico desde FastAPI. Si se quiere recuperar Streamlit, habria que anadir de nuevo la carpeta/entrada correspondiente o actualizar el README principal.
