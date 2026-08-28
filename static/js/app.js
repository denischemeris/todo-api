// === Утилиты ===
function formatApiError(payload, fallback) {
    const detail = payload && payload.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        const parts = detail.map(function (item) {
            const loc = Array.isArray(item.loc) ? item.loc : [];
            const field = loc[loc.length - 1];
            return field && field !== 'body' ? field + ': ' + item.msg : item.msg;
        });
        if (parts.length) return parts.join('; ');
    }
    return fallback;
}

// === Global State ===
const API_URL = window.location.origin;
let currentPage = 1;
let currentPageSize = 10;
let searchTimeout = null;

// === Auth ===
function getToken() {
    return localStorage.getItem('token');
}

async function checkAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = '/';
        return null;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/v1/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            localStorage.removeItem('token');
            window.location.href = '/';
            return null;
        }
        
        const user = await response.json();
        document.getElementById('user-info').textContent = `👤 ${user.username}`;
        return user;
        
    } catch (error) {
        console.error('Auth error:', error);
        localStorage.removeItem('token');
        window.location.href = '/';
        return null;
    }
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = '/';
}

// === Toast Messages ===
function showToast(message, type = 'info') {
    const toast = document.getElementById('message');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.style.display = 'block';
    
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

// === Load Todos ===
async function loadTodos() {
    const token = getToken();
    const todosList = document.getElementById('todos-list');
    
    // Показываем загрузку
    todosList.innerHTML = '<div class="loading">Загрузка задач</div>';
    
    // Собираем параметры
    const status = document.getElementById('filter-status').value;
    const priority = document.getElementById('filter-priority').value;
    const search = document.getElementById('search-input').value;
    const sortValue = document.getElementById('sort-select').value;
    const [sortBy, sortOrder] = sortValue.split('-');
    
    // Формируем URL
    const params = new URLSearchParams({
        page: currentPage,
        page_size: currentPageSize
    });
    
    if (status) params.append('status', status);
    if (priority) params.append('priority', priority);
    if (search) params.append('search', search);
    params.append('sort_by', sortBy);
    params.append('sort_order', sortOrder);
    
    try {
        const response = await fetch(`${API_URL}/api/v1/todos?${params}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            throw new Error('Ошибка загрузки');
        }
        
        const data = await response.json();
        renderTodos(data);
        
    } catch (error) {
        console.error('Load error:', error);
        todosList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">❌</div>
                <h3>Ошибка загрузки</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// === Render Todos ===
function renderTodos(data) {
    const todosList = document.getElementById('todos-list');
    const pagination = document.getElementById('pagination');
    
    if (data.items.length === 0) {
        todosList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <h3>Задач пока нет</h3>
                <p>Создайте первую задачу!</p>
            </div>
        `;
        pagination.style.display = 'none';
        return;
    }
    
    // Рендерим карточки
    todosList.innerHTML = data.items.map(todo => `
        <div class="todo-card priority-${todo.priority}">
            <div class="todo-header">
                <div class="todo-title">${escapeHtml(todo.title)}</div>
                <div class="todo-actions">
                    <button onclick="openEditModal(${todo.id})" class="btn btn-secondary btn-small">✏️ Изменить</button>
                    <button onclick="deleteTodo(${todo.id})" class="btn btn-danger btn-small">🗑️ Удалить</button>
                </div>
            </div>
            ${todo.description ? `<div class="todo-description">${escapeHtml(todo.description)}</div>` : ''}
            <div class="todo-meta">
                <span class="badge badge-status-${todo.status}">${getStatusText(todo.status)}</span>
                <span class="badge badge-priority-${todo.priority}">${getPriorityText(todo.priority)}</span>
            </div>
            <div class="todo-date">
                Создана: ${formatDate(todo.created_at)}
                ${todo.updated_at !== todo.created_at ? `| Изменена: ${formatDate(todo.updated_at)}` : ''}
            </div>
        </div>
    `).join('');
    
    // Пагинация
    if (data.pages > 1) {
        pagination.style.display = 'flex';
        document.getElementById('page-info').textContent = `Страница ${data.page} из ${data.pages} (всего: ${data.total})`;
        document.getElementById('prev-btn').disabled = data.page <= 1;
        document.getElementById('next-btn').disabled = data.page >= data.pages;
    } else {
        pagination.style.display = 'none';
    }
}

// === Helpers ===
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getStatusText(status) {
    const map = {
        'new': 'Новая',
        'in_progress': 'В работе',
        'done': 'Завершена',
        'cancelled': 'Отменена'
    };
    return map[status] || status;
}

function getPriorityText(priority) {
    const map = {
        'high': 'Высокий',
        'medium': 'Средний',
        'low': 'Низкий'
    };
    return map[priority] || priority;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// === Filters ===
function applyFilters() {
    currentPage = 1;
    loadTodos();
}

function debounceSearch() {
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    searchTimeout = setTimeout(() => {
        applyFilters();
    }, 500);
}

function changePage(delta) {
    currentPage += delta;
    loadTodos();
}

// === Modal ===
function openCreateModal() {
    document.getElementById('modal-title').textContent = 'Создать задачу';
    document.getElementById('todo-id').value = '';
    document.getElementById('todo-title').value = '';
    document.getElementById('todo-description').value = '';
    document.getElementById('todo-priority').value = 'medium';
    document.getElementById('status-group').style.display = 'none';
    document.getElementById('todo-modal').style.display = 'flex';
}

async function openEditModal(todoId) {
    const token = getToken();
    
    try {
        const response = await fetch(`${API_URL}/api/v1/todos/${todoId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            throw new Error('Ошибка загрузки задачи');
        }
        
        const todo = await response.json();
        
        document.getElementById('modal-title').textContent = 'Редактировать задачу';
        document.getElementById('todo-id').value = todo.id;
        document.getElementById('todo-title').value = todo.title;
        document.getElementById('todo-description').value = todo.description || '';
        document.getElementById('todo-priority').value = todo.priority;
        document.getElementById('todo-status').value = todo.status;
        document.getElementById('status-group').style.display = 'block';
        document.getElementById('todo-modal').style.display = 'flex';
        
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function closeModal() {
    document.getElementById('todo-modal').style.display = 'none';
}

// === Save Todo ===
async function handleSaveTodo(event) {
    event.preventDefault();
    
    const token = getToken();
    const todoId = document.getElementById('todo-id').value;
    const title = document.getElementById('todo-title').value;
    const description = document.getElementById('todo-description').value;
    const priority = document.getElementById('todo-priority').value;
    const status = document.getElementById('todo-status').value;
    
    const data = { title, description, priority };
    if (todoId) {
        data.status = status;
    }
    
    try {
        let response;
        
        if (todoId) {
            // Обновление
            response = await fetch(`${API_URL}/api/v1/todos/${todoId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        } else {
            // Создание
            response = await fetch(`${API_URL}/api/v1/todos`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(formatApiError(error, 'Ошибка сохранения'));
        }
        
        showToast(todoId ? 'Задача обновлена' : 'Задача создана', 'success');
        closeModal();
        loadTodos();
        
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// === Delete Todo ===
async function deleteTodo(todoId) {
    if (!confirm('Вы уверены, что хотите удалить эту задачу?')) {
        return;
    }
    
    const token = getToken();
    
    try {
        const response = await fetch(`${API_URL}/api/v1/todos/${todoId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(formatApiError(error, 'Ошибка удаления'));
        }
        
        showToast('Задача удалена', 'success');
        loadTodos();
        
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// === Init ===
document.addEventListener('DOMContentLoaded', async () => {
    const user = await checkAuth();
    if (user) {
        loadTodos();
    }
});

// Закрытие модалки по клику вне неё
document.getElementById('todo-modal')?.addEventListener('click', (e) => {
    if (e.target.id === 'todo-modal') {
        closeModal();
    }
});
