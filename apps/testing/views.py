from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlencode
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from zoneinfo import ZoneInfo

from .models import TeacherProfile, StudentGroup, GroupMembership, Test, TestAttempt
from apps.tasks.models import Task, UserTaskAttempt


def is_teacher(user):
    if not user.is_authenticated:
        return False
    return hasattr(user, 'teacher_profile') and user.teacher_profile is not None


def testing_home(request):
    """Главная вкладки «Тестирование»: для преподавателя — группы и тесты, для студента — подключение к группе и активные тесты."""
    if not request.user.is_authenticated:
        messages.warning(
            request,
            'Тестирование доступно только зарегистрированным пользователям. Войдите или зарегистрируйтесь.'
        )
        return redirect(reverse('login') + '?' + urlencode({'next': request.get_full_path()}))
    user = request.user
    teacher = is_teacher(user)

    if teacher:
        groups = StudentGroup.objects.filter(teacher=user).prefetch_related('members')
        tests = Test.objects.filter(owner=user).select_related('group').prefetch_related('tasks')
        return render(request, 'testing/teacher_home.html', {
            'groups': groups,
            'tests': tests,
        })

    # Студент: группы, в которых состоит, и все тесты по ним (активные, будущие, завершённые)
    memberships = GroupMembership.objects.filter(user=user).select_related('group')
    group_ids = [m.group_id for m in memberships]
    now = timezone.now()
    all_tests = []
    if group_ids:
        all_tests = list(
            Test.objects.filter(group_id__in=group_ids)
            .select_related('group')
            .prefetch_related('tasks')
            .order_by('-opens_at')
        )
    # Для каждого теста определяем статус: active, future, past
    tests_with_status = []
    for t in all_tests:
        if t.opens_at <= now <= t.closes_at:
            status = 'active'
        elif now < t.opens_at:
            status = 'future'
        else:
            status = 'past'
        tests_with_status.append({'test': t, 'status': status})
    # Уже начатые попытки (в процессе или завершённые)
    my_attempts = TestAttempt.objects.filter(user=user).select_related('test')

    return render(request, 'testing/student_home.html', {
        'memberships': memberships,
        'tests_with_status': tests_with_status,
        'my_attempts': my_attempts,
    })


@login_required
def join_group(request):
    """Подключиться к группе по коду."""
    if request.method == 'POST':
        code = (request.POST.get('join_code') or '').strip().upper()
        if not code:
            messages.error(request, 'Введите код группы.')
            return redirect('testing:home')
        group = StudentGroup.objects.filter(join_code=code).first()
        if not group:
            messages.error(request, 'Группа с таким кодом не найдена.')
            return redirect('testing:home')
        _, created = GroupMembership.objects.get_or_create(user=request.user, group=group)
        if created:
            messages.success(request, f'Вы подключились к группе «{group.name}».')
        else:
            messages.info(request, f'Вы уже в группе «{group.name}».')
        return redirect('testing:home')
    return redirect('testing:home')


@login_required
def create_group(request):
    """Создать группу (только преподаватель)."""
    if not is_teacher(request.user):
        messages.error(request, 'Доступ только для преподавателей.')
        return redirect('testing:home')
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        if not name:
            messages.error(request, 'Введите название группы.')
            return redirect('testing:home')
        group = StudentGroup.objects.create(teacher=request.user, name=name)
        messages.success(request, f'Группа «{group.name}» создана. Код подключения: {group.join_code}')
        return redirect('testing:home')
    return redirect('testing:home')


@login_required
def create_test(request):
    """Создать тест (только преподаватель)."""
    if not is_teacher(request.user):
        messages.error(request, 'Доступ только для преподавателей.')
        return redirect('testing:home')
    groups = StudentGroup.objects.filter(teacher=request.user)
    tasks = Task.objects.all().order_by('tags__order', 'order')
    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        group_id = request.POST.get('group')
        time_limit = request.POST.get('time_limit_minutes') or 30
        opens_at = request.POST.get('opens_at')
        closes_at = request.POST.get('closes_at')
        task_ids = request.POST.getlist('tasks')
        if not title or not group_id:
            messages.error(request, 'Укажите название и группу.')
            return render(request, 'testing/create_test.html', {'groups': groups, 'tasks': tasks})
        group = get_object_or_404(StudentGroup, pk=group_id, teacher=request.user)
        try:
            time_limit = int(time_limit)
            # Интерпретируем даты из формы как локальное время (напр. Europe/Moscow), не UTC
            tz_name = getattr(settings, 'TEST_DATETIME_TIMEZONE', None) or settings.TIME_ZONE
            try:
                tz = ZoneInfo(tz_name)
            except Exception:
                tz = ZoneInfo('UTC')
            if opens_at:
                try:
                    opens_at = datetime.strptime(opens_at, '%Y-%m-%dT%H:%M')
                    if timezone.is_naive(opens_at):
                        opens_at = timezone.make_aware(opens_at, tz)
                except ValueError:
                    opens_at = timezone.now()
            else:
                opens_at = timezone.now()
            if closes_at:
                try:
                    closes_at = datetime.strptime(closes_at, '%Y-%m-%dT%H:%M')
                    if timezone.is_naive(closes_at):
                        closes_at = timezone.make_aware(closes_at, tz)
                except ValueError:
                    closes_at = opens_at + timedelta(days=1)
            else:
                closes_at = opens_at + timedelta(days=1)
            if closes_at <= opens_at:
                closes_at = opens_at + timedelta(days=1)
        except (ValueError, TypeError):
            messages.error(request, 'Некорректные даты или время.')
            return render(request, 'testing/create_test.html', {'groups': groups, 'tasks': tasks})
        test = Test.objects.create(
            owner=request.user,
            group=group,
            title=title,
            time_limit_minutes=time_limit,
            opens_at=opens_at,
            closes_at=closes_at,
        )
        if task_ids:
            test.tasks.set(Task.objects.filter(pk__in=task_ids))
        messages.success(request, f'Тест «{test.title}» создан.')
        return redirect('testing:home')
    return render(request, 'testing/create_test.html', {'groups': groups, 'tasks': tasks})


@login_required
def start_test(request, test_id):
    """Начать тест (студент): создать TestAttempt и перейти на страницу прохождения."""
    test = get_object_or_404(Test, pk=test_id)
    if not test.is_active():
        messages.error(request, 'Этот тест сейчас недоступен.')
        return redirect('testing:home')
    # Проверяем, что пользователь в группе
    if not GroupMembership.objects.filter(user=request.user, group=test.group).exists():
        messages.error(request, 'Вы не в группе этого теста.')
        return redirect('testing:home')
    attempt, created = TestAttempt.objects.get_or_create(user=request.user, test=test)
    if not created and attempt.submitted_at:
        messages.info(request, 'Вы уже сдали этот тест.')
        return redirect('testing:home')
    return redirect('testing:take_test', attempt_id=attempt.pk)


@login_required
def take_test(request, attempt_id):
    """Страница прохождения теста: таймер и список заданий."""
    attempt = get_object_or_404(TestAttempt, pk=attempt_id, user=request.user)
    test = attempt.test
    if attempt.submitted_at:
        messages.info(request, 'Тест уже сдан.')
        return redirect('testing:home')
    if not test.is_active():
        messages.error(request, 'Время теста истекло.')
        return redirect('testing:home')
    task_list = list(test.tasks.all().order_by('tags__order', 'order'))
    # Время окончания: started_at + time_limit_minutes или closes_at — что раньше
    end_by_time = attempt.started_at + timedelta(minutes=test.time_limit_minutes)
    end_by_deadline = test.closes_at
    ends_at = min(end_by_time, end_by_deadline)
    return render(request, 'testing/take_test.html', {
        'attempt': attempt,
        'test': test,
        'task_list': task_list,
        'ends_at': ends_at,
    })


@login_required
def submit_test(request, attempt_id):
    """Завершить тест (поставить submitted_at)."""
    if request.method != 'POST':
        return redirect('testing:home')
    attempt = get_object_or_404(TestAttempt, pk=attempt_id, user=request.user)
    if attempt.submitted_at:
        return redirect('testing:home')
    attempt.submitted_at = timezone.now()
    attempt.save()
    messages.success(request, 'Тест сдан.')
    return redirect('testing:home')


@login_required
def test_results(request, test_id):
    """Результаты теста (преподаватель — по своему тесту)."""
    test = get_object_or_404(Test, pk=test_id)
    if test.owner_id != request.user.pk and not is_teacher(request.user):
        messages.error(request, 'Нет доступа.')
        return redirect('testing:home')
    attempts = TestAttempt.objects.filter(test=test).select_related('user').order_by('-started_at')
    return render(request, 'testing/test_results.html', {'test': test, 'attempts': attempts})
