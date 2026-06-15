# Code Review: Análisis y Refactorización del Pipeline RAG

```python
import openai
import json
import chromadb
 
API_KEY = "sk-proj-xxxxxxxxxxxxxxxx"
client = chromadb.Client()
collection = client.create_collection("docs")
 
def ingest_documents(docs: list[str]):
    for i, doc in enumerate(docs):
        embedding = openai.Embedding.create(
            input=doc,
            model="text-embedding-ada-002",
            api_key=API_KEY
        )["data"][0]["embedding"]
        collection.add(
            documents=[doc],
            embeddings=[embedding],
            ids=[str(i)]
        )
 
def ask(question: str, history: list) -> str:
    q_embedding = openai.Embedding.create(
        input=question,
        model="text-embedding-ada-002",
        api_key=API_KEY
    )["data"][0]["embedding"]
 
    results = collection.query(query_embeddings=[q_embedding], n_results=5)
    context = " ".join(results["documents"][0])
 
    messages = [{"role": "system", "content": "Responde usando: " + context}]
    for turn in history:
        messages.append({"role": "user", "content": turn[0]})
        messages.append({"role": "assistant", "content": turn[1]})
    messages.append({"role": "user", "content": question})
 
    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        api_key=API_KEY
    )
    answer = resp["choices"][0]["message"]["content"]
    history.append((question, answer))
    open("history.json", "w").write(json.dumps(history))
    return answer
```

---

## 1. Problemas Identificados

### 1.1 Exposición de API Key

La API Key de OpenAI (`sk-proj-xxxxxxxxxxxxxxxx`) está escrita en duro (*hardcoded*) en el código. Esto viola el principio de menor privilegio y arriesga la filtración de credenciales si el código se sube a un repositorio público. Una vez en el historial de Git, la clave queda expuesta permanentemente aunque se elimine en un commit posterior.

- **Solución**: Cargar la API Key desde variables de entorno utilizando `os.getenv` o librerías como `python-dotenv`, con el fichero `.env` en `.gitignore`.

### 1.2 Ingesta Secuencial

En la función `ingest_documents`, se realiza una llamada HTTP individual a la API de OpenAI por cada documento (`openai.Embedding.create`) dentro de un bucle. Si hay 100 documentos, se realizan 100 peticiones secuenciales.

- **Solución**: Realizar llamadas de embeddings en lotes (*batching*) enviando la lista completa de documentos en una sola llamada de red y guardando en ChromaDB en una única operación.

### 1.3 Error ante Resultados Vacíos

`results["documents"][0]` asume que siempre habrá al menos un documento devuelto y que la consulta no fallará. Si no se encuentran coincidencias, lanzará un error de índice (`IndexError`).

- **Solución**: Verificar la existencia de resultados antes de intentar acceder a ellos mediante índice.

### 1.4 Base de Datos en Memoria Volátil

Se utiliza `chromadb.Client()`, lo que crea un cliente efímero en memoria. Los datos indexados se perderán cada vez que se detenga o reinicie el proceso de Python.

- **Solución**: Usar `chromadb.PersistentClient(path=...)` para persistir la base de datos de vectores en disco de forma local.

### 1.5 Error al Re-crear Colección

`client.create_collection("docs")` lanzará un error en ejecuciones subsiguientes si la colección ya existe (en caso de usar persistencia).

- **Solución**: Usar `client.get_or_create_collection("docs")`.

### 1.6 Colisión de IDs en Re-ingestas

Los IDs de los documentos se generan como `str(i)` (enteros secuenciales: `"0"`, `"1"`...). Si se llama a `ingest_documents` más de una vez, los nuevos documentos tendrán los mismos IDs que los anteriores, provocando un error o sobreescritura silenciosa en ChromaDB.

- **Solución**: Generar IDs deterministas basados en el contenido del documento (p.ej. `f"doc_{hash(doc)}"`) o usar UUIDs para garantizar unicidad.

### 1.7 Sin Control de Excepciones

No hay bloques `try/except` para llamadas a la red (OpenAI), lectura/escritura de archivos (`history.json`), ni operaciones de base de datos. Un solo fallo de red tirará abajo la ejecución completa.

- **Solución**: Envolver las operaciones críticas en bloques `try/except` y devolver un mensaje de error controlado al usuario.

### 1.8 Resource Leak _ Fichero sin Cerrar

`open("history.json", "w").write(...)` abre el fichero pero nunca lo cierra explícitamente; el cierre queda delegado al recolector de basura. Bajo alta carga o en caso de excepción, esto puede dejar descriptores de fichero abiertos.

- **Solución**: Usar siempre el gestor de contexto `with open(...) as f: json.dump(...)` para garantizar el cierre del recurso.


---

## 2. Versión Mejorada y Razonada

Se mantiene la misma estructura funcional del original. Los cambios son quirúrgicos: solo se corrigen los problemas identificados en la sección anterior.

```python
import os
import json
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# [Fix #1] API key desde variable de entorno, nunca hardcodeada
_openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# [Fix #4] Cliente persistente: los datos no se pierden al reiniciar
# [Fix #5] get_or_create evita error si la colección ya existe
_chroma = chromadb.PersistentClient(path="./.chroma_db")
collection = _chroma.get_or_create_collection("docs")

EMBEDDING_MODEL = "text-embedding-ada-002"
CHAT_MODEL = "gpt-4"


def ingest_documents(docs: list[str]) -> None:
    if not docs:
        return
    try:
        # [Fix #2] Una sola llamada HTTP para todos los documentos (batch)
        response = _openai.embeddings.create(input=docs, model=EMBEDDING_MODEL)
        embeddings = [item.embedding for item in response.data]
        # [Fix #6] IDs basados en hash del contenido para evitar colisiones en re-ingestas
        ids = [f"doc_{hash(doc)}" for doc in docs]
        collection.add(documents=docs, embeddings=embeddings, ids=ids)
    except Exception as e:
        raise RuntimeError(f"Error en ingesta: {e}") from e


def ask(question: str, history: list, history_file: str = "history.json") -> str:
    try:
        q_embedding = _openai.embeddings.create(
            input=[question], model=EMBEDDING_MODEL
        ).data[0].embedding

        results = collection.query(query_embeddings=[q_embedding], n_results=5)

        # [Fix #3] Guard contra resultados vacíos (evita IndexError)
        docs = results.get("documents", [[]])
        context = " ".join(docs[0]) if docs and docs[0] else "Sin contexto disponible."

        messages = [{"role": "system", "content": "Responde usando: " + context}]
        for turn in history:
            messages.append({"role": "user", "content": turn[0]})
            messages.append({"role": "assistant", "content": turn[1]})
        messages.append({"role": "user", "content": question})

        resp = _openai.chat.completions.create(model=CHAT_MODEL, messages=messages)
        answer = resp.choices[0].message.content

        history.append((question, answer))
        # [Fix #8] Gestor de contexto garantiza cierre del fichero
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return answer

    except Exception as e:
        # [Fix #7] Captura de excepciones para no romper la ejecución ante fallos de red
        return f"Error interno al procesar tu pregunta: {e}"
```

