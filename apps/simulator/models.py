from django.db import models
from django.contrib.auth.models import User

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
    order = models.IntegerField(default=0, verbose_name="Порядок")
    
    # Поля для кода
    function_name = models.CharField(max_length=100, help_text="Имя функции, которую должен написать юзер")
    initial_code = models.TextField(verbose_name="Заготовка кода")
    solution_code = models.TextField(verbose_name="Эталонное решение (для проверки)")
    
    # Тестовые данные (JSON)
    test_input = models.JSONField(default=dict, verbose_name="Входные данные теста")
    expected_output = models.JSONField(default=dict, verbose_name="Ожидаемый ответ")

    def __str__(self):
        return f"{self.order}. {self.title}"

    class Meta:
        ordering = ['order']
