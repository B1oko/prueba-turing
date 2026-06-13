# Diagramas

Los diagramas estan escritos en Mermaid para que puedan renderizarse en GitHub, VS Code u otros visores compatibles.

## Componentes

```mermaid
flowchart LR
    User[Usuario] --> UI[Frontend estatico src/ui]
    UI --> API[FastAPI src/main.py]
    API --> ChatRouter[/POST /chat/]
    API --> HealthRouter[/GET /health/]
    API --> CustomRouter[/GET /api/custom-cards/]
    API --> StaticCards[StaticFiles /custom_cards]

    ChatRouter --> AgentGraph[Grafo LangGraph principal]
    AgentGraph --> Gemini[Gemini ChatGoogleGenerativeAI]
    AgentGraph --> Tools[ToolNode]

    Tools --> RulesTool[SearchRulesTool]
    Tools --> CardsTool[SearchCardsTool]
    Tools --> SetsTool[SearchSetsTool]
    Tools --> CreateTool[CreateCustomCardTool]

    RulesTool --> Chroma[(ChromaDB .chroma_db)]
    CardsTool --> MTGAPI[MTG API publica]
    SetsTool --> MTGAPI
    CreateTool --> CardSubgraph[Grafo generador de carta]
    CardSubgraph --> Imagen[Imagen API]
    CardSubgraph --> Renderer[Pillow render_card]
    CardSubgraph --> Repo[LocalCustomCardRepository]
    Repo --> Files[(custom_cards/)]
```

## Flujo de chat

```mermaid
flowchart TD
    A[Cliente envia POST /chat] --> B[Validar ChatRequest]
    B --> C[Obtener app.state.graph]
    C --> D[Configurar thread_id con session_id]
    D --> E[Invocar grafo con HumanMessage]
    E --> F[agent_node agrega SystemMessage si falta]
    F --> G[LLM responde o solicita tool_calls]
    G --> H{Necesita herramienta?}
    H -- No --> I[Devolver respuesta final]
    H -- Si --> J[ToolNode ejecuta herramienta]
    J --> K[Agregar ToolMessage al estado]
    K --> F
    I --> L[Extraer cartas de ToolMessage search_cards]
    L --> M[Extraer reglas de ToolMessage search_rules]
    M --> N[Responder ChatResponse]
```

## Flujo RAG de reglas

```mermaid
flowchart TD
    A[Pregunta del usuario sobre reglas] --> B[Agente decide usar search_rules]
    B --> C[SearchRulesTool recibe query]
    C --> D[Chroma.asimilarity_search k=5]
    D --> E[Recuperar Document con rule_id page source]
    E --> F[Formatear JSON rules]
    F --> G[ToolMessage vuelve al agente]
    G --> H[LLM redacta respuesta con reglas recuperadas]
    H --> I[API extrae grounding para ChatResponse.rules]
```

## Flujo de ingesta

```mermaid
flowchart TD
    A[uv run python ingestion/run_ingestion.py] --> B[Comprobar PDF en data/]
    B --> C{Existe PDF?}
    C -- No --> D[Log error y exit 1]
    C -- Si --> E[Eliminar .chroma_db anterior]
    E --> F[parse_mtg_rules_pdf]
    F --> G[Leer paginas con PyMuPDF]
    G --> H[Detectar inicios de regla con regex]
    H --> I[Crear Document por regla con metadata]
    I --> J[get_vectorstore]
    J --> K[Inicializar Chroma mtg_rules]
    K --> L[Agregar documentos en lotes de 200]
    L --> M[ChromaDB poblado]
```

## Flujo de creacion de carta custom

```mermaid
flowchart TD
    A[Agente invoca create_custom_card] --> B[CreateCustomCardTool]
    B --> C[Grafo generador]
    C --> D[design_card]
    D --> E[LLM produce CardSpecs estructurado]
    E --> F[generate_art]
    F --> G[Imagen genera bytes PNG]
    G --> H[render_and_save]
    H --> I[render_card compone mockup con Pillow]
    I --> J[LocalCustomCardRepository.save]
    J --> K[Guardar PNG si existe]
    J --> L[Guardar JSON metadata]
    K --> M[Devolver image_url]
    L --> M
```

## Diagrama de clases

```mermaid
classDiagram
    class Settings {
        +str API_URL
        +bool SERVE_FRONTEND
        +str GEMINI_API_KEY
        +str GEMINI_MODEL
        +float GEMINI_TEMPERATURE
        +str CHROMA_DB_PATH
        +str CHROMA_COLLECTION_NAME
        +bool LANGSMITH_TRACING
    }

    class AgentState {
        +list messages
    }

    class ChatRequest {
        +str message
        +str session_id
    }

    class RuleGrounding {
        +str rule_id
        +int page
        +str text
    }

    class ChatResponse {
        +str response
        +list~Card~ cards
        +list~RuleGrounding~ rules
    }

    class Card {
        +str name
        +str mana_cost
        +str type
        +str text
        +str image_url
        +str power
        +str toughness
        +str rarity
        +str flavor
        +list~str~ colors
        +str set
    }

    class MTGCard {
        +str name
        +str manaCost
        +float cmc
        +list~str~ colors
        +str type
        +str rarity
        +str text
        +str imageUrl
    }

    class ICardSearch {
        <<Protocol>>
        +search_cards(...) list~MTGCard~
    }

    class ISetSearch {
        <<Protocol>>
        +search_sets(...) list~dict~
    }

    class MTGClient {
        -AsyncClient _client
        +search_cards(...) list~MTGCard~
        +search_sets(...) list~dict~
    }

    class ImageGenerationClient {
        <<Protocol>>
        +generate(prompt) bytes
    }

    class ImagenGenerationClient {
        -Client _client
        +generate(prompt) bytes
    }

    class CustomCardRepository {
        <<Protocol>>
        +save(card_specs, image_bytes) Card
        +find_all() list~Card~
    }

    class LocalCustomCardRepository {
        -str _base_dir
        +save(card_specs, image_bytes) Card
        +find_all() list~Card~
    }

    class SearchRulesTool {
        +str name
        +str description
        -Any _vectorstore
        +_arun(query) str
    }

    class SearchCardsTool {
        +str name
        +str description
        -ICardSearch _client
        +_arun(...) tuple
    }

    class SearchSetsTool {
        +str name
        +str description
        -ISetSearch _client
        +_arun(...) str
    }

    class CreateCustomCardTool {
        +str name
        +str description
        -Any _graph
        +_run(description) str
        +_arun(description) str
    }

    class CardSpecs {
        +str name
        +str mana_cost
        +list~str~ colors
        +str type_line
        +str rules_text
        +str flavor_text
        +str art_prompt
        +str power
        +str toughness
    }

    class CardGeneratorState {
        +str description
        +dict card_specs
        +bytes art_bytes
        +str card_path
    }

    MTGClient ..|> ICardSearch
    MTGClient ..|> ISetSearch
    ImagenGenerationClient ..|> ImageGenerationClient
    LocalCustomCardRepository ..|> CustomCardRepository

    SearchCardsTool --> ICardSearch
    SearchSetsTool --> ISetSearch
    SearchRulesTool --> Chroma
    CreateCustomCardTool --> ImageGenerationClient
    CreateCustomCardTool --> CustomCardRepository
    CreateCustomCardTool --> CardSpecs
    LocalCustomCardRepository --> Card
    ChatResponse --> Card
    ChatResponse --> RuleGrounding
```
