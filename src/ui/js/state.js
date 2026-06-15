// Gestor de Estado para la UI del MTG Call Center

export function generateUUID() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  });
}

let state = {
  sessionId: "",
  chatHistory: [],
  recentCards: [],
  selectedCard: null,
  customCards: []
};

// Mapa de suscriptores para eventos de cambio de estado
const subscribers = {
  sessionId: [],
  chatHistory: [],
  recentCards: [],
  selectedCard: [],
  customCards: []
};

/**
 * Suscribirse a los cambios de una propiedad específica del estado.
 * 
 * @param {string} key La propiedad a la que suscribirse ('sessionId', 'chatHistory', 'recentCards', 'selectedCard')
 * @param {Function} callback La función que se ejecutará cuando cambie el valor
 */
export function subscribe(key, callback) {
  if (subscribers[key]) {
    subscribers[key].push(callback);
    // Ejecutar callback inmediatamente con el valor actual
    callback(state[key]);
  }
}

/**
 * Notificar a todos los suscriptores de un cambio en el estado.
 * 
 * @param {string} key La propiedad que cambió
 */
function notify(key) {
  if (subscribers[key]) {
    subscribers[key].forEach(callback => callback(state[key]));
  }
}

/**
 * Inicializar la sesión y cargar datos guardados desde localStorage.
 */
export function initSession() {
  // Obtener o crear ID de sesión
  let session = localStorage.getItem("mtg_chat_session_id");
  if (!session) {
    session = generateUUID();
    localStorage.setItem("mtg_chat_session_id", session);
  }
  state.sessionId = session;
  notify("sessionId");

  // Cargar historial de chat
  const savedHistory = localStorage.getItem("mtg_chat_history");
  if (savedHistory) {
    try {
      state.chatHistory = JSON.parse(savedHistory);
      notify("chatHistory");
    } catch (e) {
      console.error("Error leyendo historial de chat desde localStorage", e);
    }
  }

  // Cargar cartas recientes
  const savedRecent = localStorage.getItem("mtg_recent_cards");
  if (savedRecent) {
    try {
      const parsed = JSON.parse(savedRecent);
      state.recentCards = parsed.map(item => {
        let cardObj = typeof item === 'string' ? { name: item, image_url: null } : item;
        
        // Recuperar url de imagen desde el historial de chat si no la tiene
        if (!cardObj.image_url) {
          for (const msg of state.chatHistory) {
            if (msg.cards) {
              const found = msg.cards.find(c => c.name.toLowerCase() === cardObj.name.toLowerCase());
              if (found && found.image_url) {
                cardObj.image_url = found.image_url;
                break;
              }
            }
          }
        }
        return cardObj;
      });
      notify("recentCards");
    } catch (e) {
      console.error("Error leyendo cartas recientes desde localStorage", e);
    }
  }
}

/**
 * Añadir un nuevo mensaje al historial de chat.
 * 
 * @param {Object} message Objeto de mensaje ({ id, role, content, cards, rules })
 */
export function addChatMessage(message) {
  state.chatHistory = [...state.chatHistory, message];
  localStorage.setItem("mtg_chat_history", JSON.stringify(state.chatHistory));
  notify("chatHistory");
}

/**
 * Añadir una carta a la lista de cartas recientes consultadas.
 * 
 * @param {Object} card Objeto de la carta ({ name, image_url })
 */
export function addRecentCard(card) {
  if (!card || !card.name) return;
  
  // Evitar duplicados basándose en el nombre de la carta
  const filtered = state.recentCards.filter(c => c.name.toLowerCase() !== card.name.toLowerCase());
  const updatedCards = [card, ...filtered].slice(0, 15);
  state.recentCards = updatedCards;
  localStorage.setItem("mtg_recent_cards", JSON.stringify(state.recentCards));
  notify("recentCards");
}

/**
 * Actualizar la carta actualmente seleccionada en el inspector.
 * 
 * @param {Object|null} card Objeto de datos de la carta
 */
export function setSelectedCard(card) {
  state.selectedCard = card;
  notify("selectedCard");
}

/**
 * Resetear la sesión actual y limpiar todos los datos persistentes del chat y cartas.
 */
export function resetSession() {
  const newSession = generateUUID();
  localStorage.setItem("mtg_chat_session_id", newSession);
  localStorage.removeItem("mtg_chat_history");
  localStorage.removeItem("mtg_recent_cards");

  state.sessionId = newSession;
  state.chatHistory = [];
  state.recentCards = [];
  state.selectedCard = null;

  notify("sessionId");
  notify("chatHistory");
  notify("recentCards");
  notify("selectedCard");
}

/**
 * Actualizar la lista de cartas customizadas.
 * 
 * @param {Array} cards Lista de cartas customizadas
 */
export function setCustomCards(cards) {
  state.customCards = cards;
  notify("customCards");
}

/**
 * Obtener una copia de sólo lectura del estado actual.
 * 
 * @returns {Object} El estado actual de la aplicación
 */
export function getSessionState() {
  return { ...state };
}
