from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .engine import KMeansEngine
import json
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class RunKMeans(APIView):
    """API для запуска K-Means алгоритма пошагово"""
    
    def post(self, request):
        try:
            # Получаем данные из запроса
            data = request.data
            points = data.get('points', [])
            k = int(data.get('k', 3))
            
            if not points or len(points) == 0:
                return Response({"error": "No points provided"}, status=400)
            
            if k < 1 or k > 10:
                return Response({"error": "K must be between 1 and 10"}, status=400)
            
            # Запускаем движок
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

def simulator_view(request):
    """Главная страница тренажера"""
    return render(request, 'simulator/index.html')
