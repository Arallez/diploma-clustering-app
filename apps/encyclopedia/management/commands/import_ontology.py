from django.core.management.base import BaseCommand
from apps.encyclopedia.ontology import sync_ontology

class Command(BaseCommand):
    help = 'Импортирует OWL-онтологию из файла в базу данных (Concept и ConceptRelation)'

    def handle(self, *args, **options):
        self.stdout.write("Начинаю загрузку OWL онтологии...")
        try:
            sync_ontology()
            self.stdout.write(self.style.SUCCESS("✅ Успешно импортировано!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка при импорте: {e}"))
