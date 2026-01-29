from django.core.management.base import BaseCommand
from apps.simulator.models import Task, TaskTag

class Command(BaseCommand):
    help = 'Adds a combined K-Means quiz task'

    def handle(self, *args, **kwargs):
        # 1. Create/Get the Tag
        tag, created = TaskTag.objects.get_or_create(
            slug='kmeans-theory',
            defaults={'name': 'K-Means: Теория', 'order': 10}
        )

        # 2. Define the Multi-Question Quiz
        quiz_questions = [
            {
                'text': '1. Что означает параметр <b>K</b> в названии алгоритма K-Means?',
                'options': [
                    'Количество итераций алгоритма',
                    'Количество кластеров, которые мы хотим найти',
                    'Количество признаков (измерений) в данных'
                ]
            },
            {
                'text': '2. Какое условие обычно используется для остановки алгоритма?',
                'options': [
                    'Когда все точки посещены',
                    'Когда центроиды перестают менять своё положение',
                    'Ровно через 100 итераций'
                ]
            },
            {
                'text': '3. К чему чувствителен алгоритм K-Means?',
                'options': [
                    'К начальному случайному положению центроидов',
                    'Только к масштабу данных',
                    'К порядку строк в базе данных'
                ]
            },
            {
                'text': '4. С какими кластерами K-Means справляется плохо?',
                'options': [
                    'Сферическими (круглыми)',
                    'Выпуклыми облаками точек',
                    'Кластерами сложной формы (дуги, кольца)'
                ]
            }
        ]

        # Correct answers in order
        correct_answers = [
            'Количество кластеров, которые мы хотим найти',
            'Когда центроиды перестают менять своё положение',
            'К начальному случайному положению центроидов',
            'Кластерами сложной формы (дуги, кольца)'
        ]

        # 3. Create/Update the Single Task
        task, created = Task.objects.update_or_create(
            slug='kmeans-final-quiz',
            defaults={
                'title': 'Итоговый тест по теории K-Means',
                'description': '<p>Ответьте на все вопросы, чтобы проверить понимание алгоритма.</p>',
                'task_type': 'choice',
                'difficulty': 2,
                'tags': tag,
                'order': 5,
                
                # New Structure for Multi-Questions
                'test_input': {'questions': quiz_questions},
                'expected_output': correct_answers,
                
                'function_name': '',
                'initial_code': '',
                'solution_code': ''
            }
        )
        
        # Cleanup old single tasks if they exist (optional, keeping clean)
        old_slugs = ['kmeans-quiz-k-meaning', 'kmeans-quiz-convergence', 'kmeans-quiz-init', 'kmeans-quiz-shape']
        Task.objects.filter(slug__in=old_slugs).delete()

        self.stdout.write(self.style.SUCCESS(f'Successfully created combined quiz: {task.title}'))
