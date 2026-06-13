import os
import re
import uuid
import requests
import streamlit as st

from src.config.settings import get_settings

# Configure Page
st.set_page_config(
    page_title="MTG Chatbot Assistant",
    page_icon="🧙‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern design aesthetics (dark theme look, sleek card containers)
st.markdown(
    """
<style>
    .reportview-container {
        background: #0e1117;
    }
    .card-viewer {
        background-color: #1f2937;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #374151;
        margin-top: 20px;
    }
    .custom-title {
        font-family: 'Outfit', sans-serif;
        color: #f3f4f6;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .custom-subtitle {
        color: #9ca3af;
        margin-bottom: 2rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

settings = get_settings()
API_URL = settings.API_URL

# Initialize session state variables
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_card_image" not in st.session_state:
    st.session_state.last_card_image = None
if "last_card_name" not in st.session_state:
    st.session_state.last_card_name = None

# Sidebar Content
with st.sidebar:
    st.image(
        "https://svgsilh.com/svg/309783.svg", width=60
    )  # Sleek wizard symbol or similar logo
    st.title("MTG Call Center")
    st.markdown("---")

    # Actions
    if st.button("Resetear Conversación"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.session_state.last_card_image = None
        st.session_state.last_card_name = None
        st.rerun()

    # Card Viewer Box in Sidebar
    if st.session_state.last_card_image:
        st.markdown('<div class="card-viewer">', unsafe_allow_html=True)
        st.subheader(f"🎴 Vista Rápida: {st.session_state.last_card_name}")
        st.image(st.session_state.last_card_image, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Main Panel
st.markdown(
    '<h1 class="custom-title">🧙‍♂️ Asistente de Magic: The Gathering</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="custom-subtitle">Soporte automático para dudas de reglas y consulta de cartas de MTG en tiempo real</p>',
    unsafe_allow_html=True,
)

# Check API backend health status
try:
    health_resp = requests.get(f"{API_URL}/health", timeout=3)
    if health_resp.status_code == 200:
        health_data = health_resp.json()
        if not health_data.get("database_initialized"):
            st.warning(
                "⚠️ La base de datos vectorial de reglas no ha sido inicializada en el backend. Las consultas de reglas no devolverán contexto. Corre la ingesta de reglas en el host o contenedor."
            )
    else:
        st.error(
            f"⚠️ El servidor API respondió con error de estado: {health_resp.status_code}"
        )
except Exception:
    st.error(
        f"❌ No se puede conectar con el backend API en {API_URL}. Asegúrate de que el servidor FastAPI está corriendo (`uv run uvicorn src.main:app` o vía Docker Compose)."
    )

# Render chat history
for role, message_content in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message_content)

        # Check if the message contains card images and display them inline as well
        image_urls = re.findall(
            r"https?://[^\s)]+\.(?:png|jpg|jpeg|gif)", message_content
        )
        for url in image_urls:
            st.image(url, width=220, caption="Carta de la API")

        # Check if custom card image path is mentioned
        custom_card_paths = re.findall(
            r"custom_cards/[a-z0-9_-]+\.png", message_content, re.IGNORECASE
        )
        for path in custom_card_paths:
            if os.path.exists(path):
                st.image(path, width=220, caption="Mockup de Carta Custom")

# Chat Input
user_input = st.chat_input("Pregúntame sobre reglas, cartas o crea una customizada...")

if user_input:
    # Append user question
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate Assistant Response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()

        with st.spinner("Buscando respuestas y cartas..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "message": user_input,
                        "session_id": st.session_state.session_id,
                    },
                    timeout=60,
                )

                if response.status_code == 200:
                    assistant_msg = response.json()["response"]
                    response_placeholder.markdown(assistant_msg)

                    # Append response to history
                    st.session_state.chat_history.append(("assistant", assistant_msg))

                    # Scan response for card image URLs to update the Sidebar Viewer
                    image_urls = re.findall(
                        r"https?://[^\s)]+\.(?:png|jpg|jpeg|gif)", assistant_msg
                    )
                    custom_card_paths = re.findall(
                        r"custom_cards/[a-z0-9_-]+\.png", assistant_msg, re.IGNORECASE
                    )

                    if custom_card_paths and os.path.exists(custom_card_paths[0]):
                        st.session_state.last_card_image = custom_card_paths[0]
                        st.session_state.last_card_name = "Carta Creada"
                        st.rerun()
                    elif image_urls:
                        st.session_state.last_card_image = image_urls[0]
                        st.session_state.last_card_name = "Carta de la API"
                        st.rerun()
                else:
                    error_detail = response.json().get("detail", "Error desconocido.")
                    st.error(
                        f"Error del servidor API (Código {response.status_code}): {error_detail}"
                    )
            except Exception as e:
                st.error(f"Ocurrió un error de red al comunicarse con el backend: {e}")
