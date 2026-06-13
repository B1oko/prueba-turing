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
  avatar.className = "message-avatar";
  avatar.innerText = "🧙‍♂️";
  
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
  avatar.className = "message-avatar";
  avatar.innerText = msg.role === "user" ? "👤" : "🧙‍♂️";
  
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

  // Si tiene reglas citadas para la fundamentación (RAG), añadir badges
  if (msg.role === "assistant" && msg.rules && msg.rules.length > 0) {
    const groundingDiv = document.createElement("div");
    groundingDiv.className = "message-rules-grounding";
    
    const titleSpan = document.createElement("span");
    titleSpan.className = "grounding-title";
    titleSpan.innerHTML = "📖 Reglas citadas:";
    groundingDiv.appendChild(titleSpan);
    
    const tagsDiv = document.createElement("div");
    tagsDiv.className = "grounding-tags";
    
    msg.rules.forEach(rule => {
      const badge = document.createElement("a");
      badge.href = `/rules.pdf#page=${rule.page}`;
      badge.target = "_blank";
      badge.className = "rule-badge";
      badge.innerText = `Regla ${rule.rule_id} (Pág. ${rule.page})`;
      
      const tooltipText = rule.text
        .replace(/"/g, "&quot;")
        .substring(0, 300) + (rule.text.length > 300 ? "..." : "");
      badge.setAttribute("title", tooltipText);
      
      tagsDiv.appendChild(badge);
    });
    
    groundingDiv.appendChild(tagsDiv);
    wrapper.appendChild(groundingDiv);
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
      <div class="welcome-avatar">🧙‍♂️</div>
      <h2>¡Saludos, Planeswalker!</h2>
      <p>
        Soy tu asistente experto en **Magic: The Gathering**. Puedo ayudarte a resolver dudas complejas de reglas (consultando el reglamento oficial offline), buscar cartas en tiempo real o diseñar cartas personalizadas (ej. <em>crea una carta custom...</em>).
      </p>
      <div class="suggested-prompts">
        <button class="suggested-prompt-btn" data-prompt="¿Cómo funciona la habilidad de Arrollar (Trample)?">📜 Explicar Arrollar</button>
        <button class="suggested-prompt-btn" data-prompt="Busca la carta Black Lotus">🔍 Buscar Black Lotus</button>
        <button class="suggested-prompt-btn" data-prompt="Crea una carta custom llamada Fénix de Ceniza con coste 2RR, tipo Criatura Fénix, fuerza 4, resistencia 3, con Volar, Prisa y 'Al morir vuelve a tu mano'.">🎨 Crear carta customizada</button>
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
