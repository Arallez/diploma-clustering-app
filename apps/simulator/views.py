import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from .models import Task, TaskTag, UserTaskAttempt
from .services import SolutionValidator
from .algorithms import (
    kmeans_step, 
    dbscan_step, 
    forel_step, 
    agglomerative_step,
    mean_shift_step
)

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
    Checks user solution using SolutionValidator service.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            slug = data.get('slug')
            user_input = data.get('code') 
            
            task = get_object_or_404(Task, slug=slug)
            
            # Delegate logic to Service Layer
            is_correct, message, error_msg, details = SolutionValidator.validate(task, user_input)

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
            
            response_data = {'success': is_correct}
            if is_correct:
                response_data['message'] = 'Правильно!'
            else:
                response_data['error'] = error_msg
                
            # Merge extra details (like quiz results)
            if details:
                response_data.update(details)
            
            return JsonResponse(response_data)
                
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
