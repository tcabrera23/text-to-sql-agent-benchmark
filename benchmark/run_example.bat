@echo off
REM Script de ejemplo para ejecutar el Arena Runner en Windows
REM Asegurate de tener tu API key de OpenRouter
REM Ejecutar desde la raiz del repo: benchmark\run_example.bat

echo ================================================================================
echo                       LLM ARENA - SCRIPT DE EJEMPLO
echo ================================================================================
echo.

REM Verifica que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    pause
    exit /b 1
)

echo Python detectado correctamente.
echo.

REM Pide la API key al usuario (o usa variable de entorno)
if "%OPENROUTER_API_KEY%"=="" (
    set /p OPENROUTER_API_KEY="Introduce tu API Key de OpenRouter: "
)

if "%OPENROUTER_API_KEY%"=="" (
    echo ERROR: No se proporciono una API Key
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo                        OPCIONES DE EJECUCION
echo ================================================================================
echo.
echo 1. Ejecutar TODOS los tests (15 tests x 5 modelos = 75 ejecuciones)
echo 2. Ejecutar solo tests de Nivel 1 - Facil (5 tests x 5 modelos = 25 ejecuciones)
echo 3. Ejecutar solo tests de Nivel 2 - Medio (5 tests x 5 modelos = 25 ejecuciones)
echo 4. Ejecutar solo tests de Nivel 3 - Dificil (5 tests x 5 modelos = 25 ejecuciones)
echo 5. Comparar solo modelos pequenos (Mini + Ligero) en Nivel 1
echo 6. Benchmark completo del modelo GPT-4o
echo 7. Salir
echo.

set /p OPCION="Selecciona una opcion (1-7): "

if "%OPCION%"=="1" (
    echo.
    echo Ejecutando TODOS los tests...
    python benchmark\runner.py --api-key %OPENROUTER_API_KEY% --output data\arena_full_results.json
)

if "%OPCION%"=="2" (
    echo.
    echo Ejecutando tests de Nivel 1...
    python benchmark\runner.py --api-key %OPENROUTER_API_KEY% --level 1 --output data\arena_level1.json
)

if "%OPCION%"=="3" (
    echo.
    echo Ejecutando tests de Nivel 2...
    python benchmark\runner.py --api-key %OPENROUTER_API_KEY% --level 2 --output data\arena_level2.json
)

if "%OPCION%"=="4" (
    echo.
    echo Ejecutando tests de Nivel 3...
    python benchmark\runner.py --api-key %OPENROUTER_API_KEY% --level 3 --output data\arena_level3.json
)

if "%OPCION%"=="5" (
    echo.
    echo Comparando modelos pequenos en Nivel 1...
    python benchmark\runner.py --api-key %OPENROUTER_API_KEY% --level 1 --models mini lightweight --output data\arena_small_models.json
)

if "%OPCION%"=="6" (
    echo.
    echo Benchmark completo de GPT-4o...
    python benchmark\runner.py --api-key %OPENROUTER_API_KEY% --models heavyweight --output data\arena_gpt4o.json
)

if "%OPCION%"=="7" (
    echo.
    echo Saliendo...
    exit /b 0
)

echo.
echo ================================================================================
echo                           EJECUCION COMPLETADA
echo ================================================================================
echo.
echo Los resultados han sido guardados en el archivo JSON correspondiente.
echo Puedes ver las metricas detalladas en la pestana "Metricas" de la aplicacion.
echo.
pause
