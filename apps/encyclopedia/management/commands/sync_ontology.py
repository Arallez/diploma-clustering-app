"""
Django management command для синхронизации OWL онтологии с БД.

Использование:
    python manage.py sync_ontology
"""
from django.core.management.base import BaseCommand
from apps.encyclopedia.ontology import sync_ontology


class Command(BaseCommand):
    help = 'Синхронизирует OWL онтологию (приоритет: clustering.2.owl → clustering_1.0.owl → clustering.owl → clustering_domain.owl) с БД Django'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Начало синхронизации онтологии...'))
        
        try:
            sync_ontology()
            self.stdout.write(self.style.SUCCESS('✅ Синхронизация завершена успешно!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка при синхронизации: {e}'))
            raise
