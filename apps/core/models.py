from django.db import models
from django.urls import reverse

class Material(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="Slug (URL)")
    content = models.TextField(verbose_name="Содержание (HTML/Markdown)")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")
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
