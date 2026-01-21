from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Task
from .algorithms import kmeans_step, dbscan_step

def simulator_index(request):
    return render(request, 'simulator/index.html')

def task_list(request):
    tasks = Task.objects.all()
    if tasks.exists():
        return render(request, 'simulator/task_list.html', {'tasks': tasks})
    else:
        return render(request, 'simulator/no_tasks.html')

def challenge_detail(request, slug):
    task = get_object_or_404(Task, slug=slug)
    return render(request, 'simulator/challenge.html', {'task': task})

@csrf_exempt
def run_kmeans(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            points = data.get('points', [])
            k = int(data.get('k', 3))
            
            if len(points) < k:
                return JsonResponse({'success': False, 'error': 'Not enough points'})
            
            history = kmeans_step(points, k)
            return JsonResponse({'success': True, 'history': history})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def run_dbscan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            points = data.get('points', [])
            eps = float(data.get('eps', 1.0))
            min_pts = int(data.get('min_pts', 3))
            
            if len(points) < 2:
                return JsonResponse({'success': False, 'error': 'Need at least 2 points'})
            
            history = dbscan_step(points, eps, min_pts)
            return JsonResponse({'success': True, 'history': history})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def check_solution(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_slug = data.get('task_slug')
            user_code = data.get('code')
            test_input = data.get('test_input')
            
            task = get_object_or_404(Task, slug=task_slug)
            
            # Basic validation (actual execution happens in Pyodide on client)
            return JsonResponse({
                'success': True, 
                'message': 'Code received',
                'expected': task.expected_output
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})
