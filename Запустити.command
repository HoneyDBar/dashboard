#!/bin/bash

# Переходимо в папку де лежить цей файл
cd "$(dirname "$0")"

echo "======================================="
echo "  Amazon Europe P&L Dashboard"
echo "======================================="
echo ""

# Перевіряємо чи встановлений Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python не знайдено."
    echo ""
    echo "Встановіть Python з https://python.org/downloads"
    echo "Після встановлення запустіть цей файл знову."
    echo ""
    read -p "Натисніть Enter щоб закрити..."
    exit 1
fi

echo "✅ Python знайдено: $(python3 --version)"
echo ""

# Встановлюємо залежності якщо потрібно
echo "🔄 Перевіряємо залежності..."
python3 -m pip install -r requirements.txt --quiet --disable-pip-version-check
echo "✅ Залежності встановлено"
echo ""

# Запускаємо дашборд
echo "🚀 Запускаємо дашборд..."
echo "   Браузер відкриється автоматично на http://localhost:8501"
echo ""
echo "   Щоб зупинити — закрийте це вікно або натисніть Ctrl+C"
echo ""

python3 -m streamlit run app.py --server.headless false
