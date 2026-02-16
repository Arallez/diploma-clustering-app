import secrets
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def generate_join_code():
    """Генерирует уникальный код подключения к группе (8 символов)."""
    return secrets.token_hex(4).upper()


class TeacherProfile(models.Model):
    """Профиль преподавателя — пользователи с такой записью могут создавать группы и тесты."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Преподаватель'
        verbose_name_plural = 'Преподаватели'

    def __str__(self):
        return self.user.get_username()


class StudentGroup(models.Model):
    """Учебная группа. Студенты подключаются по коду."""
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_groups')
    name = models.CharField(max_length=200, verbose_name='Название группы')
    join_code = models.CharField(max_length=16, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return f"{self.name} ({self.join_code})"

    def save(self, *args, **kwargs):
        if not self.join_code:
            self.join_code = generate_join_code()
            while StudentGroup.objects.filter(join_code=self.join_code).exists():
                self.join_code = generate_join_code()
        super().save(*args, **kwargs)


class GroupMembership(models.Model):
    """Участие студента в группе."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE, related_name='members')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'group')]
        verbose_name = 'Участник группы'
        verbose_name_plural = 'Участники групп'

    def __str__(self):
        return f"{self.user.username} в {self.group.name}"


class Test(models.Model):
    """Тест: создаётся преподавателем для группы, с ограничением по времени и окном доступности."""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_tests')
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE, related_name='tests')
    title = models.CharField(max_length=200, verbose_name='Название теста')
    tasks = models.ManyToManyField(
        'tasks.Task',
        related_name='scheduled_tests',
        blank=True,
        verbose_name='Задания'
    )
    time_limit_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name='Лимит времени (минут)'
    )
    opens_at = models.DateTimeField(verbose_name='Открывается')
    closes_at = models.DateTimeField(verbose_name='Закрывается')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'

    def __str__(self):
        return f"{self.title} ({self.group.name})"

    def is_active(self):
        now = timezone.now()
        return self.opens_at <= now <= self.closes_at

    def is_future(self):
        return timezone.now() < self.opens_at

    def is_past(self):
        return timezone.now() > self.closes_at


class TestAttempt(models.Model):
    """Попытка студента пройти тест (одна попытка на тест на студента — можно ослабить при необходимости)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Попытка прохождения теста'
        verbose_name_plural = 'Попытки прохождения тестов'
        # Один студент — одна попытка на тест (при желании можно убрать и разрешить несколько)
        unique_together = [('user', 'test')]

    def __str__(self):
        status = 'Завершён' if self.submitted_at else 'В процессе'
        return f"{self.user.username} — {self.test.title} ({status})"

    @property
    def is_submitted(self):
        return self.submitted_at is not None
