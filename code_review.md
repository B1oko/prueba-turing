# Code Review: Análisis y Refactorización del Pipeline RAG

Este documento contiene un análisis exhaustivo del código proporcionado en el **Apartado 2** del reto técnico, identificando vulnerabilidades de seguridad, problemas de rendimiento, mantenibilidad, diseño y compatibilidad, seguido de una propuesta de mejora estructurada y moderna.

---

## 1. Problemas Identificados

### 🔍 Seguridad y Gestión de Credenciales
* **Exposición de API Key**: La API Key de OpenAI (`sk-proj-xxxxxxxxxxxxxxxx`) está escrita en duro (*hardcoded*) en el código. Esto viola el principio de menor privilegio y arriesga la filtración de credenciales si el código se sube a un repositorio público.
  * **Solución**: Cargar la API Key desde variables de entorno utilizando `os.getenv` o librerías como `python-dotenv`.

### ⚡ Rendimiento (Eficiencia de Red)
* **Ingesta Secuencial (N+1 Requests)**: En la función `ingest_documents`, se realiza una llamada HTTP individual a la API de OpenAI por cada documento (`openai.Embedding.create`) dentro de un bucle. Si hay 100 documentos, se realizan 100 peticiones secuenciales.
  * **Solución**: Realizar llamadas de embeddings en lotes (*batching*) enviando la lista completa de documentos en una sola llamada de red y guardando en ChromaDB en una única operación.

### 💾 Persistencia y Gestión del Vector DB
* **Base de Datos en Memoria Volátil**: Se utiliza `chromadb.Client()`, lo que crea un cliente efímero en memoria. Los datos indexados se perderán cada vez que se detenga o reinicie el proceso de Python.
  * **Solución**: Usar `chromadb.PersistentClient(path=...)` para persistir la base de datos de vectores en disco de forma local.
* **Error al Re-crear Colección**: `client.create_collection("docs")` lanzará un error en ejecuciones subsiguientes si la colección ya existe (en caso de usar persistencia).
  * **Solución**: Usar `client.get_or_create_collection("docs")`.

### 🔄 Depreciación de Librerías (API Antigua de OpenAI)
* **Sintaxis Obsoleta del SDK**: El código utiliza `openai.Embedding.create` y `openai.ChatCompletion.create`. Esta sintaxis corresponde a la versión `<1.0.0` del SDK de OpenAI (publicada antes de finales de 2023). La versión actual requiere instanciar un objeto cliente (`client = openai.OpenAI()`) y utilizar `client.embeddings.create` y `client.chat.completions.create`.
  * **Solución**: Actualizar el código para usar la sintaxis moderna del SDK v1.0.0+.

### 🧩 Diseño de Software y Mantenibilidad
* **Estado Global Compartido**: Variables críticas como `client`, `collection` y `API_KEY` están definidas a nivel de módulo (globales). Esto dificulta los tests unitarios (no se pueden mockear fácilmente) y reduce la reusabilidad del código.
  * **Solución**: Encapsular el comportamiento en una clase (`MTGChatbotService` o `RAGPipeline`) para inyectar la configuración en el constructor.
* **Falta de Tipado Estricto**: El parámetro `history: list` es demasiado genérico.
  * **Solución**: Usar tipado explícito (ej. `list[tuple[str, str]]` o modelos Pydantic).

### 🛠️ Robustez y Control de Errores
* **Error ante Resultados Vacíos**: `results["documents"][0]` asume que siempre habrá al menos un documento devuelto y que la consulta no fallará. Si no se encuentran coincidencias, lanzará un error de índice (`IndexError`).
  * **Solución**: Verificar la existencia de resultados antes de intentar acceder a ellos mediante índice.
* **Sin Control de Excepciones**: No hay bloques `try/except` para llamadas a la red (OpenAI), lectura/escritura de archivos (`history.json`), ni operaciones de base de datos. Un solo fallo de red tirará abajo la ejecución completa.

### 👥 Gestión de Sesión / Concurrencia
* **Historial de Chat Global y Sobreescritura Sucia**: Guardar el historial con `open("history.json", "w").write(json.dumps(history))` sobrescribe el archivo en cada turno y mezcla los chats de todos los usuarios del sistema. En un entorno real multipropósito, las sesiones de usuarios distintos colisionarán y causarán fugas de datos de conversación.
  * **Solución**: Separar el historial de chat por ID de sesión/usuario único y usar una abstracción de base de datos de sesión.

---

## 2. Versión Mejorada y Razonada

A continuación se propone una versión refactorizada que implementa las mejores prácticas: encapsulamiento en una clase, uso del SDK de OpenAI moderno, batching de embeddings, persistencia local de ChromaDB, tipado estricto, manejo de excepciones y carga de variables de entorno de forma segura.

```python
import os
import json
import logging
from typing import List, Tuple, Dict, Any, Optional
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Cargar variables de entorno del archivo .env
load_dotenv()

class RAGChatbotService:
    def __init__(
        self, 
        db_path: str = "./.chroma_db", 
        collection_name: str = "docs",
        embedding_model: str = "text-embedding-3-small",
        llm_model: str = "gpt-4o-mini"
    ):
        """
        Inicializa el servicio RAG con inyección de dependencias y configuración encapsulada.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("La variable de entorno OPENAI_API_KEY es obligatoria.")
        
        # Inicialización de clientes
        self.openai_client = OpenAI(api_key=self.api_key)
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(collection_name)
        
        # Parámetros configurables
        self.embedding_model = embedding_model
        self.llm_model = llm_model

    def ingest_documents(self, docs: List[str]) -> None:
        """
        Ingesta documentos en ChromaDB de forma eficiente realizando llamadas en batch
        tanto al servicio de embeddings de OpenAI como a la inserción en base de datos.
        """
        if not docs:
            logger.warning("Lista de documentos vacía. Saltando ingesta.")
            return

        try:
            logger.info(f"Obteniendo embeddings en batch para {len(docs)} documentos...")
            # Petición única de red para todos los documentos (Batching)
            response = self.openai_client.embeddings.create(
                input=docs,
                model=self.embedding_model
            )
            embeddings = [data.embedding for data in response.data]
            ids = [f"doc_{i}_{hash(doc)}" for i, doc in enumerate(docs)]

            logger.info("Guardando en ChromaDB...")
            # Inserción en batch en base de datos
            self.collection.add(
                documents=docs,
                embeddings=embeddings,
                ids=ids
            )
            logger.info("Ingesta completada correctamente.")
        except Exception as e:
            logger.error(f"Error durante la ingesta de documentos: {e}")
            raise

    def _get_query_embedding(self, query: str) -> List[float]:
        """Obtiene el embedding del query utilizando el SDK moderno."""
        response = self.openai_client.embeddings.create(
            input=[query],
            model=self.embedding_model
        )
        return response.data[0].embedding

    def ask(self, question: str, session_id: str, history_file: str = "history.json") -> str:
        """
        Resuelve una consulta utilizando RAG y actualiza el historial por sesión de usuario.
        """
        try:
            # 1. Obtener embedding de la consulta
            q_embedding = self._get_query_embedding(question)

            # 2. Consultar Vector DB con control de vacíos
            results = self.collection.query(query_embeddings=[q_embedding], n_results=5)
            
            # Control de errores y formateo de contexto
            documents = results.get("documents", [[]])
            if documents and documents[0]:
                context = "\n\n".join(documents[0])
            else:
                context = "No se encontró contexto relevante en la base de datos de conocimiento."
                logger.warning("ChromaDB retornó resultados vacíos para la consulta.")

            # 3. Recuperar el historial específico de la sesión
            history = self._load_history(session_id, history_file)

            # 4. Construir mensajes para el Chat LLM con un System Prompt robusto
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente experto. Responde a la pregunta del usuario utilizando únicamente "
                        "el contexto proporcionado a continuación. Si el contexto no contiene la información "
                        "suficiente para responder, indícalo de forma amable y no inventes información.\n\n"
                        f"Contexto:\n{context}"
                    )
                }
            ]
            
            for user_msg, assistant_msg in history:
                messages.append({"role": "user", "content": user_msg})
                messages.append({"role": "assistant", "content": assistant_msg})
            
            messages.append({"role": "user", "content": question})

            # 5. Generar respuesta con OpenAI SDK moderno
            logger.info("Enviando petición a la API de ChatCompletion...")
            resp = self.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                temperature=0.2  # Temperatura baja para evitar alucinaciones
            )
            
            answer = resp.choices[0].message.content
            if not answer:
                raise ValueError("La API de OpenAI devolvió una respuesta vacía.")

            # 6. Actualizar y guardar el historial para la sesión específica
            history.append((question, answer))
            self._save_history(session_id, history, history_file)

            return answer

        except Exception as e:
            logger.error(f"Error procesando la consulta 'ask': {e}")
            return "Lo siento, ocurrió un error interno al procesar tu pregunta."

    def _load_history(self, session_id: str, filepath: str) -> List[Tuple[str, str]]:
        """Carga el historial de chat para un session_id específico desde un archivo JSON."""
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(session_id, [])
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"No se pudo cargar el historial de {session_id}: {e}")
            return []

    def _save_history(self, session_id: str, history: List[Tuple[str, str]], filepath: str) -> None:
        """Guarda de forma segura el historial de chat agrupado por session_id."""
        data = {}
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                logger.warning("Fichero de historial corrupto o no legible. Sobrescribiendo.")
        
        data[session_id] = history
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except IOError as e:
            logger.error(f"Error escribiendo el historial en disco: {e}")
