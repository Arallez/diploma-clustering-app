from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .forms import UserRegisterForm
from apps.simulator.models import Task, UserTaskAttempt

def home(request):
    return render(request, 'core/home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            
            # Send Welcome Email
            try:
                subject = 'Добро пожаловать в Clustering Trainer!'
                html_message = render_to_string('emails/welcome.html', {'username': username})
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject,
                    plain_message,
                    None, # Uses DEFAULT_FROM_EMAIL
                    [email],
                    html_message=html_message,
                    fail_silently=True # Don't crash if email fails
                )
            except Exception as e:
                print(f"Error sending email: {e}")

            messages.success(request, f'Создан аккаунт для {username}! Письмо отправлено на почту.')
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
