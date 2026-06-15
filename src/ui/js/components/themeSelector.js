import { MANA_COLORS } from '../config.js';

let manaSelector;

/**
 * Aplica el tema de color del maná correspondiente al elemento raíz HTML.
 * 
 * @param {string} mana Carácter de maná ('W', 'U', 'B', 'R', 'G')
 */
export function applyManaTheme(mana) {
  const color = MANA_COLORS[mana] || MANA_COLORS.U;
  
  // Establecer variables CSS dinámicas en el documento
  document.documentElement.style.setProperty("--theme-accent-color", color);
  document.documentElement.style.setProperty("--theme-accent-glow", `0 0 12px ${color}55`);
  
  // Resaltar la burbuja activa y apagar las otras
  document.querySelectorAll(".mana-bubble").forEach(b => {
    const isThis = b.getAttribute("data-mana") === mana;
    b.style.borderColor = isThis ? color : "transparent";
    b.style.boxShadow = isThis ? `0 0 10px ${color}` : "none";
    if (isThis) {
      b.classList.add("active");
    } else {
      b.classList.remove("active");
    }
  });
}

/**
 * Inicializa el selector de temas, vincula los eventos de clic de las burbujas de maná
 * y establece el tema predeterminado inicial ("U").
 */
export function initThemeSelector() {
  // Tema inicial por defecto (Azul/Isla)
  applyManaTheme("U");

  manaSelector = document.getElementById("manaSelector");
  if (!manaSelector) return;

  manaSelector.addEventListener("click", (e) => {
    const bubble = e.target.closest(".mana-bubble");
    if (!bubble) return;
    
    const mana = bubble.getAttribute("data-mana");
    applyManaTheme(mana);
  });
}
