from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from .engine import KMeansEngine
import json

class RunKMeans(APIView):
    def post(self, request):
        try:
            # Получаем данные из запроса
            # Ожидаем JSON: {"points": [[1,1], [2,2]], "k": 3}
            data = request.data
            points = data.get('points', [])
            k = int(data.get('k', 3))
            
            if not points:
                return Response({"error": "No points provided"}, status=400)
            
            # Запускаем движок
            engine = KMeansEngine(n_clusters=k)
            history = engine.run_step_by_step(points)
            
            return Response(history)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

def simulator_view(request):
    """Отображает страницу тренажера"""
    return render(request, 'simulator/index.html')
