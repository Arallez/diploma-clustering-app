from django.db import models
from django.contrib.auth.models import User

class TaskCategory(models.Model):
    """Категория (блок) задач, например 'Модуль 1: Основы'"""
    title = models.CharField(max_length=200, verbose_name="Название блока")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")
    
    class Meta:
        verbose_name = "Блок задач"
        verbose_name_plural = "Блоки задач"
        ordering = ['order']

    def __str__(self):
        return self.title


class Task(models.Model):
    DIFFICULTY_CHOICES = [
        (1, '⭐ Novice (Основы)'),
        (2, '⭐⭐ Beginner (Логика)'),
        (3, '⭐⭐⭐ Intermediate (Алгоритмы)'),
    ]

    ALGORITHM_CHOICES = [
        ('kmeans', 'K-Means'),
        ('dbscan', 'DBSCAN'),
        ('hierarchical', 'Иерархическая кластеризация'),
        ('general', 'Общие знания'),
    ]

    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks', verbose_name="Блок (Категория)")
    
    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(unique=True, help_text="URL-имя, например 'euclidean-dist'")
    description = models.TextField(verbose_name="Описание (HTML)")
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=1)
    
    # We keep algorithm for backward compatibility or filtering, but grouping will now primarily rely on Category
    algorithm = models.CharField(max_length=50, choices=ALGORITHM_CHOICES, default='general', verbose_name="Алгоритм (Тег)")
    
    order = models.IntegerField(default=0, verbose_name="Порядок в блоке")
    
    function_name = models.CharField(max_length=100, help_text="Имя функции")
    initial_code = models.TextField(verbose_name="Заготовка кода")
    solution_code = models.TextField(verbose_name="Эталонное решение")
    
    test_input = models.JSONField(default=dict, verbose_name="Входные данные")
    expected_output = models.JSONField(default=dict, verbose_name="Ожидаемый ответ")

    def __str__(self):
        return f"{self.order}. {self.title}"

    class Meta:
        ordering = ['category__order', 'order']


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
