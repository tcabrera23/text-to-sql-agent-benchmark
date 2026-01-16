# 🏟️ LLM Arena - Comparación de Modelos SQL

## 📖 Descripción

El **LLM Arena** es un sistema de evaluación comparativa para modelos de lenguaje en tareas de generación de SQL. Permite comparar 5 modelos diferentes de OpenRouter para encontrar el equilibrio perfecto entre **precio** y **calidad**.

## 🤖 Modelos en Competencia

### Comparativa de Modelos y Precios

| Categoría | Modelo | Nombre Técnico | Precio Input ($/M tokens) | Precio Output ($/M tokens) | Descripción |
|-----------|--------|----------------|---------------------------|----------------------------|-------------|
| **🏋️ Pesado** | GPT-4o | `openai/gpt-4o` | $2.50 | $10.00 | El estándar de oro. "El que no debería fallar". |
| **💪 Mediano** | DeepSeek-V3-70b | `deepseek/deepseek-v3` | $0.27 | $1.10 | El retador de código (sucesor del popular V2.5). |
| **⚡ Crossover** | GPT-4o-mini | `openai/gpt-4o-mini` | $0.15 | $0.60 | El modelo "abierto" de OpenAI (estilo OT-preview). |
| **🚀 Ligero** | Llama-3.3-70b | `meta-llama/llama-3.3-70b-instruct` | $0.59 | $0.79 | El rey de la eficiencia. |
| **🐭 Mini** | Phi-4-mini-4b | `microsoft/phi-4` | $0.00 | $0.00 | El "underdog" que sorprende por su tamaño. |

### Análisis de Costos Esperados

Para una consulta típica con:
- **Input:** ~500 tokens (esquema + prompt)
- **Output:** ~150 tokens (query SQL)

**Costo por consulta:**

| Modelo | Costo Estimado |
|--------|----------------|
| GPT-4o | $0.00275 |
| DeepSeek-V3 | $0.000300 |
| GPT-4o-mini | $0.000165 |
| Llama-3.3-70b | $0.000413 |
| Phi-4 | $0.000000 |

## 📝 Sistema de Tests

### Estructura de Tests

El arena incluye **15 tests profesionales** divididos en **3 niveles de dificultad**:

#### Nivel 1: Fácil (5 tests)
- Consultas simples con 1-2 tablas
- Agregaciones básicas (COUNT, SUM, AVG)
- GROUP BY y ORDER BY simples
- **Ejemplo:** "¿Cuáles son los 5 artistas con más álbumes?"

#### Nivel 2: Medio (5 tests)
- JOINs múltiples (3-4 tablas)
- Subconsultas
- Agregaciones complejas
- Análisis temporal
- **Ejemplo:** "Top 10 clientes VIP con su agente de soporte"

#### Nivel 3: Difícil (5 tests)
- CTEs (Common Table Expressions)
- Window Functions
- Análisis de cohortes
- Análisis RFM
- Consultas multi-paso
- **Ejemplo:** "Análisis de afinidad de géneros musicales"

### Tests Incluidos

| ID | Nivel | Nombre | Descripción |
|----|-------|--------|-------------|
| L1_T1 | 1 | Top 5 Artistas por Álbumes | Artistas con más álbumes en catálogo |
| L1_T2 | 1 | Distribución de Clientes por País | Cantidad de clientes por país |
| L1_T3 | 1 | Estadísticas de Precios | Precio promedio/min/max de canciones |
| L1_T4 | 1 | Ingresos Totales | Total de ingresos generados |
| L1_T5 | 1 | Conteo de Empleados | Empleados totales y agentes de soporte |
| L2_T1 | 2 | Top 5 Géneros por Ingresos | Géneros que generan más ingresos |
| L2_T2 | 2 | Top 10 Clientes VIP con Agente | Clientes que más gastan con su agente |
| L2_T3 | 2 | Tendencia de Ventas Mensuales | Análisis de ventas mes a mes |
| L2_T4 | 2 | Álbumes Más Vendidos | Álbumes con más tracks vendidos |
| L2_T5 | 2 | Performance de Empleados | Ingresos generados por cada agente |
| L3_T1 | 3 | Análisis de Cohortes de Clientes | Cohortes por año de primera compra |
| L3_T2 | 3 | Ranking de Artistas con Percentiles | Top 20 artistas con percentiles |
| L3_T3 | 3 | Análisis RFM de Clientes | Recency, Frequency, Monetary |
| L3_T4 | 3 | Crecimiento Interanual por País | Crecimiento año a año por país |
| L3_T5 | 3 | Análisis de Afinidad de Géneros | Géneros que se compran juntos |

## 📊 Métricas Trackeadas (El "Money Shot")

Para cada ejecución, el Arena trackea:

### 1. ✅ Éxito de Ejecución (Binario)
- ¿La query corrió sin errores?
- ¿El resultado es el correcto?
- Validación contra reglas esperadas

### 2. ⚡ Latencia
- **TTFT (Time to First Token):** Tiempo hasta el primer token de respuesta
- **Latencia Total:** Tiempo total de la llamada API
- **Tiempo de Ejecución:** Tiempo total incluyendo ejecución SQL

### 3. 💰 Costo Real
- Fórmula: `(Tokens Entrada × Precio Input) + (Tokens Salida × Precio Output)`
- Calculado con precios actualizados de OpenRouter
- Permite comparación económica directa

### 4. 🚀 Eficiencia (Tokens/Seg)
- Fórmula: `Tokens Totales / Tiempo de Ejecución`
- Mide qué tan "rápido" se siente el agente
- Balance entre velocidad y throughput

## 🚀 Uso

### Opción 1: Interfaz Web (Streamlit)

1. Inicia la aplicación:
```bash
streamlit run main.py
```

2. Ve a la pestaña **"🏟️ Arena LLM"**

3. Introduce tu API key de OpenRouter en la barra lateral

4. Selecciona un test y haz clic en **"🚀 Ejecutar Test en los 5 Modelos"**

5. Analiza los resultados comparativos

### Opción 2: Script Automatizado (CLI)

Para ejecutar tests en lote desde la línea de comandos:

```bash
# Ejecutar todos los tests en todos los modelos
python arena_runner.py --api-key TU_API_KEY

# Ejecutar solo tests de nivel 1
python arena_runner.py --api-key TU_API_KEY --level 1

# Ejecutar tests específicos
python arena_runner.py --api-key TU_API_KEY --tests L1_T1 L2_T1 L3_T1

# Comparar solo algunos modelos
python arena_runner.py --api-key TU_API_KEY --models pesado ligero mini

# Guardar resultados en archivo personalizado
python arena_runner.py --api-key TU_API_KEY --output mis_resultados.json
```

### Ejemplos de Uso Avanzado

**Benchmark completo de nivel 2:**
```bash
python arena_runner.py --api-key TU_API_KEY --level 2 --output benchmark_medio.json
```

**Comparar solo modelos pequeños:**
```bash
python arena_runner.py --api-key TU_API_KEY --models ligero mini --output small_models.json
```

**Tests difíciles solo en el modelo pesado:**
```bash
python arena_runner.py --api-key TU_API_KEY --level 3 --models pesado --output gpt4o_hard.json
```

## 📈 Análisis de Resultados

### En la Interfaz Web

La pestaña Arena muestra:

1. **Tabla Comparativa:** Todos los modelos lado a lado con métricas clave
2. **Money Shot KPIs:** 
   - Tasa de éxito global
   - Costo total
   - Latencia promedio
   - Eficiencia promedio
3. **Gráficos:**
   - Éxito por modelo
   - Costo vs Tiempo (scatter plot)
4. **SQL Generado:** Comparación del código generado por cada modelo

### En la Pestaña de Métricas

Después de ejecutar tests, la pestaña **"📈 Métricas"** mostrará:

- Métricas del Arena agregadas
- Tests ejecutados y tasa de éxito
- Éxito por nivel de dificultad
- Costo acumulado por modelo
- TTFT vs Latencia Total

## 🎯 Interpretación de Resultados

### Escenarios de Uso

**Producción de Alto Volumen:**
- Priorizar: **Costo** y **Eficiencia**
- Modelos recomendados: Phi-4, Llama-3.3, DeepSeek-V3

**Aplicaciones Críticas:**
- Priorizar: **Éxito** y **Precisión**
- Modelos recomendados: GPT-4o, GPT-4o-mini

**Prototipado Rápido:**
- Priorizar: **Velocidad** (TTFT)
- Modelos recomendados: GPT-4o-mini, Phi-4

**Balance Precio-Calidad:**
- Buscar: **Éxito > 80%** con **Costo mínimo**
- Modelos candidatos: DeepSeek-V3, Llama-3.3

## 🔧 Personalización

### Agregar Nuevos Tests

Edita `arena_tests.py`:

```python
{
    "id": "L2_T6",
    "level": 2,
    "name": "Mi Test Personalizado",
    "prompt": "¿Pregunta en lenguaje natural?",
    "expected_sql_keywords": ["SELECT", "JOIN", "GROUP BY"],
    "validation_rules": {
        "min_rows": 1,
        "required_columns": 2
    }
}
```

### Agregar Nuevos Modelos

Edita `main.py` y `arena_runner.py`:

```python
ARENA_MODELS["nuevo"] = {
    "name": "proveedor/modelo-nombre",
    "display_name": "Nombre Display",
    "category": "Categoría",
    "color": "#HEXCOLOR",
    "description": "Descripción"
}
```

Y actualiza precios en `metrics.py`:

```python
MODEL_PRICING["proveedor/modelo-nombre"] = {
    "input": 0.00, 
    "output": 0.00
}
```

## 📦 Archivos del Sistema

- `main.py` - Aplicación principal con interfaz Streamlit
- `arena_tests.py` - Definición de tests y validaciones
- `arena_runner.py` - Script CLI para ejecución automatizada
- `metrics.py` - Sistema de métricas y logging
- `metrics.csv` - Almacenamiento de métricas (generado automáticamente)
- `arena_results.json` - Resultados de arena_runner (generado por CLI)

## 🐛 Troubleshooting

**Error: "No OpenRouter API key"**
- Asegúrate de introducir tu API key en la barra lateral o como argumento `--api-key`

**Error: "Rate limit exceeded"**
- Los scripts incluyen pausas automáticas entre llamadas
- Considera usar `--models` para reducir el número de modelos simultáneos

**Tests fallan con "SQL error"**
- Los modelos a veces generan SQL con markdown, esto se limpia automáticamente
- Revisa el SQL generado en los detalles del test

**Costos mayores a los esperados**
- Verifica precios actualizados en `metrics.py`
- Los precios de OpenRouter pueden cambiar

## 🤝 Contribuciones

Para agregar más tests o mejorar el sistema:

1. Analiza el schema de `chinook.db`
2. Crea tests con `expected_sql_keywords` apropiados
3. Define `validation_rules` claras
4. Prueba en múltiples modelos

## 📄 Licencia

Este proyecto es parte del Agente SQL y Dashboard IA.

---

**¡Que gane el mejor modelo! 🏆**
