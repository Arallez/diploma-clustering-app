from django.db import models
from django.urls import reverse

class Material(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="Slug (URL)")
    content = models.TextField(verbose_name="Содержание (HTML/Markdown)")
    order = models.PositiveIntegerField(
        unique=True,  # Запрет дублирования позиций
        verbose_name="Порядок сортировки",
        help_text="Уникальная позиция в списке материалов"
    )
    
    # Связь с тегами задач (ManyToMany для гибкости)
    tags = models.ManyToManyField(
        'tasks.TaskTag',
        blank=True,
        related_name='materials',
        verbose_name="Связанные темы",
        help_text="К каким темам задач относится этот материал"
    )
    
    # Связь с онтологией для адаптивного обучения
    concept = models.ForeignKey(
        'encyclopedia.Concept',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='materials',
        verbose_name="Понятие из онтологии",
        help_text="Какое понятие из онтологии объясняет этот материал"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Учебный материал"
        verbose_name_plural = "Учебные материалы"
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:material_detail', kwargs={'slug': self.slug})
