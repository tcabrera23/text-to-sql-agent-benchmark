"""Prompts, herramientas (tool calling) y lógica de los agentes LLM.

Separado de main.py (que solo hace configuración/sidebar) y de tabs.py
(que solo renderiza la UI) para que cada archivo se pueda leer de punta
a punta sin desplazarse por cientos de líneas ajenas a su propósito.
"""

import json
import time

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import streamlit as st
from openai import OpenAI

from core.database import execute_sql
from core.metrics import log_metrics, calculate_cost, calculate_efficiency
from core.models import ARENA_MODELS
from core.schema import CHINOOK_SCHEMA_DDL
from benchmark.catalog import validate_result

# --- PROMPTS DEL SISTEMA ---

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

# --- HERRAMIENTAS (TOOLS) ---

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

# --- LÓGICA DE LOS AGENTES ---

def run_chat_agent(prompt: str, llm_client, model_name: str, session_id: str):
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


def run_dashboard_agent(user_prompt: str, llm_client, model_name: str, session_id: str):
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

def run_arena_test(test: dict, openrouter_api_key: str, session_id: str):
    """
    Ejecuta un test del arena contra los 5 modelos y recopila métricas.

    Args:
        test: Diccionario con la información del test
        openrouter_api_key: API key de OpenRouter
        session_id: ID de la sesión actual, para el registro de métricas

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
