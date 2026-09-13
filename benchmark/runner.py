"""
Arena Runner - Sistema de Ejecución Automatizada de Tests para LLM Arena

Este script permite ejecutar tests automáticamente contra múltiples modelos de OpenRouter
para comparar su desempeño en tareas de generación de SQL.

Uso:
    python benchmark/runner.py --api-key TU_API_KEY [opciones]

Opciones:
    --api-key: API key de OpenRouter (requerido)
    --tests: IDs de tests a ejecutar (default: todos)
    --models: Modelos a comparar (default: todos los 5)
    --output: Archivo de salida para resultados (default: data/arena_results.json)
    --level: Nivel de dificultad (1, 2, 3 o 'all')
"""

import sys
from pathlib import Path

# Permite importar core/ y benchmark/ como paquetes de nivel de repo cuando este
# archivo se ejecuta directamente (python benchmark/runner.py), ya que Python solo
# agrega al sys.path la carpeta del propio script, no la raíz del proyecto.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import json
import time
from datetime import datetime

from openai import OpenAI

from benchmark.catalog import ARENA_TESTS, validate_result, get_tests_by_level
from core.database import execute_sql
from core.metrics import log_metrics, calculate_cost, calculate_efficiency
from core.models import ARENA_MODELS
from core.paths import ARENA_RESULTS_PATH
from core.schema import CHINOOK_SCHEMA_DDL

# Prompt del sistema para generación de SQL
SYSTEM_PROMPT = f"""
Eres un analista de datos experto en SQL. Tu objetivo es convertir preguntas en lenguaje natural en consultas SQL válidas para SQLite.

Reglas importantes:
1. Genera ÚNICAMENTE la consulta SQL, sin explicaciones ni texto adicional.
2. La consulta debe ser un SELECT válido para SQLite.
3. Los nombres de tablas y columnas usan PascalCase (ej: "ArtistId", "artists").
4. Usa JOINs apropiados cuando necesites datos de múltiples tablas.
5. Incluye ORDER BY y LIMIT cuando sea relevante.
6. NO uses punto y coma al final.

Esquema de la base de datos Chinook:
{CHINOOK_SCHEMA_DDL}

Responde SOLO con la consulta SQL.
"""

def run_test_on_model(test: dict, model_config: dict, client: OpenAI) -> dict:
    """
    Ejecuta un test específico en un modelo específico.

    Returns:
        dict con las métricas y resultados
    """
    start_time = time.time()
    result = {
        "test_id": test["id"],
        "test_name": test["name"],
        "test_level": test["level"],
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
        "validation": {}
    }

    try:
        # Preparar mensajes
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": test["prompt"]}
        ]

        # Llamada a la API con medición de TTFT
        api_start = time.time()
        ttft_start = time.time()

        response = client.chat.completions.create(
            model=model_config["name"],
            messages=messages,
            temperature=0,  # Determinístico para tests
            max_tokens=500,
            stream=False
        )

        ttft = time.time() - ttft_start  # En este caso, TTFT = latencia total (no streaming)
        latency_api = time.time() - api_start

        # Extraer SQL generado
        sql_generated = response.choices[0].message.content.strip()

        # Limpiar el SQL (a veces los modelos agregan markdown)
        if "```sql" in sql_generated:
            sql_generated = sql_generated.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql_generated:
            sql_generated = sql_generated.split("```")[1].split("```")[0].strip()

        result["sql_generated"] = sql_generated

        # Métricas de tokens
        if response.usage:
            result["tokens_input"] = response.usage.prompt_tokens
            result["tokens_output"] = response.usage.completion_tokens
            result["tokens_total"] = response.usage.total_tokens

        # Ejecutar la consulta SQL
        df, error = execute_sql(sql_generated)

        if error:
            result["error"] = error
            result["success"] = False
        else:
            # Validar resultado
            validation = validate_result(test["id"], df)
            result["validation"] = validation
            result["success"] = validation["success"]

        # Calcular tiempo total
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

    except Exception as e:
        result["error"] = str(e)
        result["success"] = False
        result["execution_time"] = time.time() - start_time

    return result

def run_arena(api_key: str, test_ids: list = None, model_keys: list = None, level: str = "all"):
    """
    Ejecuta el arena completo.

    Args:
        api_key: API key de OpenRouter
        test_ids: Lista de IDs de tests a ejecutar (None = todos)
        model_keys: Lista de claves de modelos a usar (None = todos)
        level: Nivel de dificultad ('all', '1', '2', '3')

    Returns:
        dict con resultados completos
    """
    # Inicializar cliente
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

    # Determinar tests a ejecutar
    if test_ids:
        tests = [t for t in ARENA_TESTS if t["id"] in test_ids]
    elif level != "all":
        tests = get_tests_by_level(int(level))
    else:
        tests = ARENA_TESTS

    # Determinar modelos a usar
    if model_keys:
        models = {k: ARENA_MODELS[k] for k in model_keys if k in ARENA_MODELS}
    else:
        models = ARENA_MODELS

    # Ejecutar tests
    results = []
    total_tests = len(tests) * len(models)
    current = 0

    print(f"\n{'='*80}")
    print(f"🏟️  INICIANDO LLM ARENA - Comparación de Modelos SQL")
    print(f"{'='*80}")
    print(f"📊 Tests a ejecutar: {len(tests)}")
    print(f"🤖 Modelos a comparar: {len(models)}")
    print(f"🎯 Total de ejecuciones: {total_tests}")
    print(f"{'='*80}\n")

    for test in tests:
        print(f"\n📝 Test: {test['id']} - {test['name']} (Nivel {test['level']})")
        print(f"   Pregunta: {test['prompt'][:80]}...")

        for model_key, model_config in models.items():
            current += 1
            print(f"\n   [{current}/{total_tests}] 🤖 Ejecutando en {model_config['display_name']}...", end=" ")

            result = run_test_on_model(test, model_config, client)
            results.append(result)

            # Mostrar resultado
            status = "✅" if result["success"] else "❌"
            print(f"{status} ({result['execution_time']:.2f}s, ${result['cost']:.6f})")

            # Pequeña pausa para no saturar la API
            time.sleep(0.5)

    # Compilar resultados
    arena_results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(tests),
            "total_models": len(models),
            "total_executions": total_tests
        },
        "models": models,
        "tests": [{"id": t["id"], "name": t["name"], "level": t["level"], "prompt": t["prompt"]} for t in tests],
        "results": results
    }

    # Generar estadísticas
    print(f"\n{'='*80}")
    print("📈 RESUMEN DE RESULTADOS")
    print(f"{'='*80}\n")

    for model_key, model_config in models.items():
        model_results = [r for r in results if r["model_name"] == model_config["name"]]
        success_count = sum(1 for r in model_results if r["success"])
        total_cost = sum(r["cost"] for r in model_results)
        avg_time = sum(r["execution_time"] for r in model_results) / len(model_results)
        avg_efficiency = sum(r["efficiency"] for r in model_results) / len(model_results)

        print(f"🤖 {model_config['display_name']} ({model_config['category']})")
        print(f"   ✅ Éxito: {success_count}/{len(model_results)} ({success_count/len(model_results)*100:.1f}%)")
        print(f"   💰 Costo total: ${total_cost:.6f}")
        print(f"   ⚡ Tiempo promedio: {avg_time:.2f}s")
        print(f"   🚀 Eficiencia: {avg_efficiency:.0f} tokens/seg")
        print()

    return arena_results

def save_results(results: dict, output_file: str):
    """Guarda los resultados en un archivo JSON."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"💾 Resultados guardados en: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Arena Runner - Ejecutor de Tests para LLM Arena")
    parser.add_argument("--api-key", required=True, help="API key de OpenRouter")
    parser.add_argument("--tests", nargs="+", help="IDs de tests específicos a ejecutar")
    parser.add_argument("--models", nargs="+", choices=list(ARENA_MODELS.keys()), help="Modelos a comparar")
    parser.add_argument("--level", choices=["all", "1", "2", "3"], default="all", help="Nivel de dificultad")
    parser.add_argument("--output", default=str(ARENA_RESULTS_PATH), help="Archivo de salida")

    args = parser.parse_args()

    # Ejecutar arena
    results = run_arena(
        api_key=args.api_key,
        test_ids=args.tests,
        model_keys=args.models,
        level=args.level
    )

    # Guardar resultados
    save_results(results, args.output)

    print(f"\n{'='*80}")
    print("✨ Arena completado exitosamente!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
