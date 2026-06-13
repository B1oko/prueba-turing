import { COLOR_NAMES_ES } from '../config.js';

/**
 * Helper to render MTG mana costs in a premium graphical format.
 * Converts symbols inside curly braces (e.g., {2}{W}{U}) into HTML span tags.
 * 
 * @param {string} manaStr The raw mana cost string (e.g. "{2}{W}{B}")
 * @returns {string} The HTML string representation of the mana symbols
 */
export function renderManaCost(manaStr) {
  if (!manaStr) return "";
  
  // Match each brace content, e.g. {2}, {W}, {U/B}, {2/W}, {G/P}, {B/G/P}, {100}, {∞}
  const regex = /{([^{}]+)}/g;
  return manaStr.replace(regex, (match, symbol) => {
    const sym = symbol.toUpperCase();
    let className = "generic";
    let content = sym;
    let title = `${sym} maná`;
    
    if (sym === "W") {
      className = "W";
      content = "☀️";
      title = "Maná blanco";
    } else if (sym === "U") {
      className = "U";
      content = "💧";
      title = "Maná azul";
    } else if (sym === "B") {
      className = "B";
      content = "💀";
      title = "Maná negro";
    } else if (sym === "R") {
      className = "R";
      content = "🔥";
      title = "Maná rojo";
    } else if (sym === "G") {
      className = "G";
      content = "🌳";
      title = "Maná verde";
    } else if (sym === "C") {
      className = "C";
      content = "💎";
      title = "Maná incoloro";
    } else if (sym === "S") {
      className = "S";
      content = "❄️";
      title = "Maná gélido (requiere permanente nevado)";
    } else if (sym === "T") {
      className = "T";
      content = "↩️";
      title = "Girar este permanente (Tap)";
    } else if (sym === "Q") {
      className = "Q";
      content = "🔄";
      title = "Enderezar este permanente (Untap)";
    } else if (sym === "E") {
      className = "E";
      content = "⚡";
      title = "Reserva de energía";
    } else if (sym === "CHAOS") {
      className = "chaos";
      content = "🌀";
      title = "Símbolo de Caos";
    } else if (sym === "HW") {
      className = "W-half";
      content = "½☀️";
      title = "Medio maná blanco";
    } else if (sym === "HR") {
      className = "R-half";
      content = "½🔥";
      title = "Medio maná rojo";
    } else if (sym === "∞") {
      className = "generic";
      content = "∞";
      title = "Maná genérico infinito";
    } else if (/^\d+$/.test(sym)) {
      className = "generic";
      content = sym;
      title = `${sym} maná genérico`;
    } else if (sym === "X" || sym === "Y" || sym === "Z") {
      className = "generic";
      content = sym;
      title = `Maná genérico variable (${sym})`;
    } else {
      // Check for hybrid, mono-hybrid, phyrexian
      const hybridPhyrexianMatch = sym.match(/^([WUBRG])\/([WUBRG])\/P$/);
      const phyrexianMatch = sym.match(/^([WUBRG])\/P$/);
      const monoHybridMatch = sym.match(/^2\/([WUBRG])$/);
      const hybridMatch = sym.match(/^([WUBRG])\/([WUBRG])$/);
      
      if (hybridPhyrexianMatch) {
        const c1 = hybridPhyrexianMatch[1];
        const c2 = hybridPhyrexianMatch[2];
        className = `phyrexian hybrid ${c1}-${c2}`;
        content = "Φ";
        title = `Maná híbrido pirexiano: 1 maná ${COLOR_NAMES_ES[c1]}, 1 maná ${COLOR_NAMES_ES[c2]} o pagar 2 vidas`;
      } else if (phyrexianMatch) {
        const c = phyrexianMatch[1];
        className = `phyrexian ${c}`;
        content = "Φ";
        title = `Maná pirexiano: 1 maná ${COLOR_NAMES_ES[c]} o pagar 2 vidas`;
      } else if (monoHybridMatch) {
        const c = monoHybridMatch[1];
        className = `mono-hybrid 2-${c}`;
        content = `2/${c}`;
        title = `Maná híbrido monocolor: 2 maná genérico o 1 maná ${COLOR_NAMES_ES[c]}`;
      } else if (hybridMatch) {
        const c1 = hybridMatch[1];
        const c2 = hybridMatch[2];
        className = `hybrid ${c1}-${c2}`;
        content = `${c1}/${c2}`;
        title = `Maná híbrido: 1 maná ${COLOR_NAMES_ES[c1]} o 1 maná ${COLOR_NAMES_ES[c2]}`;
      } else {
        // Fallback generic
        className = "generic";
        content = sym;
        title = `Maná genérico (${sym})`;
      }
    }
    
    return `<span class="mana-symbol ${className}" title="${title}">${content}</span>`;
  });
}
