"""Rutas compartidas del proyecto, resueltas de forma absoluta desde la raíz del repo."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

DB_PATH = DATA_DIR / "chinook.db"
METRICS_CSV_PATH = DATA_DIR / "metrics.csv"
ARENA_RESULTS_PATH = DATA_DIR / "arena_results.json"
