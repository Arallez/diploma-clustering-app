from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Concept
from .recommendations import get_recommended_tasks, get_user_progress, get_recommended_materials

def graph_view(request):
    """Отображение графа знаний"""
    concepts = Concept.objects.all()
    return render(request, 'encyclopedia/graph.html', {'concepts': concepts})

def concept_detail(request, pk):
    """Детальная страница понятия с отображением связей и рекомендаций"""
    concept = get_object_or_404(Concept, pk=pk)
    # Получаем входящие и исходящие связи
    relations_out = concept.relations_out.select_related('target')
    relations_in = concept.relations_in.select_related('source')
    
    # Задачи и материалы, привязанные к этому концепту
    related_tasks = concept.tasks.all() if hasattr(concept, 'tasks') else []
    related_materials = concept.materials.all() if hasattr(concept, 'materials') else []
    
    return render(request, 'encyclopedia/detail.html', {
        'concept': concept,
        'relations_out': relations_out,
        'relations_in': relations_in,
        'related_tasks': related_tasks,
        'related_materials': related_materials,
    })

@login_required
def recommendations_view(request):
    """
    Страница адаптивного обучения.
    Показывает прогресс пользователя по онтологии и рекомендует следующие шаги.
    """
    # Получаем общую статистику
    progress_stats = get_user_progress(request.user)
    
    # Рекомендуем следующие задачи (те, для которых пройдены пререквизиты)
    recommended_tasks = get_recommended_tasks(request.user, limit=5)
    
    # Рекомендуем теорию (материалы) для тех концептов, которые еще не изучены,
    # но требуются для задач
    recommended_materials = get_recommended_materials(request.user, limit=3)
    
    return render(request, 'encyclopedia/recommendations.html', {
        'progress': progress_stats,
        'recommended_tasks': recommended_tasks,
        'recommended_materials': recommended_materials,
    })
