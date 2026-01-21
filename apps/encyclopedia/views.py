from django.shortcuts import render, get_object_or_404
from .models import Concept

def graph_view(request):
    """Отображение графа знаний"""
    concepts = Concept.objects.all()
    return render(request, 'encyclopedia/graph.html', {'concepts': concepts})

def concept_detail(request, pk):
    """Детальная страница понятия с отображением связей"""
    concept = get_object_or_404(Concept, pk=pk)
    # Получаем входящие и исходящие связи
    relations_out = concept.relations_out.all()
    relations_in = concept.relations_in.all()
    
    return render(request, 'encyclopedia/detail.html', {
        'concept': concept,
        'relations_out': relations_out,
        'relations_in': relations_in
    })
