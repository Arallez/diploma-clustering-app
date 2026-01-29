import json
import math
import numpy as np
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from .models import Task, TaskTag, UserTaskAttempt
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
    """List of educational tasks grouped by Tag/Block"""
    tags = TaskTag.objects.prefetch_related('tasks').order_by('order')
    uncategorized = Task.objects.filter(tags__isnull=True).order_by('order')
    return render(request, 'simulator/task_list.html', {
        'tags': tags,
        'uncategorized': uncategorized
    })

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
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

@csrf_exempt
def check_solution(request):
    """
    Checks user solution (Code execution or Quiz answer).
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            slug = data.get('slug')
            user_input = data.get('code') # Contains code or selected option(s)
            
            task = get_object_or_404(Task, slug=slug)
            
            is_correct = False
            result_message = ""
            
            # --- HANDLE QUIZ (CHOICE) ---
            if task.task_type == 'choice':
                expected = task.expected_output
                
                # Normalize types for comparison
                if isinstance(user_input, list) and isinstance(expected, list):
                    # Multi-question comparison
                    is_correct = (user_input == expected)
                    result_message = "Ответы приняты"
                else:
                    # Single question comparison
                    expected_str = str(expected).strip()
                    submitted_str = str(user_input).strip()
                    is_correct = (submitted_str == expected_str)
                    result_message = submitted_str
                
                if not is_correct:
                    if isinstance(expected, list):
                        # Simple error for multi-quiz
                        error_msg = f"Некоторые ответы неверны. Попробуйте снова."
                    else:
                        error_msg = f"Выбрано: {user_input}. Попробуйте еще раз."
                else:
                    error_msg = None

            # --- HANDLE CODE ---
            else:
                # Prepare Context
                execution_context = {
                    'np': np, 'math': math, 'List': list, 'Dict': dict,
                    'abs': abs, 'len': len, 'range': range, 'sum': sum, 
                    'min': min, 'max': max, 'int': int, 'float': float, 
                    'sorted': sorted, 'zip': zip, 'map': map, 'filter': filter, 'enumerate': enumerate,
                }
                
                try:
                    exec(user_input, execution_context)
                except Exception as e:
                    return JsonResponse({'success': False, 'error': f'Syntax Error: {e}'})
                    
                func_name = task.function_name
                if func_name not in execution_context:
                    return JsonResponse({'success': False, 'error': f'Функция {func_name} не найдена.'})
                    
                user_func = execution_context[func_name]
                test_input = task.test_input
                expected = task.expected_output
                
                try:
                    if isinstance(test_input, dict):
                        result = user_func(**test_input)
                    elif isinstance(test_input, list):
                        try:
                            result = user_func(*test_input)
                        except TypeError:
                            result = user_func(test_input)
                    else:
                        result = user_func(test_input)
                except Exception as e:
                    return JsonResponse({'success': False, 'error': f'Runtime Error: {e}'})
                
                # Compare
                if isinstance(result, np.ndarray): result = result.tolist()
                if isinstance(expected, np.ndarray): expected = expected.tolist()

                if isinstance(expected, (list, dict)):
                    is_correct = (str(result) == str(expected)) 
                    if not is_correct:
                        try: is_correct = np.allclose(result, expected, atol=1e-2)
                        except: pass
                else:
                    is_correct = (result == expected)
                    
                result_message = str(result)
                error_msg = f"Ожидалось: {expected}, Получено: {result}" if not is_correct else None

            # --- SAVE ATTEMPT ---
            if request.user.is_authenticated:
                # Store complex inputs as JSON string if needed
                code_to_save = json.dumps(user_input, ensure_ascii=False) if isinstance(user_input, (list, dict)) else str(user_input)
                
                UserTaskAttempt.objects.create(
                    user=request.user,
                    task=task,
                    code=code_to_save,
                    is_correct=is_correct,
                    error_message=error_msg
                )
                
            if is_correct:
                return JsonResponse({'success': True, 'message': 'Правильно!'})
            else:
                return JsonResponse({'success': False, 'error': error_msg})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

# Legacy stubs
@csrf_exempt
def get_preset(request): return JsonResponse({'success': False})
@csrf_exempt
def get_dendrogram(request): return JsonResponse({'success': False})
@csrf_exempt
def run_kmeans(request): return run_algorithm(request)
@csrf_exempt
def run_dbscan(request): return run_algorithm(request)
@csrf_exempt
def run_forel(request): return run_algorithm(request)
@csrf_exempt
def run_agglomerative(request): return run_algorithm(request)
