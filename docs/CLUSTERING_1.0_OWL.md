# Онтология clustering_1.0.owl

## Роль в проекте

**clustering_1.0.owl** — запасной файл онтологии. Основным источником является **clustering.2.owl** (если он есть в корне проекта).

Приоритет загрузки при запуске `python manage.py sync_ontology`:

1. **clustering.2.owl** — основной источник (последняя версия)
2. **clustering_1.0.owl** — запасной вариант
3. **clustering.owl** — запасной вариант
4. **clustering_domain.owl** — для обратной совместимости

## Отличия от clustering.owl

- Версионирование: явная версия 1.0 в имени файла.
- Расширенные описания: у алгоритмов заданы `rdfs:comment` с `xml:lang="ru"` — полные текстовые описания на русском.
- Дополнительные индивиды:
  - **Algo_MiniBatchKMeans** — MiniBatch K-Means (параметры: Param_NumClusters, Param_BatchSize).
  - **Algo_Maximin** — Алгоритм Максимина (параметр: Param_DistanceThreshold).
- Дополнительный параметр: **Param_BatchSize** (batch size / размер пакета).

## Структура (кратко)

- **Object Properties**: assumesClusterSize, hasInferenceType, hasParameter, hasScalability, solvesTask, supportsGeometry, usesMetric.
- **Classes**: Algorithm (PartitioningAlgorithm, DensityBasedAlgorithm, HierarchicalAlgorithm, ModelBasedAlgorithm), Metric, Parameter, Geometry, ClusterSize, Scalability, InferenceType, UseCase.
- **Individuals**: алгоритмы (K-Means, DBSCAN, BIRCH, MiniBatch K-Means, Максимин и др.), метрики, параметры, геометрии, масштабируемость, типы вывода, сценарии использования.

## Синхронизация с БД

При синхронизации:

- Каждый индивид превращается в запись `Concept` (полный URI в `uri`, русский `rdfs:label` в `title`, при наличии — русский `rdfs:comment` в `description`).
- Свойства маппятся на связи `ConceptRelation`: `usesMetric` → USES, остальные перечисленные выше → RELATED (или DEPENDS для обратной совместимости).

Для обновления данных после изменения OWL достаточно снова выполнить:

```bash
python manage.py sync_ontology
```

## Где используется в коде

- Загрузка и синхронизация: `apps/encyclopedia/ontology.py` (список `OWL_FILENAMES`, функция `sync_ontology()`).
- Команда: `apps/encyclopedia/management/commands/sync_ontology.py`.
- Рекомендации и адаптивное обучение: `apps/encyclopedia/recommendations.py` (работа с уже загруженными Concept и ConceptRelation).
