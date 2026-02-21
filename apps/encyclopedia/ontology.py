import os
from owlready2 import *
from django.conf import settings
from .models import Concept as DjangoConcept, ConceptRelation  # Renamed import

# Порядок поиска OWL-файла: последняя версия (clustering.2.owl) — основной, затем 1.0, clustering.owl, clustering_domain.owl
OWL_FILENAMES = ('clustering.2.owl', 'clustering_1.0.owl', 'clustering.owl', 'clustering_domain.owl')


def sync_ontology():
    """
    Загружает существующий OWL-файл и синхронизирует его с БД Django.
    Приоритет: clustering.2.owl → clustering_1.0.owl → clustering.owl → clustering_domain.owl.
    Обеспечивает "Гибридный подход" для диплома.
    """
    
    # 1. Ищем первый существующий OWL файл по приоритету
    base_dir = settings.BASE_DIR
    onto_path = None
    for filename in OWL_FILENAMES:
        path = os.path.join(base_dir, filename)
        if os.path.exists(path):
            onto_path = path
            break
    
    if not onto_path:
        print("❌ Файл онтологии не найден. Ожидается один из:")
        for fn in OWL_FILENAMES:
            print(f"   — {fn}")
        print("💡 Поместите clustering.2.owl (или другой из списка) в корень проекта.")
        return
    
    print(f"🧬 Загрузка онтологии из файла: {onto_path}")
    
    # Загружаем онтологию из файла
    onto = get_ontology(f"file://{onto_path}")
    onto.load()
    
    individuals_list = list(onto.individuals())
    print(f"✅ Онтология загружена. Найдено индивидов: {len(individuals_list)}")

    # 3. Синхронизация с БД Django (Реляционная проекция)
    print("🔄 Синхронизация с базой данных...")
    
    def extract_name_from_uri(uri):
        """Извлекает короткое имя из полного URI"""
        if '#' in str(uri):
            return str(uri).split('#')[-1]
        if '/' in str(uri):
            return str(uri).split('/')[-1]
        return str(uri)
    
    def get_or_create_concept(owl_entity):
        # Извлекаем имя из URI (может быть полным URI или коротким именем)
        entity_name = extract_name_from_uri(owl_entity.name)
        full_uri = str(owl_entity.name)
        
        # Обрабатываем label (может быть списком или строкой, может иметь xml:lang)
        title = entity_name  # По умолчанию используем имя
        if hasattr(owl_entity, 'label') and owl_entity.label:
            labels = owl_entity.label if isinstance(owl_entity.label, list) else [owl_entity.label]
            # Предпочитаем русский label, если есть
            for label in labels:
                if hasattr(label, 'lang') and label.lang == 'ru':
                    title = str(label)
                    break
            if title == entity_name and len(labels) > 0:
                title = str(labels[0])
        
        # Обрабатываем comment (может быть списком или строкой, с xml:lang="ru")
        desc = ""
        if hasattr(owl_entity, 'comment') and owl_entity.comment:
            comments = owl_entity.comment if isinstance(owl_entity.comment, list) else [owl_entity.comment]
            for c in comments:
                if hasattr(c, 'lang') and c.lang == 'ru':
                    desc = str(c)
                    break
            if not desc and len(comments) > 0:
                desc = str(comments[0])
        
        # Use DjangoConcept explicitly
        obj, created = DjangoConcept.objects.get_or_create(
            uri=full_uri,
            defaults={'title': title, 'description': desc}
        )
        if not created:
            obj.title = title
            obj.description = desc
            obj.save()
        return obj

    # Маппинг свойств OWL на типы связей в БД
    PROPERTY_MAPPING = {
        'usesMetric': 'USES',           # Алгоритм использует метрику
        'uses_metric': 'USES',          # Для обратной совместимости
        'hasParameter': 'RELATED',      # Алгоритм имеет параметр
        'solvesTask': 'RELATED',        # Алгоритм решает задачу (UseCase)
        'supportsGeometry': 'RELATED',  # Алгоритм поддерживает геометрию
        'assumesClusterSize': 'RELATED', # Алгоритм предполагает размер кластеров
        'hasScalability': 'RELATED',     # Алгоритм имеет масштабируемость
        'hasInferenceType': 'RELATED',  # Алгоритм имеет тип вывода
        'requires_knowledge': 'DEPENDS', # Для обратной совместимости
    }
    
    # Проходим по всем индивидам онтологии
    individuals_list = list(onto.individuals())
    print(f"📊 Обработка {len(individuals_list)} индивидов...")
    
    for entity in individuals_list:
        source_obj = get_or_create_concept(entity)
        entity_name_short = extract_name_from_uri(entity.name)
        print(f"  ✓ {source_obj.title} ({entity_name_short})")
        
        # Обрабатываем все свойства из маппинга
        relations_created = 0
        for prop_name, relation_type in PROPERTY_MAPPING.items():
            # Проверяем наличие свойства (может быть с разными регистрами)
            prop_value = None
            for attr_name in dir(entity):
                if attr_name.lower() == prop_name.lower():
                    prop_value = getattr(entity, attr_name, None)
                    break
            
            if prop_value:
                # prop_value может быть списком или одним значением
                target_entities = prop_value if isinstance(prop_value, list) else [prop_value]
                
                for target_entity in target_entities:
                    if target_entity:  # Проверяем, что значение не None
                        target_obj = get_or_create_concept(target_entity)
                        ConceptRelation.objects.get_or_create(
                            source=source_obj,
                            target=target_obj,
                            relation_type=relation_type
                        )
                        relations_created += 1
                        print(f"    → {relation_type}: {target_obj.title}")
        
        if relations_created == 0:
            print(f"    (нет связей)")

    print("✅ База данных синхронизирована с онтологией.")
