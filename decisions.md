# Documento de Decisiones Técnicas (DDT) - Chatbot MTG

Este documento detalla y justifica las decisiones arquitectónicas tomadas para la solución demo del asistente conversacional de Magic: The Gathering (MTG), así como la propuesta para una arquitectura completa productiva.

---

## 1. Decisiones Arquitectónicas del Prototipo (Demo)

### 1.1 Orquestación: LangGraph vs LangChain AgentExecutor
* **Decisión**: Se ha implementado **LangGraph** para modelar el agente mediante un grafo de estados cíclico.
* **Justificación**:
  - Los agentes tradicionales de caja negra (`AgentExecutor`) suelen entrar en bucles infinitos o llamar a herramientas de forma desordenada en dominios complejos.
  - Para resolver dudas de interacciones en MTG, el agente debe seguir una secuencia estricta: primero extraer nombres de cartas, luego buscar *ambas* cartas en la API, después buscar las reglas asociadas y finalmente responder. 
  - LangGraph permite definir este flujo de control explícito, persistir el estado de la conversación de manera nativa mediante checkpointers (`MemorySaver`) y facilitar la depuración de trazas.

### 1.2 Base de Datos Vectorial: ChromaDB con Embeddings Locales (ONNX)
* **Decisión**: Se ha utilizado **ChromaDB** persistente localmente con embeddings locales **all-MiniLM-L6-v2** a través de ONNX.
* **Justificación**:
  - **Eficiencia de Coste y Límites**: Indexar secuencialmente más de 3,500 reglas individuales en la API de Google Gemini (o cualquier otro proveedor) consume gran parte de la cuota gratuita de embeddings, genera costes y corre el riesgo de suspender la API Key (como ocurrió con la clave proporcionada).
  - **Latencia y Autonomía**: Los embeddings basados en ONNX se ejecutan en local sobre CPU a una velocidad extremadamente alta (~10 ms por búsqueda) y no requieren llamadas a APIs externas ni claves de acceso, garantizando que el sistema de RAG de reglas funcione de manera 100% offline y gratuita.

### 1.3 Segmentación del PDF (Chunking Estratégico)
* **Decisión**: En lugar de usar divisores de caracteres ciegos (`RecursiveCharacterTextSplitter`), se ha implementado un **parseador personalizado** en base a expresiones regulares.
* **Justificación**:
  - El reglamento oficial de MTG está altamente estructurado en secciones jerárquicas (ej. `104.3a`, `104.3b`).
  - Un splitter tradicional rompe las reglas por la mitad o mezcla párrafos inconexos. Nuestro parseador segmenta el texto exactamente en cada inicio de regla numerada y guarda el ID de la regla y la página real como metadatos en ChromaDB. Esto permite al LLM citar de forma exacta la fuente de su razonamiento (ej. "según la regla 105.2a (página 12)...").

### 1.4 API de MTG y Estrategia de Caching
* **Decisión**: Conexión directa con la API oficial sin autenticación y almacenamiento de respuestas en un caché en memoria.
* **Justificación**:
  - La API de MTG (`magicthegathering.io`) puede presentar latencias elevadas o cortes esporádicos.
  - La implementación de un diccionario de caché simple a nivel de módulo en las herramientas evita repetir peticiones HTTP idénticas en la misma sesión, mejorando drásticamente el tiempo de respuesta y evitando el *rate-limiting*.

### 1.5 Frontend: SPA Estática integrada en FastAPI (en lugar de Streamlit)
* **Decisión**: La interfaz web es una SPA estática (HTML + CSS + JS vanilla) ubicada en `src/ui/` y servida directamente por FastAPI mediante `StaticFiles` cuando `SERVE_FRONTEND=True`.
* **Justificación**:
  - **Eliminación de dependencia pesada**: Streamlit añade ~30 dependencias transitivas, fuerza un proceso Python separado y expone un puerto adicional (8501). La SPA estática elimina todo eso: cero dependencias de frontend en `pyproject.toml`.
  - **Proceso único y despliegue simplificado**: API y UI conviven en el mismo proceso FastAPI en el puerto `8000`, lo que reduce la complejidad operativa tanto en local como en Docker (un solo contenedor, un solo servicio).
  - **Separación de responsabilidades sin fricción de proceso**: El código de frontend (JS/CSS/HTML) vive en `src/ui/` separado del código Python del backend, pero sin requerir un servidor dedicado. En producción podría extraerse fácilmente a un CDN o un contenedor nginx independiente.
  - **Scripts de ingesta independientes**: `ingestion/` permanece en la raíz del repositorio, desacoplado del paquete `src/` que constituye la aplicación desplegable.

### 1.6 Contenerización con Docker y Docker Compose
* **Decisión**: Un `Dockerfile` único con `uv` empaqueta la API FastAPI (backend + frontend estático). `docker-compose.yml` define dos servicios: `api` (la aplicación) y `test` (batería de pruebas aislada).
* **Justificación**:
  - **Aislamiento y portabilidad**: Garantiza reproducibilidad en cualquier sistema operativo sin depender de la versión local de Python ni de librerías nativas como PyMuPDF o SQLite.
  - **Volúmenes para persistencia**: `.chroma_db` y `custom_cards/` se montan como volúmenes en `api`, permitiendo ejecutar la ingesta en local y que el contenedor lea la base vectorial inmediatamente sin reconstruir la imagen.
  - **Servicio de test aislado**: El servicio `test` no monta el directorio host para evitar conflictos de arquitectura entre entornos virtuales Windows y el sistema de ficheros Linux del contenedor.

---

## 2. Arquitectura de Producción Propuesta

Para escalar este sistema a producción, dar servicio a miles de usuarios concurrentes en múltiples canales (WhatsApp, Web, Teléfono) y garantizar fiabilidad, se propone la siguiente arquitectura:

```mermaid
flowchart TD
    subgraph frontend [Canal de Entrada]
        webchat[Web Chat Widget]
        whatsapp[WhatsApp API - Twilio]
        phone[Telefonía / IVR Voice]
    end

    subgraph gateway [Capa de Entrada / API Gateway]
        apigw["FastAPI Gateway\n(Auth + Rate Limiting + CORS)"]
    end

    subgraph agent_svc [Servicio de Agentes]
        graph_svc["LangGraph Server / FastAPI\n(Lógica de Agente y Memoria)"]
        redis_cache["Redis\n(Caché de consultas + Estados de Sesión)"]
    end

    subgraph rag_svc [Servicio de RAG]
        vectorDB[("Vertex AI Vector Search\n/ Pinecone (Escalable)")]
        embedSvc["Embedding Service\n(Google text-embedding-004)"]
    end

    subgraph external [Fuentes de Datos]
        mtgAPI["MTG API\nmagicthegathering.io"]
        rulesDoc["Reglamento PDF\n(Pipeline de Ingesta S3/GCS)"]
    end

    subgraph monitoring [Monitoreo y Observabilidad]
        langsmith["LangSmith\n(Trazas de LLM y debugging)"]
        prometheus["Prometheus + Grafana\n(Métricas de infraestructura y latencias)"]
    end

    frontend --> gateway
    gateway --> agent_svc
    graph_svc --> redis_cache
    graph_svc --> rag_svc
    graph_svc --> mtgAPI
    embedSvc --> rulesDoc
    embedSvc --> vectorDB
    graph_svc --> langsmith
    gateway --> prometheus
```

### Componentes de Producción Explicados:
1. **API Gateway (FastAPI / Kong)**: Gestiona la autenticación de usuarios, enruta peticiones, y controla el número de peticiones por minuto (*rate-limiting*) para evitar costes excesivos en LLM.
2. **LangGraph Graph Service**: Desplegado de forma independiente en contenedores (ej. Kubernetes o ECS). Utiliza Redis para almacenar el estado de la sesión de chat y provee endpoints de streaming para las respuestas del bot.
3. **Redis**: Funciona como base de datos en memoria para almacenar las conversaciones de los usuarios de forma segura y veloz, además de cachear respuestas de la API de MTG y preguntas frecuentes del call center.
4. **Vertex AI Vector Search / Pinecone**: Reemplaza al ChromaDB local de archivo por una base de datos de vectores en la nube gestionada, distribuida y con alta disponibilidad, optimizada para búsquedas rápidas con millones de vectores.
5. **Observabilidad (LangSmith + Prometheus + Grafana)**:
   - **LangSmith**: Esencial en producción para evaluar el comportamiento del agente, analizar qué herramientas está llamando y dónde se producen fallos de lógica.
   - **Prometheus/Grafana**: Monitorea las métricas del sistema: latencia de la API, consumo de CPU/Memoria y porcentaje de errores HTTP.
