# 📡 API Documentation

## Base URL
```
http://localhost:8000/simulator/api/
```

## Endpoints

### 1. Run K-Means Algorithm

**Endpoint:** `POST /run-kmeans/`

**Description:** Запускает алгоритм K-Means и возвращает пошаговую историю выполнения.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "points": [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]],
  "k": 2
}
```

**Parameters:**
- `points` (array of arrays): Массив точек, каждая точка — массив из 2 чисел `[x, y]`
- `k` (integer): Количество кластеров (от 1 до 10)

#### Response

**Success (200 OK):**
```json
{
  "success": true,
  "history": [
    {
      "step": 0,
      "centroids": [[2.0, 3.0], [5.0, 6.0]],
      "labels": [0, 0, 1],
      "inertia": 2.5,
      "converged": false
    },
    {
      "step": 1,
      "centroids": [[2.5, 3.5], [5.0, 6.0]],
      "labels": [0, 0, 1],
      "inertia": 1.0,
      "converged": true
    }
  ],
  "total_steps": 2
}
```

**Fields:**
- `success` (boolean): Успешность выполнения
- `history` (array): Массив шагов алгоритма
  - `step` (integer): Номер итерации
  - `centroids` (array): Координаты центроидов `[[x1, y1], [x2, y2], ...]`
  - `labels` (array): Метки кластеров для каждой точки `[0, 1, 0, ...]`
  - `inertia` (float): Сумма квадратов расстояний до центроидов
  - `converged` (boolean): Сошелся ли алгоритм
- `total_steps` (integer): Общее количество итераций

**Error (400 Bad Request):**
```json
{
  "success": false,
  "error": "Not enough points for K=3"
}
```

**Error (500 Internal Server Error):**
```json
{
  "success": false,
  "error": "Algorithm execution failed"
}
```

---

### 2. Check Solution

**Endpoint:** `POST /check-solution/`

**Description:** Проверяет правильность решения задания пользователем.

#### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "task_id": "euclidean-dist",
  "result": 5.0
}
```

**Parameters:**
- `task_id` (string): Slug задания (например, `"euclidean-dist"`)
- `result` (any): Ответ пользователя (число, массив, объект)

#### Response

**Success — Correct Answer (200 OK):**
```json
{
  "correct": true,
  "message": "✅ Верно! Отличное решение."
}
```

**Success — Incorrect Answer (200 OK):**
```json
{
  "correct": false,
  "message": "❌ Ошибка. Ожидалось: 5.0, Получено: 4.9"
}
```

**Error (404 Not Found):**
```json
{
  "correct": false,
  "message": "Задание не найдено"
}
```

**Error (400 Bad Request):**
```json
{
  "correct": false,
  "message": "Неверный формат данных"
}
```

---

## Common Errors

| Status Code | Описание |
|-------------|----------|
| 400 | Неверный формат запроса |
| 404 | Ресурс не найден |
| 405 | Метод не поддерживается (только POST) |
| 500 | Внутренняя ошибка сервера |

---

## Rate Limiting

**⚠️ Текущая версия:** Без ограничений (не для продакшена!)

**Рекомендация для продакшена:**
- 100 запросов/минуту на IP
- Использовать Django Ratelimit или Nginx

---

## Authentication

**⚠️ Текущая версия:** Без авторизации (анонимные запросы)

**Планы:**
- JWT-токены для личного кабинета
- Сохранение прогресса пользователей

---

## CORS

**Текущие настройки:** Разрешены запросы только с того же домена (same-origin)

**Для кросс-доменных запросов:** Установить `django-cors-headers`

---
## Testing

### cURL Example

```bash
# Test K-Means
curl -X POST http://localhost:8000/simulator/api/run-kmeans/ \
  -H "Content-Type: application/json" \
  -d '{
    "points": [[1, 2], [2, 3], [8, 9], [9, 10]],
    "k": 2
  }'

# Test Solution Check
curl -X POST http://localhost:8000/simulator/api/check-solution/ \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "euclidean-dist",
    "result": 5.0
  }'
```

### Python Example

```python
import requests

# Run K-Means
response = requests.post(
    'http://localhost:8000/simulator/api/run-kmeans/',
    json={
        'points': [[1, 2], [3, 4]],
        'k': 2
    }
)
print(response.json())

# Check Solution
response = requests.post(
    'http://localhost:8000/simulator/api/check-solution/',
    json={
        'task_id': 'euclidean-dist',
        'result': 5.0
    }
)
print(response.json())
```

---

## Changelog

### v1.0 (Initial Release)
- ✅ `POST /run-kmeans/` — запуск K-Means
- ✅ `POST /check-solution/` — проверка заданий

### Future (v2.0)
- 🔜 `POST /run-dbscan/` — поддержка DBSCAN
- 🔜 `GET /tasks/` — список заданий (JSON API)
- 🔜 `POST /auth/login/` — авторизация