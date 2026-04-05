#!/bin/bash
# Скрипт деплоя Todo API на сервер

set -e  # Остановка при ошибке

SERVER="root@109.73.201.197"
PROJECT_DIR="/opt/todo-api"
DOMAIN="todo.denischemeris.ru"

echo "🚀 Деплой Todo API на сервер 109.73.201.197"
echo ""

# Проверка подключения
echo "📡 Проверка подключения к серверу..."
ssh -o ConnectTimeout=5 $SERVER "echo '✅ Подключение успешно'" || {
    echo "❌ Ошибка подключения к серверу"
    exit 1
}

echo ""
echo "📁 Создание директории проекта..."
ssh $SERVER "mkdir -p $PROJECT_DIR"

echo "📤 Копирование файлов..."
# Исключаем .env, __pycache__, локальную БД
rsync -avz --exclude='.env' --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv' --exclude='todo.db' --exclude='static/lib/' \
    ./ $SERVER:$PROJECT_DIR/

echo ""
echo "📦 Скачивание CDN файлов на сервере..."
ssh $SERVER "mkdir -p $PROJECT_DIR/static/lib && \
    cd $PROJECT_DIR/static/lib && \
    curl -sL https://unpkg.com/redoc@2.1.3/bundles/redoc.standalone.js -o redoc.standalone.js && \
    curl -sL https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js -o swagger-ui-bundle.js && \
    curl -sL https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui.css -o swagger-ui.css && \
    echo '✅ CDN файлы скачены'"

echo ""
echo "🔧 Создание .env файла..."
JWT_SECRET=$(openssl rand -hex 32)
ssh $SERVER "cat > $PROJECT_DIR/.env << EOF
APP_NAME=Todo API
APP_VERSION=1.0.0
DEBUG=False

DB_HOST=db
DB_PORT=5432
DB_NAME=todo_db
DB_USER=todo_user
DB_PASSWORD=todo_secret

JWT_SECRET=$JWT_SECRET
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
EOF"

echo ""
echo "🛑 Остановка старых контейнеров..."
ssh $SERVER "cd $PROJECT_DIR && docker compose down || true"

echo ""
echo "🚀 Запуск контейнеров..."
ssh $SERVER "cd $PROJECT_DIR && docker compose up -d --build"

echo ""
echo "⏳ Ожидание запуска (15 сек)..."
sleep 15

# Проверка API
echo "🔍 Проверка API..."
HTTP_STATUS=$(ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/docs" 2>/dev/null || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Деплой успешен!"
    echo ""
    echo "📚 Ссылки:"
    echo "   Swagger UI: http://109.73.201.197:8000/docs"
    echo "   ReDoc: http://109.73.201.197:8000/redoc"
    echo "   UI: http://109.73.201.197:8000"
    echo "   SQL примеры: http://109.73.201.197:8000/docs-files/sql-examples.md"
    echo ""
    echo "📝 Логи:"
    echo "   ssh $SERVER 'cd $PROJECT_DIR && docker compose logs -f'"
else
    echo "⚠️  Возможно, API не запустился корректно (HTTP $HTTP_STATUS)"
    echo ""
    echo "Проверьте логи:"
    echo "   ssh $SERVER 'cd $PROJECT_DIR && docker compose logs'"
fi

echo ""
echo "🎉 Готово!"
