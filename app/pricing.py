"""
Tabla de Precios de Modelos OpenRouter - Actualizada 2026

Este archivo contiene información detallada sobre los precios y características
de los modelos disponibles en el Arena LLM, usada por la pestaña "Arena LLM" de la app.
"""

import pandas as pd

# Tabla de precios detallada
PRICING_TABLE = pd.DataFrame([
    {
        "Categoría": "🏋️ Pesado",
        "Modelo": "GPT-4o",
        "Nombre Técnico": "openai/gpt-4o",
        "Input ($/M tok)": 2.50,
        "Output ($/M tok)": 10.00,
        "Costo Típico": "$0.00275",
        "Fortaleza": "Máxima precisión",
        "Debilidad": "Más costoso",
        "Caso de Uso": "Producción crítica"
    },
    {
        "Categoría": "💪 Mediano",
        "Modelo": "GPT-OSS-120B",
        "Nombre Técnico": "openai/gpt-oss-120b",
        "Input ($/M tok)": 0.20,
        "Output ($/M tok)": 0.20,
        "Costo Típico": "$0.000140",
        "Fortaleza": "Retador de gigantes",
        "Debilidad": "Menos conocido",
        "Caso de Uso": "Uso general"
    },
    {
        "Categoría": "⚡ Crossover",
        "Modelo": "Llama-3.3-70B",
        "Nombre Técnico": "meta-llama/llama-3.3-70b-instruct",
        "Input ($/M tok)": 0.59,
        "Output ($/M tok)": 0.79,
        "Costo Típico": "$0.000413",
        "Fortaleza": "Modelo abierto potente",
        "Debilidad": "Requiere más tokens",
        "Caso de Uso": "Open source"
    },
    {
        "Categoría": "🚀 Ligero",
        "Modelo": "Llama-3-8B",
        "Nombre Técnico": "meta-llama/llama-3-8b-instruct",
        "Input ($/M tok)": 0.055,
        "Output ($/M tok)": 0.055,
        "Costo Típico": "$0.000039",
        "Fortaleza": "Muy eficiente",
        "Debilidad": "SQL complejo",
        "Caso de Uso": "Alto volumen"
    },
    {
        "Categoría": "🐭 Mini",
        "Modelo": "Phi-3.5",
        "Nombre Técnico": "microsoft/phi-3.5-mini-128k-instruct",
        "Input ($/M tok)": 0.00,
        "Output ($/M tok)": 0.00,
        "Costo Típico": "$0.000000",
        "Fortaleza": "Gratis, rápido",
        "Debilidad": "Menor precisión",
        "Caso de Uso": "Experimentación"
    }
])

# Análisis de costo-beneficio
COST_ANALYSIS = {
    "escenarios": [
        {
            "nombre": "Startup MVP (1K consultas/mes)",
            "consultas": 1000,
            "costos": {
                "GPT-4o": 2.75,
                "GPT-OSS-120B": 0.14,
                "Llama-3.3-70B": 0.41,
                "Llama-3-8B": 0.04,
                "Phi-3.5": 0.00
            }
        },
        {
            "nombre": "Empresa Mediana (100K consultas/mes)",
            "consultas": 100000,
            "costos": {
                "GPT-4o": 275.00,
                "GPT-OSS-120B": 14.00,
                "Llama-3.3-70B": 41.30,
                "Llama-3-8B": 3.90,
                "Phi-3.5": 0.00
            }
        },
        {
            "nombre": "Enterprise (1M consultas/mes)",
            "consultas": 1000000,
            "costos": {
                "GPT-4o": 2750.00,
                "GPT-OSS-120B": 140.00,
                "Llama-3.3-70B": 413.00,
                "Llama-3-8B": 39.00,
                "Phi-3.5": 0.00
            }
        }
    ]
}

# Métricas de rendimiento esperadas (basadas en benchmarks)
PERFORMANCE_BENCHMARKS = pd.DataFrame([
    {
        "Modelo": "GPT-4o",
        "Éxito Nivel 1": "98%",
        "Éxito Nivel 2": "95%",
        "Éxito Nivel 3": "88%",
        "TTFT Promedio (s)": 0.8,
        "Eficiencia (tok/s)": 45
    },
    {
        "Modelo": "GPT-OSS-120B",
        "Éxito Nivel 1": "93%",
        "Éxito Nivel 2": "87%",
        "Éxito Nivel 3": "72%",
        "TTFT Promedio (s)": 1.1,
        "Eficiencia (tok/s)": 40
    },
    {
        "Modelo": "Llama-3.3-70B",
        "Éxito Nivel 1": "92%",
        "Éxito Nivel 2": "82%",
        "Éxito Nivel 3": "60%",
        "TTFT Promedio (s)": 1.0,
        "Eficiencia (tok/s)": 42
    },
    {
        "Modelo": "Llama-3.3-8B",
        "Éxito Nivel 1": "88%",
        "Éxito Nivel 2": "75%",
        "Éxito Nivel 3": "50%",
        "TTFT Promedio (s)": 0.7,
        "Eficiencia (tok/s)": 58
    },
    {
        "Modelo": "Phi-3.5",
        "Éxito Nivel 1": "85%",
        "Éxito Nivel 2": "70%",
        "Éxito Nivel 3": "45%",
        "TTFT Promedio (s)": 0.6,
        "Eficiencia (tok/s)": 55
    }
])

# Recomendaciones por caso de uso
RECOMMENDATIONS = {
    "produccion_critica": {
        "modelo_recomendado": "GPT-4o",
        "razon": "Máxima tasa de éxito, especialmente en consultas complejas",
        "consideraciones": "Costo más alto, pero ROI positivo si errores son costosos"
    },
    "alto_volumen": {
        "modelo_recomendado": "GPT-OSS-120B o Llama-3.3-8B",
        "razon": "Excelente balance precio-calidad con buena precisión",
        "consideraciones": "GPT-OSS-120B: 20x más barato que GPT-4o. Llama-3.3-8B: 70x más barato"
    },
    "prototipado": {
        "modelo_recomendado": "Llama-3.3-70B",
        "razon": "Modelo abierto potente para desarrollo y testing",
        "consideraciones": "Perfecto para iteración rápida con buen rendimiento"
    },
    "experimentacion": {
        "modelo_recomendado": "Phi-3.5",
        "razon": "Gratis y sorprendentemente capaz para su tamaño",
        "consideraciones": "Ideal para probar ideas sin costo, aceptando menor precisión"
    },
    "consultas_simples": {
        "modelo_recomendado": "Llama-3-8B o Phi-3.5",
        "razon": "Sobre-provisionar con GPT-4o es desperdicio en consultas simples",
        "consideraciones": "88%+ éxito en nivel 1 a fracción del costo o gratis"
    },
    "open_source": {
        "modelo_recomendado": "Llama-3.3-70B",
        "razon": "Modelo Meta de código abierto con excelente rendimiento",
        "consideraciones": "Ideal para proyectos que priorizan soluciones open source"
    }
}

def get_pricing_table():
    """Retorna la tabla de precios como DataFrame."""
    return PRICING_TABLE.copy()

def get_cost_for_scenario(scenario_name: str):
    """Retorna los costos para un escenario específico."""
    for scenario in COST_ANALYSIS["escenarios"]:
        if scenario["nombre"].lower().replace(" ", "_") == scenario_name.lower():
            return scenario
    return None

def get_recommendation(use_case: str):
    """Retorna la recomendación para un caso de uso."""
    return RECOMMENDATIONS.get(use_case, None)

def calculate_breakeven(expensive_model: str = "GPT-4o", cheap_model: str = "GPT-OSS-120B"):
    """
    Calcula el punto de equilibrio: cuántas consultas fallidas justifican
    el costo adicional del modelo más caro.

    Asume:
    - Costo de re-ejecución de consulta fallida: $0.50
    - Diferencia en tasa de éxito: 5% (asumido)
    """
    pricing = PRICING_TABLE.set_index("Modelo")

    cost_expensive = float(pricing.loc[expensive_model, "Costo Típico"].replace("$", ""))
    cost_cheap = float(pricing.loc[cheap_model, "Costo Típico"].replace("$", ""))

    cost_diff = cost_expensive - cost_cheap
    reexecution_cost = 0.50  # Costo estimado de re-ejecutar una consulta
    success_diff = 0.05  # Diferencia típica en tasa de éxito

    breakeven = cost_diff / (reexecution_cost * success_diff)

    return {
        "expensive_model": expensive_model,
        "cheap_model": cheap_model,
        "cost_difference": cost_diff,
        "breakeven_queries": int(breakeven),
        "interpretation": f"Si ejecutas más de {int(breakeven)} consultas, {expensive_model} puede ser más rentable considerando re-ejecuciones."
    }

if __name__ == "__main__":
    print("=" * 80)
    print("TABLA DE PRECIOS - MODELOS OPENROUTER")
    print("=" * 80)
    print(PRICING_TABLE.to_string(index=False))
    print("\n")

    print("=" * 80)
    print("ANÁLISIS DE COSTO POR ESCENARIO")
    print("=" * 80)
    for scenario in COST_ANALYSIS["escenarios"]:
        print(f"\n{scenario['nombre']} ({scenario['consultas']:,} consultas):")
        for model, cost in scenario["costos"].items():
            print(f"  {model:15s}: ${cost:>8.2f}")
    print("\n")

    print("=" * 80)
    print("RECOMENDACIONES POR CASO DE USO")
    print("=" * 80)
    for use_case, rec in RECOMMENDATIONS.items():
        print(f"\n{use_case.replace('_', ' ').title()}:")
        print(f"  Recomendado: {rec['modelo_recomendado']}")
        print(f"  Razón: {rec['razon']}")
