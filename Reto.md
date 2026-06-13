Hola Pablo,

Te envío a continuación el reto técnico como te comenté. Creo que no deberías tener problema para tenerlo listo antes del martes 16 de junio. Aunque, en cualquier caso, dímelo si tuvieras cualquier imprevisto o necesitaras más tiempo.

Necesitaría que me envíes la solución en un repositorio abierto para poder compartirlo. Tienes toda la información a continuación, aunque, para cualquier duda pongo a @Alejandro Ramon, técnico del equipo que será quien revise la prueba.

No es un reto extenso, pero nos gusta dejar un margen de tiempo para que puedas tener tiempo de calidad para prepararlo 😊

Sin más, a continuación tienes el reto:

Reto Técnico — Data Scientist · AI Engineer
Departamento: Delivery

Nota sobre el uso de IA y herramientas de Asistencia En este reto se permite y se espera que uses asistentes de código (GitHub Copilot, Claude, ChatGPT, Cursor, etc.). Trabajamos con estas herramientas en el día a día y saber usarlas bien es parte del perfil que buscamos. Lo que evaluamos no es si escribiste cada línea a mano, sino si entiendes lo que has construido, por qué tomaste cada decisión y si eres capaz de defenderlo en la entrevista. Durante la revisión te haremos preguntas directas sobre el código y el diseño.

## Apartado 1 — Implementación Técnica

## Contexto del reto

Vas a construir un asistente que combine múltiples fuentes de información y sea capaz de ir más allá de la búsqueda simple: extraer datos estructurados, usar herramientas externas y mantener el hilo de la conversación.

El foco está en que el código sea limpio, testado y explicado, no en que sea el más sofisticado del mundo.

### El sistema a construir

Nuestro cliente tiene un call center para resolución de dudas y consejos para el juego de cartas Magic the gathering. Nos pide construir un chatbot para poder automatizar las respuestas a sus clientes. Para ello nos ha dado un reglamento de juego ([MagicCompRules 20260417.pdf](./data/MagicCompRules 20260417.pdf)) y una API para poder disponer de imágenes de cartas y nuevos releases ([https://docs.magicthegathering.io/](https://docs.magicthegathering.io/)).

Se pide un sistema que sea capaz de:

- Resolver dudas de reglas básicas del juego (¿Qué fases hay en un turno de juego?, ¿Cómo funciona el mana?, etc.)
- Interacciones entre cartas (Mi rapaz del campo de batalla ha hecho daño con su daña primero, si lo cambio con mi ninja de horas tardías ¿Aplico el daño?)
- Búsqueda de cartas según descripción del usuario (Busco una carta de color blanco de coste inferior a dos de mana que sea guerrero)
- (Bonus) Creación de cartas custom (Quiero una carta de Han solo, blanca-roja que tenga dañar primero)

Se pide:

Un documento explicando una solución completa productiva (Servicios, tipo de agentes, monitorización etc) Se pueden añadir diagramas si se considera necesario

Una solución demo básica respondiendo a los requerimientos pedidos por el cliente. No se evaluará la veracidad de las respuestas del chatbot aunque sí se pide que tengan una base de referencia (i.e. No importa si no responde correctamente a interacciones, pero sí que debe ser capaz de justificar su respuesta)

Alternativas: Si se prefiere hacer otro juego/hobby para tener un mayor conocimiento del caso de uso, está permitido. Se requiere que la solución contenga un gran documento de normativa (O varios documentos de menor tamaño) así como un acceso a una página web/API para obtener información actualizada. Si se decide ir con una alternativa, se pide que se comunique para validar que sería un caso de uso interesante

## Apartado 2 — Revisión de Código

El siguiente código implementa el pipeline de ingesta y consulta de un compañero. Identifica todos los problemas que encuentres (bugs, seguridad, mantenibilidad, diseño, rendimiento) y propón una versión mejorada razonada.

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
    return answer```
Entrega: Fichero code_review.md con tu análisis y el código mejorado.
Entregables
Entregable
	
Descripción


Repositorio Git
	
Código con historial de commits visible


README.md
	
Instrucciones de instalación, configuración y ejemplos


decisions.md
	
Documento de Decisiones Técnicas (DDT)


code_review.md
	
Análisis y mejora del fragmento de código
 
Comparte el enlace al repositorio antes de la entrevista. Lo revisaremos en detalle durante la misma.
```

