import { subscribe, setSelectedCard, getSessionState } from '../state.js';

/**
 * Inicializa el componente de la lista de cartas recientes del panel lateral.
 * Se suscribe a los cambios del estado 'recentCards' para volver a renderizar.
 */
export function initRecentCardsList() {
  const recentCardsSection = document.getElementById("recentCardsSection");
  const recentCardsList = document.getElementById("recentCardsList");
  if (!recentCardsSection || !recentCardsList) return;

  subscribe("recentCards", (recentCards) => {
    if (!recentCards || recentCards.length === 0) {
      recentCardsSection.style.display = "none";
      recentCardsList.innerHTML = "";
      return;
    }
    
    recentCardsSection.style.display = "flex";
    recentCardsList.innerHTML = "";
    
    // Si hay más de 8 cartas, aplicar clase de solapamiento
    if (recentCards.length > 8) {
      recentCardsList.classList.add("has-overlap");
    } else {
      recentCardsList.classList.remove("has-overlap");
    }
    
    // Mostrar más antiguas primero (invertir orden)
    const oldestFirst = [...recentCards].reverse();
    oldestFirst.forEach((card, index) => {
      const item = document.createElement("div");
      item.className = "recent-card-item";
      item.style.zIndex = index + 1;
      item.setAttribute("role", "button");
      item.setAttribute("tabindex", "0");
      item.title = `Ver detalles de ${card.name}`;
      
      // Renderizar la imagen si existe, o el marco de texto fallback
      if (card.image_url) {
        const img = document.createElement("img");
        img.src = card.image_url.startsWith("http") || card.image_url.startsWith("/")
          ? card.image_url
          : "/" + card.image_url;
        img.alt = card.name;
        item.appendChild(img);
      } else {
        const fallback = document.createElement("div");
        fallback.className = "recent-card-fallback-frame";
        fallback.innerHTML = `
          <div class="recent-card-fallback-name">${card.name}</div>
          <span style="font-size: 1.25rem; display: block; text-align: center; margin-top: 4px;">🃏</span>
        `;
        item.appendChild(fallback);
      }
      
      const selectCardHandler = () => {
        // Buscar el objeto completo de la carta en el historial del chat
        let cardObject = null;
        const state = getSessionState();
        for (const msg of state.chatHistory) {
          if (msg.cards) {
            cardObject = msg.cards.find(c => c.name.toLowerCase() === card.name.toLowerCase());
            if (cardObject) break;
          }
        }
        
        if (cardObject) {
          // Seleccionar directamente la carta
          setSelectedCard(cardObject);
        } else {
          // Disparar evento personalizado para que el chat envíe la consulta
          document.dispatchEvent(new CustomEvent('send-chat-message', {
            detail: `Busca la carta ${card.name}`
          }));
        }
      };

      item.addEventListener("click", selectCardHandler);
      item.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          selectCardHandler();
        }
      });
      
      recentCardsList.appendChild(item);
    });
  });
}
