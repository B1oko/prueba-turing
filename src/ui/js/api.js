// Servicio de API para interactuar con el backend del MTG Call Center

/**
 * Consulta el estado de salud del servidor backend.
 * 
 * @returns {Promise<Object|null>} Los datos de salud del sistema o null en caso de error
 */
export async function fetchHealthStatus() {
  try {
    const response = await fetch("/health");
    if (response.ok) {
      return await response.json();
    }
    return null;
  } catch (error) {
    console.error("Error consultando estado del servidor:", error);
    return null;
  }
}

/**
 * Envía una consulta de chat al backend del asistente de MTG.
 * 
 * @param {string} text El mensaje del usuario
 * @param {string} sessionId ID único de la sesión del chat
 * @returns {Promise<Response>} La respuesta HTTP del backend
 */
export async function sendChatMessage(text, sessionId) {
  return fetch("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      message: text,
      session_id: sessionId
    })
  });
}
