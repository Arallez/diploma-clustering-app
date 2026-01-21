import os
from owlready2 import *
from django.conf import settings
from .models import Concept as DjangoConcept, ConceptRelation  # Renamed import

def sync_ontology():
    """
    Генерирует OWL-файл (стандарт Semantic Web) и синхронизирует его с БД Django.
    Обеспечивает "Гибридный подход" для диплома.
    """
    
    # 1. Создаем (или загружаем) онтологию в памяти
    onto_path = os.path.join(settings.BASE_DIR, 'clustering_domain.owl')
    onto = get_ontology(f"file://{onto_path}")

    print(f"🧬 Генерация онтологии: {onto_path}")

    with onto:
        # Определяем базовые классы онтологии
        class KnowledgeItem(Thing): pass
        
        class Algorithm(KnowledgeItem): pass
        class Metric(KnowledgeItem): pass
        class OntologyConcept(KnowledgeItem): pass # Renamed to avoid conflict
        
        # Определяем свойства (Relationships)
        class uses_metric(ObjectProperty):
            domain = [Algorithm]
            range = [Metric]

        class requires_knowledge(ObjectProperty):
            domain = [KnowledgeItem]
            range = [KnowledgeItem]

        # --- НАПОЛНЕНИЕ ЗНАНИЯМИ (SEEDS) ---
        
        # Метрики
        euclidean = Metric("EuclideanDistance")
        euclidean.label = ["Евклидово расстояние"]
        euclidean.comment = ["Геометрическое расстояние между двумя точками в евклидовом пространстве."]

        manhattan = Metric("ManhattanDistance")
        manhattan.label = ["Манхэттенское расстояние"]
        manhattan.comment = ["Расстояние между двумя точками, равное сумме модулей разностей их координат."]

        # Алгоритмы
        kmeans = Algorithm("KMeans")
        kmeans.label = ["K-Means (К-средних)"]
        kmeans.comment = ["Итеративный алгоритм кластеризации, минимизирующий суммарное квадратичное отклонение точек кластеров от центроидов."]
        kmeans.uses_metric = [euclidean]
        kmeans.requires_knowledge = [euclidean]

        dbscan = Algorithm("DBSCAN")
        dbscan.label = ["DBSCAN"]
        dbscan.comment = ["Алгоритм кластеризации, основанный на плотности. Способен находить кластеры произвольной формы и выделять шум."]
        dbscan.uses_metric = [euclidean] # Может использовать разные, но по умолчанию евклид

        centroid = OntologyConcept("Centroid")
        centroid.label = ["Центроид"]
        centroid.comment = ["Геометрический центр кластера. В K-Means координаты центроида вычисляются как среднее арифметическое всех точек кластера."]
        
        kmeans.requires_knowledge.append(centroid)

    # 2. Сохраняем OWL файл (Артефакт для диплома)
    onto.save()
    print("✅ Файл clustering_domain.owl успешно сохранен (Semantic Web Standard).")

    # 3. Синхронизация с БД Django (Реляционная проекция)
    print("🔄 Синхронизация с базой данных...")
    
    def get_or_create_concept(owl_entity):
        title = owl_entity.label[0] if owl_entity.label else owl_entity.name
        desc = owl_entity.comment[0] if owl_entity.comment else ""
        
        # Use DjangoConcept explicitly
        obj, created = DjangoConcept.objects.get_or_create(
            uri=owl_entity.name,
            defaults={'title': title, 'description': desc}
        )
        if not created:
            obj.title = title
            obj.description = desc
            obj.save()
        return obj

    # Проходим по всем индивидам онтологии
    for entity in onto.individuals():
        source_obj = get_or_create_concept(entity)
        
        # Обрабатываем связи "uses_metric"
        if hasattr(entity, 'uses_metric'):
            for target_entity in entity.uses_metric:
                target_obj = get_or_create_concept(target_entity)
                ConceptRelation.objects.get_or_create(
                    source=source_obj,
                    target=target_obj,
                    relation_type='USES'
                )

        # Обрабатываем связи "requires_knowledge"
        if hasattr(entity, 'requires_knowledge'):
            for target_entity in entity.requires_knowledge:
                target_obj = get_or_create_concept(target_entity)
                ConceptRelation.objects.get_or_create(
                    source=source_obj,
                    target=target_obj,
                    relation_type='DEPENDS'
                )

    print("✅ База данных синхронизирована с онтологией.")
