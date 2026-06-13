# Documentacion del proyecto

Este directorio contiene la documentacion tecnica del asistente de Magic: The Gathering.

## Indice

- [Arquitectura](./arquitectura.md): vision general, modulos y responsabilidades.
- [Diagramas](./diagramas.md): diagramas Mermaid de flujo, componentes y clases.
- [API](./api.md): endpoints HTTP, contratos de entrada/salida y errores esperados.
- [Operacion y desarrollo](./operacion.md): configuracion, ejecucion, ingesta, tests y datos persistidos.

## Resumen

El proyecto implementa un asistente conversacional para consultar reglas y cartas de Magic: The Gathering. La aplicacion expone una API FastAPI, sirve un frontend estatico integrado, ejecuta un agente LangGraph con herramientas y usa ChromaDB como base vectorial local para busqueda semantica sobre el PDF oficial de reglas.

Las capacidades principales son:

- Chat con memoria por `session_id`.
- Busqueda de reglas MTG mediante RAG local en ChromaDB.
- Busqueda de cartas y expansiones mediante la API publica de Magic: The Gathering.
- Generacion de cartas custom usando Gemini/Imagen, Pillow y almacenamiento local.
- Endpoint de salud para comprobar API, base vectorial y clave Gemini.

## Estructura documentada

```text
src/
  main.py                    Punto de entrada FastAPI
  api/                       Routers HTTP
  agent/                     Grafo LangGraph principal
  tools/                     Herramientas invocables por el agente
  clients/                   Clientes externos: MTG API e Imagen
  repositories/              Persistencia local de cartas custom
  services/                  Renderizado de cartas
  ui/                        Frontend estatico servido por FastAPI
ingestion/
  pdf_parser.py              Parser del PDF de reglas
  vectorstore.py             Inicializacion de ChromaDB
  run_ingestion.py           Pipeline de ingesta
tests/
  test_agent.py              Test del grafo del agente
  test_tools.py              Tests de herramientas
```

## Nota sobre README principal

El README de raiz menciona Streamlit, pero el codigo actual sirve una interfaz estatica desde `src/ui` usando FastAPI cuando `SERVE_FRONTEND=True`. Esta documentacion describe el comportamiento observado en el codigo actual.
