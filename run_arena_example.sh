#!/bin/bash
# Script de ejemplo para ejecutar el Arena Runner en Linux/Mac
# Asegúrate de tener tu API key de OpenRouter

echo "================================================================================"
echo "                       LLM ARENA - SCRIPT DE EJEMPLO"
echo "================================================================================"
echo ""

# Verifica que Python esté instalado
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python no está instalado o no está en el PATH"
    exit 1
fi

echo "Python detectado correctamente."
echo ""

# Pide la API key al usuario (o usa variable de entorno)
if [ -z "$OPENROUTER_API_KEY" ]; then
    read -p "Introduce tu API Key de OpenRouter: " OPENROUTER_API_KEY
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "ERROR: No se proporcionó una API Key"
    exit 1
fi

echo ""
echo "================================================================================"
echo "                        OPCIONES DE EJECUCIÓN"
echo "================================================================================"
echo ""
echo "1. Ejecutar TODOS los tests (15 tests x 5 modelos = 75 ejecuciones)"
echo "2. Ejecutar solo tests de Nivel 1 - Fácil (5 tests x 5 modelos = 25 ejecuciones)"
echo "3. Ejecutar solo tests de Nivel 2 - Medio (5 tests x 5 modelos = 25 ejecuciones)"
echo "4. Ejecutar solo tests de Nivel 3 - Difícil (5 tests x 5 modelos = 25 ejecuciones)"
echo "5. Comparar solo modelos pequeños (Mini + Ligero) en Nivel 1"
echo "6. Benchmark completo del modelo GPT-4o"
echo "7. Salir"
echo ""

read -p "Selecciona una opción (1-7): " OPCION

case $OPCION in
    1)
        echo ""
        echo "Ejecutando TODOS los tests..."
        python3 arena_runner.py --api-key $OPENROUTER_API_KEY --output arena_full_results.json
        ;;
    2)
        echo ""
        echo "Ejecutando tests de Nivel 1..."
        python3 arena_runner.py --api-key $OPENROUTER_API_KEY --level 1 --output arena_level1.json
        ;;
    3)
        echo ""
        echo "Ejecutando tests de Nivel 2..."
        python3 arena_runner.py --api-key $OPENROUTER_API_KEY --level 2 --output arena_level2.json
        ;;
    4)
        echo ""
        echo "Ejecutando tests de Nivel 3..."
        python3 arena_runner.py --api-key $OPENROUTER_API_KEY --level 3 --output arena_level3.json
        ;;
    5)
        echo ""
        echo "Comparando modelos pequeños en Nivel 1..."
        python3 arena_runner.py --api-key $OPENROUTER_API_KEY --level 1 --models mini ligero --output arena_small_models.json
        ;;
    6)
        echo ""
        echo "Benchmark completo de GPT-4o..."
        python3 arena_runner.py --api-key $OPENROUTER_API_KEY --models pesado --output arena_gpt4o.json
        ;;
    7)
        echo ""
        echo "Saliendo..."
        exit 0
        ;;
    *)
        echo "Opción inválida"
        exit 1
        ;;
esac

echo ""
echo "================================================================================"
echo "                           EJECUCIÓN COMPLETADA"
echo "================================================================================"
echo ""
echo "Los resultados han sido guardados en el archivo JSON correspondiente."
echo "Puedes ver las métricas detalladas en la pestaña 'Métricas' de la aplicación."
echo ""
