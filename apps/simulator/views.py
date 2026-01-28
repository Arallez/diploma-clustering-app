from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Task, UserTaskAttempt
from .algorithms import kmeans_step, dbscan_step, forel_step, agglomerative_step
from .presets import generate_preset

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
def run_forel(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            points = data.get('points', [])
            r = float(data.get('r', 1.0))
            
            if len(points) < 1:
                return JsonResponse({'success': False, 'error': 'Need points'})
            
            history = forel_step(points, r)
            return JsonResponse({'success': True, 'history': history})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def run_agglomerative(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            points = data.get('points', [])
            n_clusters = int(data.get('n_clusters', 2))
            
            if len(points) < n_clusters:
                return JsonResponse({'success': False, 'error': 'Not enough points'})
            
            history = agglomerative_step(points, n_clusters)
            return JsonResponse({'success': True, 'history': history})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def check_solution(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_slug = data.get('task_slug') or data.get('task_id')
            user_result = data.get('result')
            user_code = data.get('code', '')
            
            if not task_slug:
                return JsonResponse({'correct': False, 'message': 'Missing task_slug'})

            task = get_object_or_404(Task, slug=task_slug)
            expected = task.expected_output
            
            is_correct = False
            
            if isinstance(expected, float) and isinstance(user_result, (int, float)):
                is_correct = abs(user_result - expected) < 0.0001
            elif isinstance(expected, list) and isinstance(user_result, list):
                if len(expected) == len(user_result):
                    is_correct = all(
                        abs(e - u) < 0.0001 if isinstance(e, float) else e == u
                        for e, u in zip(expected, user_result)
                    )
            else:
                is_correct = user_result == expected
            
            if request.user.is_authenticated:
                UserTaskAttempt.objects.create(
                    user=request.user,
                    task=task,
                    code=user_code,
                    is_correct=is_correct,
                    error_message=None if is_correct else f'Expected: {expected}, Got: {user_result}'
                )
            
            if is_correct:
                return JsonResponse({
                    'correct': True,
                    'message': 'Правильно! Задание выполнено.'
                })
            else:
                return JsonResponse({
                    'correct': False,
                    'message': f'Неверно. Ожидалось: {expected}, получено: {user_result}'
                })
                
        except Exception as e:
            return JsonResponse({'correct': False, 'message': f'Ошибка сервера: {str(e)}'})
    return JsonResponse({'correct': False, 'message': 'Invalid request'})

@csrf_exempt
def get_preset(request):
    """Generate dataset presets for quick testing"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            preset_type = data.get('type', 'blobs')
            n_samples = int(data.get('n_samples', 100))
            
            points = generate_preset(preset_type, n_samples)
            return JsonResponse({'success': True, 'points': points})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})
