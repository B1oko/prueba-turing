import { subscribe, addChatMessage, addRecentCard, setSelectedCard, resetSession, getSessionState } from '../state.js';
import { sendChatMessage } from '../api.js';
import { formatMarkdown } from '../utils/markdown.js';
import { renderManaCost } from '../utils/manaRenderer.js';

let chatMessages, chatForm, chatInput, sendBtn, resetBtn;

/**
 * Hace scroll al final del área de mensajes del chat.
 */
function scrollChatToBottom() {
  if (chatMessages) {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

/**
 * Añade una burbuja de error al chat.
 * 
 * @param {string} text Texto del error
 */
function appendErrorBubble(text) {
  const errorMsg = {
    id: crypto.randomUUID(),
    role: "assistant",
    content: text
  };
  appendMessageElement(errorMsg);
}

/**
 * Añade el indicador de escritura ("Typing...") al final del chat.
 */
function appendTypingIndicator() {
  if (!chatMessages) return;

  const row = document.createElement("div");
  row.className = "chat-message-row assistant typing-loader";
  row.id = "typingIndicator";
  
  const avatar = document.createElement("div");
  avatar.className = "message-avatar assistant-avatar";
  avatar.innerHTML = `
    <svg class="avatar-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <!-- Hat cone -->
      <path d="M 6 13 L 12 3 L 18 13 Z" fill="rgba(212, 175, 55, 0.15)" />
      <!-- Hat brim -->
      <path d="M 3 13 L 21 13" />
      <!-- Face/Head -->
      <path d="M 8 13 V 15 C 8 17, 16 17, 16 15 V 13" />
      <!-- Beard -->
      <path d="M 8 15 C 8 20, 12 22, 12 22 C 12 22, 16 20, 16 15 Z" fill="rgba(255, 255, 255, 0.1)" />
      <!-- Eyes -->
      <circle cx="10.5" cy="14.5" r="0.7" fill="currentColor" />
      <circle cx="13.5" cy="14.5" r="0.7" fill="currentColor" />
    </svg>
  `;
  
  const wrapper = document.createElement("div");
  wrapper.className = "message-bubble-wrapper";
  
  const bubble = document.createElement("div");
  bubble.className = "message-bubble loading-bubble";
  bubble.innerHTML = `
    <div class="typing-indicator">
      <span></span>
      <span></span>
      <span></span>
    </div>
  `;
  
  wrapper.appendChild(bubble);
  row.appendChild(avatar);
  row.appendChild(wrapper);
  chatMessages.appendChild(row);
}

/**
 * Elimina el indicador de escritura de la pantalla.
 */
function removeTypingIndicator() {
  const indicator = document.getElementById("typingIndicator");
  if (indicator) {
    indicator.remove();
  }
}

/**
 * Vincula los clicks en las sugerencias de la pantalla de bienvenida.
 */
function bindSuggestedPrompts() {
  document.querySelectorAll(".suggested-prompt-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const prompt = btn.getAttribute("data-prompt");
      sendMessage(prompt);
    });
  });
}

/**
 * Agrega un elemento HTML de mensaje al DOM.
 * 
 * @param {Object} msg Objeto del mensaje
 */
function appendMessageElement(msg) {
  if (!chatMessages) return;

  const row = document.createElement("div");
  row.className = `chat-message-row ${msg.role}`;
  row.setAttribute("data-msg-id", msg.id);
  
  const avatar = document.createElement("div");
  avatar.className = `message-avatar ${msg.role}-avatar`;
  if (msg.role === "user") {
    avatar.innerHTML = `
      <svg class="avatar-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    `;
  } else {
    avatar.innerHTML = `
      <svg class="avatar-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <!-- Hat cone -->
        <path d="M 6 13 L 12 3 L 18 13 Z" fill="rgba(212, 175, 55, 0.15)" />
        <!-- Hat brim -->
        <path d="M 3 13 L 21 13" />
        <!-- Face/Head -->
        <path d="M 8 13 V 15 C 8 17, 16 17, 16 15 V 13" />
        <!-- Beard -->
        <path d="M 8 15 C 8 20, 12 22, 12 22 C 12 22, 16 20, 16 15 Z" fill="rgba(255, 255, 255, 0.1)" />
        <!-- Eyes -->
        <circle cx="10.5" cy="14.5" r="0.7" fill="currentColor" />
        <circle cx="13.5" cy="14.5" r="0.7" fill="currentColor" />
      </svg>
    `;
  }
  
  const wrapper = document.createElement("div");
  wrapper.className = "message-bubble-wrapper";
  
  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.innerHTML = `<div class="message-text">${formatMarkdown(msg.content)}</div>`;
  
  wrapper.appendChild(bubble);
  
  // Si es un mensaje del asistente y tiene cartas asociadas, dibujar miniaturas
  if (msg.role === "assistant" && msg.cards && msg.cards.length > 0) {
    const cardsGrid = document.createElement("div");
    cardsGrid.className = "message-cards-grid";
    
    msg.cards.forEach(card => {
      const thumb = document.createElement("div");
      thumb.className = "chat-card-thumbnail";
      thumb.title = "Haz clic para ver detalles en el inspector";
      
      const imgContainer = document.createElement("div");
      imgContainer.className = "thumbnail-img-container";
      
      if (card.image_url) {
        const img = document.createElement("img");
        img.src = card.image_url.startsWith("http") || card.image_url.startsWith("/")
          ? card.image_url
          : "/" + card.image_url;
        img.alt = card.name;
        imgContainer.appendChild(img);
      } else {
        imgContainer.innerHTML = '<div class="empty-thumbnail">🃏</div>';
      }
      
      const info = document.createElement("div");
      info.className = "thumbnail-info";
      info.innerHTML = `
        <span class="thumbnail-name">${card.name}</span>
        <span class="thumbnail-meta">${card.mana_cost ? renderManaCost(card.mana_cost) : "Sin Coste"}</span>
      `;
      
      thumb.appendChild(imgContainer);
      thumb.appendChild(info);
      
      // Al hacer click, selecciona la carta
      thumb.addEventListener("click", () => setSelectedCard(card));
      
      cardsGrid.appendChild(thumb);
    });
    
    wrapper.appendChild(cardsGrid);
  }

  
  row.appendChild(avatar);
  row.appendChild(wrapper);
  chatMessages.appendChild(row);
}

/**
 * Renderiza todo el historial de chat actual en pantalla.
 * Si está vacío, dibuja la pantalla de bienvenida.
 * 
 * @param {Array} chatHistory Historial completo de mensajes
 */
function renderChatHistory(chatHistory) {
  if (!chatMessages) return;

  chatMessages.innerHTML = "";
  
  if (chatHistory.length === 0) {
    const welcome = document.createElement("div");
    welcome.className = "chat-welcome-container";
    welcome.id = "welcomeScreen";
    welcome.innerHTML = `
      <div class="welcome-avatar-wrapper">
        <svg class="welcome-avatar-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <!-- Hat cone -->
          <path d="M 6 13 L 12 3 L 18 13 Z" fill="rgba(212, 175, 55, 0.2)" stroke="#d4af37" stroke-width="1.5" />
          <!-- Hat brim -->
          <path d="M 3 13 L 21 13" stroke="#d4af37" stroke-width="1.8" />
          <!-- Face/Head -->
          <path d="M 8 13 V 15 C 8 17, 16 17, 16 15 V 13" stroke="#d4af37" stroke-width="1.5" />
          <!-- Beard -->
          <path d="M 8 15 C 8 20, 12 22, 12 22 C 12 22, 16 20, 16 15 Z" fill="rgba(255, 255, 255, 0.15)" stroke="#ffe082" stroke-width="1.5" />
          <!-- Eyes -->
          <circle cx="10.5" cy="14.5" r="0.8" fill="#ffe082" />
          <circle cx="13.5" cy="14.5" r="0.8" fill="#ffe082" />
          <!-- Star sparks around the hat -->
          <path d="M 4 8 L 4.5 8.5 L 4 9 L 3.5 8.5 Z" fill="#ffe082" stroke="#ffe082" stroke-width="0.5" />
          <path d="M 20 8 L 20.5 8.5 L 20 9 L 19.5 8.5 Z" fill="#ffe082" stroke="#ffe082" stroke-width="0.5" />
        </svg>
      </div>
      <h2>¡Saludos, Planeswalker!</h2>
      <p>
        Soy tu asistente experto en **Magic: The Gathering**. Puedo ayudarte a resolver dudas complejas de reglas (consultando el reglamento oficial offline), buscar cartas en tiempo real o diseñar cartas personalizadas (ej. <em>crea una carta custom...</em>).
      </p>
      <div class="suggested-prompts">
        <button class="suggested-prompt-btn" data-prompt="¿Cómo funciona la habilidad de Arrollar (Trample)?">
          <svg class="btn-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
          </svg>
          Explicar Arrollar
        </button>
        <button class="suggested-prompt-btn" data-prompt="Busca la carta Black Lotus">
          <svg class="btn-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          Buscar Black Lotus
        </button>
        <button class="suggested-prompt-btn" data-prompt="Crea una carta custom llamada Fénix de Ceniza con coste 2RR, tipo Criatura Fénix, fuerza 4, resistencia 3, con Volar, Prisa y 'Al morir vuelve a tu mano'.">
          <svg class="btn-svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 2l4 4M2 22l14-14M16 3l1 1M12 2v2M20 10h2M19 17l1 1M5 5L4 4" />
          </svg>
          Crear carta customizada
        </button>
      </div>
    `;
    chatMessages.appendChild(welcome);
    bindSuggestedPrompts();
    return;
  }
  
  chatHistory.forEach(msg => {
    appendMessageElement(msg);
  });
  
  scrollChatToBottom();
}

/**
 * Envía el mensaje del usuario al backend y procesa la respuesta.
 * 
 * @param {string} text Consulta del usuario
 */
export async function sendMessage(text) {
  if (!text.trim()) return;

  // Quitar pantalla de bienvenida al enviar
  const welcomeScreen = document.getElementById("welcomeScreen");
  if (welcomeScreen) {
    welcomeScreen.remove();
  }

  // Registrar el mensaje del usuario en el historial (actualiza estado y localstorage)
  const userMsg = {
    id: crypto.randomUUID(),
    role: "user",
    content: text
  };
  
  addChatMessage(userMsg);
  
  // Mostrar cargador
  appendTypingIndicator();
  scrollChatToBottom();
  
  // Bloquear entrada mientras se procesa la consulta
  if (chatInput) {
    chatInput.disabled = true;
  }
  
  try {
    const session = getSessionState().sessionId;
    const resp = await sendChatMessage(text, session);
    
    removeTypingIndicator();
    
    if (resp.ok) {
      const data = await resp.json();
      
      const assistantMsg = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.response,
        cards: data.cards || [],
        rules: data.rules || []
      };
      
      addChatMessage(assistantMsg);
      
      // Agregar a las cartas recientes en el panel
      if (data.cards && data.cards.length > 0) {
        data.cards.forEach(c => addRecentCard({ name: c.name, image_url: c.image_url }));
      } else {
        // Fallback: Si en el texto hay referencias a cartas creadas dinámicamente
        const customCardRegex = /custom_cards\/[a-zA-Z0-9_-]+\.png/gi;
        const matches = data.response.match(customCardRegex);
        if (matches && matches.length > 0) {
          const filename = matches[0].split("/").pop() || "carta_creada.png";
          const cleanName = filename
            .replace(".png", "")
            .replace(/[-_]/g, " ")
            .split(" ")
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");

          const mockCustomCard = {
            name: cleanName,
            mana_cost: "Custom",
            type: "Carta Personalizada",
            text: "Esta es una carta customizada generada dinámicamente mediante Pillow.",
            image_url: matches[0]
          };

          addRecentCard(mockCustomCard);
        }
      }
    } else {
      const errorData = await resp.json().catch(() => ({}));
      const errorText = errorData.detail || "Error en la llamada del servidor API.";
      appendErrorBubble(`❌ **Error del Backend**: ${errorText}`);
    }
  } catch (err) {
    removeTypingIndicator();
    appendErrorBubble(`❌ **Error de Red**: No se pudo conectar con el servidor. Asegúrate de que el backend está corriendo.`);
  } finally {
    if (chatInput) {
      chatInput.disabled = false;
      chatInput.focus();
    }
    scrollChatToBottom();
  }
}

/**
 * Inicializa el área de chat, buscando elementos DOM, vinculando eventos
 * de envío de formularios, inputs, reseteo de chat, y escuchando búsquedas externas.
 */
export function initChatArea() {
  chatMessages = document.getElementById("chatMessages");
  chatForm = document.getElementById("chatForm");
  chatInput = document.getElementById("chatInput");
  sendBtn = document.getElementById("sendBtn");
  resetBtn = document.getElementById("resetBtn");

  if (!chatForm) return;

  // Manejo de envío de formulario de chat
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;
    sendMessage(text);
    chatInput.value = "";
    if (sendBtn) {
      sendBtn.disabled = true;
    }
  });

  // Habilitar/deshabilitar botón según el input
  chatInput.addEventListener("input", () => {
    if (sendBtn) {
      sendBtn.disabled = !chatInput.value.trim();
    }
  });

  // Botón resetear conversación
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      resetSession();
    });
  }

  // Escuchar evento personalizado para enviar mensajes de chat desde otros módulos
  document.addEventListener('send-chat-message', (e) => {
    sendMessage(e.detail);
  });

  // Suscribirse a los cambios del historial de chat para redibujar
  subscribe("chatHistory", renderChatHistory);
}
