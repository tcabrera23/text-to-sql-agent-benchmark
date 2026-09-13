import sys
from pathlib import Path

# Permite importar core/, app/ y benchmark/ como paquetes de nivel de repo, ya que
# `streamlit run app/main.py` solo agrega al sys.path la carpeta de este script,
# no la raíz del proyecto.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import os
from dotenv import load_dotenv
import uuid

from app import tabs

# Imports opcionales de LLM providers con manejo de errores
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except Exception as e:
    GROQ_AVAILABLE = False
    st.warning(f"Groq no disponible: {e}")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception as e:
    OPENAI_AVAILABLE = False
    st.warning(f"OpenAI no disponible: {e}")

# --- 1. CONFIGURACIÓN GENERAL Y VARIABLES DE ENTORNO ---

# Cargar variables de entorno desde .env
load_dotenv()

# No se requieren validaciones estrictas de variables de entorno
# ya que las API keys se pueden introducir en la interfaz

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Agente SQL y Dashboard IA",
    page_icon="🚀",
    layout="wide"
)

# --- 2. INICIALIZACIÓN DE CLIENTES Y ESTADO DE LA SESIÓN ---

# Inicializar estado de la sesión
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = ""
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""
if "openrouter_api_key" not in st.session_state:
    st.session_state.openrouter_api_key = ""
if 'query_results' not in st.session_state:
    st.session_state.query_results = []
if "dashboard_layout" not in st.session_state:
    st.session_state.dashboard_layout = {"title": "Dashboard de Análisis de Negocio", "kpis": [], "charts": []}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'arena_results' not in st.session_state:
    st.session_state.arena_results = []
if 'custom_arena_models' not in st.session_state:
    st.session_state.custom_arena_models = {}

session_id = st.session_state.session_id

# --- 3. SIDEBAR DE CONFIGURACIÓN ---

st.sidebar.title("⚙️ Configuración General")

# Determinar proveedores disponibles
available_providers = []
if GROQ_AVAILABLE:
    available_providers.append("Groq")
if OPENAI_AVAILABLE:
    available_providers.append("OpenAI")
    available_providers.append("OpenRouter")  # OpenRouter usa el cliente de OpenAI

if not available_providers:
    st.error("No hay proveedores LLM disponibles. Por favor reinstala las dependencias.")
    st.stop()

# Selección de proveedor de LLM
selected_provider = st.sidebar.radio(
    "Elige el proveedor del modelo",
    available_providers,
    key="selected_provider"
)

# Inputs para las API Keys
st.sidebar.title("🔑 API Keys")
if selected_provider == "Groq":
    user_groq_key = st.sidebar.text_input("Introduce tu API Key de Groq", value=st.session_state.groq_api_key, type="password")
    if user_groq_key and user_groq_key != st.session_state.groq_api_key:
        st.session_state.groq_api_key = user_groq_key
        st.sidebar.success("API Key de Groq actualizada.")
        st.rerun()
elif selected_provider == "OpenAI":
    user_openai_key = st.sidebar.text_input("Introduce tu API Key de OpenAI", value=st.session_state.openai_api_key, type="password")
    if user_openai_key and user_openai_key != st.session_state.openai_api_key:
        st.session_state.openai_api_key = user_openai_key
        st.sidebar.success("API Key de OpenAI actualizada.")
        st.rerun()
elif selected_provider == "OpenRouter":
    user_openrouter_key = st.sidebar.text_input("Introduce tu API Key de OpenRouter", value=st.session_state.openrouter_api_key, type="password")
    if user_openrouter_key and user_openrouter_key != st.session_state.openrouter_api_key:
        st.session_state.openrouter_api_key = user_openrouter_key
        st.sidebar.success("API Key de OpenRouter actualizada.")
        st.rerun()

    # Selector de modelo para OpenRouter
    openrouter_model = st.sidebar.selectbox(
        "Selecciona el modelo",
        [
            "meta-llama/llama-3.3-70b-instruct",
            "openai/gpt-4o",
            "google/gemini-2.0-flash-exp:free",
            "anthropic/claude-3.5-sonnet",
            "mistralai/mistral-large"
        ],
        key="openrouter_model"
    )

# --- 4. CONEXIONES A SERVICIOS ---

# Determinar la API key a usar
effective_groq_key = st.session_state.get("groq_api_key") or os.getenv("GROQ_API_KEY")
effective_openai_key = st.session_state.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
effective_openrouter_key = st.session_state.get("openrouter_api_key") or os.getenv("OPENROUTER_API_KEY")

# Inicializar cliente del LLM
llm_client = None
model_name = ""
error_message = ""

if selected_provider == "Groq":
    if not GROQ_AVAILABLE:
        error_message = "Groq no está disponible. Reinstala con: pip install groq"
    elif effective_groq_key:
        try:
            llm_client = Groq(api_key=effective_groq_key)
            model_name = "llama-3.3-70b-versatile"
        except Exception as e:
            error_message = f"Error al inicializar Groq: {e}"
    else:
        error_message = "Falta la API Key de Groq."
elif selected_provider == "OpenAI":
    if not OPENAI_AVAILABLE:
        error_message = "OpenAI no está disponible. Reinstala con: pip install openai"
    elif effective_openai_key:
        try:
            llm_client = OpenAI(api_key=effective_openai_key)
            model_name = "gpt-4o"
        except Exception as e:
            error_message = f"Error al inicializar OpenAI: {e}"
    else:
        error_message = "Falta la API Key de OpenAI."
elif selected_provider == "OpenRouter":
    if not OPENAI_AVAILABLE:
        error_message = "OpenRouter requiere el cliente de OpenAI. Reinstala con: pip install openai"
    elif effective_openrouter_key:
        try:
            llm_client = OpenAI(
                api_key=effective_openrouter_key,
                base_url="https://openrouter.ai/api/v1"
            )
            model_name = st.session_state.get("openrouter_model", "meta-llama/llama-3.3-70b-instruct")
        except Exception as e:
            error_message = f"Error al inicializar OpenRouter: {e}"
    else:
        error_message = "Falta la API Key de OpenRouter."

if not llm_client:
    st.error(error_message + " Por favor, introdúcela en la barra lateral o en tu archivo .env.")
    st.stop()

# --- 5. INTERFAZ DE USUARIO (PESTAÑAS) ---

st.title("🚀 Agente SQL y Dashboard IA")
st.caption(f"Proveedor de Modelo: {selected_provider} | Modelo: {model_name}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat de Análisis", "📊 Dashboard Interactivo", "🏟️ Arena LLM", "📊 Resultados Arena", "📈 Métricas"])

with tab1:
    tabs.render_chat_tab(llm_client, model_name, session_id)

with tab2:
    tabs.render_dashboard_tab(llm_client, model_name, session_id)

with tab3:
    tabs.render_arena_tab(effective_openrouter_key, session_id)

with tab4:
    tabs.render_arena_results_tab()

with tab5:
    tabs.render_metrics_tab()
