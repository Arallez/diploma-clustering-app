import json
import math
import random
import sys
import numpy as np
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

from .models import Task, TaskTag, UserTaskAttempt
from apps.simulator.services import (
    is_safe_code,
    create_tracer,
    TimeLimitException,
    get_safe_builtins,
)
from apps.encyclopedia.recommendations import is_task_available


def task_list(request):
    tags = TaskTag.objects.prefetch_related('tasks').order_by('order')
    uncategorized = Task.objects.filter(tags__isnull=True).order_by('order')
    completed_task_ids = set()
    available_task_ids = set()
    blocked_tasks_info = {}  # task_id -> list of missing concepts
    
    if request.user.is_authenticated:
        completed_task_ids = set(
            UserTaskAttempt.objects.filter(user=request.user, is_correct=True).values_list('task_id', flat=True)
        )
        
        # Проверяем доступность задач на основе онтологии
        all_tasks = Task.objects.filter(concept__isnull=False).select_related('concept')
        for task in all_tasks:
            is_available, missing_concepts = is_task_available(request.user, task)
            if is_available:
                available_task_ids.add(task.id)
            else:
                blocked_tasks_info[task.id] = missing_concepts
    
    # Задачи без связи с онтологией всегда доступны
    tasks_without_concept = Task.objects.filter(concept__isnull=True)
    available_task_ids.update(tasks_without_concept.values_list('id', flat=True))
    
    return render(request, 'tasks/task_list.html', {
        'tags': tags,
        'uncategorized': uncategorized,
        'completed_task_ids': completed_task_ids,
        'available_task_ids': available_task_ids,
        'blocked_tasks_info': blocked_tasks_info,
    })


@ensure_csrf_cookie
def challenge_detail(request, slug):
    task = get_object_or_404(Task, slug=slug)
    previous_code = ""
    test_attempt_id = None
    is_available = True
    missing_concepts = []
    required_materials = []
    
    if request.user.is_authenticated:
        last_attempt = request.user.task_attempts.filter(task=task, is_correct=True).first()
        if last_attempt:
            previous_code = last_attempt.code
        ta_id = request.GET.get('test_attempt')
        if ta_id:
            from apps.testing.models import TestAttempt
            ta = TestAttempt.objects.filter(pk=ta_id, user=request.user).first()
            if ta and not ta.submitted_at:
                test_attempt_id = ta.pk
        
        # Проверяем доступность задачи на основе онтологии
        if task.concept:
            is_available, missing_concepts = is_task_available(request.user, task)
            if missing_concepts:
                from apps.core.models import Material
                required_materials = Material.objects.filter(concept__in=missing_concepts)
    
    return render(request, 'tasks/challenge_detail.html', {
        'task': task,
        'previous_code': previous_code or task.initial_code,
        'test_attempt_id': test_attempt_id,
        'is_available': is_available,
        'missing_concepts': missing_concepts,
        'required_materials': required_materials,
    })


@csrf_exempt
def check_solution(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    try:
        data = json.loads(request.body)
        slug = data.get('slug') or data.get('task_slug')
        user_input = data.get('code')
        test_attempt_id = data.get('test_attempt_id')
        task = get_object_or_404(Task, slug=slug)
        is_correct = False
        result_details = {}
        error_msg = None

        if task.task_type == 'choice':
            expected = task.expected_output
            if isinstance(user_input, list) and isinstance(expected, list):
                is_correct = user_input == expected
                result_details = {'quiz_results': [
                    i < len(user_input) and user_input[i] == expected[i] for i in range(len(expected))
                ]}
            else:
                is_correct = (str(user_input).strip() == str(expected).strip())
            if not is_correct:
                error_msg = "Некоторые ответы неверны." if isinstance(expected, list) else f"Выбрано: {user_input}."
        else:
            is_safe, security_msg = is_safe_code(user_input)
            if not is_safe:
                return JsonResponse({'success': False, 'error': security_msg})
            safe_builtins = get_safe_builtins()
            execution_context = {'__builtins__': safe_builtins, 'np': np, 'math': math, 'random': random}
            try:
                sys.settrace(create_tracer(max_instructions=200000))
                try:
                    exec(user_input, execution_context)
                finally:
                    sys.settrace(None)
            except TimeLimitException as e:
                return JsonResponse({'success': False, 'error': str(e)})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Syntax/Runtime Error: {e}'})
            if task.function_name not in execution_context:
                return JsonResponse({'success': False, 'error': f'Функция {task.function_name} не найдена.'})
            user_func = execution_context[task.function_name]
            test_input = task.test_input
            expected = task.expected_output
            try:
                sys.settrace(create_tracer(max_instructions=200000))
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
                finally:
                    sys.settrace(None)
            except TimeLimitException as e:
                return JsonResponse({'success': False, 'error': str(e)})
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Runtime Error: {e}'})
            if isinstance(result, np.ndarray):
                result = result.tolist()
            if isinstance(expected, np.ndarray):
                expected = expected.tolist()
            is_correct = str(result) == str(expected) if isinstance(expected, (list, dict)) else (result == expected)
            if not is_correct and isinstance(expected, (list, dict)):
                try:
                    is_correct = np.allclose(result, expected, atol=1e-2)
                except Exception:
                    pass
            error_msg = f"Ожидалось: {expected}, Получено: {result}" if not is_correct else None

        if request.user.is_authenticated:
            code_to_save = json.dumps(user_input, ensure_ascii=False) if isinstance(user_input, (list, dict)) else str(user_input)
            test_attempt = None
            if test_attempt_id:
                from apps.testing.models import TestAttempt
                ta = TestAttempt.objects.filter(pk=test_attempt_id, user=request.user).first()
                if ta and not ta.submitted_at:
                    test_attempt = ta
            UserTaskAttempt.objects.create(
                user=request.user, task=task, code=code_to_save, is_correct=is_correct,
                error_message=error_msg, test_attempt=test_attempt,
            )
        response_data = {'success': is_correct, 'correct': is_correct}
        if is_correct:
            response_data['message'] = 'Правильно!'
        else:
            response_data['error'] = error_msg
        response_data.update(result_details)
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
