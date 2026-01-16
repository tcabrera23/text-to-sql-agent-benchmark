import os
import csv
from datetime import datetime

# Precios por millón de tokens para OpenRouter (USD) - Actualizado 2026
MODEL_PRICING = {
    # Modelos Arena - Configuración actual
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},  # Pesado - El estándar de oro
    "openai/gpt-oss-120b": {"input": 0.20, "output": 0.20},  # Mediano - El retador de los gigantes de la IA
    "meta-llama/llama-3.3-70b-instruct": {"input": 0.59, "output": 0.79},  # Crossover - Modelo abierto de Meta
    "meta-llama/llama-3-8b-instruct": {"input": 0.055, "output": 0.055},  # Ligero - Rey de la eficiencia
    "microsoft/phi-3.5-mini-128k-instruct": {"input": 0.00, "output": 0.00},  # Mini - El "underdog" que sorprende (GRATIS)
    "microsoft/phi-4": {"input": 0.00, "output": 0.00},  # Alternativa (si se usa)
    
    # Modelos adicionales compatibles
    "deepseek/deepseek-v3": {"input": 0.27, "output": 1.10},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "meta-llama/llama-3.2-11b-vision-instruct": {"input": 0.055, "output": 0.055},
    "deepseek/deepseek-chat": {"input": 0.27, "output": 1.10},
    "anthropic/claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    "google/gemini-2.0-flash-exp:free": {"input": 0.00, "output": 0.00},
    "mistralai/mistral-large": {"input": 2.00, "output": 6.00},
}

def calculate_cost(model_name: str, tokens_input: int, tokens_output: int) -> float:
    """
    Calcula el costo real basado en tokens de entrada y salida.
    
    Args:
        model_name: Nombre del modelo
        tokens_input: Tokens de entrada
        tokens_output: Tokens de salida
        
    Returns:
        Costo en USD
    """
    pricing = MODEL_PRICING.get(model_name, {"input": 0.0, "output": 0.0})
    cost_input = (tokens_input / 1_000_000) * pricing["input"]
    cost_output = (tokens_output / 1_000_000) * pricing["output"]
    return cost_input + cost_output

def calculate_efficiency(tokens_processed: int, execution_time: float) -> float:
    """
    Calcula la eficiencia en tokens por segundo.
    
    Args:
        tokens_processed: Total de tokens procesados
        execution_time: Tiempo de ejecución en segundos
        
    Returns:
        Tokens por segundo
    """
    if execution_time <= 0:
        return 0.0
    return tokens_processed / execution_time

def log_metrics(session_id, tokens_input, tokens_output, tokens_processed, message_count, 
                api_key_source, llm_model, latency_api, execution_time, 
                success=None, ttft=None, test_id=None, test_level=None):
    """
    Registra las métricas de uso en un archivo CSV.

    Args:
        session_id (str): El ID de la sesión del usuario.
        tokens_input (int): El número de tokens de entrada.
        tokens_output (int): El número de tokens de salida.
        tokens_processed (int): El número total de tokens procesados.
        message_count (int): El número total de mensajes en la conversación.
        api_key_source (str): La fuente de la API key ('user' o 'default').
        llm_model (str): El modelo LLM utilizado.
        latency_api (float): Latencia de la API en segundos.
        execution_time (float): Tiempo total de ejecución en segundos.
        success (bool, optional): Si la ejecución fue exitosa (para arena).
        ttft (float, optional): Time to first token en segundos.
        test_id (str, optional): ID del test ejecutado (para arena).
        test_level (str, optional): Nivel de dificultad del test (para arena).
    """
    file_path = "metrics.csv"
    file_exists = os.path.exists(file_path)
    
    # Calcular métricas derivadas
    real_cost = calculate_cost(llm_model, tokens_input, tokens_output)
    efficiency = calculate_efficiency(tokens_processed, execution_time)

    try:
        with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['date', 'session_id', 'tokens_input', 'tokens_output', 'tokens_processed', 
                         'message_count', 'api_key_source', 'llm_model', 'latency_api', 'execution_time',
                         'success', 'ttft', 'real_cost', 'efficiency', 'test_id', 'test_level']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'date': datetime.now().isoformat(),
                'session_id': session_id,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'tokens_processed': tokens_processed,
                'message_count': message_count,
                'api_key_source': api_key_source,
                'llm_model': llm_model,
                'latency_api': round(latency_api, 3) if latency_api else None,
                'execution_time': round(execution_time, 3) if execution_time else None,
                'success': success,
                'ttft': round(ttft, 3) if ttft else None,
                'real_cost': round(real_cost, 6) if real_cost else None,
                'efficiency': round(efficiency, 2) if efficiency else None,
                'test_id': test_id,
                'test_level': test_level
            })
    except IOError as e:
        print(f"Error al escribir en el archivo de métricas: {e}")
