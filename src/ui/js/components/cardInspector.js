import { subscribe, setSelectedCard } from '../state.js';
import { renderManaCost } from '../utils/manaRenderer.js';

const RARITY_COLORS = {
  "Common": "#a0a0a0",
  "Uncommon": "#7ec8e3",
  "Rare": "#d4af37",
  "Mythic Rare": "#e87a2a",
  "Special": "#b784a7",
  "Basic Land": "#6aab69",
};

const COLOR_SYMBOLS = {
  W: { symbol: "☀️", label: "White" },
  U: { symbol: "💧", label: "Blue" },
  B: { symbol: "💀", label: "Black" },
  R: { symbol: "🔥", label: "Red" },
  G: { symbol: "🌲", label: "Green" },
};

let appContainer;
let cardDetailsView, interactiveCard, closeInspectorBtn;
let cardNameVal, cardManaVal, cardTypeVal, cardRulesVal, cardPtVal, cardRarityVal, cardFlavorVal, cardMetaVal;
let downloadCardBtn;

/**
 * Renderiza los detalles de la carta seleccionada en el inspector modal.
 * Si es null, oculta el modal completo.
 * 
 * @param {Object|null} card Datos de la carta seleccionada
 */
function renderSelectedCard(card) {
  if (!cardDetailsView || !closeInspectorBtn) return;

  if (!card) {
    cardDetailsView.style.display = "none";
    if (appContainer) {
      appContainer.classList.remove("inspector-open");
    }
    return;
  }

  cardDetailsView.style.display = "flex";

  // Datos principales
  cardNameVal.innerText = card.name;
  cardManaVal.innerHTML = card.mana_cost ? renderManaCost(card.mana_cost) : "Sin Coste";
  cardTypeVal.innerText = card.type || "Desconocido";
  cardRulesVal.innerText = card.text || "Esta carta no tiene texto de reglas.";

  // Flavor text
  if (cardFlavorVal) {
    if (card.flavor) {
      cardFlavorVal.innerText = card.flavor;
      cardFlavorVal.style.display = "block";
    } else {
      cardFlavorVal.style.display = "none";
    }
  }

  // Rareza
  if (cardRarityVal) {
    if (card.rarity) {
      cardRarityVal.innerText = card.rarity;
      cardRarityVal.style.color = RARITY_COLORS[card.rarity] || "#ccc";
      cardRarityVal.style.display = "inline-block";
    } else {
      cardRarityVal.style.display = "none";
    }
  }

  // Meta: colores + set
  if (cardMetaVal) {
    const parts = [];
    if (card.colors && card.colors.length > 0) {
      const colorIcons = card.colors
        .map(c => COLOR_SYMBOLS[c] ? `${COLOR_SYMBOLS[c].symbol}` : c)
        .join(" ");
      parts.push(colorIcons);
    }
    if (card.set) {
      parts.push(`Set: ${card.set.toUpperCase()}`);
    }
    cardMetaVal.innerText = parts.join("  ·  ");
    cardMetaVal.style.display = parts.length ? "block" : "none";
  }

  // Fuerza y Resistencia (P/T)
  if (card.power && card.toughness) {
    cardPtVal.style.display = "inline-block";
    cardPtVal.innerText = `⚔️ ${card.power}/${card.toughness}`;
  } else {
    cardPtVal.style.display = "none";
  }

  // Limpiar la carta interactiva (manteniendo la capa foil)
  const shine = interactiveCard.querySelector(".card-shine-foil");
  interactiveCard.innerHTML = "";
  if (shine) {
    interactiveCard.appendChild(shine);
  } else {
    const newShine = document.createElement("div");
    newShine.className = "card-shine-foil";
    interactiveCard.appendChild(newShine);
  }

  // Renderizar la imagen si existe la url, o el frame de texto alternativo
  if (card.image_url) {
    const img = document.createElement("img");
    img.src = card.image_url.startsWith("http") || card.image_url.startsWith("/")
      ? card.image_url
      : "/" + card.image_url;
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
        <span class="placeholder-cost">${card.mana_cost ? renderManaCost(card.mana_cost) : ""}</span>
      </div>
      <div class="placeholder-card-art">🃏</div>
      <div class="placeholder-card-type">${card.type || ""}</div>
      <div class="placeholder-card-text">${card.text || ""}</div>
      ${card.power && card.toughness ? `<div class="placeholder-card-pt">${card.power}/${card.toughness}</div>` : ""}
    `;
    interactiveCard.appendChild(frame);
  }

  // Botón de descarga
  if (downloadCardBtn) {
    if (card.image_url) {
      const src = card.image_url.startsWith("http") || card.image_url.startsWith("/")
        ? card.image_url
        : "/" + card.image_url;
      downloadCardBtn.style.display = "flex";
      downloadCardBtn.onclick = () => downloadCardImage(src, card.name);
    } else {
      downloadCardBtn.style.display = "none";
    }
  }

  // Mostrar el modal agregando la clase al contenedor raíz
  if (appContainer) {
    appContainer.classList.add("inspector-open");
  }
}

async function downloadCardImage(src, cardName) {
  try {
    const response = await fetch(src);
    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = `${cardName.replace(/\s+/g, "_").toLowerCase()}.png`;
    a.click();
    URL.revokeObjectURL(blobUrl);
  } catch {
    window.open(src, "_blank");
  }
}

/**
 * Inicializa el componente del inspector de cartas: vincula elementos DOM,
 * configura eventos de ratón para el efecto 3D Tilt, y se suscribe a 'selectedCard'.
 */
export function initCardInspector() {
  appContainer = document.getElementById("appContainer");
  const cardInspector = document.getElementById("cardInspector");
  cardDetailsView = document.getElementById("cardDetailsView");
  interactiveCard = document.getElementById("interactiveCard");
  closeInspectorBtn = document.getElementById("closeInspectorBtn");

  cardNameVal = document.getElementById("cardNameVal");
  cardManaVal = document.getElementById("cardManaVal");
  cardTypeVal = document.getElementById("cardTypeVal");
  cardRulesVal = document.getElementById("cardRulesVal");
  cardPtVal = document.getElementById("cardPtVal");
  cardRarityVal = document.getElementById("cardRarityVal");
  cardFlavorVal = document.getElementById("cardFlavorVal");
  cardMetaVal = document.getElementById("cardMetaVal");
  downloadCardBtn = document.getElementById("downloadCardBtn");

  if (!interactiveCard) return;

  // Botón para cerrar inspector
  closeInspectorBtn.addEventListener("click", () => {
    setSelectedCard(null);
  });

  // Cerrar el inspector al hacer clic en el fondo oscuro (fuera de la tarjeta del modal)
  if (cardInspector) {
    cardInspector.addEventListener("click", (e) => {
      if (e.target === cardInspector) {
        setSelectedCard(null);
      }
    });
  }

  // Movimientos interactivos 3D Tilt (ocurre al mover el ratón en cualquier parte del modal)
  if (cardInspector) {
    cardInspector.addEventListener("mousemove", (e) => {
      if (!interactiveCard) return;
      
      const box = interactiveCard.getBoundingClientRect();
      if (box.width === 0 || box.height === 0) return; // Si la carta no es visible, ignorar
      
      // Coordenadas del centro de la carta en la pantalla
      const cardCenterX = box.left + box.width / 2;
      const cardCenterY = box.top + box.height / 2;
      
      // Distancia del cursor al centro de la carta
      const x = e.clientX - cardCenterX;
      const y = e.clientY - cardCenterY;
      
      // Distancia máxima de normalización (medio ancho/alto de pantalla)
      const maxDistanceX = window.innerWidth / 2;
      const maxDistanceY = window.innerHeight / 2;
      
      const clamp = (val, min, max) => Math.max(min, Math.min(max, val));
      
      // Rotación máxima de 12 grados, escalada por la distancia en pantalla y más suave
      const rotateX = clamp(-(y / maxDistanceY) * 12, -12, 12);
      const rotateY = clamp(-(x / maxDistanceX) * 12, -12, 12);
      
      interactiveCard.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.05, 1.05, 1.05)`;
      
      // Iluminación del brillo foil (mapeado de 0% a 100% sobre la caja de la carta)
      const shineX = clamp(((e.clientX - box.left) / box.width) * 100, 0, 100);
      const shineY = clamp(((e.clientY - box.top) / box.height) * 100, 0, 100);
      interactiveCard.style.setProperty("--shine-x", `${shineX}%`);
      interactiveCard.style.setProperty("--shine-y", `${shineY}%`);
    });

    cardInspector.addEventListener("mouseleave", () => {
      if (!interactiveCard) return;
      // Restaurar a la posición plana inicial cuando el cursor sale del modal
      interactiveCard.style.transform = "rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
      interactiveCard.style.setProperty("--shine-x", "50%");
      interactiveCard.style.setProperty("--shine-y", "50%");
    });
  }

  // Suscribirse a los cambios del estado de carta seleccionada
  subscribe("selectedCard", renderSelectedCard);
}
