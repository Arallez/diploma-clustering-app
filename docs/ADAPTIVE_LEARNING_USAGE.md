# 📚 Руководство по использованию адаптивного обучения

## Быстрый старт

### 1. Синхронизация онтологии

После добавления или изменения файла `clustering_domain.owl` выполните команду:

```bash
python manage.py sync_ontology
```

Эта команда:
- Загружает OWL файл из корня проекта
- Синхронизирует Concepts и связи с базой данных Django
- Выводит информацию о загруженных индивидах и связях

### 2. Связывание задач и материалов с онтологией

#### В админке Django:

**Для задач (Task):**
1. Откройте задачу в админке
2. В поле "Понятие из онтологии" выберите соответствующий Concept
3. Сохраните

**Для материалов (Material):**
1. Откройте материал в админке
2. В поле "Понятие из онтологии" выберите Concept, который объясняет этот материал
3. Сохраните

### 3. Как работает адаптивное обучение

#### Логика доступности задач:

1. **Задачи без связи с онтологией** - всегда доступны
2. **Задачи с Concept** - доступны только если:
   - Все зависимости (requires_knowledge) изучены
   - Пользователь решил задачи, связанные с зависимостями

#### Пример:

```
EuclideanDistance (Евклидово расстояние)
  ↓ DEPENDS
KMeans (K-Means алгоритм)
  ↓ DEPENDS  
Centroid (Центроид)
```

**Сценарий:**
- Пользователь решает задачу про "Евклидово расстояние" → Concept "EuclideanDistance" помечается как изученный
- Система проверяет задачу "K-Means": требуется "EuclideanDistance" и "Centroid"
- Если "Centroid" не изучен → задача заблокирована
- Система рекомендует материал про "Centroid"
- После изучения → задача "K-Means" становится доступной

---

## API для разработчиков

### Получение рекомендаций

```python
from apps.encyclopedia.recommendations import (
    get_recommended_tasks,
    get_recommended_materials,
    get_user_progress,
    is_task_available,
    get_learning_path
)

# Рекомендуемые задачи
tasks = get_recommended_tasks(user, limit=10)

# Рекомендуемые материалы
materials = get_recommended_materials(user, limit=5)

# Прогресс пользователя
progress = get_user_progress(user)
# Возвращает: learned_count, total_count, progress_percent, 
#             available_tasks_count, blocked_tasks_count

# Проверка доступности задачи
is_available, missing = is_task_available(user, task)

# Путь обучения до целевого Concept
path = get_learning_path(user, target_concept)
```

---

## Структура OWL файла

### Классы:
- `KnowledgeItem` - базовый класс для всех понятий
- `Algorithm` - алгоритмы кластеризации
- `Metric` - метрики расстояния
- `OntologyConcept` - общие понятия

### Свойства:
- `uses_metric` - алгоритм использует метрику
- `requires_knowledge` - требует знания другого Concept (пререквизит)

### Пример индивида:

```xml
<owl:NamedIndividual rdf:about="#KMeans">
  <rdf:type rdf:resource="#Algorithm"/>
  <uses_metric rdf:resource="#EuclideanDistance"/>
  <requires_knowledge rdf:resource="#EuclideanDistance"/>
  <requires_knowledge rdf:resource="#Centroid"/>
  <rdfs:label>K-Means (К-средних)</rdfs:label>
  <rdfs:comment>Итеративный алгоритм кластеризации...</rdfs:comment>
</owl:NamedIndividual>
```

---

## Интеграция в шаблоны

### В списке задач (`task_list.html`):

```django
{% for task in tasks %}
  {% if task.id in available_task_ids %}
    {# Задача доступна #}
  {% else %}
    {# Задача заблокирована - показать недостающие Concepts #}
    {% for concept in blocked_tasks_info|get_item:task.id %}
      <span class="badge">Требуется: {{ concept.title }}</span>
    {% endfor %}
  {% endif %}
{% endfor %}
```

### В профиле пользователя (`profile.html`):

```django
{% if recommended_tasks %}
  <h3>Рекомендуемые задачи</h3>
  {% for task in recommended_tasks %}
    <a href="{% url 'tasks:challenge_detail' task.slug %}">{{ task.title }}</a>
  {% endfor %}
{% endif %}

{% if recommended_materials %}
  <h3>Рекомендуемые материалы</h3>
  {% for material in recommended_materials %}
    <a href="{% url 'core:material_detail' material.slug %}">{{ material.title }}</a>
  {% endfor %}
{% endif %}
```

---

## Расширение онтологии

### Добавление нового Concept:

1. Откройте `clustering_domain.owl` в текстовом редакторе
2. Добавьте новый индивид:

```xml
<owl:NamedIndividual rdf:about="#NewConcept">
  <rdf:type rdf:resource="#OntologyConcept"/>
  <rdfs:label>Новое понятие</rdfs:label>
  <rdfs:comment>Описание понятия</rdfs:comment>
</owl:NamedIndividual>
```

3. Добавьте связи (если нужно):

```xml
<owl:NamedIndividual rdf:about="#ExistingConcept">
  <requires_knowledge rdf:resource="#NewConcept"/>
</owl:NamedIndividual>
```

4. Выполните `python manage.py sync_ontology`

---

## Отладка

### Проверка синхронизации:

```python
from apps.encyclopedia.models import Concept, ConceptRelation

# Все Concepts
concepts = Concept.objects.all()
for c in concepts:
    print(f"{c.title} ({c.uri})")

# Все связи
relations = ConceptRelation.objects.all()
for r in relations:
    print(f"{r.source.title} --[{r.relation_type}]--> {r.target.title}")
```

### Проверка доступности:

```python
from apps.encyclopedia.recommendations import get_learned_concepts, is_task_available

# Изученные Concepts
learned = get_learned_concepts(user)
print(f"Изучено: {[c.title for c in learned]}")

# Проверка задачи
is_available, missing = is_task_available(user, task)
print(f"Доступна: {is_available}")
print(f"Недостающие: {[c.title for c in missing]}")
```
