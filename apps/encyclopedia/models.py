from django.db import models

class Concept(models.Model):
    """
    Узел онтологии (Понятие).
    Хранит информацию о термине, алгоритме или метрике.
    """
    uri = models.CharField(max_length=255, unique=True, help_text="Уникальный ID из OWL-онтологии")
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание (Markdown)", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Понятие"
        verbose_name_plural = "Понятия"

class ConceptRelation(models.Model):
    """
    Ребро графа онтологии.
    Описывает семантическую связь между двумя понятиями.
    """
    RELATION_TYPES = [
        ('IS_A', 'Является (Is A)'),
        ('PART_OF', 'Является частью'),
        ('USES', 'Использует'),
        ('DEPENDS', 'Зависит от (Пререквизит)'),
        ('RELATED', 'Связано с'),
    ]

    source = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='relations_out', verbose_name="Откуда")
    target = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='relations_in', verbose_name="Куда")
    relation_type = models.CharField(max_length=20, choices=RELATION_TYPES, verbose_name="Тип связи")

    def __str__(self):
        return f"{self.source} -> [{self.relation_type}] -> {self.target}"

    class Meta:
        verbose_name = "Семантическая связь"
        verbose_name_plural = "Связи"
        unique_together = ('source', 'target', 'relation_type')
