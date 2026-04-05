from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.todo_models import User
from app.schemas.todo_schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from app.security import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Авторизация"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создает нового пользователя и возвращает его данные"
)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Регистрация нового пользователя.
    
    - **username**: имя пользователя (3-50 символов)
    - **email**: электронная почта
    - **password**: пароль (минимум 6 символов)
    """
    # Проверка на существующий email
    existing_user = await db.execute(select(User).where(User.email == user_data.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    # Проверка на существующий username
    existing_username = await db.execute(select(User).where(User.username == user_data.username))
    if existing_username.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Такое имя пользователя уже занято"
        )
    
    # Создание пользователя
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )
    
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    
    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход в систему",
    description="Аутентифицирует пользователя и возвращает JWT токен"
)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Вход в систему.
    
    - **email**: электронная почта
    - **password**: пароль
    
    Возвращает JWT токен для последующей авторизации запросов.
    """
    # Поиск пользователя
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    # Создание токена
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Текущий пользователь",
    description="Возвращает данные текущего авторизованного пользователя"
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Получение данных текущего пользователя.
    
    Требует валидный JWT токен в заголовке Authorization.
    """
    return current_user
