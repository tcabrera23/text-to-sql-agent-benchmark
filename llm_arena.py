"""
LLM Arena - Sistema de comparación de modelos para consultas SQL
Compara 5 modelos diferentes de OpenRouter ejecutando las mismas consultas
"""

import asyncio
import time
import json
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv
from test_queries import get_all_tests, get_tests_by_level
from metrics import log_metrics, calculate_cost, calculate_efficiency
import uuid

load_dotenv()

# ==============================================================================
# CONFIGURACIÓN DE MODELOS
# ==============================================================================

ARENA_MODELS = {
    "heavyweight": {
        "name": "openai/gpt-4o",
        "display_name": "GPT-4o (Pesado)",
        "category": "Pesado",
        "description": "El estándar de oro. 'El que no debería fallar'."
    },
    "medium": {
        "name": "openai/gpt-oss-120b",
        "display_name": "GPT-OSS-120B (Mediano)",
        "category": "Mediano", 
        "description": "El retador de los gigantes de la IA."
    },
    "crossover": {
        "name": "meta-llama/llama-3.3-70b-instruct",
        "display_name": "Llama-3.3-70B (Crossover)",
        "category": "Crossover",
        "description": "El modelo 'abierto' de Meta (estilo OT-preview)."
    },
    "lightweight": {
        "name": "meta-llama/llama-3-8b-instruct",
        "display_name": "Llama-3-8B (Ligero)",
        "category": "Ligero",
        "description": "El rey de la eficiencia."
    },
    "mini": {
        "name": "microsoft/phi-3.5-mini-128k-instruct",
        "display_name": "Phi-3.5 (Mini)",
        "category": "Mini",
        "description": "El 'underdog' que sorprende por su tamaño."
    }
}

# ==============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ==============================================================================

DB_PATH = os.path.join(os.path.dirname(__file__), "chinook.db")

chinook_schema = """
CREATE TABLE "artists" (
    "ArtistId" INTEGER NOT NULL,
    "Name" NVARCHAR(120),
    PRIMARY KEY ("ArtistId")
);
CREATE TABLE "albums" (
    "AlbumId" INTEGER NOT NULL,
    "Title" NVARCHAR(160) NOT NULL,
    "ArtistId" INTEGER NOT NULL,
    PRIMARY KEY ("AlbumId"),
    FOREIGN KEY ("ArtistId") REFERENCES "artists" ("ArtistId")
);
CREATE TABLE "employees" (
    "EmployeeId" INTEGER NOT NULL,
    "LastName" NVARCHAR(20) NOT NULL,
    "FirstName" NVARCHAR(20) NOT NULL,
    "Title" NVARCHAR(30),
    "ReportsTo" INTEGER,
    "BirthDate" DATETIME,
    "HireDate" DATETIME,
    "Address" NVARCHAR(70),
    "City" NVARCHAR(40),
    "State" NVARCHAR(40),
    "Country" NVARCHAR(40),
    "PostalCode" NVARCHAR(10),
    "Phone" NVARCHAR(24),
    "Fax" NVARCHAR(24),
    "Email" NVARCHAR(60),
    PRIMARY KEY ("EmployeeId"),
    FOREIGN KEY ("ReportsTo") REFERENCES "employees" ("EmployeeId")
);
CREATE TABLE "customers" (
    "CustomerId" INTEGER NOT NULL,
    "FirstName" NVARCHAR(40) NOT NULL,
    "LastName" NVARCHAR(20) NOT NULL,
    "Company" NVARCHAR(80),
    "Address" NVARCHAR(70),
    "City" NVARCHAR(40),
    "State" NVARCHAR(40),
    "Country" NVARCHAR(40),
    "PostalCode" NVARCHAR(10),
    "Phone" NVARCHAR(24),
    "Fax" NVARCHAR(24),
    "Email" NVARCHAR(60) NOT NULL,
    "SupportRepId" INTEGER,
    PRIMARY KEY ("CustomerId"),
    FOREIGN KEY ("SupportRepId") REFERENCES "employees" ("EmployeeId")
);
CREATE TABLE "invoices" (
    "InvoiceId" INTEGER NOT NULL,
    "CustomerId" INTEGER NOT NULL,
    "InvoiceDate" DATETIME NOT NULL,
    "BillingAddress" NVARCHAR(70),
    "BillingCity" NVARCHAR(40),
    "BillingState" NVARCHAR(40),
    "BillingCountry" NVARCHAR(40),
    "BillingPostalCode" NVARCHAR(10),
    "Total" NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY ("InvoiceId"),
    FOREIGN KEY ("CustomerId") REFERENCES "customers" ("CustomerId")
);
CREATE TABLE "invoice_items" (
    "InvoiceLineId" INTEGER NOT NULL,
    "InvoiceId" INTEGER NOT NULL,
    "TrackId" INTEGER NOT NULL,
    "UnitPrice" NUMERIC(10, 2) NOT NULL,
    "Quantity" INTEGER NOT NULL,
    PRIMARY KEY ("InvoiceLineId"),
    FOREIGN KEY ("InvoiceId") REFERENCES "invoices" ("InvoiceId"),
    FOREIGN KEY ("TrackId") REFERENCES "tracks" ("TrackId")
);
CREATE TABLE "media_types" (
    "MediaTypeId" INTEGER NOT NULL,
    "Name" NVARCHAR(120),
    PRIMARY KEY ("MediaTypeId")
);
CREATE TABLE "genres" (
    "GenreId" INTEGER NOT NULL,
    "Name" NVARCHAR(120),
    PRIMARY KEY ("GenreId")
);
CREATE TABLE "tracks" (
    "TrackId" INTEGER NOT NULL,
    "Name" NVARCHAR(200) NOT NULL,
    "AlbumId" INTEGER,
    "MediaTypeId" INTEGER NOT NULL,
    "GenreId" INTEGER,
    "Composer" NVARCHAR(220),
    "Milliseconds" INTEGER NOT NULL,
    "Bytes" INTEGER,
    "UnitPrice" NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY ("TrackId"),
    FOREIGN KEY ("AlbumId") REFERENCES "albums" ("AlbumId"),
    FOREIGN KEY ("GenreId") REFERENCES "genres" ("GenreId"),
    FOREIGN KEY ("MediaTypeId") REFERENCES "media_types" ("MediaTypeId")
);
CREATE TABLE "playlists" (
    "PlaylistId" INTEGER NOT NULL,
    "Name" NVARCHAR(120),
    PRIMARY KEY ("PlaylistId")
);
CREATE TABLE "playlist_track" (
    "PlaylistId" INTEGER NOT NULL,
    "TrackId" INTEGER NOT NULL,
    PRIMARY KEY ("PlaylistId", "TrackId"),
    FOREIGN KEY ("PlaylistId") REFERENCES "playlists" ("PlaylistId"),
    FOREIGN KEY ("TrackId") REFERENCES "tracks" ("TrackId")
);
"""

SYSTEM_PROMPT = f"""
Eres un analista de datos experto en SQL. Tu objetivo es generar consultas SQL válidas para SQLite.

IMPORTANTE:
1. Genera SOLO la consulta SQL, sin explicaciones adicionales.
2. La consulta debe ser válida para SQLite.
3. Usa SELECT únicamente.
4. Los nombres de tablas y columnas usan PascalCase (ej: "artists", "ArtistId").
5. Responde ÚNICAMENTE con el código SQL, nada más.

Esquema de la base de datos:
{chinook_schema}
"""

# ==============================================================================
# HERRAMIENTAS DE EJECUCIÓN
# ==============================================================================

def execute_sql(sql_query: str) -> tuple[pd.DataFrame, Optional[str]]:
    """
    Ejecuta una consulta SQL y retorna el DataFrame y posible error.
    """
    try:
        sql_query = sql_query.strip().rstrip(';')
        
        # Permitir SELECT y WITH (CTEs - Common Table Expressions)
        sql_upper = sql_query.upper()
        if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
            return pd.DataFrame(), "Solo se permiten consultas SELECT."
        
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

def normalize_sql(sql: str) -> str:
    """Normaliza SQL para comparación"""
    return ' '.join(sql.upper().split())

def compare_results(df1: pd.DataFrame, df2: pd.DataFrame) -> bool:
    """
    Compara dos DataFrames para verificar si tienen los mismos datos.
    """
    try:
        # Si alguno está vacío, no son iguales (a menos que ambos estén vacíos)
        if df1.empty or df2.empty:
            return df1.empty and df2.empty
        
        # Si tienen diferente número de filas o columnas, no son iguales
        if df1.shape != df2.shape:
            return False
        
        # Si no hay columnas para ordenar, solo comparar forma
        if len(df1.columns) == 0:
            return True
        
        # Ordenar columnas y filas para comparación justa
        # Convertir todos los valores a string para comparación más flexible
        df1_sorted = df1.sort_index(axis=1)
        df2_sorted = df2.sort_index(axis=1)
        
        # Si hay columnas, ordenar por la primera columna
        if len(df1.columns) > 0:
            first_col = df1.columns[0]
            df1_sorted = df1_sorted.sort_values(by=first_col).reset_index(drop=True)
            df2_sorted = df2_sorted.sort_values(by=first_col).reset_index(drop=True)
        
        # Comparar con tolerancia para números float
        return df1_sorted.round(2).equals(df2_sorted.round(2))
    except Exception as e:
        print(f"⚠️ Error en comparación: {e}")
        return False

# ==============================================================================
# AGENTE SQL
# ==============================================================================

class SQLAgent:
    """Agente SQL que usa un modelo específico de OpenRouter"""
    
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    
    def generate_sql(self, question: str) -> Dict[str, Any]:
        """
        Genera SQL para una pregunta dada.
        
        Returns:
            Dict con: sql, tokens_input, tokens_output, ttft, latency, error
        """
        start_time = time.time()
        ttft = None
        
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Genera la consulta SQL para: {question}"}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=1000
            )
            
            # TTFT es aproximadamente el tiempo hasta recibir la respuesta
            ttft = time.time() - start_time
            
            sql_query = response.choices[0].message.content.strip()
            
            # Limpiar el SQL de markdown si viene con ```sql
            if sql_query.startswith("```"):
                lines = sql_query.split('\n')
                sql_query = '\n'.join(lines[1:-1]) if len(lines) > 2 else sql_query
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            
            latency = time.time() - start_time
            
            return {
                "sql": sql_query,
                "tokens_input": response.usage.prompt_tokens if response.usage else 0,
                "tokens_output": response.usage.completion_tokens if response.usage else 0,
                "tokens_total": response.usage.total_tokens if response.usage else 0,
                "ttft": ttft,
                "latency": latency,
                "error": None
            }
            
        except Exception as e:
            return {
                "sql": None,
                "tokens_input": 0,
                "tokens_output": 0,
                "tokens_total": 0,
                "ttft": ttft,
                "latency": time.time() - start_time,
                "error": str(e)
            }

# ==============================================================================
# ARENA - COMPARACIÓN DE MODELOS
# ==============================================================================

def run_arena_test(test: Dict, api_key: str, session_id: str = None) -> Dict[str, Any]:
    """
    Ejecuta un test en todos los modelos del arena.
    
    Args:
        test: Dict con la información del test
        api_key: API key de OpenRouter
        session_id: ID de sesión (opcional)
    
    Returns:
        Dict con resultados de todos los modelos
    """
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    question = test["description"]
    test_id = test["id"]
    
    # Determinar nivel de dificultad
    if test_id.startswith("B"):
        test_level = "basic"
    elif test_id.startswith("M"):
        test_level = "medium"
    else:
        test_level = "advanced"
    
    results = {
        "test_id": test_id,
        "test_level": test_level,
        "question": question,
        "models": {}
    }
    
    # Ejecutar consulta correcta para comparación
    correct_sql = test.get("correct_sql", "").strip()
    correct_df, correct_error = execute_sql(correct_sql)
    
    # Ejecutar en cada modelo
    for model_key, model_info in ARENA_MODELS.items():
        print(f"🤖 Ejecutando {model_info['display_name']}...")
        
        agent = SQLAgent(model_info["name"], api_key)
        generation_result = agent.generate_sql(question)
        
        # Ejecutar el SQL generado
        success = False
        execution_error = None
        result_df = pd.DataFrame()
        
        if generation_result["sql"] and not generation_result["error"]:
            result_df, execution_error = execute_sql(generation_result["sql"])
            
            if execution_error is None and not result_df.empty:
                # Verificar si el resultado coincide con la consulta correcta
                success = compare_results(result_df, correct_df)
        
        # Calcular métricas
        execution_time = generation_result["latency"]
        tokens_total = generation_result["tokens_total"]
        efficiency = calculate_efficiency(tokens_total, execution_time)
        real_cost = calculate_cost(
            model_info["name"],
            generation_result["tokens_input"],
            generation_result["tokens_output"]
        )
        
        # Guardar resultados
        results["models"][model_key] = {
            "name": model_info["display_name"],
            "category": model_info["category"],
            "sql": generation_result["sql"],
            "success": success,
            "tokens_input": generation_result["tokens_input"],
            "tokens_output": generation_result["tokens_output"],
            "tokens_total": tokens_total,
            "ttft": generation_result["ttft"],
            "latency": generation_result["latency"],
            "execution_time": execution_time,
            "real_cost": real_cost,
            "efficiency": efficiency,
            "generation_error": generation_result["error"],
            "execution_error": execution_error,
            "result_rows": len(result_df) if not result_df.empty else 0
        }
        
        # Log metrics
        log_metrics(
            session_id=session_id,
            tokens_input=generation_result["tokens_input"],
            tokens_output=generation_result["tokens_output"],
            tokens_processed=tokens_total,
            message_count=1,
            api_key_source="user",
            llm_model=model_info["name"],
            latency_api=generation_result["latency"],
            execution_time=execution_time,
            success=success,
            ttft=generation_result["ttft"],
            test_id=test_id,
            test_level=test_level
        )
    
    return results

def run_arena_batch(tests: List[Dict], api_key: str) -> List[Dict[str, Any]]:
    """
    Ejecuta un batch de tests en todos los modelos.
    
    Args:
        tests: Lista de tests a ejecutar
        api_key: API key de OpenRouter
    
    Returns:
        Lista de resultados
    """
    session_id = str(uuid.uuid4())
    results = []
    
    for i, test in enumerate(tests, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(tests)}: {test['id']} - {test['description']}")
        print(f"{'='*80}")
        
        result = run_arena_test(test, api_key, session_id)
        results.append(result)
        
        # Pequeña pausa para no saturar la API
        time.sleep(1)
    
    return results

# ==============================================================================
# ANÁLISIS Y REPORTES
# ==============================================================================

def generate_summary_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Genera un reporte resumen de todos los resultados.
    """
    summary = {
        "total_tests": len(results),
        "models": {}
    }
    
    # Inicializar métricas por modelo
    for model_key, model_info in ARENA_MODELS.items():
        summary["models"][model_key] = {
            "name": model_info["display_name"],
            "category": model_info["category"],
            "total_success": 0,
            "total_tests": 0,
            "success_rate": 0.0,
            "avg_latency": 0.0,
            "avg_ttft": 0.0,
            "total_cost": 0.0,
            "avg_efficiency": 0.0,
            "total_tokens": 0
        }
    
    # Agregar datos
    for result in results:
        for model_key, model_result in result["models"].items():
            summary["models"][model_key]["total_tests"] += 1
            summary["models"][model_key]["total_success"] += 1 if model_result["success"] else 0
            summary["models"][model_key]["avg_latency"] += model_result["latency"]
            summary["models"][model_key]["avg_ttft"] += model_result["ttft"] or 0
            summary["models"][model_key]["total_cost"] += model_result["real_cost"] or 0
            summary["models"][model_key]["avg_efficiency"] += model_result["efficiency"] or 0
            summary["models"][model_key]["total_tokens"] += model_result["tokens_total"]
    
    # Calcular promedios
    for model_key in summary["models"]:
        total = summary["models"][model_key]["total_tests"]
        if total > 0:
            summary["models"][model_key]["success_rate"] = (
                summary["models"][model_key]["total_success"] / total * 100
            )
            summary["models"][model_key]["avg_latency"] /= total
            summary["models"][model_key]["avg_ttft"] /= total
            summary["models"][model_key]["avg_efficiency"] /= total
    
    return summary

def print_summary_report(summary: Dict[str, Any]):
    """Imprime el reporte resumen de forma legible"""
    print("\n" + "="*100)
    print("📊 RESUMEN DEL LLM ARENA")
    print("="*100)
    print(f"\nTotal de tests ejecutados: {summary['total_tests']}")
    print("\n" + "-"*100)
    print(f"{'Modelo':<30} {'Éxito':<12} {'Latencia':<12} {'TTFT':<12} {'Costo':<12} {'Eficiencia':<15}")
    print("-"*100)
    
    # Ordenar por success rate
    sorted_models = sorted(
        summary["models"].items(),
        key=lambda x: (x[1]["success_rate"], -x[1]["avg_latency"]),
        reverse=True
    )
    
    for model_key, metrics in sorted_models:
        print(f"{metrics['name']:<30} "
              f"{metrics['success_rate']:>6.1f}% ({metrics['total_success']}/{metrics['total_tests']})  "
              f"{metrics['avg_latency']:>8.2f}s    "
              f"{metrics['avg_ttft']:>8.2f}s    "
              f"${metrics['total_cost']:>8.6f}    "
              f"{metrics['avg_efficiency']:>10.1f} tok/s")
    
    print("="*100)

# ==============================================================================
# MAIN - EJECUCIÓN DE PRUEBAS
# ==============================================================================

def main():
    """Función principal para ejecutar el arena"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM Arena - Comparación de modelos SQL")
    parser.add_argument("--level", choices=["basic", "medium", "advanced", "all"], 
                       default="all", help="Nivel de dificultad de los tests")
    parser.add_argument("--api-key", help="API Key de OpenRouter")
    parser.add_argument("--limit", type=int, help="Límite de tests a ejecutar")
    
    args = parser.parse_args()
    
    # Obtener API key
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: Necesitas proporcionar una API key de OpenRouter")
        print("   Usa --api-key o configura OPENROUTER_API_KEY en .env")
        return
    
    # Obtener tests
    if args.level == "all":
        tests = get_all_tests()
    else:
        tests = get_tests_by_level(args.level)
    
    if args.limit:
        tests = tests[:args.limit]
    
    print(f"\n🎯 Iniciando LLM Arena con {len(tests)} tests")
    print(f"📊 Nivel: {args.level}")
    print(f"🤖 Modelos: {len(ARENA_MODELS)}")
    
    # Ejecutar tests
    results = run_arena_batch(tests, api_key)
    
    # Generar y mostrar reporte
    summary = generate_summary_report(results)
    print_summary_report(summary)
    
    # Guardar resultados detallados
    output_file = f"arena_results_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": summary,
            "detailed_results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Resultados guardados en: {output_file}")

if __name__ == "__main__":
    main()
