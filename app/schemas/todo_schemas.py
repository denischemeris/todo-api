from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# === User Schemas ===

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["johndoe"])
    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=6, max_length=100, examples=["securepass123"])


class UserLogin(BaseModel):
    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., examples=["securepass123"])


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# === Todo Schemas ===

class PriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StatusEnum(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, examples=["Срочная задача"])
    description: Optional[str] = Field(None, max_length=1000, examples=["Описание задачи"])
    priority: PriorityEnum = PriorityEnum.MEDIUM


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[StatusEnum] = None
    priority: Optional[PriorityEnum] = None


class TodoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: StatusEnum
    priority: PriorityEnum
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TodoListResponse(BaseModel):
    """Ответ с пагинацией для списка задач"""
    items: list[TodoResponse]
    total: int
    page: int
    page_size: int
    pages: int


class TodoSortParams(BaseModel):
    """Параметры сортировки"""
    sort_by: str = Field(default="created_at", pattern="^(title|priority|created_at|updated_at|status)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class TodoFilterParams(BaseModel):
    """Параметры фильтрации и пагинации"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    status: Optional[StatusEnum] = None
    priority: Optional[PriorityEnum] = None
    search: Optional[str] = Field(None, max_length=200)
    sort_by: str = Field(default="created_at", pattern="^(title|priority|created_at|updated_at|status)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
