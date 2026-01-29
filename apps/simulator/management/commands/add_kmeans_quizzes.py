from django.core.management.base import BaseCommand
from apps.simulator.models import Task, TaskTag

class Command(BaseCommand):
    help = 'Adds K-Means quiz tasks'

    def handle(self, *args, **kwargs):
        # 1. Create/Get the Tag
        tag, created = TaskTag.objects.get_or_create(
            slug='kmeans-theory',
            defaults={'name': 'K-Means: Теория', 'order': 10}
        )
        if created:
            self.stdout.write(f"Created tag: {tag.name}")
        else:
            self.stdout.write(f"Using existing tag: {tag.name}")

        # 2. Define Tasks
        tasks_data = [
            {
                'slug': 'kmeans-quiz-k-meaning',
                'title': 'Значение параметра K',
                'description': '<p>Что означает параметр <b>K</b> в названии алгоритма K-Means?</p>',
                'difficulty': 1,
                'options': [
                    'Количество итераций алгоритма',
                    'Количество кластеров, которые мы хотим найти',
                    'Количество признаков (измерений) в данных',
                    'Количество соседей для проверки'
                ],
                'answer': 'Количество кластеров, которые мы хотим найти',
                'order': 1
            },
            {
                'slug': 'kmeans-quiz-convergence',
                'title': 'Условие остановки',
                'description': '<p>Какое условие обычно используется для остановки алгоритма K-Means?</p>',
                'difficulty': 2,
                'options': [
                    'Когда все точки посещены',
                    'Когда центроиды перестают менять своё положение',
                    'Ровно через 100 итераций',
                    'Когда расстояние между всеми точками становится равным 0'
                ],
                'answer': 'Когда центроиды перестают менять своё положение',
                'order': 2
            },
            {
                'slug': 'kmeans-quiz-init',
                'title': 'Проблема инициализации',
                'description': '<p>К чему чувствителен алгоритм K-Means?</p>',
                'difficulty': 2,
                'options': [
                    'Только к масштабу данных',
                    'К начальному случайному положению центроидов',
                    'К порядку строк в базе данных',
                    'Он ни к чему не чувствителен'
                ],
                'answer': 'К начальному случайному положению центроидов',
                'order': 3
            },
            {
                'slug': 'kmeans-quiz-shape',
                'title': 'Форма кластеров',
                'description': '<p>С какими кластерами K-Means справляется <b>плохо</b>?</p>',
                'difficulty': 3,
                'options': [
                    'Сферическими (круглыми)',
                    'Выпуклыми облаками точек',
                    'Кластерами сложной формы (дуги, кольца, спирали)',
                    'Плотными компактными группами'
                ],
                'answer': 'Кластерами сложной формы (дуги, кольца, спирали)',
                'order': 4
            }
        ]

        # 3. Create Tasks
        for data in tasks_data:
            task, created = Task.objects.update_or_create(
                slug=data['slug'],
                defaults={
                    'title': data['title'],
                    'description': data['description'],
                    'task_type': 'choice',  # Quiz type
                    'difficulty': data['difficulty'],
                    'tags': tag,
                    'order': data['order'],
                    'test_input': {'options': data['options']}, # Options go here
                    'expected_output': data['answer'],          # Correct answer string
                    
                    # Empty fields for code tasks
                    'function_name': '',
                    'initial_code': '',
                    'solution_code': ''
                }
            )
            status = "Created" if created else "Updated"
            self.stdout.write(f"{status} task: {task.title}")

        self.stdout.write(self.style.SUCCESS(f'Successfully processed {len(tasks_data)} quiz tasks!'))
