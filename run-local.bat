@echo off
REM Скрипт для локального запуска Todo API с SQLite
echo 🚀 Установка зависимостей...
pip install -r requirements.txt

echo.
echo 🗑️  Очистка старой БД (если есть)...
if exist todo.db del todo.db

echo.
echo 🚀 Запуск Todo API...
echo 📚 Swagger UI: http://localhost:8000/docs
echo 🌐 UI: http://localhost:8000
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
