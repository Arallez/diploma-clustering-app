from django.db import models
from django.contrib.auth.models import User


class TaskTag(models.Model):
    """Теги (категории) для группировки задач."""
    name = models.CharField(max_length=100, verbose_name="Название тега")
    slug = models.SlugField(unique=True, verbose_name="Slug (для URL)")
    order = models.IntegerField(default=0, verbose_name="Порядок вывода")

    class Meta:
        db_table = 'simulator_tasktag'
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
    TASK_TYPE_CHOICES = [
        ('code', '💻 Написание кода'),
        ('choice', '📝 Выбор ответа (Тест)'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(unique=True, help_text="URL-имя, например 'euclidean-dist'")
    description = models.TextField(verbose_name="Описание (HTML)")
    task_type = models.CharField(
        max_length=20, choices=TASK_TYPE_CHOICES, default='code', verbose_name="Тип задачи"
    )
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=1)
    tags = models.ForeignKey(
        TaskTag,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name="Тег (Блок)",
    )
    order = models.IntegerField(
        default=0,
        verbose_name="Порядок",
        help_text="Позиция внутри тега (должна быть уникальной)",
    )
    function_name = models.CharField(max_length=100, blank=True, null=True, help_text="Только для задач с кодом")
    initial_code = models.TextField(blank=True, verbose_name="Заготовка кода / Комментарий")
    solution_code = models.TextField(blank=True, verbose_name="Эталонное решение / Пояснение")
    test_input = models.JSONField(default=dict, blank=True, verbose_name="Входные данные / Варианты ответа")
    expected_output = models.JSONField(default=dict, blank=True, verbose_name="Ожидаемый ответ")

    class Meta:
        db_table = 'simulator_task'
        ordering = ['tags__order', 'order']
        constraints = [
            models.UniqueConstraint(
                fields=['tags', 'order'],
                name='unique_task_order_per_tag',
                violation_error_message="Задание с такой позицией уже существует в этом теге.",
            )
        ]

    def __str__(self):
        tag_name = self.tags.name if self.tags else "Без тега"
        type_icon = "💻" if self.task_type == 'code' else "📝"
        return f"{self.order}. {type_icon} {self.title} ({tag_name})"


class UserTaskAttempt(models.Model):
    """История попыток решения заданий."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_attempts')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attempts')
    code = models.TextField(verbose_name="Код решения / Ответ пользователя")
    is_correct = models.BooleanField(default=False, verbose_name="Правильно")
    error_message = models.TextField(blank=True, null=True, verbose_name="Сообщение об ошибке")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата попытки")
    test_attempt = models.ForeignKey(
        'testing.TestAttempt',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='task_attempts',
        verbose_name='Попытка теста (если в рамках теста)',
    )

    class Meta:
        db_table = 'simulator_usertaskattempt'
        ordering = ['-created_at']
        verbose_name = "Попытка решения"
        verbose_name_plural = "Попытки решений"

    def __str__(self):
        status = "✅" if self.is_correct else "❌"
        return f"{status} {self.user.username} - {self.task.title} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"
