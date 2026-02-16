# Структура проекта Clustering Trainer

Краткое описание каждой папки и файла, чтобы ориентироваться в проекте.

---

## Корень проекта

| Файл | Назначение |
|------|------------|
| `manage.py` | Точка входа Django: запуск сервера, миграций, команд (`python manage.py runserver`, `migrate`, `createsuperuser` и т.д.). |
| `db.sqlite3` | База данных SQLite (создаётся после `migrate`). |

---

## config/ — настройки проекта

| Файл | Назначение |
|------|------------|
| `__init__.py` | Помечает папку как пакет Python. |
| `settings.py` | Все настройки: INSTALLED_APPS, БД, шаблоны, статика, логин/логаут, email, язык, таймзона. |
| `urls.py` | Главный маршрутизатор: подключает админку, симулятор, задачи, энциклопедию, тестирование, core (главная, логин, материалы), редиректы `/auth/` → `/login/`. |
| `wsgi.py` | Точка входа для WSGI-сервера (деплой на production). |
| `asgi.py` | Точка входа для ASGI (асинхронный режим, при необходимости). |

---

## apps/core/ — пользователи, профиль, материалы

**Назначение:** главная страница, регистрация/вход/выход, профиль пользователя, список и детали учебных материалов.

| Файл | Назначение |
|------|------------|
| `__init__.py` | Пакет приложения. |
| `apps.py` | Конфиг приложения (имя, метка). |
| `models.py` | **Material** — учебный материал (title, slug, content, order, связь с тегами задач `TaskTag` для «связанных тем»). |
| `views.py` | **home** — главная; **register** — регистрация + приветственное письмо; **login/logout** — через Django; **profile** — профиль (статистика по задачам, последние попытки); **materials_list**, **material_detail** — список и страница материала. |
| `urls.py` | Маршруты: `''` → home, `register/`, `profile/`, `materials/`, `materials/<slug>/`, `login/`, `logout/`. |
| `forms.py` | **UserRegisterForm** — форма регистрации (username, email, пароль). |
| `admin.py` | Регистрация модели Material в админке. |
| `migrations/` | Миграции БД для Material (0001, 0002 — теги, 0003 — переход ссылки тегов на apps.tasks). |

---

## apps/simulator/ — песочница кластеризации

**Назначение:** одна страница, где можно кликать точки на холсте, выбирать алгоритм (K-Means, DBSCAN, FOREL, иерархический, MeanShift), загружать пресеты данных и пошагово смотреть результат. Без заданий и без сохранения решений — только визуализация.

| Файл | Назначение |
|------|------------|
| `__init__.py` | Пакет приложения. |
| `apps.py` | Конфиг приложения. |
| `models.py` | Пусто (модели заданий перенесены в apps.tasks). |
| `views.py` | **index** — страница песочницы; **_redirect_legacy_challenge** — редирект старых `/simulator/challenge/<slug>/` на `/tasks/challenge/<slug>/`; **get_preset** — JSON с точками пресета; **run_algorithm** — единый API запуска алгоритма (kmeans, dbscan, forel, agglomerative, meanshift); **get_dendrogram** — данные для дендрограммы; заглушки run_kmeans, run_dbscan и т.д. |
| `urls.py` | Маршруты: `''` → index, `run/`, `preset/`, `dendrogram/`, редиректы tasks/challenge, legacy API. |
| `algorithms.py` | Реализации пошаговой кластеризации: **normalize_points**, **kmeans_step**, **dbscan_step**, **forel_step**, **agglomerative_step**, **mean_shift_step**, **compute_dendrogram_data** (numpy/scipy). |
| `presets.py` | **generate_preset** — генерация датасетов (moons, circles, blobs, grid, hierarchy, dense_sparse) через sklearn/numpy. |
| `services.py` | Безопасное выполнение кода: **is_safe_code** (статическая проверка импортов), **create_tracer** (ограничение числа шагов от бесконечных циклов), **TimeLimitException**, **get_safe_builtins** — используются при проверке решений заданий в apps.tasks. |
| `admin.py` | Пусто (админка заданий в apps.tasks). |
| `forms.py` | Пусто (формы заданий в apps.tasks). |
| `templates/simulator/index.html` | Шаблон страницы симулятора: разметка с Vue-директивами (v-model, v-if), сайдбар с выбором алгоритма и пресета, холст, кнопки шагов. |
| `management/commands/add_kmeans_quizzes.py` | Команда `python manage.py add_kmeans_quizzes` — создаёт тестовые квизы по K-Means в apps.tasks. |
| `management/commands/download_static_libs.py` | Скачивание vendor-библиотек (Vue, Plotly) в static. |
| `migrations/` | Исторические миграции (в т.ч. 0010 — удаление моделей Task/TaskTag/UserTaskAttempt из state симулятора). |

---

## apps/tasks/ — задания (список и страница задания)

**Назначение:** модели заданий и попыток, список заданий по тегам, страница задания (код или квиз), проверка решений на сервере.

| Файл | Назначение |
|------|------------|
| `__init__.py` | Пакет приложения. |
| `apps.py` | Конфиг приложения (verbose_name «Задачи»). |
| `models.py` | **TaskTag** — тег/блок задач; **Task** — задание (title, slug, description, task_type: code/choice, difficulty, tags, order, function_name, initial_code, solution_code, test_input, expected_output); **UserTaskAttempt** — попытка пользователя (user, task, code, is_correct, test_attempt — связь с тестом). Таблицы в БД те же, что раньше в simulator (`db_table`). |
| `views.py` | **task_list** — список заданий по тегам + непройденные; **challenge_detail** — страница задания (код или квиз), передаёт previous_code, test_attempt_id; **check_solution** — POST API: проверка кода (через simulator.services) или ответов квиза, сохранение UserTaskAttempt, ответ JSON (correct, message, error). |
| `urls.py` | Маршруты: `''` → task_list, `challenge/<slug>/`, `api/check-solution/`. |
| `forms.py` | **TaskAdminForm** + **_parse_quiz_from_post** — разбор конструктора квиза в админке (вопросы/варианты/правильный ответ) в test_input и expected_output. |
| `admin.py` | TaskTag, Task, UserTaskAttempt в админке; для Task — кастомный change_form с конструктором квиза. |
| `migrations/0001_initial.py` | Добавляет в state модели TaskTag, Task, UserTaskAttempt с `db_table` на существующие таблицы simulator_* (без создания таблиц). |

---

## apps/testing/ — группы и тесты по времени

**Назначение:** преподаватели создают группы и тесты, студенты подключаются по коду, проходят тест с таймером; попытки привязаны к TestAttempt.

| Файл | Назначение |
|------|------------|
| `__init__.py` | Пакет приложения. |
| `apps.py` | Конфиг приложения. |
| `models.py` | **TeacherProfile** — пользователь-преподаватель; **StudentGroup** — группа (teacher, name, join_code); **GroupMembership** — студент в группе; **Test** — тест (owner, group, title, tasks M2M к tasks.Task, time_limit_minutes, opens_at, closes_at); **TestAttempt** — попытка прохождения теста (user, test, started_at, submitted_at). |
| `views.py` | **testing_home** — для неавторизованных редирект на логин + сообщение; для преподавателя — группы и тесты; для студента — присоединённые группы и тесты; **join_group** — вход по коду группы; **create_group** — создание группы; **create_test** — создание теста; **start_test** — старт попытки; **take_test** — страница теста с таймером; **submit_test** — сдача; **test_results** — результаты по тесту. |
| `urls.py` | Маршруты: `''` → testing_home, `join/`, `groups/create/`, `tests/create/`, `tests/<id>/start/`, `attempt/<id>/`, `attempt/<id>/submit/`, `tests/<id>/results/`. |
| `admin.py` | TeacherProfile, StudentGroup, Test, TestAttempt в админке. |
| `migrations/` | 0001 — создание моделей (Test.tasks → simulator.Task); 0002 — переход ссылки Test.tasks на tasks.Task (state only). |

---

## apps/encyclopedia/ — база знаний (онтология)

**Назначение:** граф понятий по кластеризации (из OWL), страница графа и страница понятия.

| Файл | Назначение |
|------|------------|
| `__init__.py` | Пакет приложения. |
| `apps.py` | Конфиг приложения. |
| `models.py` | **Concept** — узел (uri, title, description); **ConceptRelation** — ребро (source, target, relation_type: IS_A, PART_OF, USES, DEPENDS, RELATED). |
| `ontology.py` | Загрузка/парсинг OWL-файла, заполнение Concept и ConceptRelation. |
| `views.py` | **graph_view** — страница графа; **concept_detail** — страница одного понятия. |
| `urls.py` | Маршруты: `''` → graph, `concept/<pk>/` → detail. |
| `admin.py` | Concept, ConceptRelation в админке. |
| `migrations/0001_initial.py` | Создание таблиц Concept, ConceptRelation. |

---

## templates/ — HTML-шаблоны

| Путь | Назначение |
|------|------------|
| `base.html` | Базовый шаблон: head, навбар, блок для сообщений (toast), `{% block content %}`, подключение base.css. |
| `includes/navbar.html` | Навбар: логотип, ссылки (главная, Симулятор, Задачи, База знаний, Материалы, Тестирование), кнопки Вход/профиль. |
| **core/** | |
| `core/home.html` | Главная страница. |
| `core/login.html` | Форма входа (username, password). |
| `core/register.html` | Форма регистрации. |
| `core/profile.html` | Профиль: статистика заданий, последние попытки, ссылка на задания. |
| `core/materials_list.html` | Список учебных материалов. |
| `core/material_detail.html` | Один материал (контент). |
| **simulator/** | |
| `simulator/index.html` | Страница симулятора (песочница): Vue-разметка, подключает simulator.css, vue.global.js, simulator/app.js. |
| `simulator/challenge.html` | Старый/альтернативный шаблон задания (может использовать js/challenge.js). |
| `simulator/no_tasks.html` | Сообщение «заданий пока нет». |
| **tasks/** | |
| `tasks/task_list.html` | Список заданий по тегам, карточки с ссылками на challenge. |
| `tasks/challenge_detail.html` | Страница задания: описание, редактор кода (Monaco) или квиз; скрытые поля (task-slug, check-solution-url, test_attempt_id); подключает tasks.css, simulator/css/challenge.css, simulator/js/challenge.js. |
| **testing/** | |
| `testing/teacher_home.html` | Для преподавателя: группы, тесты, создание. |
| `testing/student_home.html` | Для студента: присоединиться к группе, активные тесты. |
| `testing/create_test.html` | Форма создания теста (название, группа, задания, время, окно открытия). |
| `testing/take_test.html` | Страница прохождения теста (таймер, ссылки на задания, сдача). |
| `testing/test_results.html` | Результаты по тесту. |
| **encyclopedia/** | |
| `encyclopedia/graph.html` | Граф понятий (визуализация). |
| `encyclopedia/detail.html` | Страница одного понятия. |
| **admin/** | |
| `admin/tasks/task/change_form.html` | Кастомная форма редактирования Task в админке: конструктор квиза (вопросы, варианты, правильный ответ). |
| `admin/simulator/task/change_form.html` | Старый путь (можно удалить, если везде используется tasks). |
| **emails/** | |
| `emails/welcome.html` | Письмо приветствия после регистрации. |

---

## static/ — CSS и JavaScript

| Путь | Назначение |
|------|------------|
| **css/** | |
| `base.css` | Общие переменные, стили навбара, кнопок, main-content, тосты (уведомления). |
| `auth.css` | Стили страниц входа/регистрации. |
| `home.css` | Стили главной страницы. |
| `profile.css` | Стили профиля. |
| `tasks.css` | Стили списка заданий (карточки, секции). |
| `simulator.css` | Стили страницы симулятора (сайдбар, холст, контролы). |
| `testing.css` | Стили разделов тестирования. |
| `materials.css` | Стили списка и страницы материалов. |
| `encyclopedia.css` | Стили графа и страницы понятия. |
| **js/** | |
| `challenge.js` | Вариант логики страницы задания (Vue + Monaco) — может использоваться старым challenge.html. |
| **simulator/** | Единый источник для страницы задания (задачи). |
| `simulator/js/challenge.js` | Логика страницы задания: инициализация Monaco или квиза, отправка кода/ответов на `/tasks/api/check-solution/`, отображение результата. |
| `simulator/css/challenge.css` | Стили страницы задания: сетка (сайдбар + редактор/квиз), кнопки, блоки вопросов, результат. |
| **js/simulator/** | |
| `app.js` | Vue-приложение симулятора: состояние (алгоритм, параметры, точки, история шагов), клик по холсту, загрузка пресета, вызов runAlgorithm, отрисовка. |
| `api.js` | Функции запросов к API: runKMeans, runDBSCAN, runForel, runAgglomerative, runMeanShift, generatePreset, getDendrogram (fetch к /simulator/run/, preset/, dendrogram/). |
| `plot.js` | Работа с Plotly: initPlot, drawPoints, drawStep, convertClickToPoint (координаты клика в данные графика). |
| **js/testing.js** | Логика страниц тестирования (если есть). |
| **js/vendor/** | |
| `vue.global.js` | Vue 3 (глобальная сборка). |
| `plotly.min.js` | Plotly для графиков. |

---

## scripts/ — разовые и утилитарные скрипты

Запуск из корня проекта: `python scripts/<имя>.py`.

| Файл | Назначение |
|------|------------|
| `README.md` | Описание скриптов и как их запускать. |
| `fix_migrations.py` | Добавляет в таблицу django_migrations записи о core.0003 и testing.0002 (чтобы state миграций был согласован после переноса задач). |
| `fix_migrations.sql` | То же через SQL (sqlite3 db.sqlite3 < scripts/fix_migrations.sql). |
| `init_tasks.py` | Создаёт базовые задания (Евклидово расстояние, центроид, ближайший кластер) и теги (apps.tasks.models). |
| `init_materials.py` | Создаёт материал «Метод K-средних (K-Means)» (apps.core.models.Material). |
| `fix_materials.py` | Обновляет контент материала K-Means (update_or_create по slug). |

---

## Прочее (в корне, если есть)

| Файл | Назначение |
|------|------------|
| `clustering_domain.owl` | OWL-онтология домена кластеризации (источник для энциклопедии). |

---

## Как связаны приложения

- **core** использует **tasks**: в профиле показываются Task, UserTaskAttempt, TaskTag; материалы связаны с TaskTag.
- **testing** использует **tasks**: Test имеет M2M к Task; TestAttempt связывается с UserTaskAttempt при проверке решений в рамках теста.
- **tasks** использует **simulator**: при проверке кода вызываются simulator.services (is_safe_code, create_tracer, get_safe_builtins).
- Статика: симулятор подключает `static/js/simulator/app.js` + api.js + plot.js; страница задания подключает `static/simulator/js/challenge.js` и `static/simulator/css/challenge.css`.

Если нужно, можно добавить в этот файл разделы «Типичный сценарий: от главной до сдачи теста» или «Куда смотреть при баге в X».
