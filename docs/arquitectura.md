# Arquitectura

## Vision general

La aplicacion se organiza alrededor de FastAPI como proceso principal. Durante el arranque (`lifespan`) se inicializan la configuracion, el vector store Chroma, los clientes externos, el repositorio local de cartas custom, el LLM de Gemini y el grafo LangGraph.

El frontend estatico vive en `src/ui` y se sirve desde la misma API. El usuario envia mensajes a `/chat`; el router delega en el grafo del agente, y el agente decide si responde directamente o invoca herramientas.

## Componentes

### API FastAPI

Responsable de:

- Inicializar dependencias de aplicacion.
- Servir rutas HTTP.
- Montar archivos estaticos de `custom_cards/`.
- Servir el frontend y el PDF de reglas si `SERVE_FRONTEND=True`.

Archivos principales:

- `src/main.py`
- `src/api/chat.py`
- `src/api/health.py`
- `src/api/custom_cards.py`
- `src/ui/router.py`

### Agente LangGraph

El grafo principal se define en `src/agent/graph.py`.

Nodos:

- `agent`: llama al LLM con el prompt de sistema y las herramientas vinculadas.
- `tools`: ejecuta la herramienta solicitada por el LLM mediante `ToolNode`.

El checkpointer `MemorySaver` mantiene el historial de conversacion por `thread_id`, que se alimenta desde `session_id` en el endpoint `/chat`.

### Herramientas

Las herramientas disponibles para el agente son:

- `SearchRulesTool`: busca reglas en ChromaDB.
- `SearchCardsTool`: busca cartas en la API publica MTG.
- `SearchSetsTool`: busca expansiones en la API publica MTG.
- `CreateCustomCardTool`: disena, genera arte, renderiza y guarda una carta custom.

### RAG de reglas

El pipeline de ingesta lee `data/MagicCompRules 20260417.pdf`, extrae reglas con PyMuPDF y las guarda como documentos en ChromaDB.

El vector store se guarda en `.chroma_db/` y la coleccion por defecto es `mtg_rules`.

### Creacion de cartas custom

La creacion de cartas usa un subgrafo LangGraph:

1. El LLM genera una especificacion estructurada (`CardSpecs`).
2. El cliente de Imagen intenta generar una imagen.
3. `render_card` compone una carta PNG con Pillow.
4. `LocalCustomCardRepository` guarda PNG y JSON en `custom_cards/<nombre>/`.

## Dependencias externas

- Google Gemini para razonamiento del agente.
- Google Imagen para arte de cartas custom.
- Magic: The Gathering API publica para cartas y sets.
- ChromaDB local para busqueda vectorial.
- PyMuPDF para parsear el PDF.
- Pillow para renderizar cartas custom.

## Persistencia local

- `.chroma_db/`: base vectorial de reglas.
- `custom_cards/`: imagenes y metadatos JSON de cartas generadas.
- `.env`: configuracion local, especialmente `GEMINI_API_KEY`.

## Configuracion

La configuracion esta centralizada en `src/config/settings.py`.

Variables relevantes:

| Variable | Valor por defecto | Uso |
| --- | --- | --- |
| `SERVE_FRONTEND` | `True` | Activa el frontend estatico integrado |
| `GEMINI_API_KEY` | requerido | Clave para Gemini/Imagen |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Modelo principal del agente |
| `GEMINI_TEMPERATURE` | `0` | Temperatura del LLM |
| `CHROMA_DB_PATH` | `./.chroma_db` | Ruta de persistencia Chroma |
| `CHROMA_COLLECTION_NAME` | `mtg_rules` | Coleccion de reglas |
| `LANGSMITH_TRACING` | `False` | Activa trazas LangSmith |
