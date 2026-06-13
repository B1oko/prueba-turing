import { subscribe, setSelectedCard, setCustomCards } from '../state.js';

/**
 * Realiza la petición al backend para cargar las cartas creadas.
 */
export async function loadCustomCards() {
  try {
    const response = await fetch('/api/custom-cards');
    if (response.ok) {
      const cards = await response.json();
      setCustomCards(cards);
    } else {
      console.error('Error fetching custom cards:', response.statusText);
    }
  } catch (error) {
    console.error('Failed to load custom cards:', error);
  }
}

/**
 * Inicializa el componente de la lista de cartas creadas (custom) del panel lateral.
 * Se suscribe a los cambios del estado 'customCards' para volver a renderizar.
 */
export function initCustomCardsList() {
  const customCardsSection = document.getElementById("customCardsSection");
  const customCardsList = document.getElementById("customCardsList");
  if (!customCardsSection || !customCardsList) return;

  subscribe("customCards", (customCards) => {
    if (!customCards || customCards.length === 0) {
      customCardsList.innerHTML = `
        <div class="custom-cards-empty">
          <p>Aún no has creado cartas.</p>
          <span>Pídele al chatbot que cree una para verla aquí.</span>
        </div>
      `;
      return;
    }
    
    customCardsList.innerHTML = "";
    
    // Si hay más de 8 cartas, aplicar clase de solapamiento
    if (customCards.length > 8) {
      customCardsList.classList.add("has-overlap");
    } else {
      customCardsList.classList.remove("has-overlap");
    }
    
    // Mostrar más nuevas primero (invertir orden)
    const newestFirst = [...customCards].reverse();
    newestFirst.forEach((card, index) => {
      const item = document.createElement("div");
      item.className = "recent-card-item";
      item.style.zIndex = index + 1;
      item.setAttribute("role", "button");
      item.setAttribute("tabindex", "0");
      item.title = `Ver detalles de ${card.name}`;
      
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
        setSelectedCard(card);
      };

      item.addEventListener("click", selectCardHandler);
      item.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          selectCardHandler();
        }
      });
      
      customCardsList.appendChild(item);
    });
  });

  // Cargar las cartas inicialmente
  loadCustomCards();
}
