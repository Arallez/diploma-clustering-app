import json
import math
import numpy as np
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from .models import Task, UserTaskAttempt
from .algorithms import (
    kmeans_step, 
    dbscan_step, 
    forel_step, 
    agglomerative_step,
    compute_dendrogram_data,
    mean_shift_step
)
from .presets import generate_preset

# --- Page Views ---

def index(request):
    """Main simulator page"""
    return render(request, 'simulator/index.html')

def task_list(request):
    """List of educational tasks (Reverted to flat list)"""
    tasks = Task.objects.all().order_by('algorithm', 'order')
    return render(request, 'simulator/task_list.html', {'tasks': tasks})

def challenge_detail(request, slug):
    """Specific challenge page"""
    task = get_object_or_404(Task, slug=slug)
    
    previous_code = ""
    if request.user.is_authenticated:
        last_attempt = request.user.task_attempts.filter(task=task, is_correct=True).first()
        if last_attempt:
            previous_code = last_attempt.code
    
    return render(request, 'simulator/challenge_detail.html', {
        'task': task,
        'previous_code': previous_code or task.initial_code
    })

# --- API Endpoints ---

@csrf_exempt
def run_algorithm(request):
    """Unified endpoint for running all clustering algorithms"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            algo = data.get('algorithm')
            points = data.get('points', [])
            params = data.get('params', {})
            
            history = []
            
            if algo == 'kmeans':
                k = int(params.get('k', 3))
                history = kmeans_step(points, k)
            elif algo == 'dbscan':
                eps = float(params.get('eps', 0.5))
                min_pts = int(params.get('minPts', 3))
                history = dbscan_step(points, eps, min_pts)
            elif algo == 'forel':
                r = float(params.get('radius', 1.0))
                history = forel_step(points, r)
            elif algo == 'agglomerative':
                k = int(params.get('k', 2))
                history = agglomerative_step(points, k)
            elif algo == 'meanshift':
                bandwidth = float(params.get('bandwidth', 1.0))
                history = mean_shift_step(points, bandwidth)
            else:
                return JsonResponse({'success': False, 'error': f'Unknown algorithm: {algo}'})
                
            return JsonResponse({'success': True, 'history': history})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

@csrf_exempt
def check_solution(request):
    """
    Checks user solution by running it against test data.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            slug = data.get('slug')
            user_code = data.get('code')
            
            task = get_object_or_404(Task, slug=slug)
            
            # Prepare Execution Context (Globals)
            # This ensures functions defined in user_code can see these imports
            execution_context = {
                'np': np,
                'math': math,
                'List': list,
                'Dict': dict,
                'abs': abs,
                'len': len,
                'range': range,
                'sum': sum,
                'min': min,
                'max': max,
                'int': int,
                'float': float,
                'sorted': sorted,
                'zip': zip,
                'map': map,
                'filter': filter,
                'enumerate': enumerate,
            }
            
            # 1. Execute User Code
            try:
                # Pass execution_context as globals so defined functions inherit it
                exec(user_code, execution_context)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Syntax Error: {e}'})
                
            func_name = task.function_name
            if func_name not in execution_context:
                return JsonResponse({'success': False, 'error': f'Функция {func_name} не найдена. Не меняйте название!'})
                
            user_func = execution_context[func_name]
            
            # 2. Prepare Inputs
            test_input = task.test_input
            expected = task.expected_output
            
            # 3. Smart Execution (Handle unpacking vs single arg)
            try:
                if isinstance(test_input, dict):
                    # Keyword arguments
                    result = user_func(**test_input)
                elif isinstance(test_input, list):
                    # Try unpacking first (*args)
                    try:
                        result = user_func(*test_input)
                    except TypeError:
                        # Fallback: Pass the list as a single argument
                        result = user_func(test_input)
                else:
                    result = user_func(test_input)
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Runtime Error: {e}'})
                
            # 4. Compare Results
            is_correct = False
            
            # Normalize results for comparison (numpy arrays to lists)
            if isinstance(result, np.ndarray):
                result = result.tolist()
            if isinstance(expected, np.ndarray):
                expected = expected.tolist()

            if isinstance(expected, (list, dict)):
                is_correct = (str(result) == str(expected)) 
                
                if not is_correct:
                    try:
                         # Try loose comparison for floats
                         is_correct = np.allclose(result, expected, atol=1e-2)
                    except:
                        pass
            else:
                is_correct = (result == expected)
                
            if request.user.is_authenticated:
                UserTaskAttempt.objects.create(
                    user=request.user,
                    task=task,
                    code=user_code,
                    is_correct=is_correct,
                    error_message=None if is_correct else f"Expected {expected}, got {result}"
                )
                
            if is_correct:
                return JsonResponse({'success': True, 'message': f'Тест пройден! Ответ: {result}'})
            else:
                return JsonResponse({
                    'success': False, 
                    'error': f'Неверный ответ. Ожидалось: {expected}, Получено: {result}'
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

# Legacy stubs
@csrf_exempt
def get_preset(request):
    if request.method == 'GET':
        name = request.GET.get('name')
        n_samples = int(request.GET.get('samples', 100))
        try:
            points = generate_preset(name, n_samples)
            return JsonResponse({'success': True, 'points': points})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

@csrf_exempt
def get_dendrogram(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            points = data.get('points', [])
            dendro_data = compute_dendrogram_data(points)
            return JsonResponse({
                'success': True, 
                'dendrogram': {
                    'icoord': dendro_data['icoord'],
                    'dcoord': dendro_data['dcoord'],
                    'ivl': dendro_data['ivl'],
                    'leaves': dendro_data['leaves']
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

@csrf_exempt
def run_kmeans(request): return run_algorithm(request)
@csrf_exempt
def run_dbscan(request): return run_algorithm(request)
@csrf_exempt
def run_forel(request): return run_algorithm(request)
@csrf_exempt
def run_agglomerative(request): return run_algorithm(request)
