"""
Система рекомендаций на основе онтологии для адаптивного обучения.

Использует зависимости между Concepts (requires_knowledge) для определения,
какие задачи и материалы доступны пользователю.
"""
from django.db.models import Q, Exists, OuterRef
from apps.encyclopedia.models import Concept, ConceptRelation
from apps.tasks.models import Task, UserTaskAttempt
from apps.core.models import Material


def get_learned_concepts(user):
    """
    Возвращает набор Concepts, которые пользователь изучил
    (решил связанные задачи с is_correct=True).
    
    Args:
        user: User объект
        
    Returns:
        QuerySet Concept объектов
    """
    # Находим все задачи, которые пользователь решил правильно
    solved_tasks = Task.objects.filter(
        attempts__user=user,
        attempts__is_correct=True
    ).distinct()
    
    # Получаем Concepts, связанные с решенными задачами
    learned_concepts = Concept.objects.filter(
        tasks__in=solved_tasks
    ).distinct()
    
    return learned_concepts


def get_required_concepts(concept):
    """
    Возвращает все Concepts, которые требуются для изучения данного Concept.
    Зависимости определяются через:
    - DEPENDS (явные зависимости)
    - USES (если алгоритм использует метрику/концепт, то знание этого концепта требуется)
    
    Args:
        concept: Concept объект
        
    Returns:
        QuerySet Concept объектов (зависимости)
    """
    # Находим все Concepts, от которых зависит данный Concept через DEPENDS
    required_depends = Concept.objects.filter(
        relations_in__source=concept,
        relations_in__relation_type='DEPENDS'
    ).distinct()
    
    # Также считаем USES как зависимости (если алгоритм использует метрику,
    # то знание этой метрики требуется)
    required_uses = Concept.objects.filter(
        relations_in__source=concept,
        relations_in__relation_type='USES'
    ).distinct()
    
    # Объединяем оба типа зависимостей
    from django.db.models import Q
    required = Concept.objects.filter(
        Q(id__in=required_depends.values_list('id', flat=True)) |
        Q(id__in=required_uses.values_list('id', flat=True))
    ).distinct()
    
    return required


def get_all_required_concepts(concept, visited=None):
    """
    Рекурсивно получает все зависимости Concept (включая зависимости зависимостей).
    
    Args:
        concept: Concept объект
        visited: set для отслеживания уже посещенных Concepts (предотвращение циклов)
        
    Returns:
        set Concept объектов (все зависимости)
    """
    if visited is None:
        visited = set()
    
    if concept.id in visited:
        return set()
    
    visited.add(concept.id)
    all_required = set()
    
    # Прямые зависимости
    direct_required = get_required_concepts(concept)
    all_required.update(direct_required)
    
    # Рекурсивно получаем зависимости зависимостей
    for req_concept in direct_required:
        all_required.update(get_all_required_concepts(req_concept, visited))
    
    return all_required


def is_task_available(user, task):
    """
    Проверяет, доступна ли задача пользователю
    (все зависимости изучены).
    
    Args:
        user: User объект
        task: Task объект
        
    Returns:
        tuple (bool доступна, list недостающие Concepts)
    """
    if not task.concept:
        # Если задача не связана с онтологией, она доступна
        return True, []
    
    learned_concepts = set(get_learned_concepts(user).values_list('id', flat=True))
    required_concepts = get_all_required_concepts(task.concept)
    required_ids = {c.id for c in required_concepts}
    
    missing = required_ids - learned_concepts
    
    return len(missing) == 0, list(Concept.objects.filter(id__in=missing))


def get_recommended_tasks(user, limit=10):
    """
    Возвращает задачи, которые пользователь может решить
    (все зависимости изучены).
    
    Args:
        user: User объект
        limit: максимальное количество задач
        
    Returns:
        QuerySet Task объектов
    """
    learned_concepts = set(get_learned_concepts(user).values_list('id', flat=True))
    
    # Находим задачи, у которых все зависимости изучены
    available_tasks = []
    for task in Task.objects.filter(concept__isnull=False).select_related('concept'):
        is_available, missing = is_task_available(user, task)
        if is_available:
            # Проверяем, что задача еще не решена
            if not UserTaskAttempt.objects.filter(user=user, task=task, is_correct=True).exists():
                available_tasks.append(task)
    
    return available_tasks[:limit]


def get_recommended_materials(user, limit=5):
    """
    Возвращает материалы для изучения недостающих Concepts.
    
    Args:
        user: User объект
        limit: максимальное количество материалов
        
    Returns:
        QuerySet Material объектов
    """
    learned_concepts = set(get_learned_concepts(user).values_list('id', flat=True))
    
    # Находим Concepts, которые требуются для доступных задач, но еще не изучены
    all_required = set()
    for task in Task.objects.filter(concept__isnull=False).select_related('concept'):
        if task.concept:
            required = get_all_required_concepts(task.concept)
            all_required.update(required)
    
    missing_concepts = all_required - learned_concepts
    
    # Находим материалы, связанные с недостающими Concepts
    materials = Material.objects.filter(
        concept__id__in=[c.id for c in missing_concepts]
    ).distinct()[:limit]
    
    return materials


def get_learning_path(user, target_concept):
    """
    Возвращает путь обучения от текущего уровня до target_concept.
    
    Args:
        user: User объект
        target_concept: Concept объект (целевое понятие)
        
    Returns:
        dict с ключами:
            - 'path': список Concepts в порядке изучения
            - 'tasks': список Task объектов для каждого Concept
            - 'materials': список Material объектов для каждого Concept
    """
    learned_concepts = set(get_learned_concepts(user).values_list('id', flat=True))
    required_concepts = get_all_required_concepts(target_concept)
    
    # Фильтруем только те Concepts, которые еще не изучены
    missing_concepts = [c for c in required_concepts if c.id not in learned_concepts]
    
    # Добавляем сам target_concept, если он не изучен
    if target_concept.id not in learned_concepts:
        missing_concepts.append(target_concept)
    
    # Сортируем по количеству зависимостей (сначала простые)
    def get_dependency_count(concept):
        return len(get_all_required_concepts(concept))
    
    missing_concepts.sort(key=get_dependency_count)
    
    # Собираем задачи и материалы для каждого Concept
    path_tasks = {}
    path_materials = {}
    
    for concept in missing_concepts:
        path_tasks[concept] = Task.objects.filter(concept=concept)
        path_materials[concept] = Material.objects.filter(concept=concept)
    
    return {
        'path': missing_concepts,
        'tasks': path_tasks,
        'materials': path_materials
    }


def get_user_progress(user):
    """
    Возвращает статистику прогресса пользователя по онтологии.
    
    Args:
        user: User объект
        
    Returns:
        dict с ключами:
            - 'learned_count': количество изученных Concepts
            - 'total_count': общее количество Concepts
            - 'progress_percent': процент прогресса
            - 'available_tasks_count': количество доступных задач
            - 'blocked_tasks_count': количество заблокированных задач
    """
    learned_concepts = get_learned_concepts(user)
    total_concepts = Concept.objects.count()
    
    available_count = 0
    blocked_count = 0
    
    for task in Task.objects.filter(concept__isnull=False):
        is_available, _ = is_task_available(user, task)
        if is_available:
            if not UserTaskAttempt.objects.filter(user=user, task=task, is_correct=True).exists():
                available_count += 1
        else:
            blocked_count += 1
    
    progress_percent = int((learned_concepts.count() / total_concepts * 100)) if total_concepts > 0 else 0
    
    return {
        'learned_count': learned_concepts.count(),
        'total_count': total_concepts,
        'progress_percent': progress_percent,
        'available_tasks_count': available_count,
        'blocked_tasks_count': blocked_count
    }
