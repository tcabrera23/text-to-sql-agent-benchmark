"""
Catálogo de tests para el LLM Arena - Comparación de Modelos en Tareas SQL
Basado en la base de datos Chinook (tienda de música)

Estructura:
- Nivel 1 (Fácil): Consultas simples con 1-2 tablas, agregaciones básicas
- Nivel 2 (Medio): JOINs múltiples, subconsultas, GROUP BY avanzado
- Nivel 3 (Difícil): CTEs, Window Functions, análisis complejos

Cada test incluye:
- id: Identificador único
- level: Nivel de dificultad (1, 2, 3)
- prompt: Pregunta en lenguaje natural
- expected_sql_keywords: Palabras clave que deben aparecer en la consulta SQL generada
- validation_rules: Reglas para validar el resultado
"""

ARENA_TESTS = [
    # ==================== NIVEL 1: FÁCIL ====================
    {
        "id": "L1_T1",
        "level": 1,
        "name": "Top 5 Artistas por Álbumes",
        "prompt": "¿Cuáles son los 5 artistas con más álbumes en nuestro catálogo? Muestra el nombre del artista y la cantidad de álbumes.",
        "expected_sql_keywords": ["artists", "albums", "JOIN", "GROUP BY", "COUNT", "ORDER BY", "LIMIT 5"],
        "validation_rules": {
            "min_rows": 5,
            "max_rows": 5,
            "required_columns": 2,
            "column_types": ["string", "numeric"]
        }
    },
    {
        "id": "L1_T2",
        "level": 1,
        "name": "Distribución de Clientes por País",
        "prompt": "Muéstrame cuántos clientes tenemos en cada país, ordenados de mayor a menor.",
        "expected_sql_keywords": ["customers", "Country", "GROUP BY", "COUNT", "ORDER BY"],
        "validation_rules": {
            "min_rows": 1,
            "required_columns": 2,
            "column_types": ["string", "numeric"]
        }
    },
    {
        "id": "L1_T3",
        "level": 1,
        "name": "Estadísticas de Precios",
        "prompt": "¿Cuál es el precio promedio, mínimo y máximo de las canciones en nuestra tienda?",
        "expected_sql_keywords": ["tracks", "AVG", "MIN", "MAX", "UnitPrice"],
        "validation_rules": {
            "min_rows": 1,
            "max_rows": 1,
            "required_columns": 3,
            "column_types": ["numeric", "numeric", "numeric"]
        }
    },
    {
        "id": "L1_T4",
        "level": 1,
        "name": "Ingresos Totales",
        "prompt": "¿Cuál es el total de ingresos generados por todas las ventas?",
        "expected_sql_keywords": ["invoices", "SUM", "Total"],
        "validation_rules": {
            "min_rows": 1,
            "max_rows": 1,
            "required_columns": 1,
            "column_types": ["numeric"]
        }
    },
    {
        "id": "L1_T5",
        "level": 1,
        "name": "Conteo de Empleados",
        "prompt": "¿Cuántos empleados tenemos en total y cuántos de ellos son agentes de soporte (tienen clientes asignados)?",
        "expected_sql_keywords": ["employees", "COUNT", "SupportRepId"],
        "validation_rules": {
            "min_rows": 1,
            "required_columns": 2,
            "column_types": ["numeric", "numeric"]
        }
    },

    # ==================== NIVEL 2: MEDIO ====================
    {
        "id": "L2_T1",
        "level": 2,
        "name": "Top 5 Géneros por Ingresos",
        "prompt": "¿Cuáles son los 5 géneros musicales que generan más ingresos? Incluye el nombre del género y el total de ingresos generados.",
        "expected_sql_keywords": ["genres", "tracks", "invoice_items", "JOIN", "SUM", "GROUP BY", "ORDER BY", "LIMIT 5"],
        "validation_rules": {
            "min_rows": 5,
            "max_rows": 5,
            "required_columns": 2,
            "column_types": ["string", "numeric"]
        }
    },
    {
        "id": "L2_T2",
        "level": 2,
        "name": "Top 10 Clientes VIP con su Agente",
        "prompt": "Muéstrame los 10 clientes que más han gastado, incluyendo su nombre completo, el total gastado y el nombre de su agente de soporte.",
        "expected_sql_keywords": ["customers", "invoices", "employees", "JOIN", "SUM", "GROUP BY", "ORDER BY", "LIMIT 10"],
        "validation_rules": {
            "min_rows": 10,
            "max_rows": 10,
            "required_columns": 3,
            "column_types": ["string", "numeric", "string"]
        }
    },
    {
        "id": "L2_T3",
        "level": 2,
        "name": "Tendencia de Ventas Mensuales",
        "prompt": "Analiza las ventas mensuales del año 2009. Muestra el mes, el número de facturas y el total de ingresos para cada mes.",
        "expected_sql_keywords": ["invoices", "strftime", "GROUP BY", "SUM", "COUNT", "2009", "ORDER BY"],
        "validation_rules": {
            "min_rows": 1,
            "max_rows": 12,
            "required_columns": 3,
            "column_types": ["string", "numeric", "numeric"]
        }
    },
    {
        "id": "L2_T4",
        "level": 2,
        "name": "Álbumes Más Vendidos",
        "prompt": "¿Cuáles son los 10 álbumes que más veces han sido comprados? Muestra el título del álbum, el artista y el número total de tracks vendidos.",
        "expected_sql_keywords": ["albums", "artists", "tracks", "invoice_items", "JOIN", "SUM", "GROUP BY", "ORDER BY", "LIMIT 10"],
        "validation_rules": {
            "min_rows": 10,
            "max_rows": 10,
            "required_columns": 3,
            "column_types": ["string", "string", "numeric"]
        }
    },
    {
        "id": "L2_T5",
        "level": 2,
        "name": "Performance de Empleados",
        "prompt": "Para cada empleado que es agente de soporte, muestra su nombre completo, cuántos clientes tiene asignados y el total de ingresos generados por sus clientes.",
        "expected_sql_keywords": ["employees", "customers", "invoices", "JOIN", "GROUP BY", "COUNT", "SUM"],
        "validation_rules": {
            "min_rows": 1,
            "required_columns": 3,
            "column_types": ["string", "numeric", "numeric"]
        }
    },

    # ==================== NIVEL 3: DIFÍCIL ====================
    {
        "id": "L3_T1",
        "level": 3,
        "name": "Análisis de Cohortes de Clientes",
        "prompt": "Realiza un análisis de cohortes: agrupa a los clientes por el año de su primera compra y muestra cuántos clientes hay en cada cohorte y el valor promedio de vida del cliente (total gastado) para cada año.",
        "expected_sql_keywords": ["WITH", "MIN", "strftime", "GROUP BY", "AVG", "SUM"],
        "validation_rules": {
            "min_rows": 1,
            "required_columns": 3,
            "column_types": ["string", "numeric", "numeric"]
        }
    },
    {
        "id": "L3_T2",
        "level": 3,
        "name": "Ranking de Artistas con Percentiles",
        "prompt": "Crea un ranking de los top 20 artistas por ingresos totales. Para cada artista, muestra su posición en el ranking, nombre, ingresos totales y qué percentil representa respecto al total de ingresos.",
        "expected_sql_keywords": ["WITH", "artists", "albums", "tracks", "invoice_items", "JOIN", "SUM", "RANK", "ORDER BY", "LIMIT 20"],
        "validation_rules": {
            "min_rows": 20,
            "max_rows": 20,
            "required_columns": 4,
            "column_types": ["numeric", "string", "numeric", "numeric"]
        }
    },
    {
        "id": "L3_T3",
        "level": 3,
        "name": "Análisis RFM de Clientes",
        "prompt": "Realiza un análisis RFM (Recency, Frequency, Monetary) de los clientes. Para cada cliente muestra: días desde su última compra (Recency), número total de compras (Frequency) y total gastado (Monetary). Ordena por valor monetario descendente y muestra solo los top 15.",
        "expected_sql_keywords": ["WITH", "customers", "invoices", "MAX", "COUNT", "SUM", "julianday", "ORDER BY", "LIMIT 15"],
        "validation_rules": {
            "min_rows": 15,
            "max_rows": 15,
            "required_columns": 4,
            "column_types": ["string", "numeric", "numeric", "numeric"]
        }
    },
    {
        "id": "L3_T4",
        "level": 3,
        "name": "Crecimiento Interanual por País",
        "prompt": "Calcula el crecimiento interanual de ventas para los top 5 países por ingresos. Muestra el país, los ingresos de 2009, los ingresos de 2010, y el porcentaje de crecimiento.",
        "expected_sql_keywords": ["WITH", "invoices", "strftime", "GROUP BY", "SUM", "CASE", "ROUND"],
        "validation_rules": {
            "min_rows": 1,
            "max_rows": 5,
            "required_columns": 4,
            "column_types": ["string", "numeric", "numeric", "numeric"]
        }
    },
    {
        "id": "L3_T5",
        "level": 3,
        "name": "Análisis de Afinidad de Géneros",
        "prompt": "Identifica qué pares de géneros musicales se compran juntos con más frecuencia. Encuentra las 10 combinaciones de géneros que aparecen juntas en las mismas facturas más veces. Muestra los dos géneros y la frecuencia de co-ocurrencia.",
        "expected_sql_keywords": ["WITH", "genres", "tracks", "invoice_items", "JOIN", "GROUP BY", "COUNT", "ORDER BY", "LIMIT 10"],
        "validation_rules": {
            "min_rows": 10,
            "max_rows": 10,
            "required_columns": 3,
            "column_types": ["string", "string", "numeric"]
        }
    }
]

def get_tests_by_level(level: int):
    """Obtiene todos los tests de un nivel específico."""
    return [test for test in ARENA_TESTS if test["level"] == level]

def get_test_by_id(test_id: str):
    """Obtiene un test específico por su ID."""
    for test in ARENA_TESTS:
        if test["id"] == test_id:
            return test
    return None

def validate_result(test_id: str, df, error: str = None) -> dict:
    """
    Valida si el resultado de una consulta cumple con las reglas esperadas.

    Returns:
        dict: {"success": bool, "message": str, "details": dict}
    """
    test = get_test_by_id(test_id)
    if not test:
        return {"success": False, "message": "Test no encontrado", "details": {}}

    # Si hubo error en la ejecución
    if error:
        return {"success": False, "message": f"Error en ejecución: {error}", "details": {}}

    validation_rules = test.get("validation_rules", {})
    details = {}

    # Validar número de filas
    if "min_rows" in validation_rules:
        if len(df) < validation_rules["min_rows"]:
            return {"success": False, "message": f"Se esperaban al menos {validation_rules['min_rows']} filas, se obtuvieron {len(df)}", "details": details}

    if "max_rows" in validation_rules:
        if len(df) > validation_rules["max_rows"]:
            return {"success": False, "message": f"Se esperaban máximo {validation_rules['max_rows']} filas, se obtuvieron {len(df)}", "details": details}

    # Validar número de columnas
    if "required_columns" in validation_rules:
        if len(df.columns) != validation_rules["required_columns"]:
            return {"success": False, "message": f"Se esperaban {validation_rules['required_columns']} columnas, se obtuvieron {len(df.columns)}", "details": details}

    # Validar que no esté vacío
    if df.empty:
        return {"success": False, "message": "El resultado está vacío", "details": details}

    details["rows_returned"] = len(df)
    details["columns_returned"] = len(df.columns)

    return {"success": True, "message": "Validación exitosa", "details": details}

# Estadísticas de los tests
TEST_STATS = {
    "total_tests": len(ARENA_TESTS),
    "level_1": len([t for t in ARENA_TESTS if t["level"] == 1]),
    "level_2": len([t for t in ARENA_TESTS if t["level"] == 2]),
    "level_3": len([t for t in ARENA_TESTS if t["level"] == 3]),
}
