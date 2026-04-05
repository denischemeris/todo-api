# SQL примеры для изучения

Этот документ показывает SQL запросы, которые соответствуют эндпоинтам API.

## Структура таблиц

### Таблица `users`
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
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

---

## 1. Базовая пагинация (LIMIT/OFFSET)

### Запрос API:
```
GET /api/todos?page=2&page_size=10
```

### SQL запрос:
```sql
-- Получение задач пользователя с пагинацией
SELECT id, title, description, status, priority, owner_id, created_at, updated_at
FROM todos
WHERE owner_id = 1
ORDER BY created_at DESC
LIMIT 10 OFFSET 10;  -- page=2, page_size=10 → OFFSET = (page-1) * page_size

-- Получение общего количества для пагинации
SELECT COUNT(*) 
FROM todos 
WHERE owner_id = 1;
```

### Объяснение:
- `LIMIT 10` — ограничивает количество строк до 10 на странице
- `OFFSET 10` — пропускает первые 10 строк (для страницы 2)
- Формула: `OFFSET = (page - 1) * page_size`
- `COUNT(*)` нужен для расчета общего количества страниц

---

## 2. Фильтрация по статусу и приоритету

### Запрос API:
```
GET /api/todos?status=in_progress&priority=high
```

### SQL запрос:
```sql
SELECT id, title, description, status, priority, owner_id, created_at, updated_at
FROM todos
WHERE owner_id = 1
  AND status = 'in_progress'
  AND priority = 'high'
ORDER BY created_at DESC
LIMIT 10 OFFSET 0;

-- Общее количество с фильтрами
SELECT COUNT(*) 
FROM todos 
WHERE owner_id = 1 
  AND status = 'in_progress' 
  AND priority = 'high';
```

### Объяснение:
- `WHERE` с несколькими условиями через `AND`
- Все условия применяются одновременно
- Индексы на `status` и `priority` ускоряют запрос

---

## 3. Полнотекстовый поиск (ILIKE)

### Запрос API:
```
GET /api/todos?search=срочный
```

### SQL запрос:
```sql
SELECT id, title, description, status, priority, owner_id, created_at, updated_at
FROM todos
WHERE owner_id = 1
  AND (
    title ILIKE '%срочный%' 
    OR description ILIKE '%срочный%'
  )
ORDER BY created_at DESC
LIMIT 10 OFFSET 0;

-- Общее количество
SELECT COUNT(*) 
FROM todos 
WHERE owner_id = 1 
  AND (
    title ILIKE '%срочный%' 
    OR description ILIKE '%срочный%'
  );
```

### Объяснение:
- `ILIKE` — регистронезависимый поиск (в отличие от `LIKE`)
- `%` — wildcard (любое количество символов)
- `OR` — поиск в обоих полях
- **Внимание**: `ILIKE '%...%'` не использует индексы, медленный на больших данных
- Для production лучше использовать `tsvector` и полнотекстовый поиск PostgreSQL

---

## 4. Кастомная сортировка по приоритету (CASE)

### Запрос API:
```
GET /api/todos?sort_by=priority&sort_order=desc
```

### SQL запрос:
```sql
SELECT id, title, description, status, priority, owner_id, created_at, updated_at
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

### Объяснение:
- `CASE` создает виртуальное поле для сортировки
- `high` → 1, `medium` → 2, `low` → 3
- `DESC` сортирует от 1 к 3 (high сначала)
- Второе поле `created_at` — вторичная сортировка

---

## 5. Множественная фильтрация и сортировка

### Запрос API:
```
GET /api/todos?status=new&status=in_progress&sort_by=created_at&sort_order=asc
```

### SQL запрос:
```sql
SELECT id, title, description, status, priority, owner_id, created_at, updated_at
FROM todos
WHERE owner_id = 1
  AND status IN ('new', 'in_progress')
ORDER BY created_at ASC
LIMIT 20 OFFSET 0;
```

### Объяснение:
- `IN` — фильтрация по нескольким значениям
- `ASC` — сортировка от старых к новым

---

## 6. Оконные функции (продвинутый уровень)

### Запрос API:
```
GET /api/todos?page=1&page_size=10
```

### SQL с оконной функцией:
```sql
SELECT 
  id, 
  title, 
  description, 
  status, 
  priority, 
  owner_id, 
  created_at, 
  updated_at,
  COUNT(*) OVER() as total_count
FROM todos
WHERE owner_id = 1
  AND status = 'in_progress'
ORDER BY created_at DESC
LIMIT 10 OFFSET 0;
```

### Объяснение:
- `COUNT(*) OVER()` — оконная функция, возвращает общее количество строк **без** LIMIT
- Каждый ряд содержит `total_count` — не нужен отдельный COUNT запрос
- **Плюс**: один запрос вместо двух
- **Минус**: может быть медленнее на больших данных

---

## 7. Создание задачи (INSERT)

### Запрос API:
```
POST /api/todos
{
  "title": "Новая задача",
  "description": "Описание",
  "priority": "high"
}
```

### SQL запрос:
```sql
INSERT INTO todos (title, description, priority, owner_id, status)
VALUES ('Новая задача', 'Описание', 'high', 1, 'new')
RETURNING id, title, description, status, priority, owner_id, created_at, updated_at;
```

### Объяснение:
- `RETURNING` — возвращает созданную запись
- `status` по умолчанию `'new'`
- `created_at` и `updated_at` устанавливаются автоматически через `DEFAULT NOW()`

---

## 8. Обновление задачи (UPDATE)

### Запрос API:
```
PUT /api/todos/42
{
  "status": "done",
  "priority": "low"
}
```

### SQL запрос:
```sql
UPDATE todos
SET 
  status = 'done',
  priority = 'low',
  updated_at = NOW()
WHERE id = 42 AND owner_id = 1
RETURNING id, title, description, status, priority, owner_id, created_at, updated_at;
```

### Объяснение:
- `WHERE id = 42 AND owner_id = 1` — проверка владельца (безопасность)
- `updated_at = NOW()` — обновление времени изменения
- `RETURNING` — возвращает обновленную запись

---

## 9. Удаление задачи (DELETE)

### Запрос API:
```
DELETE /api/todos/42
```

### SQL запрос:
```sql
DELETE FROM todos
WHERE id = 42 AND owner_id = 1
RETURNING id;
```

### Объяснение:
- `WHERE id = 42 AND owner_id = 1` — проверка владельца
- Если задача чужая — вернется 0 строк (эквивалент 404)

---

## 10. JOIN с таблицей пользователей

### Запрос API:
```
GET /api/todos (включая информацию о владельце)
```

### SQL запрос:
```sql
SELECT 
  t.id, 
  t.title, 
  t.status, 
  t.priority,
  t.created_at,
  u.username as owner_username,
  u.email as owner_email
FROM todos t
INNER JOIN users u ON t.owner_id = u.id
WHERE t.owner_id = 1
ORDER BY t.created_at DESC
LIMIT 10;
```

### Объяснение:
- `INNER JOIN` — связывает задачи с пользователями
- `t` и `u` — алиасы таблиц
- Полезно для админ-панелей

---

## 11. Агрегация и группировка

### Пример: статистика по задачам

### SQL запрос:
```sql
SELECT 
  status,
  COUNT(*) as count,
  MIN(created_at) as first_task,
  MAX(created_at) as last_task
FROM todos
WHERE owner_id = 1
GROUP BY status
ORDER BY count DESC;
```

### Результат:
```
status      | count | first_task           | last_task
------------|-------|----------------------|----------------------
in_progress | 15    | 2024-01-15 10:30:00  | 2024-03-20 14:20:00
done        | 42    | 2024-01-10 09:00:00  | 2024-03-19 16:45:00
new         | 8     | 2024-02-01 11:00:00  | 2024-03-18 08:30:00
```

---

## 12. Индексы для оптимизации

### Создание индексов:
```sql
-- Базовые индексы (уже есть в модели)
CREATE INDEX idx_todos_owner_id ON todos(owner_id);
CREATE INDEX idx_todos_status ON todos(status);
CREATE INDEX idx_todos_priority ON todos(priority);
CREATE INDEX idx_todos_created_at ON todos(created_at);

-- Составной индекс для частых запросов
CREATE INDEX idx_todos_owner_status ON todos(owner_id, status);

-- Индекс для полнотекстового поиска
CREATE INDEX idx_todos_title_search ON todos USING gin(to_tsvector('russian', title));
```

### Объяснение:
- Индексы ускоряют `WHERE`, `ORDER BY`, `JOIN`
- Составные индексы работают для нескольких полей
-GIN индекс для полнотекстового поиска

---

## Практическое задание для студентов

1. **Напишите SQL запрос** для получения всех задач пользователя со статусом `done`, отсортированных по дате создания (новые сначала), страница 3, по 20 задач на странице.

2. **Создайте запрос** для поиска задач, содержащих слово "отчет" в названии или описании, с приоритетом `high`.

3. **Напишите агрегирующий запрос** для подсчета количества задач по каждому приоритету.

4. **Оптимизируйте запрос** с `ILIKE` используя полнотекстовый поиск PostgreSQL.

### Ответы:

<details>
<summary>Задание 1</summary>

```sql
SELECT id, title, description, status, priority, owner_id, created_at, updated_at
FROM todos
WHERE owner_id = 1 AND status = 'done'
ORDER BY created_at DESC
LIMIT 20 OFFSET 40;  -- page=3, page_size=20 → OFFSET = (3-1)*20 = 40
```
</details>

<details>
<summary>Задание 2</summary>

```sql
SELECT id, title, description, status, priority, owner_id, created_at, updated_at
FROM todos
WHERE owner_id = 1
  AND priority = 'high'
  AND (title ILIKE '%отчет%' OR description ILIKE '%отчет%')
ORDER BY created_at DESC;
```
</details>

<details>
<summary>Задание 3</summary>

```sql
SELECT 
  priority,
  COUNT(*) as count
FROM todos
WHERE owner_id = 1
GROUP BY priority
ORDER BY count DESC;
```
</details>

<details>
<summary>Задание 4</summary>

```sql
-- Создание индекса
CREATE INDEX idx_todos_search ON todos USING gin(to_tsvector('russian', title || ' ' || description));

-- Запрос с полнотекстовым поиском
SELECT id, title, description, status, priority, owner_id, created_at, updated_at
FROM todos
WHERE owner_id = 1
  AND to_tsvector('russian', title || ' ' || description) @@ to_tsquery('russian', 'отчет')
ORDER BY created_at DESC;
```
</details>
