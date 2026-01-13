from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .engine import KMeansEngine
import json
import logging
import os

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
    API для проверки ответов (схема 'Оракул').
    Принимает user_output (результат вычислений), сравнивает с эталоном.
    """
    def post(self, request):
        try:
            data = request.data
            task_id = data.get('task_id')
            user_result = data.get('result')

            # Пока хардкодим проверку для демо-задания "Центроид"
            # Тест: [[0,0], [4,4], [2,2]] -> Среднее должно быть [2.0, 2.0]
            if task_id == 'centroid_calc':
                try:
                    # Ожидаем список [x, y]
                    if not isinstance(user_result, list) or len(user_result) != 2:
                        return Response({"correct": False, "message": "Функция должна вернуть список из 2 чисел [x, y]"})
                    
                    # Проверяем значения с допуском (float precision)
                    target = [2.0, 2.0]
                    tolerance = 0.01
                    
                    is_correct = (abs(user_result[0] - target[0]) < tolerance) and \
                                 (abs(user_result[1] - target[1]) < tolerance)
                    
                    if is_correct:
                        return Response({"correct": True, "message": "Верно! Вы правильно реализовали поиск центроида."})
                    else:
                        return Response({"correct": False, "message": f"Ожидалось {target}, получено {user_result}"})
                
                except Exception:
                    return Response({"correct": False, "message": "Ошибка формата ответа"})
            
            return Response({"error": "Unknown task"}, status=404)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


def simulator_view(request):
    """Главная страница тренажера"""
    template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'templates', 'simulator', 'index.html')
    return FileResponse(open(template_path, 'rb'), content_type='text/html')

def challenge_view(request):
    """Страница с заданием (Code Challenge)"""
    template_path = os.path.join(os.path.dirname(__file__), '..', '..', 'templates', 'simulator', 'challenge.html')
    if not os.path.exists(template_path):
         return Response("Template not found", status=404)
    return FileResponse(open(template_path, 'rb'), content_type='text/html')
