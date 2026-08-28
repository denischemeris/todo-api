#!/usr/bin/env bash
# Деплой Todo API на сервере. Запускается из GitHub Actions по ssh,
# либо руками: ssh root@109.73.201.197 "bash /opt/todo-api/scripts/deploy-on-server.sh"
#
# Что скрипт НЕ трогает (эти файлы лежат только на сервере и не в репозитории):
#   .env, .env.production, docker-compose.prod.yml, static/lib/

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/opt/todo-api}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/openapi.json}"

cd "$PROJECT_DIR"

echo "==> Текущий коммит: $(git rev-parse --short HEAD)"

echo "==> Забираем master из GitHub"
git fetch --quiet origin master
git reset --hard origin/master
echo "==> Новый коммит:   $(git rev-parse --short HEAD)"

# Swagger UI и ReDoc отдаются с локальных файлов, в репозитории их нет
# (static/lib в .gitignore). Dockerfile копирует static/ в образ, поэтому
# без этих файлов страница /docs соберётся пустой.
echo "==> Проверяем статические библиотеки"
mkdir -p static/lib
download_if_missing() {
    local file="$1" url="$2"
    if [ ! -s "static/lib/$file" ]; then
        echo "    качаем $file"
        curl -sfL "$url" -o "static/lib/$file"
    fi
}
download_if_missing redoc.standalone.js   https://unpkg.com/redoc@2.1.3/bundles/redoc.standalone.js
download_if_missing swagger-ui-bundle.js  https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js
download_if_missing swagger-ui.css        https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui.css

echo "==> Сборка и запуск контейнера"
docker compose -f "$COMPOSE_FILE" up -d --build

echo "==> Ждём готовности приложения"
ok=""
for i in $(seq 1 30); do
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$HEALTH_URL" || echo 000)
    if [ "$code" = "200" ]; then
        ok="yes"
        echo "    поднялось за $i попыток"
        break
    fi
    sleep 2
done

if [ -z "$ok" ]; then
    echo "ОШИБКА: приложение не отвечает на $HEALTH_URL"
    echo "--- логи контейнера ---"
    docker compose -f "$COMPOSE_FILE" logs --tail 40
    exit 1
fi

# Контракт мог собраться, но приложение всё равно быть сломанным изнутри,
# поэтому проверяем и живой запрос: без токена обязан быть 401, а не 403 и не 500.
echo "==> Проверка контракта"
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:8000/api/v1/todos || echo 000)
if [ "$code" != "401" ]; then
    echo "ОШИБКА: GET /api/v1/todos без токена вернул $code, ожидали 401"
    docker compose -f "$COMPOSE_FILE" logs --tail 40
    exit 1
fi
echo "    GET /api/v1/todos без токена -> 401, как и должно быть"

echo "==> Готово: $(git rev-parse --short HEAD) выкачен"
