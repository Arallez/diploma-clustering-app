# Онтология clustering.2.owl (последняя версия)

## Роль в проекте

**clustering.2.owl** — **последняя и основная** версия онтологии домена кластеризации. Синхронизация с БД выполняется из него в первую очередь (если файл есть в корне проекта).

Приоритет загрузки при запуске `python manage.py sync_ontology`:

1. **clustering.2.owl** — основной источник (последняя версия)
2. **clustering_1.0.owl** — запасной
3. **clustering.owl** — запасной
4. **clustering_domain.owl** — для обратной совместимости

## Особенности clustering.2.owl

- **Полный глоссарий**: у классов, объектных свойств и индивидов заданы `rdfs:comment` с `xml:lang="ru"` — развёрнутые описания по материалам Б.Г. Миркина и Scikit-Learn.
- **Описание онтологии**: у корневого `<owl:Ontology>` задан `rdfs:comment` — «Полная онтология методов кластеризации с глоссарием всех терминов».
- **Относительные URI**: в файле используются короткие идентификаторы с `#` (например `#Algorithm`, `#Algo_KMeans`); при загрузке они разрешаются в полные URI с базой `http://www.semanticweb.org/diploma/clustering`.
- **Те же объектные свойства и классы**, что и в 1.0: assumesClusterSize, hasInferenceType, hasParameter, hasScalability, solvesTask, supportsGeometry, usesMetric; классы Algorithm (и подклассы), Metric, Parameter, Geometry, ClusterSize, Scalability, InferenceType, UseCase.
- **Те же индивиды**: алгоритмы (K-Means, DBSCAN, BIRCH, MiniBatch K-Means, Максимин и др.), метрики, параметры, геометрии, масштабируемость, типы вывода, сценарии использования.

## Синхронизация с БД

При синхронизации:

- Каждый индивид превращается в запись `Concept` (полный URI в `uri`, русский `rdfs:label` в `title`, при наличии — русский `rdfs:comment` в `description`).
- Свойства маппятся на связи `ConceptRelation` так же, как для других версий OWL (usesMetric → USES, остальные → RELATED / DEPENDS).

Для обновления данных после изменения онтологии:

```bash
python manage.py sync_ontology
```

## Где задаётся приоритет

- Список файлов: `apps/encyclopedia/ontology.py` — константа `OWL_FILENAMES` (первый элемент — `clustering.2.owl`).
- Команда: `apps/encyclopedia/management/commands/sync_ontology.py`.
