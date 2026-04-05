from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
import math

from app.database import get_db
from app.models.todo_models import Todo, User, PriorityEnum, StatusEnum
from app.schemas.todo_schemas import (
    TodoCreate, TodoUpdate, TodoResponse, TodoListResponse
)
from app.security import get_current_user

router = APIRouter(prefix="/api/todos", tags=["Задачи"])


@router.get(
    "",
    response_model=TodoListResponse,
    summary="Список задач с фильтрацией, сортировкой и пагинацией",
    description="""
    Возвращает список задач текущего пользователя с возможностями:
    
    - **Пагинация**: page (номер страницы), page_size (размер страницы, макс 100)
    - **Фильтрация**: status (статус), priority (приоритет), search (поиск по названию/описанию)
    - **Сортировка**: sort_by (поле), sort_order (направление)
    
    **Пример SQL запроса:**
    ```sql
    SELECT id, title, description, status, priority, owner_id, created_at, updated_at
    FROM todos
    WHERE owner_id = 1
      AND status = 'in_progress'
      AND priority = 'high'
      AND (title ILIKE '%срочный%' OR description ILIKE '%срочный%')
    ORDER BY created_at DESC
    LIMIT 10 OFFSET 0;
    ```
    """
)
async def get_todos(
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    page_size: int = Query(default=10, ge=1, le=100, description="Размер страницы (макс 100)"),
    status_filter: Optional[StatusEnum] = Query(default=None, alias="status", description="Фильтр по статусу"),
    priority: Optional[PriorityEnum] = Query(default=None, description="Фильтр по приоритету"),
    search: Optional[str] = Query(default=None, max_length=200, description="Поиск по названию/описанию"),
    sort_by: str = Query(default="created_at", pattern="^(title|priority|created_at|updated_at|status)$", description="Поле сортировки"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$", description="Направление сортировки"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получение списка задач текущего пользователя.
    
    - **page**: номер страницы (начиная с 1)
    - **page_size**: количество задач на странице (1-100)
    - **status**: фильтр по статусу (new, in_progress, done, cancelled)
    - **priority**: фильтр по приоритету (low, medium, high)
    - **search**: поиск по названию или описанию
    - **sort_by**: поле сортировки (title, priority, created_at, updated_at, status)
    - **sort_order**: направление (asc, desc)
    """
    # Базовый запрос
    query = select(Todo).where(Todo.owner_id == current_user.id)
    count_query = select(func.count()).select_from(Todo).where(Todo.owner_id == current_user.id)
    
    # Применение фильтров
    if status_filter:
        query = query.where(Todo.status == status_filter)
        count_query = count_query.where(Todo.status == status_filter)
    
    if priority:
        query = query.where(Todo.priority == priority)
        count_query = count_query.where(Todo.priority == priority)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Todo.title.ilike(search_pattern),
                Todo.description.ilike(search_pattern)
            )
        )
        count_query = count_query.where(
            or_(
                Todo.title.ilike(search_pattern),
                Todo.description.ilike(search_pattern)
            )
        )
    
    # Сортировка
    # Для priority используем кастомный порядок
    if sort_by == "priority":
        from sqlalchemy import case
        priority_order = case(
            (Todo.priority == "high", 1),
            (Todo.priority == "medium", 2),
            (Todo.priority == "low", 3),
        )
        order_clause = priority_order.desc() if sort_order == "desc" else priority_order.asc()
    else:
        column = getattr(Todo, sort_by)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
    
    query = query.order_by(order_clause)
    
    # Пагинация
    offset = (page - 1) * page_size
    query = query.limit(page_size).offset(offset)
    
    # Выполнение запросов
    result = await db.execute(query)
    todos = result.scalars().all()
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Расчет количества страниц
    pages = math.ceil(total / page_size) if total > 0 else 0
    
    return {
        "items": todos,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }


@router.get(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="Получить задачу по ID",
    description="Возвращает конкретную задачу по её ID"
)
async def get_todo(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получение отдельной задачи.
    
    - **todo_id**: ID задачи
    """
    result = await db.execute(
        select(Todo).where(Todo.id == todo_id, Todo.owner_id == current_user.id)
    )
    todo = result.scalar_one_or_none()
    
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )
    
    return todo


@router.post(
    "",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую задачу",
    description="Создает новую задачу для текущего пользователя"
)
async def create_todo(
    todo_data: TodoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создание новой задачи.
    
    - **title**: название задачи (обязательно)
    - **description**: описание задачи (опционально)
    - **priority**: приоритет (low, medium, high)
    """
    new_todo = Todo(
        title=todo_data.title,
        description=todo_data.description,
        priority=todo_data.priority,
        owner_id=current_user.id
    )
    
    db.add(new_todo)
    await db.flush()
    await db.refresh(new_todo)
    
    return new_todo


@router.put(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="Обновить задачу",
    description="Обновляет данные задачи (только для владельца)"
)
async def update_todo(
    todo_id: int,
    todo_data: TodoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновление задачи.
    
    - **todo_id**: ID задачи
    - **title**: новое название
    - **description**: новое описание
    - **status**: новый статус
    - **priority**: новый приоритет
    """
    result = await db.execute(
        select(Todo).where(Todo.id == todo_id, Todo.owner_id == current_user.id)
    )
    todo = result.scalar_one_or_none()
    
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )
    
    # Обновление полей
    update_data = todo_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)
    
    todo.updated_at = datetime.utcnow()
    
    await db.flush()
    await db.refresh(todo)
    
    return todo


@router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить задачу",
    description="Удаляет задачу (только для владельца)"
)
async def delete_todo(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удаление задачи.
    
    - **todo_id**: ID задачи
    """
    result = await db.execute(
        select(Todo).where(Todo.id == todo_id, Todo.owner_id == current_user.id)
    )
    todo = result.scalar_one_or_none()
    
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )
    
    await db.delete(todo)
    await db.flush()
    
    return None
