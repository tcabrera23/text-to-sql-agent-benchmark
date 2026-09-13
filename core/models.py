"""Registro de los 5 modelos del Arena LLM: fuente única (antes duplicada en
main.py, arena_runner.py y llm_arena.py)."""

ARENA_MODELS = {
    "heavyweight": {
        "name": "openai/gpt-4o",
        "display_name": "GPT-4o (Pesado)",
        "category": "Pesado",
        "color": "#10a37f",
        "description": "El estándar de oro. 'El que no debería fallar'."
    },
    "medium": {
        "name": "openai/gpt-oss-120b",
        "display_name": "GPT-OSS-120B (Mediano)",
        "category": "Mediano",
        "color": "#2563eb",
        "description": "El retador de los gigantes de la IA."
    },
    "crossover": {
        "name": "meta-llama/llama-3.3-70b-instruct",
        "display_name": "Llama-3.3-70B (Crossover)",
        "category": "Crossover",
        "color": "#f59e0b",
        "description": "El modelo 'abierto' de Meta (estilo OT-preview)."
    },
    "lightweight": {
        "name": "meta-llama/llama-3-8b-instruct",
        "display_name": "Llama-3-8B (Ligero)",
        "category": "Ligero",
        "color": "#8b5cf6",
        "description": "El rey de la eficiencia."
    },
    "mini": {
        "name": "microsoft/phi-3.5-mini-128k-instruct",
        "display_name": "Phi-3.5 (Mini)",
        "category": "Mini",
        "color": "#ec4899",
        "description": "El 'underdog' que sorprende por su tamaño."
    }
}
