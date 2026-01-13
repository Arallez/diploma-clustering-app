from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .engine import KMeansEngine
from .models import Task
import json
import logging
import os
import math

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class RunKMeans(APIView):
    """API для запуска K-Means алгоритма пошагово"""
    
    def post(self, request):
        try:
            data = request.data
            points = data.get('points', [])
            k = int(data.get('k', 3))
            
            if not points or len(points) == 0:
                return Response({"error": "No points provided"}, status=400)
            
            if k < 1 or k > 10:
                return Response({"error": "K must be between 1 and 10"}, status=400)
            
            engine = KMeansEngine(n_clusters=k)
            history = engine.run_step_by_step(points)
            
            return Response({
                "success": True,
                "history": history,
                "total_steps": len(history)
            })
        except Exception as e:
            logger.error(f"Error in RunKMeans: {str(e)}")
            return Response({"error": str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class CheckSolution(APIView):
    """
    API для проверки ответов.
    Теперь берет эталон из базы данных (Task.expected_output).
    """
    def post(self, request):
        try:
            data = request.data
            task_slug = data.get('task_id') # мы используем slug как ID
            user_result = data.get('result')

            task = get_object_or_404(Task, slug=task_slug)
            
            # 1. Получаем ожидаемый ответ из БД
            target = task.expected_output
            
            # 2. Сравниваем user_result и target
            # Нужно учесть float precision и типы данных (списки, числа)
            is_correct = self.compare_results(user_result, target)
            
            if is_correct:
                return Response({"correct": True, "message": "✅ Верно! Отличное решение."})
            else:
                return Response({
                    "correct": False, 
                    "message": f"❌ Ошибка. Ожидалось: {target}, Получено: {user_result}"
                })
        
        except Task.DoesNotExist:
             return Response({"error": "Task not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def compare_results(self, val1, val2):
        """Сравнивает два значения с учетом погрешности float"""
        try:
            # Если оба числа
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                return abs(val1 - val2) < 0.01
            
            # Если оба списки
            if isinstance(val1, list) and isinstance(val2, list):
                if len(val1) != len(val2): return False
                for a, b in zip(val1, val2):
                    if not self.compare_results(a, b): return False
                return True
                
            # Иначе (строки, булевы) - прямое сравнение
            return val1 == val2
        except:
            return False


def simulator_view(request):
    """Главная страница тренажера"""
    return render(request, 'simulator/index.html')

def tasks_view(request):
    """Список всех доступных заданий"""
    tasks = Task.objects.all().order_by('order')
    return render(request, 'simulator/task_list.html', {'tasks': tasks})

def challenge_view(request, slug=None):
    """Страница конкретного задания"""
    # Если slug не передан, берем первое задание или дефолтное
    if not slug:
        first_task = Task.objects.first()
        if first_task:
            return render(request, 'simulator/challenge.html', {'task': first_task})
        else:
            return render(request, 'simulator/no_tasks.html') # Заглушка, если база пуста
            
    task = get_object_or_404(Task, slug=slug)
    return render(request, 'simulator/challenge.html', {'task': task})
