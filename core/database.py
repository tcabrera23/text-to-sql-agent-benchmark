"""Ejecución segura de SQL contra chinook.db (antes duplicada como `consulta_sql`
en main.py, `execute_sql` en arena_runner.py y `execute_sql` en llm_arena.py)."""

import sqlite3

import pandas as pd

from core.paths import DB_PATH


def execute_sql(query: str, db_path=DB_PATH) -> tuple[pd.DataFrame, str | None]:
    """Ejecuta una consulta SQL de solo lectura (SELECT/WITH) y devuelve (DataFrame, error)."""
    try:
        query = query.strip().rstrip(';')

        query_upper = query.upper()
        if not (query_upper.startswith('SELECT') or query_upper.startswith('WITH')):
            return pd.DataFrame(), "Solo se permiten consultas SELECT."

        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn)
        conn.close()

        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)
