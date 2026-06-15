import { fetchHealthStatus } from '../api.js';

let apiBadge, dbBadge, keyBadge;

/**
 * Actualiza el DOM con el estado actual del backend.
 * 
 * @param {Object|null} data Datos de respuesta del endpoint de salud
 */
function updateHealthDashboard(data) {
  if (!apiBadge || !dbBadge || !keyBadge) return;

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
    // API desconectada
    apiBadge.className = "badge badge-offline";
    apiBadge.innerText = "Desconectado";
    dbBadge.className = "badge badge-loading";
    dbBadge.innerText = "Faltante";
    keyBadge.className = "badge badge-loading";
    keyBadge.innerText = "Faltante";
  }
}

/**
 * Realiza una verificación asíncrona del estado del sistema.
 */
export async function checkHealth() {
  const data = await fetchHealthStatus();
  updateHealthDashboard(data);
}

/**
 * Inicializa el componente de salud, obteniendo referencias a los elementos del DOM
 * y programando la verificación periódica cada 30 segundos.
 */
export function initHealthDashboard() {
  apiBadge = document.getElementById("apiBadge");
  dbBadge = document.getElementById("dbBadge");
  keyBadge = document.getElementById("keyBadge");

  // Realizar verificación inicial
  checkHealth();

  // Programar verificación periódica cada 30 segundos
  setInterval(checkHealth, 30000);
}
