# 🧙‍♂️ Asistente Chatbot de Magic: The Gathering (MTG)

Este proyecto implementa un asistente inteligente en formato Chatbot para dar soporte de reglas y consulta de cartas del juego **Magic: The Gathering (MTG)**. 

El asistente está construido utilizando **LangGraph** (para la orquestación del flujo de agentes), **ChromaDB** local (base de datos vectorial para RAG offline), **FastAPI** (como API backend de consulta), **Streamlit** (para la interfaz de usuario web), y se conecta con la **API oficial de MTG** para buscar cartas en tiempo real.

---

## 🚀 Características Principales

1. **RAG Inteligente (Reglas Básicas)**: El chatbot lee e indexa las más de 3,518 reglas del PDF oficial del reglamento y cita de manera exacta la sección y la página en cada respuesta.
2. **Razonador de Interacciones de Cartas**: El agente extrae de manera automática los nombres de cartas de la conversación, consulta qué hacen en la API de MTG de antemano y busca reglas en el vector store para justificar la respuesta paso a paso.
3. **Búsqueda Avanzada de Cartas**: Permite filtrar cartas de la API por color, coste de maná, tipo, subtipo y palabras clave en texto.
4. **Mockup de Cartas Customizadas (Bonus)**: Permite la creación y visualización gráfica de cartas MTG personalizadas usando Pillow.
5. **Autónomo y Offline (RAG)**: La generación de embeddings y la base de datos vectorial corren 100% en local y offline, sin consumo de API tokens ni necesidad de credenciales.
6. **Mecanismo de Seguridad en Interfaz**: La interfaz web permite ingresar una clave API de Gemini en la barra lateral en caso de que la clave del archivo `.env` del entorno esté suspendida o caducada.

---

## 📦 Requisitos e Instalación

Este proyecto se puede ejecutar de forma local con Python o a través de **Docker** de manera contenerizada.

### Variables de entorno
Crea un archivo `.env` en el directorio raíz (o edita el existente):
```env
GEMINI_API_KEY=tu_clave_de_gemini_aqui
```
*Nota: Si la clave del `.env` estuviera suspendida, el chatbot te lo indicará en la interfaz web de Streamlit, donde podrás pegar temporalmente otra clave de Gemini válida.*

---

## 🐳 Uso con Docker (Recomendado)

### 1. Ejecutar la Ingesta de Reglas
Antes de levantar la aplicación por primera vez, debes indexar el reglamento PDF (`data/MagicCompRules 20260417.pdf`) en la base de datos local. Ejecútalo con `uv` en local:
```bash
uv run python ingestion/run_ingestion.py
```
*(Esto creará la base de datos vectorial local en la carpeta `.chroma_db/`, la cual se montará automáticamente como volumen en el contenedor).*

### 2. Levantar la Aplicación Web (Streamlit) y la API (FastAPI)
Usa docker-compose para construir las imágenes y levantar ambos servicios:
```bash
docker compose up app
```
*Esto levantará de forma automática el backend `api` en el puerto `8000` y el cliente frontend `app` en el puerto `8501`.*
Abre tu navegador en: `http://localhost:8501`.

### 3. Ejecutar Tests en Docker
Para verificar que el agente y las herramientas funcionan perfectamente dentro del contenedor Docker:
```bash
docker compose run --rm test
```

---

## 🐍 Uso Local (Sin Docker)

Si prefieres ejecutar todo directamente con Python en tu sistema local, utiliza [**uv**](https://github.com/astral-sh/uv):

### 1. Instalar dependencias e iniciar el entorno virtual
`uv` creará automáticamente un entorno virtual local `.venv` e instalará todas las dependencias definidas en el `pyproject.toml`:
```bash
uv sync
```

### 2. Ejecutar la Ingesta de Reglas (Offline)
```bash
uv run python ingestion/run_ingestion.py
```

### 3. Levantar la API Backend (FastAPI)
```bash
uv run uvicorn src.main:app --host 127.0.0.1 --port 8000
```

### 4. Lanzar la Interfaz Web (Streamlit)
En una nueva terminal, corre:
```bash
uv run streamlit run ui/app.py
```
Abre `http://localhost:8501` en tu navegador.

### 5. Ejecutar los Tests Locales
```bash
uv run pytest tests/
```

---

## 📂 Estructura del Proyecto

* **`ingestion/`**: Directorio raíz para utilidades de ingesta de datos manuales (`pdf_parser.py`, `vectorstore.py`, `run_ingestion.py`).
* **`ui/`**: Directorio raíz para la interfaz web cliente de Streamlit (`app.py`), actuando como un paquete frontend externo.
* **`src/`**: Directorio del backend de la aplicación. Contiene el punto de entrada de la API REST (`main.py` basado en FastAPI), la lógica del agente LangGraph (`agent/`) y las herramientas de reglas y cartas (`tools/`).
* **`tests/`**: Suite de pruebas unitarias e integración de herramientas y grafo de agentes.
* **`Dockerfile`** y **`docker-compose.yml`**: Configuración de contenerización para despliegue y tests.
* **`code_review.md`**: Informe del análisis y código mejorado del pipeline de ingesta del compañero (Apartado 2).
* **`decisions.md`**: Justificación detallada de decisiones técnicas y propuesta de arquitectura productiva.