// Punto de entrada principal para la UI modularizada de MTG Call Center
import { initSession } from './state.js';
import { initHealthDashboard } from './components/healthDashboard.js';
import { initThemeSelector } from './components/themeSelector.js';
import { initRecentCardsList } from './components/recentCardsList.js';
import { initCardInspector } from './components/cardInspector.js';
import { initChatArea } from './components/chatArea.js';

document.addEventListener("DOMContentLoaded", () => {
  console.log("🧙‍♂️ Inicializando MTG Call Center UI modular...");
  
  // 1. Inicializar sesión y cargar datos de localStorage
  initSession();
  
  // 2. Inicializar los componentes de la interfaz
  initThemeSelector();
  initHealthDashboard();
  initRecentCardsList();
  initCardInspector();
  initChatArea();
  
  console.log("✨ MTG Call Center UI inicializada con éxito.");
});
