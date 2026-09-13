import sys
from pathlib import Path

# Permite importar core/, app/ y benchmark/ como paquetes de nivel de repo, ya que
# `streamlit run app/main.py` solo agrega al sys.path la carpeta de este script,
# no la raíz del proyecto.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import json
import pandas as pd
import httpx
import os
from dotenv import load_dotenv
import uuid
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import time

from core.database import execute_sql
from core.metrics import log_metrics, calculate_cost, calculate_efficiency
from core.models import ARENA_MODELS
from core.schema import CHINOOK_SCHEMA_DDL
from core.paths import ARENA_RESULTS_PATH, METRICS_CSV_PATH
from benchmark.catalog import ARENA_TESTS, get_tests_by_level, validate_result, TEST_STATS
from app.pricing import PRICING_TABLE, COST_ANALYSIS, RECOMMENDATIONS

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


# --- 5. ESQUEMA DE LA BASE DE DATOS Y PROMPTS DEL SISTEMA ---

# Prompt para el Agente de Chat SQL
CHAT_AGENT_PROMPT = f'''
Eres un analista de datos experto en SQL. Tu objetivo es responder a las preguntas del usuario sobre la base de datos.
1. Recibe una pregunta en lenguaje natural que puede ser amplia o específica. En caso de preguntas abiertas, como 'analiza mi negocio' o 'dame un resumen de las ventas', tu tarea es tomar la iniciativa.
Un buen análisis de negocio implica investigar varias áreas clave. Deberías considerar generar consultas que respondan a preguntas como
- Rendimiento de Ventas: ¿Cuáles son los 5 artistas, géneros musicales o canciones más vendidos?
- Análisis de Clientes: ¿De qué países provienen los clientes que más gastan? ¿Cuál es el valor de compra promedio por cliente?
- Tendencias Temporales: ¿Cómo han evolucionado las ventas mes a mes o año a año? (Implica agrupar por invoicedate).
- Rendimiento de Empleados: ¿Qué agente de soporte de ventas ha generado más ingresos?"
2. Conviértela en una consulta SQL SELECT válida para SQLite.
3. Usa SIEMPRE la herramienta "consulta_sql" para ejecutar la consulta.
4. Responde al usuario en lenguaje natural basándote en los resultados.
5. Si el usuario pide un análisis general (ej. "analiza el negocio"), crea un plan de 2-3 pasos y ejecuta una consulta para cada uno.
6. Los nombres de tablas y columnas usan PascalCase (ej: "artists", "ArtistId"). Respeta las mayúsculas.
7. Si la consulta no devuelve resultados, informa amablemente al usuario.

Alcance:
- Solo puedes usar consultas SELECT.
- Solo hablas respecto a la base de datos proporcionada.

Esquema de la base de datos:
{CHINOOK_SCHEMA_DDL}
'''

# Prompt para el Agente de Dashboard
DASHBOARD_AGENT_PROMPT = f"""
Eres un diseñador experto de dashboards de Business Intelligence. Tu objetivo es crear un dashboard claro y profesional basado en las peticiones del usuario sobre la base de datos.
Tu proceso:
1. Analiza la petición del usuario (ej: "Muéstrame las ventas por género y el total de clientes"). Cuando un usuario te haga una pregunta abierta como 'analiza mi negocio' o 'dame un resumen de las ventas', tu tarea es tomar la iniciativa.
Un buen análisis de negocio implica investigar varias áreas clave. Deberías considerar generar consultas que respondan a preguntas como
- Rendimiento de Ventas: ¿Cuáles son los 5 artistas, géneros musicales o canciones más vendidos?
- Análisis de Clientes: ¿De qué países provienen los clientes que más gastan? ¿Cuál es el valor de compra promedio por cliente?
- Tendencias Temporales: ¿Cómo han evolucionado las ventas mes a mes o año a año? (Implica agrupar por invoicedate).
- Rendimiento de Empleados: ¿Qué agente de soporte de ventas ha generado más ingresos?"
2. Descompón la petición en los componentes necesarios: KPIs y Gráficos.
3. Para cada componente, usa la herramienta específica: `add_kpi` o `add_chart`.
4. Para los gráficos, elige la librería más adecuada (`plotly`, `seaborn`, `matplotlib`) y define todos sus parámetros.
5. Llama a las herramientas necesarias para construir el dashboard.

Esquema de la Base de Datos:
{CHINOOK_SCHEMA_DDL}
"""

# --- 6. DEFINICIÓN DE HERRAMIENTAS (TOOLS) ---

# Herramienta 1: Consulta SQL (Común para ambos agentes)
def consulta_sql(sql_query: str):
    """Ejecuta una consulta SQL SELECT y devuelve un DataFrame y un JSON."""
    df, error = execute_sql(sql_query)

    if error:
        return pd.DataFrame(), None, error

    if df.empty:
        return pd.DataFrame(), json.dumps([{"message": "No se encontraron resultados."}]), "Consulta exitosa, pero sin resultados."

    json_output = df.to_json(orient='records', date_format='iso')
    return df, json_output, None

# Herramienta 2: Añadir KPI al Dashboard
def add_kpi(element_id: str, title: str, sql_query: str):
    """Añade una tarjeta de KPI al dashboard."""
    df, _, error = consulta_sql(sql_query)
    if error or df.empty:
        return f"No se pudieron obtener datos para el KPI '{title}'."
    raw_value = df.iloc[0, 0]
    value = f"${raw_value:,.2f}" if isinstance(raw_value, (int, float)) and raw_value > 1000 else str(raw_value)
    new_kpi = {"id": element_id, "title": title, "value": value}
    st.session_state.dashboard_layout["kpis"] = [k for k in st.session_state.dashboard_layout["kpis"] if k['id'] != element_id] + [new_kpi]
    return f"KPI '{title}' añadido/actualizado."

# Herramienta 3: Añadir Gráfico al Dashboard
def add_chart(element_id: str, title: str, sql_query: str, library: str, chart_type: str, x_col: str, y_col: str, color_col: str = None):
    """Añade un gráfico al dashboard."""
    df, _, error = consulta_sql(sql_query)
    if error or df.empty:
        return f"No se pudieron obtener datos para el gráfico '{title}'."

    fig = None
    try:
        if library == "plotly":
            if chart_type == "bar": fig = px.bar(df, x=x_col, y=y_col, title=title, color=color_col)
            elif chart_type == "line": fig = px.line(df, x=x_col, y=y_col, title=title, color=color_col)
            elif chart_type == "pie": fig = px.pie(df, names=x_col, values=y_col, title=title)
        else: # Matplotlib / Seaborn
            fig, ax = plt.subplots()
            if library == "seaborn":
                if chart_type == "histogram": sns.histplot(df, x=x_col, ax=ax)
                elif chart_type == "boxplot": sns.boxplot(data=df, x=x_col, y=y_col, ax=ax)
            else: # Matplotlib
                ax.bar(df[x_col], df[y_col])
            ax.set_title(title)
            ax.tick_params(axis='x', rotation=45)
    except Exception as e:
        return f"Error al generar el gráfico '{title}': {e}"

    if fig:
        new_chart = {"id": element_id, "title": title, "figure": fig}
        st.session_state.dashboard_layout["charts"] = [c for c in st.session_state.dashboard_layout["charts"] if c['id'] != element_id] + [new_chart]
        return f"Gráfico '{title}' añadido/actualizado."
    return f"No se pudo generar el gráfico '{title}' con los parámetros proporcionados."


# Definición de herramientas para el LLM
chat_tools = [{"type": "function", "function": {"name": "consulta_sql", "description": "Ejecuta una consulta SQL SELECT.", "parameters": {"type": "object", "properties": {"sql_query": {"type": "string", "description": "La consulta SQL a ejecutar."}}, "required": ["sql_query"]}}}]
dashboard_tools = [
    {"type": "function", "function": {"name": "add_kpi", "description": "Añade una tarjeta de KPI.", "parameters": {"type": "object", "properties": {"element_id": {"type": "string"}, "title": {"type": "string"}, "sql_query": {"type": "string"}}, "required": ["element_id", "title", "sql_query"]}}},
    {"type": "function", "function": {"name": "add_chart", "description": "Añade un gráfico.", "parameters": {"type": "object", "properties": {"element_id": {"type": "string"}, "title": {"type": "string"}, "sql_query": {"type": "string"}, "library": {"type": "string", "enum": ["plotly", "seaborn", "matplotlib"]}, "chart_type": {"type": "string", "enum": ["bar", "line", "pie", "histogram", "boxplot"]}, "x_col": {"type": "string"}, "y_col": {"type": "string"}, "color_col": {"type": "string"}}, "required": ["element_id", "title", "sql_query", "library", "chart_type", "x_col", "y_col"]}}}
]

# --- 7. LÓGICA DE LOS AGENTES ---

def run_chat_agent(prompt: str):
    """Ejecuta el agente de chat SQL."""
    start_time = time.time()
    st.session_state.query_results = []

    # Cargar historial desde session_state
    messages = st.session_state.chat_history.copy()

    # Contar prompts de usuario
    user_prompts = [m for m in messages if m['role'] == 'user']

    # Determinar si se está usando una API key de usuario
    using_user_api_key = bool(
        st.session_state.get("groq_api_key") or
        st.session_state.get("openai_api_key") or
        st.session_state.get("openrouter_api_key")
    )

    # Mostrar el mensaje del usuario en la UI
    with st.chat_message("user"):
        st.markdown(prompt)

    # Verificar el límite de interacciones
    if not using_user_api_key and len(user_prompts) >= 4:
        with st.chat_message("assistant"):
            st.warning("Has alcanzado el límite de 4 interacciones gratuitas. Por favor, introduce tu propia API key en la barra lateral para continuar.")
        return

    # Si la verificación pasa, continuar con la lógica del agente

    # Añadir mensaje del usuario al historial
    user_message = {"role": "user", "content": prompt}
    messages.append(user_message)
    st.session_state.chat_history.append(user_message)

    # Procesar la respuesta del asistente
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            messages_for_api = [{"role": "system", "content": CHAT_AGENT_PROMPT}] + messages
            tokens_input = 0
            tokens_output = 0
            total_tokens = 0

            try:
                api_start = time.time()
                response = llm_client.chat.completions.create(model=model_name, messages=messages_for_api, tools=chat_tools, tool_choice="auto")
                api_latency = time.time() - api_start

                if response.usage:
                    tokens_input += response.usage.prompt_tokens
                    tokens_output += response.usage.completion_tokens
                    total_tokens += response.usage.total_tokens

                response_message = response.choices[0].message
                final_response_content = ""

                if response_message.tool_calls:
                    messages_for_api.append(response_message)
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        if function_name == "consulta_sql":
                            function_args = json.loads(tool_call.function.arguments)
                            sql_query = function_args.get("sql_query")
                            df, json_output, error = consulta_sql(sql_query)
                            st.session_state.query_results.append({"sql": sql_query, "df": df, "error": error})
                            tool_output = json.dumps({"error": error}) if error else json_output
                            messages_for_api.append({"role": "tool", "tool_call_id": tool_call.id, "content": tool_output})

                    api_start_2 = time.time()
                    final_response_completion = llm_client.chat.completions.create(model=model_name, messages=messages_for_api)
                    api_latency += time.time() - api_start_2

                    if final_response_completion.usage:
                        tokens_input += final_response_completion.usage.prompt_tokens
                        tokens_output += final_response_completion.usage.completion_tokens
                        total_tokens += final_response_completion.usage.total_tokens
                    final_response_content = final_response_completion.choices[0].message.content
                else:
                    final_response_content = response_message.content

            except Exception as e:
                final_response_content = f"Se produjo un error: {e}"
                api_latency = time.time() - start_time

            st.markdown(final_response_content)
            assistant_message = {"role": "assistant", "content": final_response_content}
            messages.append(assistant_message)
            st.session_state.chat_history.append(assistant_message)

            # Calcular tiempo total de ejecución
            execution_time = time.time() - start_time

            # Log metrics
            api_key_source = "user" if using_user_api_key else "default"
            log_metrics(
                session_id=session_id,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_processed=total_tokens,
                message_count=len(messages),
                api_key_source=api_key_source,
                llm_model=model_name,
                latency_api=api_latency,
                execution_time=execution_time
            )

    st.rerun()


def run_dashboard_agent(user_prompt: str):
    """Ejecuta el agente de diseño de dashboards."""
    start_time = time.time()
    messages = [
        {"role": "system", "content": DASHBOARD_AGENT_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    with st.spinner("El agente está diseñando el dashboard..."):
        tokens_input = 0
        tokens_output = 0
        total_tokens = 0

        try:
            api_start = time.time()
            response = llm_client.chat.completions.create(model=model_name, messages=messages, tools=dashboard_tools, tool_choice="auto")
            api_latency = time.time() - api_start

            if response.usage:
                tokens_input = response.usage.prompt_tokens
                tokens_output = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens

            response_message = response.choices[0].message

            if response_message.tool_calls:
                available_functions = {"add_kpi": add_kpi, "add_chart": add_chart}
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = available_functions[function_name]
                    function_args = json.loads(tool_call.function.arguments)
                    function_to_call(**function_args)
            else:
                st.warning("El agente no pudo determinar qué acción realizar. Intenta ser más específico.")

        except Exception as e:
            st.error(f"Error al ejecutar el agente del dashboard: {e}")
            api_latency = time.time() - start_time

        # Calcular tiempo total de ejecución
        execution_time = time.time() - start_time

        # Log metrics
        using_user_api_key = bool(
            st.session_state.get("groq_api_key") or
            st.session_state.get("openai_api_key") or
            st.session_state.get("openrouter_api_key")
        )
        api_key_source = "user" if using_user_api_key else "default"
        log_metrics(
            session_id=session_id,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_processed=total_tokens,
            message_count=len(messages),
            api_key_source=api_key_source,
            llm_model=model_name,
            latency_api=api_latency,
            execution_time=execution_time
        )

    st.rerun()

def run_arena_test(test: dict, openrouter_api_key: str):
    """
    Ejecuta un test del arena contra los 5 modelos y recopila métricas.

    Args:
        test: Diccionario con la información del test
        openrouter_api_key: API key de OpenRouter

    Returns:
        Lista de resultados por modelo
    """
    if not openrouter_api_key:
        st.error("Se requiere una API key de OpenRouter para usar el Arena.")
        return []

    # Prompt del sistema para generación SQL pura
    arena_system_prompt = f"""
Eres un experto en SQL. Convierte la siguiente pregunta en una consulta SQL SELECT válida para SQLite.

Reglas:
1. Responde ÚNICAMENTE con la consulta SQL, sin explicaciones.
2. NO uses punto y coma al final.
3. Los nombres usan PascalCase (ej: "ArtistId", "artists").

Esquema:
{CHINOOK_SCHEMA_DDL}

Responde SOLO con el SQL.
"""

    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, (model_key, model_config) in enumerate(ARENA_MODELS.items()):
        status_text.text(f"Ejecutando en {model_config['display_name']}...")

        start_time = time.time()
        result = {
            "test_id": test["id"],
            "test_name": test["name"],
            "test_level": test["level"],
            "model_key": model_key,
            "model_name": model_config["name"],
            "model_display": model_config["display_name"],
            "model_category": model_config["category"],
            "success": False,
            "error": None,
            "sql_generated": None,
            "execution_time": 0,
            "ttft": 0,
            "latency_api": 0,
            "tokens_input": 0,
            "tokens_output": 0,
            "tokens_total": 0,
            "cost": 0,
            "efficiency": 0,
            "validation": {},
            "result_rows": 0
        }

        try:
            # Crear cliente para este modelo
            model_client = OpenAI(
                api_key=openrouter_api_key,
                base_url="https://openrouter.ai/api/v1"
            )

            messages = [
                {"role": "system", "content": arena_system_prompt},
                {"role": "user", "content": test["prompt"]}
            ]

            # Llamada a la API
            api_start = time.time()
            response = model_client.chat.completions.create(
                model=model_config["name"],
                messages=messages,
                temperature=0,
                max_tokens=500
            )
            latency_api = time.time() - api_start
            ttft = latency_api  # Para llamadas no-streaming, TTFT ≈ latencia total

            # Extraer SQL
            sql_generated = response.choices[0].message.content.strip()

            # Limpiar markdown si existe
            if "```sql" in sql_generated:
                sql_generated = sql_generated.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql_generated:
                sql_generated = sql_generated.split("```")[1].split("```")[0].strip()

            result["sql_generated"] = sql_generated

            # Tokens
            if response.usage:
                result["tokens_input"] = response.usage.prompt_tokens
                result["tokens_output"] = response.usage.completion_tokens
                result["tokens_total"] = response.usage.total_tokens

            # Ejecutar SQL
            df, json_output, error = consulta_sql(sql_generated)

            if error:
                result["error"] = error
                result["success"] = False
            else:
                # Validar resultado
                validation = validate_result(test["id"], df, error)
                result["validation"] = validation
                result["success"] = validation["success"]
                result["result_rows"] = len(df)

            # Métricas de tiempo
            result["execution_time"] = time.time() - start_time
            result["ttft"] = ttft
            result["latency_api"] = latency_api

            # Calcular costo y eficiencia
            result["cost"] = calculate_cost(
                model_config["name"],
                result["tokens_input"],
                result["tokens_output"]
            )
            result["efficiency"] = calculate_efficiency(
                result["tokens_total"],
                result["execution_time"]
            )

            # Log metrics
            log_metrics(
                session_id=session_id,
                tokens_input=result["tokens_input"],
                tokens_output=result["tokens_output"],
                tokens_processed=result["tokens_total"],
                message_count=1,
                api_key_source="user",
                llm_model=model_config["name"],
                latency_api=latency_api,
                execution_time=result["execution_time"],
                success=result["success"],
                ttft=ttft,
                test_id=test["id"],
                test_level=test["level"]
            )

        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
            result["execution_time"] = time.time() - start_time

        results.append(result)
        progress_bar.progress((idx + 1) / len(ARENA_MODELS))
        time.sleep(0.3)  # Evitar rate limiting

    status_text.text("✅ Test completado!")
    progress_bar.empty()
    status_text.empty()

    return results

# --- 8. INTERFAZ DE USUARIO (PESTAÑAS) ---

st.title("🚀 Agente SQL y Dashboard IA")
st.caption(f"Proveedor de Modelo: {selected_provider} | Modelo: {model_name}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat de Análisis", "📊 Dashboard Interactivo", "🏟️ Arena LLM", "📊 Resultados Arena", "📈 Métricas"])

# --- Pestaña 1: Chat de Análisis ---
with tab1:
    st.header("Análisis Conversacional de Datos")
    col_chat, col_data = st.columns([2, 1.5])

    with col_chat:
        # Contenedor para el historial de chat
        chat_container = st.container(height=600)

        # Cargar y mostrar historial
        messages = st.session_state.chat_history
        if not messages:
            messages = [{"role": "assistant", "content": "¿Qué te gustaría saber de la base de datos?"}]

        with chat_container:
            for message in messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Input del usuario
        if prompt := st.chat_input("Ej: ¿Cuáles son los 5 artistas más vendidos?"):
            run_chat_agent(prompt)

    with col_data:
        st.subheader("Resultados de la Consulta")
        if not st.session_state.query_results:
            st.code("Aquí se mostrará la consulta SQL...", language="sql")
            st.dataframe(pd.DataFrame())
        else:
            for i, result in enumerate(st.session_state.query_results):
                st.subheader(f"Consulta {i+1}")
                st.code(result["sql"], language="sql")
                if result["error"]:
                    st.error(result["error"])
                else:
                    st.dataframe(result["df"])
                    # Botón para pasar al dashboard
                    if st.button(f"Visualizar Consulta {i+1} en Dashboard", key=f"viz_{i}"):
                        prompt = f"Crea una visualización para la siguiente consulta y sus datos. La consulta es: `{result['sql']}`. Los datos son: {result['df'].to_json(orient='records')}. Elige el mejor tipo de gráfico."
                        run_dashboard_agent(prompt)
                        st.toast("Petición enviada al agente de dashboard. ¡Revisa la otra pestaña!")


# --- Pestaña 2: Dashboard Interactivo ---
with tab2:
    st.header(st.session_state.dashboard_layout["title"])

    # Controles del Dashboard en la barra lateral
    st.sidebar.title("Control del Dashboard")
    dashboard_prompt = st.sidebar.text_area("Describe el KPI o gráfico que quieres añadir/modificar:", height=100, key="dashboard_prompt")
    if st.sidebar.button("Ejecutar Petición de Dashboard"):
        if dashboard_prompt:
            run_dashboard_agent(dashboard_prompt)
        else:
            st.sidebar.warning("Por favor, introduce una descripción.")
    if st.sidebar.button("Reiniciar Dashboard"):
        st.session_state.dashboard_layout = {"title": "Dashboard de Análisis de Negocio", "kpis": [], "charts": []}
        st.rerun()

    # Renderizar KPIs
    if st.session_state.dashboard_layout["kpis"]:
        kpi_cols = st.columns(len(st.session_state.dashboard_layout["kpis"]))
        for i, kpi in enumerate(st.session_state.dashboard_layout["kpis"]):
            kpi_cols[i].metric(label=kpi["title"], value=kpi["value"])
        st.markdown("---")

    # Renderizar Gráficos
    if st.session_state.dashboard_layout["charts"]:
        chart_cols = st.columns(2)
        col_idx = 0
        for chart in st.session_state.dashboard_layout["charts"]:
            with chart_cols[col_idx]:
                st.subheader(chart["title"])
                if 'figure' in chart and chart['figure'] is not None:
                    if isinstance(chart['figure'], plt.Figure):
                        st.pyplot(chart['figure'], width=True)
                    else: # Asumimos que es Plotly
                        st.plotly_chart(chart['figure'], width=True)
            col_idx = (col_idx + 1) % 2
    elif not st.session_state.dashboard_layout["kpis"]:
        st.info("El dashboard está vacío. Usa el panel de la izquierda para añadir KPIs y gráficos.")

# --- Pestaña 3: Arena LLM ---
with tab3:
    st.header("🏟️ Arena LLM - Comparación de Modelos")

    # Verificar API key de OpenRouter
    if not effective_openrouter_key:
        st.warning("⚠️ Se requiere una API key de OpenRouter para usar el Arena. Introdúcela en la barra lateral.")
        st.info("El Arena te permite comparar 5 modelos diferentes de OpenRouter en las mismas tareas SQL para encontrar el equilibrio perfecto entre precio y calidad.")
    else:
        # Panel de información de modelos
        st.subheader("🤖 Modelos en Competencia")

        cols = st.columns(5)
        for idx, (model_key, model_config) in enumerate(ARENA_MODELS.items()):
            with cols[idx]:
                st.markdown(f"""
                <div style='background-color: {model_config['color']}20; padding: 15px; border-radius: 10px; border-left: 4px solid {model_config['color']}'>
                    <h4 style='margin: 0; color: {model_config['color']}'>{model_config['category']}</h4>
                    <p style='margin: 5px 0; font-size: 14px; font-weight: bold;'>{model_config['display_name']}</p>
                    <p style='margin: 0; font-size: 12px; color: #666;'>{model_config['description']}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Tabla de precios y recomendaciones
        with st.expander("💰 Ver Tabla de Precios y Análisis de Costos"):
            st.subheader("Comparativa de Precios")
            st.dataframe(PRICING_TABLE, use_container_width=True, hide_index=True)

            st.markdown("### 📊 Análisis de Costos por Escenario")
            col1, col2, col3 = st.columns(3)

            for idx, scenario in enumerate(COST_ANALYSIS["escenarios"]):
                with [col1, col2, col3][idx]:
                    st.markdown(f"**{scenario['nombre']}**")
                    st.caption(f"{scenario['consultas']:,} consultas/mes")
                    for model, cost in scenario["costos"].items():
                        st.text(f"{model}: ${cost:.2f}")

            st.markdown("### 🎯 Recomendaciones por Caso de Uso")
            rec_col1, rec_col2 = st.columns(2)

            rec_list = list(RECOMMENDATIONS.items())
            for idx, (use_case, rec) in enumerate(rec_list):
                with rec_col1 if idx % 2 == 0 else rec_col2:
                    st.markdown(f"**{use_case.replace('_', ' ').title()}**")
                    st.info(f"✅ {rec['modelo_recomendado']}\n\n{rec['razon']}")

        st.markdown("---")

        # Selector de tests
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📝 Selecciona un Test")

            # Filtro por nivel
            level_filter = st.selectbox(
                "Nivel de Dificultad",
                ["Todos", "Nivel 1 - Fácil", "Nivel 2 - Medio", "Nivel 3 - Difícil"],
                key="arena_level_filter"
            )

            # Filtrar tests
            if level_filter == "Todos":
                filtered_tests = ARENA_TESTS
            else:
                level_num = int(level_filter.split()[1])
                filtered_tests = get_tests_by_level(level_num)

            # Selector de test
            test_options = {f"{t['id']} - {t['name']}": t for t in filtered_tests}
            selected_test_key = st.selectbox(
                "Test",
                list(test_options.keys()),
                key="arena_test_selector"
            )

            if selected_test_key:
                selected_test = test_options[selected_test_key]

                # Mostrar detalles del test
                st.info(f"**Pregunta:** {selected_test['prompt']}")

                # Botón para ejecutar
                if st.button("🚀 Ejecutar Test en los 5 Modelos", type="primary", use_container_width=True):
                    with st.spinner("Ejecutando test en todos los modelos..."):
                        arena_results = run_arena_test(selected_test, effective_openrouter_key)
                        st.session_state.arena_results = arena_results
                    st.success("✅ Test completado!")
                    st.rerun()

        with col2:
            st.subheader("📊 Estadísticas de Tests")
            st.metric("Total de Tests", TEST_STATS['total_tests'])
            st.metric("Nivel 1 (Fácil)", TEST_STATS['level_1'])
            st.metric("Nivel 2 (Medio)", TEST_STATS['level_2'])
            st.metric("Nivel 3 (Difícil)", TEST_STATS['level_3'])

        # Mostrar resultados si existen
        if st.session_state.arena_results:
            st.markdown("---")
            st.subheader("📊 Resultados de la Competencia")

            results = st.session_state.arena_results

            # Crear tabla comparativa
            comparison_data = []
            for r in results:
                comparison_data.append({
                    "Modelo": r['model_display'],
                    "Categoría": r['model_category'],
                    "✅ Éxito": "✅" if r['success'] else "❌",
                    "⚡ Tiempo (s)": f"{r['execution_time']:.3f}",
                    "🕐 TTFT (s)": f"{r['ttft']:.3f}",
                    "💰 Costo ($)": f"${r['cost']:.6f}",
                    "🚀 Eficiencia (tok/s)": f"{r['efficiency']:.0f}",
                    "📊 Tokens": r['tokens_total'],
                    "📝 Filas": r['result_rows']
                })

            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)

            # Métricas agregadas
            st.markdown("### 🎯 Money Shot - Métricas Clave")

            col1, col2, col3, col4 = st.columns(4)

            success_rate = sum(1 for r in results if r['success']) / len(results) * 100
            total_cost = sum(r['cost'] for r in results)
            avg_latency = sum(r['latency_api'] for r in results) / len(results)
            avg_efficiency = sum(r['efficiency'] for r in results) / len(results)

            col1.metric("Tasa de Éxito", f"{success_rate:.0f}%")
            col2.metric("Costo Total", f"${total_cost:.6f}")
            col3.metric("Latencia Promedio", f"{avg_latency:.3f}s")
            col4.metric("Eficiencia Promedio", f"{avg_efficiency:.0f} tok/s")

            # Gráficos comparativos
            st.markdown("### 📈 Visualizaciones Comparativas")

            col1, col2 = st.columns(2)

            with col1:
                # Gráfico de éxito por modelo
                success_by_model = comparison_df.groupby('Modelo')['✅ Éxito'].apply(lambda x: (x == '✅').sum()).reset_index()
                success_by_model.columns = ['Modelo', 'Éxito']
                fig_success = px.bar(success_by_model, x='Modelo', y='Éxito', title='Tasa de Éxito por Modelo',
                                    color='Modelo', color_discrete_sequence=px.colors.qualitative.Set2)
                st.plotly_chart(fig_success, use_container_width=True)

            with col2:
                # Gráfico de costo vs tiempo
                cost_time_df = pd.DataFrame([{
                    'Modelo': r['model_display'],
                    'Costo': r['cost'] * 1000000,  # Convertir a costo por millón
                    'Tiempo': r['execution_time']
                } for r in results])
                fig_cost_time = px.scatter(cost_time_df, x='Tiempo', y='Costo',
                                          text='Modelo', title='Costo vs Tiempo de Ejecución',
                                          labels={'Costo': 'Costo ($M tokens)', 'Tiempo': 'Tiempo (segundos)'})
                fig_cost_time.update_traces(textposition='top center')
                st.plotly_chart(fig_cost_time, use_container_width=True)

            # Mostrar SQL generado por cada modelo
            st.markdown("### 🔍 SQL Generado por Modelo")

            for r in results:
                with st.expander(f"{r['model_display']} - {'✅ Éxito' if r['success'] else '❌ Error'}"):
                    st.code(r['sql_generated'], language='sql')
                    if r['error']:
                        st.error(f"Error: {r['error']}")
                    if r['validation']:
                        st.json(r['validation'])

            # Botón para limpiar resultados
            if st.button("🗑️ Limpiar Resultados"):
                st.session_state.arena_results = []
                st.rerun()

# --- Pestaña 4: Resultados del Arena ---
with tab4:
    st.header("📊 Resultados del LLM Arena")

    # Intentar cargar resultados del arena
    arena_file = ARENA_RESULTS_PATH

    if arena_file.exists():
        try:
            with open(arena_file, 'r', encoding='utf-8') as f:
                arena_data = json.load(f)

            # Metadata del arena
            metadata = arena_data.get("metadata", {})
            st.subheader("📋 Información General")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Tests Ejecutados", metadata.get("total_tests", 0))
            col2.metric("Modelos Comparados", metadata.get("total_models", 0))
            col3.metric("Total Ejecuciones", metadata.get("total_executions", 0))
            col4.metric("Fecha", metadata.get("timestamp", "N/A").split("T")[0] if "timestamp" in metadata else "N/A")

            st.markdown("---")

            # Resumen por modelo
            st.subheader("🏆 Resumen por Modelo")

            # Calcular estadísticas por modelo
            results = arena_data.get("results", [])
            model_stats = {}

            for result in results:
                model_display = result.get("model_display", "Unknown")
                if model_display not in model_stats:
                    model_stats[model_display] = {
                        "category": result.get("model_category", ""),
                        "total_tests": 0,
                        "successful": 0,
                        "failed": 0,
                        "total_cost": 0,
                        "total_time": 0,
                        "total_tokens": 0,
                        "avg_efficiency": []
                    }

                model_stats[model_display]["total_tests"] += 1
                if result.get("success"):
                    model_stats[model_display]["successful"] += 1
                else:
                    model_stats[model_display]["failed"] += 1

                model_stats[model_display]["total_cost"] += result.get("cost", 0)
                model_stats[model_display]["total_time"] += result.get("execution_time", 0)
                model_stats[model_display]["total_tokens"] += result.get("tokens_total", 0)
                if result.get("efficiency"):
                    model_stats[model_display]["avg_efficiency"].append(result.get("efficiency", 0))

            # Crear tabla de resumen
            summary_data = []
            for model, stats in model_stats.items():
                success_rate = (stats["successful"] / stats["total_tests"] * 100) if stats["total_tests"] > 0 else 0
                avg_time = stats["total_time"] / stats["total_tests"] if stats["total_tests"] > 0 else 0
                avg_efficiency = sum(stats["avg_efficiency"]) / len(stats["avg_efficiency"]) if stats["avg_efficiency"] else 0

                summary_data.append({
                    "Modelo": model,
                    "Categoría": stats["category"],
                    "✅ Éxitos": stats["successful"],
                    "❌ Fallos": stats["failed"],
                    "📊 Tasa Éxito": f"{success_rate:.1f}%",
                    "💰 Costo Total": f"${stats['total_cost']:.6f}",
                    "⏱️ Tiempo Prom": f"{avg_time:.2f}s",
                    "🚀 Eficiencia": f"{avg_efficiency:.0f} tok/s"
                })

            summary_df = pd.DataFrame(summary_data)
            summary_df = summary_df.sort_values(by="✅ Éxitos", ascending=False)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            st.markdown("---")

            # Gráficos de resumen
            st.subheader("📈 Análisis Comparativo")

            col1, col2 = st.columns(2)

            with col1:
                # Gráfico de éxito por modelo
                fig_success = px.bar(
                    summary_df,
                    x="Modelo",
                    y="✅ Éxitos",
                    title="Número de Tests Exitosos por Modelo",
                    color="Modelo",
                    text="✅ Éxitos"
                )
                fig_success.update_traces(textposition='outside')
                st.plotly_chart(fig_success, use_container_width=True)

            with col2:
                # Gráfico de costo vs tasa de éxito
                cost_success_data = []
                for model, stats in model_stats.items():
                    success_rate = (stats["successful"] / stats["total_tests"] * 100) if stats["total_tests"] > 0 else 0
                    cost_success_data.append({
                        "Modelo": model,
                        "Tasa de Éxito (%)": success_rate,
                        "Costo Total ($)": stats["total_cost"]
                    })

                fig_cost_success = px.scatter(
                    cost_success_data,
                    x="Costo Total ($)",
                    y="Tasa de Éxito (%)",
                    text="Modelo",
                    title="Precio vs Calidad: Costo vs Tasa de Éxito",
                    size=[10]*len(cost_success_data)
                )
                fig_cost_success.update_traces(textposition='top center')
                fig_cost_success.update_layout(showlegend=False)
                st.plotly_chart(fig_cost_success, use_container_width=True)

            st.markdown("---")

            # Resultados por test
            st.subheader("🔍 Resultados Detallados por Test")

            # Agrupar resultados por test
            tests_dict = {}
            for result in results:
                test_id = result.get("test_id", "Unknown")
                if test_id not in tests_dict:
                    tests_dict[test_id] = {
                        "name": result.get("test_name", "Unknown"),
                        "level": result.get("test_level", 0),
                        "results": []
                    }
                tests_dict[test_id]["results"].append(result)

            # Filtro por nivel
            level_filter = st.selectbox(
                "Filtrar por Nivel",
                ["Todos", "Nivel 1 - Fácil", "Nivel 2 - Medio", "Nivel 3 - Difícil"],
                key="results_level_filter"
            )

            # Mostrar cada test
            for test_id, test_data in sorted(tests_dict.items()):
                test_level = test_data["level"]

                # Aplicar filtro
                if level_filter != "Todos":
                    filter_level = int(level_filter.split()[1])
                    if test_level != filter_level:
                        continue

                with st.expander(f"**{test_id}** - {test_data['name']} (Nivel {test_level})", expanded=False):
                    # Crear tabla comparativa para este test
                    test_results = []
                    for r in test_data["results"]:
                        test_results.append({
                            "Modelo": r.get("model_display", "Unknown"),
                            "Estado": "✅ Éxito" if r.get("success") else "❌ Fallo",
                            "Tiempo (s)": f"{r.get('execution_time', 0):.3f}",
                            "TTFT (s)": f"{r.get('ttft', 0):.3f}",
                            "Costo ($)": f"{r.get('cost', 0):.6f}",
                            "Tokens": r.get("tokens_total", 0),
                            "Eficiencia": f"{r.get('efficiency', 0):.0f} tok/s"
                        })

                    test_df = pd.DataFrame(test_results)
                    st.dataframe(test_df, use_container_width=True, hide_index=True)

                    # Mostrar SQL generado por cada modelo
                    st.markdown("**💻 SQL Generado:**")

                    for r in test_data["results"]:
                        model_name_display = r.get("model_display", "Unknown")
                        success = r.get("success", False)
                        sql = r.get("sql_generated", "No SQL generado")
                        error = r.get("error", None)

                        status_emoji = "✅" if success else "❌"

                        with st.expander(f"{status_emoji} {model_name_display}", expanded=False):
                            if sql:
                                st.code(sql, language="sql")
                            else:
                                st.warning("No se generó SQL")

                            if error:
                                st.error(f"**Error:** {error}")

                            if r.get("validation"):
                                st.json(r["validation"])

                    st.markdown("---")

        except Exception as e:
            st.error(f"Error al cargar los resultados del arena: {e}")
            st.info("Por favor, ejecuta el arena primero usando la pestaña '🏟️ Arena LLM' o el script `benchmark/runner.py`")
    else:
        st.info(f"📁 No se encontró el archivo `{arena_file}`")
        st.markdown("""
        Para generar resultados del Arena, puedes:

        1. **Usar la pestaña '🏟️ Arena LLM'** en esta aplicación para ejecutar tests individuales
        2. **Ejecutar el script completo:**
           ```bash
           python benchmark/runner.py --api-key TU_API_KEY --level all
           ```

        Los resultados se guardarán automáticamente en `data/arena_results.json`
        """)

# --- Pestaña 5: Métricas de Uso ---
with tab5:
    st.header("📈 Métricas de Uso de la Aplicación")

    # PIN Protection
    pin = st.text_input("Introduce el PIN para ver las métricas", type="password", key="pin_input")

    if pin == "2406":
        st.success("PIN correcto. Mostrando métricas.")

        # Cargar datos de métricas
        try:
            metrics_df = pd.read_csv(METRICS_CSV_PATH)
            metrics_df['date'] = pd.to_datetime(metrics_df['date'])

            st.markdown("---")
            st.subheader("KPIs Principales")

            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            total_tokens = metrics_df['tokens_processed'].sum()
            total_sessions = metrics_df['session_id'].nunique()
            avg_latency = metrics_df['latency_api'].mean()
            avg_execution = metrics_df['execution_time'].mean()

            col1.metric("Total de Tokens Procesados", f"{total_tokens:,.0f}")
            col2.metric("Total de Sesiones Únicas", f"{total_sessions}")
            col3.metric("Latencia API Promedio", f"{avg_latency:.2f}s")
            col4.metric("Tiempo Ejecución Promedio", f"{avg_execution:.2f}s")

            st.markdown("---")
            st.subheader("Análisis Visual")

            # Gráficos fila 1
            col1, col2 = st.columns(2)

            with col1:
                # Gráfico de Pie: Fuente de API
                api_source_counts = metrics_df['api_key_source'].value_counts().reset_index()
                api_source_counts.columns = ['source', 'count']
                fig_pie = px.pie(api_source_counts, names='source', values='count', title='Distribución de Fuente de API')
                st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                # Gráfico de Pie: Modelos LLM utilizados
                if 'llm_model' in metrics_df.columns:
                    llm_counts = metrics_df['llm_model'].value_counts().reset_index()
                    llm_counts.columns = ['modelo', 'count']
                    fig_llm = px.pie(llm_counts, names='modelo', values='count', title='Distribución de Modelos LLM')
                    st.plotly_chart(fig_llm, use_container_width=True)

            # Gráficos fila 2
            col1, col2 = st.columns(2)

            with col1:
                # Gráfico de Líneas: Tokens a lo largo del tiempo
                tokens_over_time = metrics_df.groupby(metrics_df['date'].dt.date)['tokens_processed'].sum().reset_index()
                tokens_over_time.columns = ['Fecha', 'Tokens']
                fig_line = px.line(tokens_over_time, x='Fecha', y='Tokens', title='Tokens Usados a lo Largo del Tiempo')
                st.plotly_chart(fig_line, use_container_width=True)

            with col2:
                # Gráfico de barras: Tokens de entrada vs salida
                if 'tokens_input' in metrics_df.columns and 'tokens_output' in metrics_df.columns:
                    tokens_comparison = pd.DataFrame({
                        'Tipo': ['Input', 'Output'],
                        'Tokens': [metrics_df['tokens_input'].sum(), metrics_df['tokens_output'].sum()]
                    })
                    fig_tokens = px.bar(tokens_comparison, x='Tipo', y='Tokens', title='Tokens de Entrada vs Salida')
                    st.plotly_chart(fig_tokens, use_container_width=True)

            # Gráficos fila 3
            col1, col2 = st.columns(2)

            with col1:
                # Histograma: Distribución de latencia
                if 'latency_api' in metrics_df.columns:
                    fig_latency = px.histogram(metrics_df, x='latency_api', nbins=20, title='Distribución de Latencia API (segundos)')
                    st.plotly_chart(fig_latency, use_container_width=True)

            with col2:
                # Histograma: Distribución de tiempo de ejecución
                if 'execution_time' in metrics_df.columns:
                    fig_exec = px.histogram(metrics_df, x='execution_time', nbins=20, title='Distribución de Tiempo de Ejecución (segundos)')
                    st.plotly_chart(fig_exec, use_container_width=True)

            # Sección especial para Arena
            if 'test_id' in metrics_df.columns and not metrics_df['test_id'].isna().all():
                st.markdown("---")
                st.subheader("🏟️ Métricas del Arena")

                arena_df = metrics_df[metrics_df['test_id'].notna()].copy()

                if not arena_df.empty:
                    col1, col2, col3, col4 = st.columns(4)

                    arena_tests_count = arena_df['test_id'].nunique()
                    arena_success_rate = arena_df['success'].mean() * 100 if 'success' in arena_df.columns else 0
                    arena_total_cost = arena_df['real_cost'].sum() if 'real_cost' in arena_df.columns else 0
                    arena_avg_efficiency = arena_df['efficiency'].mean() if 'efficiency' in arena_df.columns else 0

                    col1.metric("Tests Ejecutados", arena_tests_count)
                    col2.metric("Tasa de Éxito", f"{arena_success_rate:.1f}%")
                    col3.metric("Costo Total", f"${arena_total_cost:.6f}")
                    col4.metric("Eficiencia Promedio", f"{arena_avg_efficiency:.0f} tok/s")

                    # Gráficos del Arena
                    col1, col2 = st.columns(2)

                    with col1:
                        # Éxito por nivel de test
                        if 'test_level' in arena_df.columns and 'success' in arena_df.columns:
                            success_by_level = arena_df.groupby('test_level')['success'].apply(lambda x: x.sum() / len(x) * 100).reset_index()
                            success_by_level.columns = ['Nivel', 'Tasa de Éxito (%)']
                            fig_level = px.bar(success_by_level, x='Nivel', y='Tasa de Éxito (%)',
                                             title='Tasa de Éxito por Nivel de Dificultad')
                            st.plotly_chart(fig_level, use_container_width=True)

                    with col2:
                        # Costo por modelo
                        if 'llm_model' in arena_df.columns and 'real_cost' in arena_df.columns:
                            cost_by_model = arena_df.groupby('llm_model')['real_cost'].sum().reset_index()
                            cost_by_model.columns = ['Modelo', 'Costo Total ($)']
                            # Extraer nombre corto del modelo
                            cost_by_model['Modelo'] = cost_by_model['Modelo'].apply(lambda x: x.split('/')[-1][:15])
                            fig_cost_model = px.bar(cost_by_model, x='Modelo', y='Costo Total ($)',
                                                   title='Costo Total por Modelo')
                            st.plotly_chart(fig_cost_model, use_container_width=True)

                    # Gráfico de TTFT vs Latencia Total
                    if 'ttft' in arena_df.columns and 'latency_api' in arena_df.columns:
                        st.markdown("#### ⚡ Time to First Token (TTFT) vs Latencia Total")
                        fig_ttft = px.scatter(arena_df, x='ttft', y='latency_api', color='llm_model',
                                            title='TTFT vs Latencia Total por Modelo',
                                            labels={'ttft': 'TTFT (s)', 'latency_api': 'Latencia Total (s)'})
                        st.plotly_chart(fig_ttft, use_container_width=True)

            # Mostrar datos crudos
            if st.checkbox("Mostrar datos crudos de métricas"):
                st.dataframe(metrics_df)

        except FileNotFoundError:
            st.warning("El archivo `metrics.csv` no se ha encontrado. Aún no se han registrado métricas.")
        except Exception as e:
            st.error(f"Ocurrió un error al cargar o procesar las métricas: {e}")

    elif pin:
        st.error("PIN incorrecto. Por favor, inténtalo de nuevo.")
