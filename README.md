# Diploma Clustering App

Электронное пособие по методам кластеризации с адаптивным обучением и интеллектуальным тренажером.

## Структура проекта
Проект построен по модульной архитектуре Django:

- `config/` - Настройки проекта
- `apps/`
    - `users/` - Пользователи, авторизация
    - `encyclopedia/` - Теория, лекции, онтология
    - `simulator/` - Ядро алгоритмов кластеризации (scikit-learn)
    - `testing/` - Тесты и оценивание
- `templates/` - HTML шаблоны
- `static/` - CSS, JS (Vue.js, Plotly)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Arallez/diploma-clustering-app.git
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите миграции:
```bash
python manage.py migrate
```

4. Запустите сервер:
```bash
python manage.py runserver
```
