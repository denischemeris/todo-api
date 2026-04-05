# Todo API — Учебный REST API

Полноценный REST API для управления задачами с JWT авторизацией, фильтрацией, сортировкой, пагинацией и минималистичным веб-интерфейсом.

## 🎯 Цель проекта

Этот проект создан для изучения:
- **REST API** принципов и лучших практик
- **JWT авторизации** и защиты эндпоинтов
- **Работы с PostgreSQL** через SQLAlchemy ORM
- **Фильтрации, сортировки и пагинации** на уровне SQL
- **Swagger/OpenAPI** документации
- **Docker** контейнеризации

## 🛠 Стек технологий

- **Backend:** Python 3.12 + FastAPI
- **База данных:** PostgreSQL 16
- **ORM:** SQLAlchemy (async)
- **Авторизация:** JWT (python-jose)
- **UI:** HTML + CSS + Vanilla JavaScript
- **Документация:** Swagger UI + ReDoc
- **Деплой:** Docker + docker-compose

## 📁 Структура проекта

```
todo-api/
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── config.py            # Настройки (env vars)
│   ├── database.py          # Подключение к БД
│   ├── security.py          # JWT логика
│   ├── models/              # SQLAlchemy модели
│   │   └── todo_models.py   # User и Todo модели
│   ├── schemas/             # Pydantic схемы
│   │   └── todo_schemas.py  # Схемы запросов/ответов
│   └── routers/             # Роутеры (эндпоинты)
│       ├── auth.py          # Авторизация
│       └── todos.py         # CRUD задач
├── static/                  # Веб-интерфейс
│   ├── index.html           # Страница входа/регистрации
│   ├── dashboard.html       # Дашборд задач
│   ├── css/style.css        # Стили
│   └── js/app.js            # Логика UI
├── docs/
│   └── sql-examples.md      # Примеры SQL запросов для студентов
├── Dockerfile               # Docker образ приложения
├── docker-compose.yml       # Контейнеры app + db
├── requirements.txt         # Python зависимости
└── README.md                # Этот файл
```

## 🚀 Быстрый старт

### 1. Запуск через Docker

```bash
# Клонировать репозиторий
git clone <your-repo-url>
cd todo-api

# Запустить контейнеры
docker-compose up -d

# Приложение доступно на http://localhost:8000
```

### 2. Проверка работы

Откройте в браузере:
- **Главная:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### 3. Остановка

```bash
docker-compose down
```

## 📚 Документация API

### Авторизация

#### Регистрация
```bash
POST /api/auth/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepass123"
}
```

#### Вход
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "securepass123"
}

# Ответ:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### Текущий пользователь
```bash
GET /api/auth/me
Authorization: Bearer <token>
```

### Задачи (CRUD)

#### Список задач (с фильтрацией, сортировкой, пагинацией)

```bash
GET /api/todos?page=1&page_size=10&status=in_progress&priority=high&search=отчет&sort_by=created_at&sort_order=desc
Authorization: Bearer <token>
```

**Параметры:**
- `page` (int) — номер страницы (по умолчанию: 1)
- `page_size` (int) — размер страницы (по умолчанию: 10, макс: 100)
- `status` (string) — фильтр по статусу: `new`, `in_progress`, `done`, `cancelled`
- `priority` (string) — фильтр по приоритету: `low`, `medium`, `high`
- `search` (string) — поиск по названию/описанию
- `sort_by` (string) — поле сортировки: `title`, `priority`, `created_at`, `updated_at`, `status`
- `sort_order` (string) — направление: `asc`, `desc`

**Ответ:**
```json
{
  "items": [...],
  "total": 157,
  "page": 1,
  "page_size": 10,
  "pages": 16
}
```

#### Создать задачу
```bash
POST /api/todos
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Новая задача",
  "description": "Описание задачи",
  "priority": "high"
}
```

#### Получить задачу
```bash
GET /api/todos/{id}
Authorization: Bearer <token>
```

#### Обновить задачу
```bash
PUT /api/todos/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Обновленное название",
  "status": "done",
  "priority": "low"
}
```

#### Удалить задачу
```bash
DELETE /api/todos/{id}
Authorization: Bearer <token>
```

## 🗄 Структура базы данных

### Таблица `users`
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Таблица `todos`
```sql
CREATE TABLE todos (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description VARCHAR(1000),
    status VARCHAR(20) NOT NULL DEFAULT 'new',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_todos_owner_id ON todos(owner_id);
CREATE INDEX idx_todos_status ON todos(status);
CREATE INDEX idx_todos_priority ON todos(priority);
CREATE INDEX idx_todos_created_at ON todos(created_at);
```

## 💡 SQL примеры

Подробные примеры SQL запросов с объяснениями смотрите в **[docs/sql-examples.md](docs/sql-examples.md)**.

### Пример: пагинация + фильтрация + сортировка

```sql
-- GET /api/todos?page=2&page_size=10&status=in_progress&priority=high
SELECT id, title, description, status, priority, owner_id, created_at, updated_at
FROM todos
WHERE owner_id = 1
  AND status = 'in_progress'
  AND priority = 'high'
ORDER BY created_at DESC
LIMIT 10 OFFSET 10;  -- (page-1) * page_size

-- Общее количество для пагинации
SELECT COUNT(*) FROM todos 
WHERE owner_id = 1 
  AND status = 'in_progress' 
  AND priority = 'high';
```

### Пример: кастомная сортировка по приоритету

```sql
-- GET /api/todos?sort_by=priority&sort_order=desc
SELECT id, title, status, priority, created_at
FROM todos
WHERE owner_id = 1
ORDER BY 
  CASE priority
    WHEN 'high' THEN 1
    WHEN 'medium' THEN 2
    WHEN 'low' THEN 3
  END DESC,
  created_at DESC
LIMIT 10 OFFSET 0;
```

## 🎓 Пошаговый сценарий для студентов

### Шаг 1: Регистрация
1. Откройте http://localhost:8000
2. Нажмите "Зарегистрироваться"
3. Введите имя, email и пароль
4. Нажмите "Зарегистрироваться"

### Шаг 2: Вход
1. Введите email и пароль
2. Нажмите "Войти"
3. Вы будете перенаправлены на дашборд

### Шаг 3: Создание задачи
1. Нажмите "+ Создать задачу"
2. Введите название и описание
3. Выберите приоритет
4. Нажмите "Сохранить"

### Шаг 4: Фильтрация и поиск
1. Используйте фильтры по статусу и приоритету
2. Введите текст в поле поиска
3. Измените сортировку

### Шаг 5: Редактирование и удаление
1. Нажмите "✏️ Изменить" на задаче
2. Измените данные
3. Нажмите "Сохранить"
4. Для удаления нажмите "🗑️ Удалить"

### Шаг 6: Изучение API через Swagger
1. Откройте http://localhost:8000/docs
2. Авторизуйтесь через кнопку "Authorize"
3. Попробуйте все эндпоинты

## 🔐 Безопасность

- Пароли хешируются через **bcrypt**
- JWT токены с сроком жизни 24 часа
- Каждый пользователь видит только свои задачи
- Проверка владельца при обновлении/удалении

## 🐛 Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```env
# Application
APP_NAME=Todo API
APP_VERSION=1.0.0
DEBUG=True

# Database
DB_HOST=db
DB_PORT=5432
DB_NAME=todo_db
DB_USER=todo_user
DB_PASSWORD=todo_secret

# JWT
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
```

## 📦 Локальная разработка (без Docker)

```bash
# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt

# Запустить PostgreSQL (локально или в Docker)
docker run -d --name todo-db \
  -e POSTGRES_DB=todo_db \
  -e POSTGRES_USER=todo_user \
  -e POSTGRES_PASSWORD=todo_secret \
  -p 5432:5432 \
  postgres:16-alpine

# Создать .env файл
cp .env.example .env

# Запустить приложение
uvicorn app.main:app --reload
```

## 🚀 Деплой на сервер

```bash
# На сервере (Ubuntu)
cd /opt
git clone <your-repo> todo-api
cd todo-api

# Создать .env
cat > .env << EOF
DB_HOST=db
DB_PORT=5432
DB_NAME=todo_db
DB_USER=todo_user
DB_PASSWORD=todo_secret
JWT_SECRET=$(openssl rand -hex 32)
EOF

# Запустить
docker-compose up -d

# Проверить
curl http://localhost:8000/docs
```

### Настройка Nginx (опционально)

```nginx
server {
    listen 80;
    server_name todo.denischemeris.ru;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🧪 Тестирование

```bash
# Регистрация
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"test123"}'

# Вход
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Создать задачу (с токеном)
curl -X POST http://localhost:8000/api/todos \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Тестовая задача","priority":"high"}'

# Список задач
curl -X GET "http://localhost:8000/api/todos?page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

## 📝 Примеры SQL запросов

Все SQL примеры с подробными объяснениями находятся в **[docs/sql-examples.md](docs/sql-examples.md)**:

1. Базовая пагинация (LIMIT/OFFSET)
2. Фильтрация по статусу и приоритету
3. Полнотекстовый поиск (ILIKE)
4. Кастомная сортировка (CASE)
5. Оконные функции (COUNT OVER)
6. JOIN с таблицей пользователей
7. Агрегация и группировка
8. Индексы для оптимизации

## 🤝 Вклад

1. Fork репозиторий
2. Создайте ветку (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

MIT License — используйте для обучения!

## 📞 Поддержка

Если возникли вопросы:
- Откройте Issue в репозитории
- Посмотрите документацию: http://localhost:8000/docs
- Изучите SQL примеры: [docs/sql-examples.md](docs/sql-examples.md)
