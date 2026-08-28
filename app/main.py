from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from contextlib import asynccontextmanager
import os

from app.database import engine, Base, create_tables
from app.routers.auth import router as auth_router
from app.routers.todos import router as todos_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Создание таблиц при запуске (для разработки)"""
    await create_tables()
    yield


app = FastAPI(
    title="Todo API",
    description="""
## Учебный REST API для изучения работы с задачами

Этот проект демонстрирует:
- **CRUD операции** с задачами
- **JWT авторизацию** 
- **Фильтрацию, сортировку и пагинацию** на уровне SQL
- **Swagger/OpenAPI документацию**

### Примеры SQL запросов

Все запросы с фильтрацией, сортировкой и пагинацией используют эффективные SQL паттерны:
- `LIMIT/OFFSET` для пагинации
- `WHERE` для фильтрации
- `ORDER BY` с `CASE` для кастомной сортировки
- `ILIKE` для полнотекстового поиска
- `COUNT(*) OVER()` для оконных функций

Смотрите документацию в `/docs` или `/redoc`.

### Версионирование

Актуальный префикс: `/api/v1/...`. Версия стоит в начале пути, чтобы несовместимые
изменения можно было выпустить как `/api/v2`, не ломая существующих клиентов.

Старые пути без версии (`/api/todos`, `/api/auth`) продолжают работать ради
совместимости, но считаются устаревшими и в документации не показываются.

### PUT и PATCH

- `PUT /api/v1/todos/{todo_id}` — полная замена: передаются **все** поля задачи.
  Непереданное поле не сохраняет прежнее значение, а даёт ошибку 422.
- `PATCH /api/v1/todos/{todo_id}` — частичное обновление: передаются только
  изменяемые поля, остальные сохраняют текущее значение.

### Коды ответов

У каждого метода описаны не только успешные, но и ошибочные сценарии: 400, 401,
404, 422. Чужая задача возвращает 404, а не 403: существование чужих данных
наружу не раскрывается.
""",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,  # Отключаем встроенный docs
    redoc_url=None  # Отключаем встроенный redoc
)

# Подключение роутеров
# Актуальная версия API: версия стоит в начале пути, чтобы будущие несовместимые
# изменения можно было выпустить как /api/v2, не ломая существующих клиентов.
app.include_router(auth_router, prefix="/api/v1")
app.include_router(todos_router, prefix="/api/v1")

# Совместимость: старые пути без версии продолжают работать, но в документацию
# не попадают и считаются устаревшими. Новый код должен использовать /api/v1.
app.include_router(auth_router, prefix="/api", include_in_schema=False)
app.include_router(todos_router, prefix="/api", include_in_schema=False)

# Статические файлы (UI)
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Документация (docs/)
docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")
if os.path.exists(docs_dir):
    app.mount("/docs-files", StaticFiles(directory=docs_dir), name="docs")


@app.get("/", include_in_schema=False)
async def serve_index():
    """Главная страница (логин/регистрация)"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Todo API - смотри документацию /docs"}


@app.get("/dashboard", include_in_schema=False)
async def serve_dashboard():
    """Дашборд задач"""
    dashboard_path = os.path.join(static_dir, "dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    return {"message": "Dashboard not found"}


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    """Кастомный Swagger UI с локальными файлами"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Todo API - Swagger UI</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" type="text/css" href="/static/lib/swagger-ui.css">
        <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="/static/lib/swagger-ui-bundle.js"></script>
        <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: '/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [SwaggerUIBundle.presets.apis],
                layout: "BaseLayout"
            })
            window.ui = ui
        }
        </script>
    </body>
    </html>
    """)


@app.get("/redoc", include_in_schema=False)
async def custom_redoc():
    """Кастомный ReDoc с локальными файлами"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Todo API - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
        <style>body { margin: 0; padding: 0; }</style>
    </head>
    <body>
        <redoc spec-url="/openapi.json"></redoc>
        <script src="/static/lib/redoc.standalone.js"></script>
    </body>
    </html>
    """)
