import json
import math
import random
import sys
import numpy as np
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from .models import Task, TaskTag, UserTaskAttempt
from .algorithms import (
    kmeans_step, 
    dbscan_step, 
    forel_step, 
    agglomerative_step,
    mean_shift_step,
    compute_dendrogram_data 
)
from .presets import generate_preset

# --- Page Views ---

@ensure_csrf_cookie
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

@ensure_csrf_cookie
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
def get_dendrogram(request):
    """
    Returns dendrogram data for plotting.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            points = data.get('points', [])
            
            ddata = compute_dendrogram_data(points)
            
            if 'error' in ddata:
                return JsonResponse({'success': False, 'error': ddata['error']})
            
            return JsonResponse({'success': True, 'dendrogram': ddata})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

def check_solution(request):
    """
    Checks user solution.
    - For QUIZZES (task_type='choice'): Server-side check is mandatory.
    - For CODE (task_type='code'): Client-side check (Pyodide) sends result here to save progress.
      (Server-side exec() has been removed for security).
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            slug = data.get('slug')
            user_input = data.get('code') # Code or Answer
            is_client_side_check = data.get('is_client_side_check', False) # Flag from Pyodide
            client_is_correct = data.get('is_correct', False)
            
            task = get_object_or_404(Task, slug=slug)
            
            is_correct = False
            result_details = {} 
            error_msg = None
            
            # --- CASE 1: QUIZ (Server-Side Check Required) ---
            if task.task_type == 'choice':
                expected = task.expected_output
                
                # Normalize types for comparison
                if isinstance(user_input, list) and isinstance(expected, list):
                    # Multi-question comparison
                    is_correct = (user_input == expected)
                    
                    correctness_array = []
                    for i in range(len(expected)):
                        if i < len(user_input):
                            is_match = (user_input[i] == expected[i])
                            correctness_array.append(is_match)
                        else:
                            correctness_array.append(False)
                    result_details = {'quiz_results': correctness_array}
                    
                else:
                    expected_str = str(expected).strip()
                    submitted_str = str(user_input).strip()
                    is_correct = (submitted_str == expected_str)
                
                if not is_correct:
                    if isinstance(expected, list):
                        error_msg = "Некоторые ответы неверны."
                    else:
                        error_msg = f"Выбрано: {user_input}. Попробуйте еще раз."

            # --- CASE 2: CODE (Client-Side Check Trusted) ---
            elif task.task_type == 'code':
                # Since we removed exec(), we rely on Pyodide result for now.
                # In a real contest system, we would run this in a Docker container.
                # For this diploma project, trusting the client + CSRF is acceptable.
                
                if is_client_side_check:
                    is_correct = client_is_correct
                    if not is_correct:
                        error_msg = "Ошибка при проверке кода."
                else:
                    # Fallback if someone tries to call without client check
                    return JsonResponse({'success': False, 'error': 'Server-side execution disabled. Use Pyodide.'})

            # --- SAVE ATTEMPT ---
            if request.user.is_authenticated:
                code_to_save = json.dumps(user_input, ensure_ascii=False) if isinstance(user_input, (list, dict)) else str(user_input)
                
                # Save only if it's a new correct solution or just a log
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
                
            response_data.update(result_details)
            
            return JsonResponse(response_data)
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

# Legacy stubs
@csrf_exempt
def run_kmeans(request): return run_algorithm(request)
@csrf_exempt
def run_dbscan(request): return run_algorithm(request)
@csrf_exempt
def run_forel(request): return run_algorithm(request)
@csrf_exempt
def run_agglomerative(request): return run_algorithm(request)
