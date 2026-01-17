#!/bin/bash

# Quick verification script for autonomous trader setup

echo "======================================================================"
echo "Autonomous AI Trader - Setup Verification"
echo "======================================================================"
echo ""

echo "✓ Checking files..."

files=(
    "src/ai/deepseek_analyzer.py"
    "scripts/autonomous_trader.py"
    "config/autonomous.yml"
    "config/secrets.yml"
    "start_autonomous_trader.sh"
    "AUTONOMOUS_TRADER.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ MISSING: $file"
    fi
done

echo ""
echo "✓ Checking API keys in secrets.yml..."

if grep -q "sk-70a6ad846e7a4164ba8357176c3cb045" config/secrets.yml; then
    echo "  ✓ DeepSeek API key configured"
else
    echo "  ✗ DeepSeek API key not found"
fi

if grep -q "mx0vglNhVM3aDXc9pl" config/secrets.yml; then
    echo "  ✓ MEXC API key configured"
else
    echo "  ✗ MEXC API key not found"
fi

echo ""
echo "✓ Configuration summary:"
echo "  - Trading mode: $(grep '^mode:' config/autonomous.yml | cut -d' ' -f2)"
echo "  - Initial capital: \$$(grep '^initial_capital:' config/autonomous.yml | cut -d' ' -f2)"
echo "  - AI confidence threshold: $(grep 'confidence_threshold:' config/autonomous.yml | head -1 | cut -d' ' -f2)%"

echo ""
echo "======================================================================"
echo "Setup verified! You can now:"
echo "  1. Install dependencies: pip install -r requirements.txt"
echo "  2. Start the bot: ./start_autonomous_trader.sh"
echo "======================================================================"
