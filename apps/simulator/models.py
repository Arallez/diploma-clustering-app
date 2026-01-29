from django.db import models
from django.contrib.auth.models import User

class TaskTag(models.Model):
    """Теги (Категории) для группировки задач"""
    name = models.CharField(max_length=100, verbose_name="Название тега")
    slug = models.SlugField(unique=True, verbose_name="Slug (для URL)")
    order = models.IntegerField(default=0, verbose_name="Порядок вывода")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Тег (Блок задач)"
        verbose_name_plural = "Теги задач"

    def __str__(self):
        return self.name

class Task(models.Model):
    DIFFICULTY_CHOICES = [
        (1, '⭐ Novice (Основы)'),
        (2, '⭐⭐ Beginner (Логика)'),
        (3, '⭐⭐⭐ Intermediate (Алгоритмы)'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(unique=True, help_text="URL-имя, например 'euclidean-dist'")
    description = models.TextField(verbose_name="Описание (HTML)")
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=1)
    
    # Changed from hardcoded algorithm choices to dynamic ForeignKey
    tags = models.ForeignKey(
        TaskTag, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='tasks',
        verbose_name="Тег (Блок)"
    )
    
    order = models.IntegerField(default=0, verbose_name="Порядок")
    
    function_name = models.CharField(max_length=100, help_text="Имя функции")
    initial_code = models.TextField(verbose_name="Заготовка кода")
    solution_code = models.TextField(verbose_name="Эталонное решение")
    
    test_input = models.JSONField(default=dict, verbose_name="Входные данные")
    expected_output = models.JSONField(default=dict, verbose_name="Ожидаемый ответ")

    def __str__(self):
        tag_name = self.tags.name if self.tags else "Без тега"
        return f"{self.order}. {self.title} ({tag_name})"

    class Meta:
        ordering = ['tags__order', 'order']


class UserTaskAttempt(models.Model):
    """История попыток решения заданий"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_attempts')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attempts')
    code = models.TextField(verbose_name="Код решения")
    is_correct = models.BooleanField(default=False, verbose_name="Правильно")
    error_message = models.TextField(blank=True, null=True, verbose_name="Сообщение об ошибке")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата попытки")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Попытка решения"
        verbose_name_plural = "Попытки решений"

    def __str__(self):
        status = "✅" if self.is_correct else "❌"
        return f"{status} {self.user.username} - {self.task.title} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"
