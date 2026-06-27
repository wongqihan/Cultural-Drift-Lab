#!/bin/bash
set -e

echo "=== Cultural Drift Lab ==="
echo "This script runs the entire experimental pipeline end-to-end."
echo ""

# Check for .env
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Ensure OPENAI_API_KEY and DEEPSEEK_API_KEY are set."
fi

echo "1. Generating synthetic human baselines (GPT-4o)..."
python3 src/synthetic_baselines.py

echo "2. Prompting models & scoring responses (LLM-as-a-judge)..."
python3 src/evaluate.py

echo "3. Generating scatterplot visualizations..."
python3 src/visualize.py

echo "Pipeline complete! Check the assets/ folder for the updated charts and data/ for the results."
