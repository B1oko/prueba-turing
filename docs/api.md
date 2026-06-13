# API

La aplicacion expone una API FastAPI desde `src/main.py`.

## `GET /health`

Comprueba el estado basico de la aplicacion.

### Respuesta

```json
{
  "status": "healthy",
  "database_initialized": true,
  "api_key_configured": true
}
```

Campos:

- `status`: estado general del proceso.
- `database_initialized`: `true` si existe la ruta configurada en `CHROMA_DB_PATH`.
- `api_key_configured`: `true` si `GEMINI_API_KEY` esta configurada.

## `POST /chat`

Ejecuta una conversacion contra el agente LangGraph.

### Request

```json
{
  "message": "Que pasa si una criatura con first strike lucha contra otra?",
  "session_id": "usuario-123"
}
```

Campos:

- `message`: texto del usuario.
- `session_id`: identificador de conversacion. Se usa como `thread_id` para la memoria del grafo.

### Response

```json
{
  "response": "Respuesta del asistente...",
  "cards": [
    {
      "name": "Battlefield Raptor",
      "mana_cost": "{W}",
      "type": "Creature - Bird Soldier",
      "text": "Flying, first strike",
      "image_url": "https://...",
      "power": "1",
      "toughness": "2",
      "rarity": null,
      "flavor": null,
      "colors": null,
      "set": null
    }
  ],
  "rules": [
    {
      "rule_id": "702.7",
      "page": 169,
      "text": "..."
    }
  ]
}
```

Campos:

- `response`: respuesta final del modelo.
- `cards`: cartas extraidas de la herramienta `search_cards` en el turno actual, si existen.
- `rules`: reglas extraidas de la herramienta `search_rules` en el turno actual, si existen.

### Errores

Si falla el grafo, una herramienta o una dependencia de aplicacion, el endpoint devuelve:

```json
{
  "detail": "mensaje de error"
}
```

con codigo HTTP `500`.

## `GET /api/custom-cards`

Devuelve las cartas custom guardadas por `LocalCustomCardRepository`.

### Respuesta

```json
[
  {
    "name": "Test Hero",
    "mana_cost": "{1}{R}{W}",
    "type": "Legendary Creature - Warrior",
    "text": "First strike. Haste.",
    "image_url": "/custom_cards/test_hero/test_hero.png",
    "power": "3",
    "toughness": "2",
    "rarity": "Mythic Rare",
    "flavor": "...",
    "colors": ["R", "W"],
    "set": "custom"
  }
]
```

## Archivos estaticos

### `/custom_cards/*`

Sirve imagenes y archivos generados dentro de `custom_cards/`.

### `/`

Si `SERVE_FRONTEND=True`, sirve `src/ui/index.html`.

### `/static/*`

Si `SERVE_FRONTEND=True`, sirve los assets de `src/ui`.

### `/rules.pdf`

Si `SERVE_FRONTEND=True`, sirve `data/MagicCompRules 20260417.pdf`.
