from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .forms import UserRegisterForm
from apps.simulator.models import Task, UserTaskAttempt

def home(request):
    return render(request, 'core/home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Создан аккаунт для {username}! Теперь вы можете войти.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def profile(request):
    user = request.user
    
    # 1. Общая статистика
    total_tasks = Task.objects.count()
    
    # Количество уникальных решенных задач (где is_correct=True)
    solved_tasks_count = UserTaskAttempt.objects.filter(
        user=user, 
        is_correct=True
    ).values('task').distinct().count()
    
    # Прогресс в процентах
    progress_percent = int((solved_tasks_count / total_tasks * 100)) if total_tasks > 0 else 0
    
    # 2. История последних действий (последние 10 попыток)
    recent_attempts = UserTaskAttempt.objects.filter(user=user).select_related('task')[:10]
    
    context = {
        'user': user,
        'total_tasks': total_tasks,
        'solved_tasks_count': solved_tasks_count,
        'progress_percent': progress_percent,
        'recent_attempts': recent_attempts,
    }
    
    return render(request, 'core/profile.html', context)
