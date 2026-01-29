import json
import math
import ast
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

# --- Security Helper ---
def is_safe_code(code_str):
    """
    Static analysis of user code to prevent dangerous operations.
    Returns (True, "") or (False, error_message).
    """
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"

    for node in ast.walk(tree):
        # 1. Ban direct imports (users must use provided 'np', 'math')
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return False, "Security Error: Direct imports are not allowed. Use pre-imported libraries (np, math)."
        
        # 2. Ban accessing private attributes (starting with _)
        if isinstance(node, ast.Attribute) and node.attr.startswith('_'):
             return False, "Security Error: Access to private attributes (starting with _) is forbidden."
             
        # 3. Ban 'exec', 'eval', 'open' calls if they managed to sneak in
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in ['exec', 'eval', 'open', 'help', 'exit', 'quit']:
                return False, f"Security Error: Function '{node.func.id}' is forbidden."

    return True, ""

# --- Page Views ---

def index(request):
    """Main simulator page"""
    return render(request, 'simulator/index.html')

def task_list(request):
    """List of educational tasks grouped by Tag/Block"""
    tags = TaskTag.objects.prefetch_related('tasks').order_by('order')
    uncategorized = Task.objects.filter(tags__isnull=True).order_by('order')
    
    # Get completed task IDs for the current user
    completed_task_ids = set()
    if request.user.is_authenticated:
        completed_task_ids = set(
            UserTaskAttempt.objects.filter(
                user=request.user, 
                is_correct=True
            ).values_list('task_id', flat=True)
        )
    
    return render(request, 'simulator/task_list.html', {
        'tags': tags,
        'uncategorized': uncategorized,
        'completed_task_ids': completed_task_ids
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
def get_preset(request):
    """
    Returns points for a selected preset (Blobs, Moons, etc.)
    """
    if request.method == 'GET':
        try:
            # Get params (frontend sends 'name', keeping 'preset' for backward compat)
            preset_name = request.GET.get('name') or request.GET.get('preset') or 'blobs'
            
            # Generate 300 points by default for the simulator
            data = generate_preset(preset_name, n_samples=300)
            
            return JsonResponse({'success': True, 'points': data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

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
            result_details = {} # Detailed feedback for quiz
            error_msg = None
            
            # --- HANDLE QUIZ (CHOICE) ---
            if task.task_type == 'choice':
                expected = task.expected_output
                
                # Normalize types for comparison
                if isinstance(user_input, list) and isinstance(expected, list):
                    # Multi-question comparison
                    # Compare arrays strictly
                    is_correct = (user_input == expected)
                    
                    # Generate detailed feedback (which index is wrong)
                    # We send back an array of booleans [true, false, true]
                    correctness_array = []
                    for i in range(len(expected)):
                        if i < len(user_input):
                            is_match = (user_input[i] == expected[i])
                            correctness_array.append(is_match)
                        else:
                            correctness_array.append(False)
                            
                    result_details = {'quiz_results': correctness_array}
                    
                else:
                    # Single question comparison
                    expected_str = str(expected).strip()
                    submitted_str = str(user_input).strip()
                    is_correct = (submitted_str == expected_str)
                
                if not is_correct:
                    if isinstance(expected, list):
                        error_msg = "Некоторые ответы неверны. Проверьте выделенные пункты."
                    else:
                        error_msg = f"Выбрано: {user_input}. Попробуйте еще раз."

            # --- HANDLE CODE ---
            else:
                # 1. Static Analysis Check
                is_safe, security_msg = is_safe_code(user_input)
                if not is_safe:
                    return JsonResponse({'success': False, 'error': security_msg})

                # 2. Restricted Execution Context (Whitelist)
                # Only these variables are available to the user script
                execution_context = {
                    'np': np, 'math': math, 'List': list, 'Dict': dict, 'Set': set, 'Tuple': tuple,
                    'abs': abs, 'len': len, 'range': range, 'sum': sum, 
                    'min': min, 'max': max, 'int': int, 'float': float, 'str': str, 'bool': bool,
                    'sorted': sorted, 'zip': zip, 'map': map, 'filter': filter, 'enumerate': enumerate,
                    'print': print, 'round': round, 'all': all, 'any': any, 'divmod': divmod,
                    # Explicitly block access to 'open', '__import__', etc. by not including them
                    '__builtins__': {} 
                }
                
                try:
                    exec(user_input, execution_context)
                except Exception as e:
                    return JsonResponse({'success': False, 'error': f'Syntax/Runtime Error: {e}'})
                    
                func_name = task.function_name
                if func_name not in execution_context:
                    return JsonResponse({'success': False, 'error': f'Функция {func_name} не найдена. Проверьте имя функции.'})
                    
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
                    return JsonResponse({'success': False, 'error': f'Function Call Error: {e}'})
                
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
                    
                error_msg = f"Ожидалось: {expected}, Получено: {result}" if not is_correct else None

            # --- SAVE ATTEMPT ---
            if request.user.is_authenticated:
                code_to_save = json.dumps(user_input, ensure_ascii=False) if isinstance(user_input, (list, dict)) else str(user_input)
                
                UserTaskAttempt.objects.create(
                    user=request.user,
                    task=task,
                    code=code_to_save,
                    is_correct=is_correct,
                    error_message=error_msg
                )
            
            response_data = {'success': is_correct}
            if is_correct:
                response_data['message'] = 'Правильно!'
            else:
                response_data['error'] = error_msg
                
            # Merge extra details (like per-question results)
            response_data.update(result_details)
            
            return JsonResponse(response_data)
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

# Legacy stubs
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
