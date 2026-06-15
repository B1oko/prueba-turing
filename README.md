# Asistente Chatbot de Magic: The Gathering (MTG)

Este proyecto implementa un asistente conversacional para soporte de reglas y consulta de cartas del juego **Magic: The Gathering (MTG)**.

El backend está construido con **FastAPI** y **LangGraph** (orquestación del agente), **ChromaDB** local (RAG offline sobre el reglamento oficial), y se conecta con la **API pública de MTG** para búsquedas en tiempo real. La interfaz web es una SPA estática servida directamente por FastAPI desde `src/ui/`.

---

## Características Principales

1. **RAG sobre el Reglamento Oficial**: El agente indexa más de 3.500 reglas del PDF oficial y cita la sección y página exacta en cada respuesta.
2. **Razonador de Interacciones de Cartas**: Extrae nombres de cartas de la conversación, consulta la API de MTG y busca reglas relevantes para justificar la respuesta paso a paso.
3. **Búsqueda Avanzada de Cartas**: Filtra cartas por color, coste de maná, tipo, subtipo y texto.
4. **Creación de Cartas Personalizadas (Bonus)**: Genera y visualiza cartas MTG custom con Pillow e IA generativa de imágenes.
5. **Embeddings 100% Offline**: Los embeddings (`all-MiniLM-L6-v2` vía ONNX) se ejecutan en local sin consumir cuota de API.
6. **Observabilidad con LangSmith**: Trazado opcional de llamadas al agente para debugging y evaluación.

---

## Requisitos e Instalación

Requiere [**uv**](https://github.com/astral-sh/uv) y Python `>=3.12`.

### Variables de entorno

Crea un archivo `.env` en el directorio raíz:

```env
# Obligatorio
GEMINI_API_KEY=tu_clave_de_gemini_aqui

# Opcional _ observabilidad con LangSmith
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=prueba-turing
```

---

## Instalación y uso

### Opción A _ Local (manual)

```bash	
# Instalar dependencias
uv sync

# Ejecutar la ingesta de reglas
uv run python -m ingestion.run_ingestion

# Levantar la API
uv run uvicorn src.main:app --host 127.0.0.1 --port 8000
```

Abre `http://localhost:8000` en tu navegador.

---

### Opción B _ Docker

La ingesta del reglamento se ejecuta automáticamente durante el build, por lo que la imagen arranca lista para usar.

```bash
# Construir la imagen
docker build -t mtg-chatbot .

# Ejecutar el contenedor
docker run -p 8000:8000 -e GEMINI_API_KEY=tu_clave_aqui mtg-chatbot
```

Abre `http://localhost:8000` en tu navegador.

---

## Estructura del Proyecto

```
.
├── data/                   PDF oficial de reglas (MagicCompRules)
├── ingestion/              Pipeline de ingesta: parser PDF y carga en ChromaDB
├── src/
│   ├── main.py             Punto de entrada FastAPI
│   ├── api/                Routers HTTP (chat, cartas custom, health)
│   ├── agent/              Grafo LangGraph, estado y prompts
│   ├── tools/              Herramientas del agente (reglas, cartas, sets, custom)
│   ├── clients/            Clientes externos: MTG API e imagen generativa
│   ├── repositories/       Persistencia local de cartas custom
│   ├── services/           Renderizado de cartas con Pillow
│   ├── models/             Modelos de datos Pydantic
│   ├── config/             Settings y logging
│   └── ui/                 Frontend estático (HTML/CSS/JS) servido por FastAPI
├── tests/                  Tests unitarios e integración
├── custom_cards/           Imágenes de cartas generadas (creadas en runtime)
├── Dockerfile
├── decisions.md            Decisiones Técnicas (DDT) y arquitectura de producción
└── code_review.md          Revisión del pipeline de ingesta del compañero (Apartado 2)
```

---

## Documentación Técnica

La carpeta `docs/` contiene documentación detallada del proyecto:

- [`docs/arquitectura.md`](docs/arquitectura.md): Visión general, módulos y responsabilidades.
- [`docs/diagramas.md`](docs/diagramas.md): Diagramas Mermaid de flujo, componentes y clases.
- [`docs/api.md`](docs/api.md): Endpoints HTTP, contratos de entrada/salida y errores.
- [`docs/operacion.md`](docs/operacion.md): Configuración, ejecución, ingesta y datos persistidos.
- [`docs/pipeline.md`](docs/pipeline.md): Funcionamiento detallado de la pipeline de ingesta del reglamento.
