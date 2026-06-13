---
name: Arquitectura Chatbot MTG
overview: Diseño de un agente conversacional para Magic the Gathering usando LangGraph + Gemini (API gratuita de Google), con RAG sobre el reglamento en PDF y herramientas para consultar la API de MTG.
todos:
  - id: ingestion
    content: "Implementar pipeline de ingestion: PDF parsing con PyMuPDF, chunking, embeddings Google y carga en ChromaDB HTTP (cliente-servidor)"
    status: pending
  - id: tools
    content: "Implementar las 4 herramientas: search_rules (RAG), search_cards (MTG API), get_card_image, create_custom_card (bonus)"
    status: pending
  - id: agent-graph
    content: "Definir el grafo LangGraph: AgentState, agent_node con Gemini, tools_node, condicional should_continue"
    status: pending
  - id: system-prompt
    content: Escribir el system prompt del agente con instrucciones de citacion de fuente y routing de herramientas
    status: pending
  - id: streamlit-ui
    content: "Crear app.py con UI Streamlit: input de chat, historial de mensajes, boton de reset"
    status: pending
  - id: docker
    content: Escribir Dockerfile, docker-compose.yml con servicios chromadb/ingestion/app, y .env.example
    status: pending
  - id: tests
    content: "Escribir tests: unitarios por tool (MTG API mockeada con pytest-httpx, ChromaDB en memoria) + test de integracion del grafo"
    status: pending
  - id: decisions-doc
    content: Redactar decisions.md con justificacion de cada decision arquitectonica y diagrama de arquitectura productiva
    status: pending
  - id: readme
    content: Completar README.md con instrucciones de instalacion con UV (uv sync, uv run), configuracion de GOOGLE_API_KEY y ejemplos de uso
    status: pending
isProject: false
---

# Arquitectura Chatbot Magic the Gathering

## Stack Tecnologico

- **LLM + Embeddings**: Google Gemini 2.0 Flash + `text-embedding-004` (via `langchain-google-genai`, free tier)
- **Orquestacion**: LangGraph (grafo de estados explícito)
- **Vector DB**: ChromaDB (local, persistente en disco)
- **PDF Parsing**: PyMuPDF (`fitz`)
- **MTG API**: `https://api.magicthegathering.io/v1/` (sin autenticacion)
- **UI Demo**: Streamlit
- **Gestion de entorno**: UV (`pyproject.toml` + `uv.lock`)
- **Bonus**: Imagen de carta custom via `Pillow` + generacion de texto estructurado

---

## Estructura de Carpetas

```
prueba-turing/
├── data/
│   └── MagicCompRules 20260417.pdf
├── src/
│   ├── ingestion/
│   │   ├── pdf_parser.py        # carga y chunking del PDF
│   │   └── vectorstore.py       # inicializa y persiste ChromaDB
│   ├── tools/
│   │   ├── rules_tool.py        # RAG search sobre el reglamento
│   │   ├── card_search_tool.py  # busqueda en MTG API por filtros
│   │   └── card_image_tool.py   # obtiene imagen de carta (bonus: crea custom)
│   ├── agent/
│   │   ├── state.py             # AgentState TypedDict
│   │   ├── graph.py             # definicion del grafo LangGraph
│   │   └── prompts.py           # system prompt del agente
│   └── app.py                   # UI Streamlit
├── tests/
│   ├── test_tools.py
│   └── test_agent.py
├── decisions.md
├── code_review.md
├── README.md
├── pyproject.toml       # dependencias gestionadas con UV
└── uv.lock
```

---

## Flujo del Agente (LangGraph)

```mermaid
flowchart TD
    START([START]) --> agentNode["agent_node\n(Gemini decide qué herramienta usar)"]
    agentNode --> shouldContinue{tool_calls\nen el mensaje?}
    shouldContinue -->|"Si"| toolsNode["tools_node\n(ejecuta la herramienta)"]
    toolsNode --> agentNode
    shouldContinue -->|"No"| END([END])
```

El **estado** del grafo es minimalista:

```python
# src/agent/state.py
from typing import Annotated
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
```

`add_messages` actúa como reducer: cada ciclo acumula mensajes sin sobreescribir el historial, lo que da memoria conversacional nativa.

---

## Las 4 Herramientas (Tools)

| Tool | Entrada | Fuente | Cubre requisito |
|---|---|---|---|
| `search_rules` | `query: str` | ChromaDB (PDF) | Reglas basicas + interacciones |
| `search_cards` | `color, type, cmc_max, name` | MTG API `/cards` | Busqueda por descripcion |
| `get_card_image` | `card_name: str` | MTG API `/cards?name=` | Imagen de carta |
| `create_custom_card` *(bonus)* | `description: str` | LLM (structured output) + Pillow | Cartas custom |

---

## Pipeline de Ingestion (offline, una sola vez)

```mermaid
flowchart LR
    PDF["PDF Reglamento\n(~300 paginas)"] --> parser["PyMuPDF\nextraccion de texto"]
    parser --> splitter["RecursiveCharacterTextSplitter\nchunk_size=1000, overlap=200"]
    splitter --> embedder["Google text-embedding-004"]
    embedder --> chromaDB[("ChromaDB\n(local /data/chroma)")]
```

Criterios de chunking: overlap de 200 tokens para no partir reglas a mitad. Metadatos por chunk: numero de pagina y sección (extraida del encabezado del párrafo).

---

## Tool: `search_rules`

Hace retrieval sobre ChromaDB con el query del usuario + **reranking por relevancia**.  
Devuelve los top-5 chunks con la sección de origen para que el agente pueda citar la fuente.

```python
# Firma simplificada
@tool
def search_rules(query: str) -> str:
    """Busca en el reglamento oficial de Magic the Gathering."""
    docs = vectorstore.similarity_search(query, k=5)
    return format_docs_with_source(docs)
```

---

## Tool: `search_cards`

Llama a `https://api.magicthegathering.io/v1/cards` con los filtros que el LLM extrae de la conversacion (color, tipo, coste de mana, texto de habilidad).

```python
@tool
def search_cards(colors: str = "", type: str = "", cmc: int = None, text: str = "") -> str:
    """Busca cartas de Magic segun filtros: color, tipo, coste de mana (cmc), texto."""
    ...
```

El LLM es responsable de mapear la descripcion en lenguaje natural a los parametros correctos.

---

## System Prompt

El system prompt indica al agente:
- Que es un asistente de call center para dudas de Magic the Gathering
- Que **siempre debe citar** la fuente de sus respuestas (sección del reglamento o nombre de carta de la API)
- Que use `search_rules` para dudas de reglas e interacciones
- Que use `search_cards` para busquedas de cartas por caracteristicas
- Que responda en el idioma del usuario

---

## Arquitectura Productiva (para `decisions.md`)

```mermaid
flowchart TD
    subgraph frontend [Canal de Entrada]
        webchat[Web Chat]
        whatsapp[WhatsApp / Twilio]
        phone[Telefono / IVR]
    end

    subgraph gateway [API Gateway]
        apigw["FastAPI\n+ Auth + Rate Limiting"]
    end

    subgraph agent_svc [Agente LangGraph]
        graph_svc["Agent Service\n(LangGraph)"]
        cache["Redis\n(caché de respuestas frecuentes)"]
    end

    subgraph rag_svc [RAG Service]
        vectorDB[("ChromaDB /\nVertex AI Vector Search")]
        embedSvc["Embedding Service\n(text-embedding-004)"]
    end

    subgraph external [Fuentes Externas]
        mtgAPI["MTG API\nmagicthegathering.io"]
        rulesDoc["Reglamento PDF\n(re-ingesta si hay actualizacion)"]
    end

    subgraph monitoring [Observabilidad]
        langsmith["LangSmith\n(trazas de agente)"]
        cloudmon["Cloud Monitoring\n(latencia, errores, coste tokens)"]
    end

    frontend --> gateway
    gateway --> agent_svc
    graph_svc --> rag_svc
    graph_svc --> mtgAPI
    graph_svc --> cache
    embedSvc --> rulesDoc
    embedSvc --> vectorDB
    graph_svc --> langsmith
    apigw --> cloudmon
```

---

## Entregables del Apartado 1

- `src/` — codigo del agente con tests
- `decisions.md` — explica eleccion de LangGraph vs AgentExecutor, ChromaDB vs FAISS, estrategia de chunking, diseno de herramientas
- `README.md` — instrucciones de instalacion con UV, configuracion de `GOOGLE_API_KEY`, ejecucion de ingestion y arranque de Streamlit
