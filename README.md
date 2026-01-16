# 🚀 Agente SQL y Dashboard IA + LLM Arena

Sistema completo de análisis de datos con IA que incluye:
- 💬 **Chat SQL Agent** - Conversa en lenguaje natural y obtén insights de tu base de datos
- 📊 **Dashboard Automático** - Genera KPIs y visualizaciones con un solo prompt
- 🏟️ **LLM Arena** - Compara 5 modelos diferentes de IA para encontrar el mejor balance precio-calidad
- 📈 **Métricas Avanzadas** - Trackea costos, latencia, TTFT, eficiencia y más

## 🌟 Características Principales

### Chat de Análisis SQL
- Convierte preguntas en lenguaje natural a SQL automáticamente
- Soporte para análisis exploratorios ("analiza mi negocio")
- Ejecución segura de queries (solo SELECT)
- Historial de conversación persistente
- Visualización de resultados en tiempo real

### Dashboard Interactivo
- Generación automática de KPIs
- Gráficos con Plotly, Seaborn y Matplotlib
- Diseño adaptativo y profesional
- Actualización dinámica de componentes

### 🆕 LLM Arena (Nuevo!)
- **5 Modelos en competencia:**
  - 🏋️ GPT-4o (Pesado) - El estándar de oro
  - 💪 DeepSeek-V3-70b (Mediano) - El retador de código
  - ⚡ GPT-4o-mini (Crossover) - Rápido y preciso
  - 🚀 Llama-3.3-70b (Ligero) - Rey de la eficiencia
  - 🐭 Phi-4-mini-4b (Mini) - El underdog sorprendente

- **15 Tests Profesionales:**
  - 5 tests Nivel 1 (Fácil) - Queries simples
  - 5 tests Nivel 2 (Medio) - JOINs y agregaciones
  - 5 tests Nivel 3 (Difícil) - CTEs y análisis complejos

- **Métricas "Money Shot":**
  - ✅ Éxito de ejecución
  - ⚡ Latencia (TTFT + Total)
  - 💰 Costo real calculado
  - 🚀 Eficiencia (tokens/seg)

## 📦 Instalación

### Requisitos Previos
- Python 3.8+
- pip

### Pasos de Instalación

1. **Clona el repositorio:**
```bash
git clone <tu-repositorio>
cd agente_sql
```

2. **Instala las dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configura las variables de entorno (opcional):**
Crea un archivo `.env` en la raíz del proyecto:
```env
GROQ_API_KEY=tu_api_key_aqui
OPENAI_API_KEY=tu_api_key_aqui
OPENROUTER_API_KEY=tu_api_key_aqui
```

> **Nota:** También puedes introducir las API keys directamente en la interfaz web.

## 🚀 Uso

### Opción 1: Interfaz Web (Recomendado)

```bash
streamlit run main.py
```

La aplicación se abrirá en `http://localhost:8501`

#### Pestañas Disponibles:

1. **💬 Chat de Análisis** - Pregunta sobre tus datos en lenguaje natural
2. **📊 Dashboard Interactivo** - Crea visualizaciones personalizadas
3. **🏟️ Arena LLM** - Compara modelos en tareas SQL
4. **📈 Métricas** - Analiza el uso y rendimiento (PIN: 2406)

### Opción 2: Arena CLI (Para Tests Automatizados)

**Windows:**
```bash
run_arena_example.bat
```

**Linux/Mac:**
```bash
chmod +x run_arena_example.sh
./run_arena_example.sh
```

**Manual:**
```bash
# Ejecutar todos los tests
python arena_runner.py --api-key TU_API_KEY

# Solo tests de Nivel 1
python arena_runner.py --api-key TU_API_KEY --level 1

# Comparar modelos específicos
python arena_runner.py --api-key TU_API_KEY --models pesado mini

# Tests específicos
python arena_runner.py --api-key TU_API_KEY --tests L1_T1 L2_T1 L3_T1
```

## 📊 Base de Datos

El proyecto usa la base de datos **Chinook** (tienda de música digital) que incluye:

- 🎵 Artistas, álbumes, tracks, géneros
- 👥 Clientes, empleados
- 💰 Facturas, items de factura
- 📝 Playlists

Perfecta para demostrar análisis de negocio realistas.

## 🎯 Ejemplos de Uso

### Chat SQL

**Pregunta simple:**
```
¿Cuáles son los 5 artistas más vendidos?
```

**Análisis exploratorio:**
```
Analiza el rendimiento de ventas de mi negocio
```

**Análisis temporal:**
```
Muéstrame la evolución de ventas mes a mes en 2009
```

### Arena LLM

1. Ve a la pestaña "🏟️ Arena LLM"
2. Selecciona un test (ej: "Top 5 Géneros por Ingresos")
3. Haz clic en "🚀 Ejecutar Test en los 5 Modelos"
4. Analiza los resultados comparativos:
   - ¿Qué modelo tuvo éxito?
   - ¿Cuánto costó cada ejecución?
   - ¿Qué tan rápido fue cada modelo?
   - ¿Qué SQL generó cada uno?

## 💰 Análisis de Costos (Arena)

### Precios por Millón de Tokens

| Modelo | Input | Output | Costo Típico por Query |
|--------|-------|--------|------------------------|
| GPT-4o | $2.50 | $10.00 | $0.00275 |
| DeepSeek-V3 | $0.27 | $1.10 | $0.000300 |
| GPT-4o-mini | $0.15 | $0.60 | $0.000165 |
| Llama-3.3 | $0.59 | $0.79 | $0.000413 |
| Phi-4 | $0.00 | $0.00 | $0.000000 (Gratis!) |

### Costos por Escenario

**Startup MVP (1,000 queries/mes):**
- GPT-4o: $2.75/mes
- DeepSeek-V3: $0.30/mes
- Phi-4: $0.00/mes

**Enterprise (1M queries/mes):**
- GPT-4o: $2,750/mes
- DeepSeek-V3: $300/mes
- Phi-4: $0.00/mes

## 📈 Métricas Trackeadas

El sistema registra automáticamente:

### Métricas Básicas
- Tokens de entrada/salida/total
- Modelo utilizado
- Fuente de API key (usuario vs default)
- Fecha y hora

### Métricas Avanzadas (Arena)
- ✅ **Success:** ¿La query funcionó correctamente?
- ⚡ **TTFT:** Time to First Token
- ⏱️ **Latency:** Tiempo de respuesta de la API
- 💰 **Real Cost:** Costo calculado con precios actuales
- 🚀 **Efficiency:** Tokens por segundo
- 📊 **Test ID/Level:** Para análisis por dificultad

## 🛠️ Estructura del Proyecto

```
agente_sql/
│
├── main.py                     # Aplicación principal (Streamlit)
├── metrics.py                  # Sistema de métricas y logging
├── arena_tests.py              # Definición de 15 tests del Arena
├── arena_runner.py             # CLI para ejecución automatizada
├── model_pricing_table.py      # Tabla de precios y análisis
│
├── chinook.db                  # Base de datos SQLite
├── metrics.csv                 # Métricas registradas (auto-generado)
│
├── requirements.txt            # Dependencias Python
├── .env                        # Variables de entorno (crear manualmente)
│
├── README.md                   # Este archivo
├── ARENA_README.md             # Documentación detallada del Arena
│
├── run_arena_example.bat       # Script de ejemplo (Windows)
└── run_arena_example.sh        # Script de ejemplo (Linux/Mac)
```

## 🔧 Configuración Avanzada

### Agregar Nuevos Modelos al Arena

1. Edita `main.py` y `arena_runner.py`:
```python
ARENA_MODELS["tu_modelo"] = {
    "name": "proveedor/modelo-id",
    "display_name": "Nombre Display",
    "category": "Categoría",
    "color": "#HEXCOLOR",
    "description": "Descripción"
}
```

2. Actualiza precios en `metrics.py`:
```python
MODEL_PRICING["proveedor/modelo-id"] = {
    "input": 0.00,
    "output": 0.00
}
```

### Crear Tests Personalizados

Edita `arena_tests.py`:
```python
{
    "id": "L2_T6",
    "level": 2,
    "name": "Tu Test",
    "prompt": "Pregunta en lenguaje natural",
    "expected_sql_keywords": ["SELECT", "JOIN"],
    "validation_rules": {
        "min_rows": 1,
        "required_columns": 2
    }
}
```

## 📚 Casos de Uso

### Para Desarrolladores
- ✅ Compara modelos antes de elegir para producción
- ✅ Encuentra el mejor balance precio-calidad
- ✅ Benchmarks reproducibles con tests estandarizados

### Para Data Analysts
- ✅ Explora bases de datos sin escribir SQL
- ✅ Genera dashboards en segundos
- ✅ Analiza tendencias y patrones rápidamente

### Para Empresas
- ✅ Optimiza costos de API eligiendo el modelo correcto
- ✅ Evalúa nuevos modelos objetivamente
- ✅ Auditoría de uso y costos en tiempo real

## 🤝 Proveedores Soportados

- **Groq** - `llama-3.3-70b-versatile`
- **OpenAI** - `gpt-4o`
- **OpenRouter** - Acceso a 5+ modelos:
  - OpenAI (GPT-4o, GPT-4o-mini)
  - DeepSeek (V3)
  - Meta (Llama-3.3-70b)
  - Microsoft (Phi-4)

## 🐛 Troubleshooting

**Error: "No se encontró chinook.db"**
- Asegúrate de que `chinook.db` esté en la misma carpeta que `main.py`

**Error: "API key inválida"**
- Verifica que tu API key esté activa y tenga créditos
- Para OpenRouter, verifica en https://openrouter.ai/

**Tests del Arena fallan todos**
- Verifica tu conexión a internet
- Algunos modelos pueden estar temporalmente no disponibles
- Revisa los límites de rate limit de tu API key

**Costos muy altos**
- Usa modelos más pequeños (Phi-4, DeepSeek-V3)
- Limita los tests con `--level 1` o `--models`
- Monitorea en la pestaña "Métricas"

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 🙏 Agradecimientos

- **Chinook Database** - Base de datos de ejemplo
- **Streamlit** - Framework de interfaz web
- **OpenRouter** - Acceso unificado a múltiples LLMs
- **Groq** - Inferencia rápida de LLMs
- **OpenAI** - GPT-4o y GPT-4o-mini

## 📞 Soporte

Para preguntas o problemas:
1. Revisa la documentación en `ARENA_README.md`
2. Verifica los logs en `metrics.csv`
3. Consulta los ejemplos en los scripts de ejecución

---

**¿Ansioso por ver si los modelos pequeños compiten con los grandes?** 

¡Ejecuta el Arena y descúbrelo! 🏆

```bash
streamlit run main.py
```
