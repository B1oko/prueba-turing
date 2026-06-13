// --- state variables ---
let sessionId = "";
let chatHistory = [];
let recentCards = [];
let selectedCard = null;

// --- DOM Elements ---
const appContainer = document.getElementById("appContainer");
const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const resetBtn = document.getElementById("resetBtn");
const manaSelector = document.getElementById("manaSelector");

// Health Badges
const apiBadge = document.getElementById("apiBadge");
const dbBadge = document.getElementById("dbBadge");
const keyBadge = document.getElementById("keyBadge");

// Recent Cards
const recentCardsSection = document.getElementById("recentCardsSection");
const recentCardsList = document.getElementById("recentCardsList");

// Inspector
const cardInspector = document.getElementById("cardInspector");
const noCardSelected = document.getElementById("noCardSelected");
const cardDetailsView = document.getElementById("cardDetailsView");
const interactiveCard = document.getElementById("interactiveCard");
const closeInspectorBtn = document.getElementById("closeInspectorBtn");

const cardNameVal = document.getElementById("cardNameVal");
const cardManaVal = document.getElementById("cardManaVal");
const cardTypeVal = document.getElementById("cardTypeVal");
const cardRulesVal = document.getElementById("cardRulesVal");
const cardPtVal = document.getElementById("cardPtVal");

// Mana Colors Hex Map
const MANA_COLORS = {
  W: "#f9fafb",
  U: "#2563eb",
  B: "#7c3aed",
  R: "#dc2626",
  G: "#16a34a"
};

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
  initSession();
  initListeners();
  checkHealth();
  
  // Periodically check health
  setInterval(checkHealth, 30000);
});

// Initialize session state
function initSession() {
  // Get or create session id
  sessionId = localStorage.getItem("mtg_chat_session_id");
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem("mtg_chat_session_id", sessionId);
  }

  // Load chat history
  const savedHistory = localStorage.getItem("mtg_chat_history");
  if (savedHistory) {
    try {
      chatHistory = JSON.parse(savedHistory);
      renderChatHistory();
    } catch (e) {
      console.error("Error reading chat history", e);
    }
  }

  // Load recent cards
  const savedRecent = localStorage.getItem("mtg_recent_cards");
  if (savedRecent) {
    try {
      recentCards = JSON.parse(savedRecent);
      renderRecentCards();
    } catch (e) {
      console.error("Error reading recent cards", e);
    }
  }
  
  // Set initial mana theme
  applyManaTheme("U");
}

// Bind event listeners
function initListeners() {
  // Chat submit form
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;
    sendMessage(text);
    chatInput.value = "";
    sendBtn.disabled = true;
  });

  // Enable/disable send button based on input text
  chatInput.addEventListener("input", () => {
    sendBtn.disabled = !chatInput.value.trim();
  });

  // Reset conversation button
  resetBtn.addEventListener("click", () => {
    const newSession = crypto.randomUUID();
    localStorage.setItem("mtg_chat_session_id", newSession);
    localStorage.removeItem("mtg_chat_history");
    localStorage.removeItem("mtg_recent_cards");
    
    sessionId = newSession;
    chatHistory = [];
    recentCards = [];
    selectedCard = null;
    
    // Clear DOM
    chatMessages.innerHTML = `
      <!-- Welcome Screen -->
      <div class="chat-welcome-container" id="welcomeScreen">
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
      </div>
    `;
    
    // Bind click listeners again for suggested prompts on clear
    bindSuggestedPrompts();
    
    // Reset Inspector View
    noCardSelected.style.display = "flex";
    cardDetailsView.style.display = "none";
    closeInspectorBtn.style.display = "none";
    appContainer.classList.remove("inspector-open");
    
    // Reset sidebar list
    renderRecentCards();
  });

  // Mana color selector
  manaSelector.addEventListener("click", (e) => {
    const bubble = e.target.closest(".mana-bubble");
    if (!bubble) return;
    
    // Toggle active state
    document.querySelectorAll(".mana-bubble").forEach(b => b.classList.remove("active"));
    bubble.classList.add("active");
    
    const mana = bubble.getAttribute("data-mana");
    applyManaTheme(mana);
  });

  // Close inspector button
  closeInspectorBtn.addEventListener("click", () => {
    selectedCard = null;
    noCardSelected.style.display = "flex";
    cardDetailsView.style.display = "none";
    closeInspectorBtn.style.display = "none";
    appContainer.classList.remove("inspector-open");
  });

  // 3D Tilt interactive movements
  interactiveCard.addEventListener("mousemove", (e) => {
    const box = interactiveCard.getBoundingClientRect();
    const x = e.clientX - box.left - box.width / 2;
    const y = e.clientY - box.top - box.height / 2;

    const rotateX = -(y / (box.height / 2)) * 18;
    const rotateY = (x / (box.width / 2)) * 18;

    interactiveCard.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.05, 1.05, 1.05)`;

    const shineX = ((e.clientX - box.left) / box.width) * 100;
    const shineY = ((e.clientY - box.top) / box.height) * 100;
    interactiveCard.style.setProperty("--shine-x", `${shineX}%`);
    interactiveCard.style.setProperty("--shine-y", `${shineY}%`);
  });

  interactiveCard.addEventListener("mouseleave", () => {
    interactiveCard.style.transform = "rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
    interactiveCard.style.setProperty("--shine-x", "50%");
    interactiveCard.style.setProperty("--shine-y", "50%");
  });

  // First bind of suggested prompts on welcome screen
  bindSuggestedPrompts();
}

// Helper to bind clicks on suggested prompts
function bindSuggestedPrompts() {
  document.querySelectorAll(".suggested-prompt-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const prompt = btn.getAttribute("data-prompt");
      sendMessage(prompt);
    });
  });
}

// Apply Selected Mana Color Theme
function applyManaTheme(mana) {
  const color = MANA_COLORS[mana] || MANA_COLORS.U;
  
  // Set CSS variables dynamically
  document.documentElement.style.setProperty("--theme-accent-color", color);
  document.documentElement.style.setProperty("--theme-accent-glow", `0 0 12px ${color}55`);
  
  // Set dynamic colors on active bubble in JS
  document.querySelectorAll(".mana-bubble").forEach(b => {
    const isThis = b.getAttribute("data-mana") === mana;
    b.style.borderColor = isThis ? color : "transparent";
    b.style.boxShadow = isThis ? `0 0 10px ${color}` : "none";
  });
}

// --- Health Verification ---
async function checkHealth() {
  try {
    const resp = await fetch("/health");
    if (resp.ok) {
      const data = await resp.json();
      updateHealthDashboard(data);
    } else {
      updateHealthDashboard(null);
    }
  } catch (err) {
    updateHealthDashboard(null);
  }
}

function updateHealthDashboard(data) {
  if (data && data.status === "healthy") {
    apiBadge.className = "badge badge-online";
    apiBadge.innerText = "Conectado";
    
    if (data.database_initialized) {
      dbBadge.className = "badge badge-online";
      dbBadge.innerText = "Inicializada";
    } else {
      dbBadge.className = "badge badge-warning";
      dbBadge.innerText = "Sin Ingesta";
    }
    
    if (data.api_key_configured) {
      keyBadge.className = "badge badge-online";
      keyBadge.innerText = "Configurada";
    } else {
      keyBadge.className = "badge badge-error";
      keyBadge.innerText = "Faltante";
    }
  } else {
    // API disconnected
    apiBadge.className = "badge badge-offline";
    apiBadge.innerText = "Desconectado";
    dbBadge.className = "badge badge-loading";
    dbBadge.innerText = "Faltante";
    keyBadge.className = "badge badge-loading";
    keyBadge.innerText = "Faltante";
  }
}

// --- Chat Formatter & Markdown Helper ---
function formatMarkdown(text) {
  if (!text) return "";
  
  // Sanitize simple tags
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  
  const lines = html.split("\n");
  let listActive = false;
  let resultLines = [];
  
  for (let line of lines) {
    // Unordered lists
    if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
      if (!listActive) {
        listActive = true;
        resultLines.push("<ul>");
      }
      const itemText = line.trim().substring(2);
      resultLines.push(`<li class="chat-list-item">${parseInlineStyling(itemText)}</li>`);
      continue;
    }
    
    // Close list if line is not an item
    if (listActive && !line.trim().startsWith("- ") && !line.trim().startsWith("* ")) {
      listActive = false;
      resultLines.push("</ul>");
    }
    
    // Code blocks (simple line skip for block indicators)
    if (line.trim().startsWith("```")) {
      continue;
    }
    
    // Regular paragraphs
    if (line.trim() !== "") {
      resultLines.push(`<p class="chat-paragraph">${parseInlineStyling(line)}</p>`);
    }
  }
  
  if (listActive) {
    resultLines.push("</ul>");
  }
  
  return resultLines.join("");
}

function parseInlineStyling(text) {
  // Replace bold **text** -> <strong>text</strong>
  // Replace inline code `code` -> <code class="inline-code">code</code>
  // Replace custom card path -> inline card icon link
  let parsed = text;
  
  // Bold
  parsed = parsed.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  
  // Code
  parsed = parsed.replace(/`(.*?)`/g, '<code class="inline-code">$1</code>');
  
  // Custom card image preview path highlight
  parsed = parsed.replace(/(custom_cards\/[a-zA-Z0-9_-]+\.png)/gi, '<span class="inline-card-preview-link">🖼️ $1</span>');
  
  // Rule citations inline linking (e.g. Rule 100.1a (Page 2) or Regla 510.4 (Página 87))
  const ruleRegex = /(Rule|Regla)\s+([0-9a-zA-Z.]+)\s+\((Page|P&aacute;gina|Página)\s+(\d+)\)/gi;
  parsed = parsed.replace(ruleRegex, (match, word, ruleId, pageWord, pageNum) => {
    return `<a href="/rules.pdf#page=${pageNum}" target="_blank" class="rule-link-inline" title="Ver reglamento: ${word} ${ruleId} (Pág. ${pageNum})">${match}</a>`;
  });
  
  return parsed;
}

// --- Chat Actions & Networking ---
async function sendMessage(text) {
  // Hide welcome screen if present
  const welcomeScreen = document.getElementById("welcomeScreen");
  if (welcomeScreen) {
    welcomeScreen.remove();
  }

  // Push User message
  const userMsg = {
    id: crypto.randomUUID(),
    role: "user",
    content: text
  };
  
  chatHistory.push(userMsg);
  localStorage.setItem("mtg_chat_history", JSON.stringify(chatHistory));
  appendMessageElement(userMsg);
  
  // Show Typing Indicator
  appendTypingIndicator();
  scrollChatToBottom();
  
  // Disable input while request finishes
  chatInput.disabled = true;
  
  try {
    const resp = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message: text,
        session_id: sessionId
      })
    });
    
    // Remove Typing Indicator
    removeTypingIndicator();
    
    if (resp.ok) {
      const data = await resp.json(); // ChatResponse: { response: string, cards: CardData[] }
      
      const assistantMsg = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.response,
        cards: data.cards || [],
        rules: data.rules || []
      };
      
      chatHistory.push(assistantMsg);
      localStorage.setItem("mtg_chat_history", JSON.stringify(chatHistory));
      appendMessageElement(assistantMsg);
      
      // Auto-select cards returned
      if (data.cards && data.cards.length > 0) {
        // Find first with image, otherwise use first
        const firstWithImg = data.cards.find(c => c.image_url);
        selectCard(firstWithImg || data.cards[0]);
        
        // Add card names to recent cards
        const cardNames = data.cards.map(c => c.name);
        recentCards = Array.from(new Set([...cardNames, ...recentCards])).slice(0, 15);
        localStorage.setItem("mtg_recent_cards", JSON.stringify(recentCards));
        renderRecentCards();
      } else {
        // Fallback: Check for custom generated cards paths in the response text
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

          selectCard(mockCustomCard);
          recentCards = Array.from(new Set([mockCustomCard.name, ...recentCards])).slice(0, 15);
          localStorage.setItem("mtg_recent_cards", JSON.stringify(recentCards));
          renderRecentCards();
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
    chatInput.disabled = false;
    chatInput.focus();
    scrollChatToBottom();
  }
}

// Append a standard message bubble to the DOM
function appendMessageElement(msg) {
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
  
  // Render cards grid under the assistant message bubble if cards exist
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
        // Prepend '/' if relative path
        img.src = card.image_url.startsWith("http") ? card.image_url : "/" + card.image_url;
        img.alt = card.name;
        imgContainer.appendChild(img);
      } else {
        imgContainer.innerHTML = '<div class="empty-thumbnail">🃏</div>';
      }
      
      const info = document.createElement("div");
      info.className = "thumbnail-info";
      info.innerHTML = `
        <span class="thumbnail-name">${card.name}</span>
        <span class="thumbnail-meta">${card.mana_cost || "Sin Coste"}</span>
      `;
      
      thumb.appendChild(imgContainer);
      thumb.appendChild(info);
      
      // Select card on click
      thumb.addEventListener("click", () => selectCard(card));
      
      cardsGrid.appendChild(thumb);
    });
    
    wrapper.appendChild(cardsGrid);
  }

  // Render rules grounding tags under the assistant message bubble if rules exist
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
      
      // Clean up rules text for tooltip
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
  
  scrollChatToBottom();
}

function appendErrorBubble(text) {
  const errorMsg = {
    id: crypto.randomUUID(),
    role: "assistant",
    content: text
  };
  appendMessageElement(errorMsg);
}

function renderChatHistory() {
  // Clear chatMessages of welcome screen
  const welcomeScreen = document.getElementById("welcomeScreen");
  if (welcomeScreen && chatHistory.length > 0) {
    welcomeScreen.remove();
  }
  
  chatHistory.forEach(msg => {
    appendMessageElement(msg);
  });
}

// --- Typing indicator helpers ---
function appendTypingIndicator() {
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

function removeTypingIndicator() {
  const indicator = document.getElementById("typingIndicator");
  if (indicator) {
    indicator.remove();
  }
}

function scrollChatToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// --- Sidebar Recent Cards Actions ---
function renderRecentCards() {
  if (recentCards.length === 0) {
    recentCardsSection.style.display = "none";
    recentCardsList.innerHTML = "";
    return;
  }
  
  recentCardsSection.style.display = "block";
  recentCardsList.innerHTML = "";
  
  recentCards.forEach(cardName => {
    const item = document.createElement("button");
    item.className = "recent-card-item";
    item.innerHTML = `
      <span class="item-icon">🎴</span>
      <span class="item-text">${cardName}</span>
    `;
    
    item.addEventListener("click", () => {
      // Find card in chatHistory if it exists
      let cardObject = null;
      for (const msg of chatHistory) {
        if (msg.cards) {
          cardObject = msg.cards.find(c => c.name.toLowerCase() === cardName.toLowerCase());
          if (cardObject) break;
        }
      }
      
      if (cardObject) {
        selectCard(cardObject);
      } else {
        // Send a search query
        sendMessage(`Busca la carta ${cardName}`);
      }
    });
    
    recentCardsList.appendChild(item);
  });
}

// --- Card Selection & Card Inspector Render ---
function selectCard(card) {
  selectedCard = card;
  
  noCardSelected.style.display = "none";
  cardDetailsView.style.display = "flex";
  closeInspectorBtn.style.display = "flex";
  
  // Fill details sheet
  cardNameVal.innerText = card.name;
  cardManaVal.innerText = card.mana_cost || "Sin Coste";
  cardTypeVal.innerText = card.type || "Desconocido";
  cardRulesVal.innerText = card.text || "Esta carta no tiene texto de reglas.";
  
  // Power / Toughness
  if (card.power && card.toughness) {
    cardPtVal.style.display = "inline-block";
    cardPtVal.innerText = `⚔️ ${card.power}/${card.toughness}`;
  } else {
    cardPtVal.style.display = "none";
  }
  
  // Clear interactiveCard image/frame (keeping shine layer)
  const shine = interactiveCard.querySelector(".card-shine-foil");
  interactiveCard.innerHTML = "";
  interactiveCard.appendChild(shine);
  
  // Render image if url exists, otherwise render custom text frame
  if (card.image_url) {
    const img = document.createElement("img");
    img.src = card.image_url.startsWith("http") ? card.image_url : "/" + card.image_url;
    img.alt = card.name;
    img.className = "card-artwork";
    img.loading = "lazy";
    interactiveCard.appendChild(img);
  } else {
    const frame = document.createElement("div");
    frame.className = "card-placeholder-frame";
    frame.innerHTML = `
      <div class="placeholder-card-header">
        <span class="placeholder-name">${card.name}</span>
        <span class="placeholder-cost">${card.mana_cost || ""}</span>
      </div>
      <div class="placeholder-card-art">🃏</div>
      <div class="placeholder-card-type">${card.type || ""}</div>
      <div class="placeholder-card-text">${card.text || ""}</div>
      ${card.power && card.toughness ? `<div class="placeholder-card-pt">${card.power}/${card.toughness}</div>` : ""}
    `;
    interactiveCard.appendChild(frame);
  }
  
  // Slide in card inspector on mobile
  appContainer.classList.add("inspector-open");
}
