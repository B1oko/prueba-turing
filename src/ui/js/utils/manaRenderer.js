import { COLOR_NAMES_ES } from '../config.js';

const MANA_SVGS = {
  W: `<svg class="mana-symbol-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="5" /><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" /></svg>`,
  U: `<svg class="mana-symbol-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2v0a10 10 0 0 1 10 10c0 4.5-3.5 8-10 8S2 16.5 2 12a10 10 0 0 1 10-10z" /><path d="M12 6a6 6 0 0 1 6 6" stroke-dasharray="2 2" /></svg>`,
  B: `<svg class="mana-symbol-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2c4.4 0 8 3.1 8 7c0 3-1.6 4.7-3 6v4a2 2 0 0 1-2 2h-6a2 2 0 0 1-2-2v-4c-1.4-1.3-3-3-3-6c0-3.9 3.6-7 8-7z" /><circle cx="9" cy="9" r="1.2" fill="currentColor" /><circle cx="15" cy="9" r="1.2" fill="currentColor" /><path d="M10 14h4M12 14v4" /></svg>`,
  R: `<svg class="mana-symbol-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z" /></svg>`,
  G: `<svg class="mana-symbol-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 22 2c-2.48 5-3 6.5-4.1 12.2A7 7 0 0 1 11 20z" /><path d="M9 11l3.5 3.5" /></svg>`,
  C: `<svg class="mana-symbol-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 3h12l4 6-10 13L2 9z" /></svg>`,
  S: `<svg class="mana-symbol-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2v20M2 12h20M4.93 4.93l14.14 14.14M4.93 19.07l14.14-14.14" /></svg>`,
  T: `<svg class="mana-symbol-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 14L4 9l5-5" /><path d="M20 20v-7a4 4 0 0 0-4-4H4" /></svg>`,
  Q: `<svg class="mana-symbol-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 10l5 5-5 5" /><path d="M4 4v7a4 4 0 0 0 4 4h12" /></svg>`,
  E: `<svg class="mana-symbol-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" /></svg>`,
  chaos: `<svg class="mana-symbol-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2a10 10 0 1 0 10 10" /><path d="M12 6a6 6 0 1 0 6 6" /><path d="M12 10a2 2 0 1 0 2 2" /></svg>`
};

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
      content = MANA_SVGS.W;
      title = "Maná blanco";
    } else if (sym === "U") {
      className = "U";
      content = MANA_SVGS.U;
      title = "Maná azul";
    } else if (sym === "B") {
      className = "B";
      content = MANA_SVGS.B;
      title = "Maná negro";
    } else if (sym === "R") {
      className = "R";
      content = MANA_SVGS.R;
      title = "Maná rojo";
    } else if (sym === "G") {
      className = "G";
      content = MANA_SVGS.G;
      title = "Maná verde";
    } else if (sym === "C") {
      className = "C";
      content = MANA_SVGS.C;
      title = "Maná incoloro";
    } else if (sym === "S") {
      className = "S";
      content = MANA_SVGS.S;
      title = "Maná gélido (requiere permanente nevado)";
    } else if (sym === "T") {
      className = "T";
      content = MANA_SVGS.T;
      title = "Girar este permanente (Tap)";
    } else if (sym === "Q") {
      className = "Q";
      content = MANA_SVGS.Q;
      title = "Enderezar este permanente (Untap)";
    } else if (sym === "E") {
      className = "E";
      content = MANA_SVGS.E;
      title = "Reserva de energía";
    } else if (sym === "CHAOS") {
      className = "chaos";
      content = MANA_SVGS.chaos;
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
