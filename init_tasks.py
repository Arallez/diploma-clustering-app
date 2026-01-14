import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.simulator.models import Task

def create_tasks():
    print("🧹 Очистка старых заданий...")
    Task.objects.all().delete()

    print("🚀 Создание новых заданий...")
    
    # === ОБЩИЕ ЗНАНИЯ ===
    Task.objects.create(
        title="Евклидово расстояние",
        slug="euclidean-dist",
        algorithm="general",
        order=1,
        difficulty=1,
        description="<p>Реализуйте функцию <code>dist(a, b)</code>, которая возвращает расстояние между двумя точками. Формула: √(x₂-x₁)² + (y₂-y₁)²</p>",
        function_name="dist",
        initial_code="import math\n\ndef dist(a, b):\n    # a = [x1, y1], b = [x2, y2]\n    return 0",
        solution_code="import math\n\ndef dist(a, b):\n    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)",
        test_input=[[0,0], [3,4]], 
        expected_output=5.0
    )

    # === K-MEANS ===
    Task.objects.create(
        title="Пересчет центроида",
        slug="centroid-calc",
        algorithm="kmeans",
        order=1,
        difficulty=2,
        description="<p>Реализуйте функцию <code>calculate_centroid(points)</code>, возвращающую среднее арифметическое координат [x_mean, y_mean].</p>",
        function_name="calculate_centroid",
        initial_code="import numpy as np\n\ndef calculate_centroid(points):\n    return [0, 0]",
        solution_code="import numpy as np\n\ndef calculate_centroid(points):\n    return [np.mean([p[0] for p in points]), np.mean([p[1] for p in points])]",
        test_input=[[0,0], [4,4], [2,2]],
        expected_output=[2.0, 2.0]
    )

    Task.objects.create(
        title="Поиск ближайшего кластера",
        slug="assign-cluster",
        algorithm="kmeans",
        order=2,
        difficulty=2,
        description="<p>Для точки <code>p</code> и списка <code>centroids</code> верните <b>индекс</b> (0, 1, 2..) ближайшего центроида.</p>",
        function_name="find_closest",
        initial_code="import numpy as np\n\ndef find_closest(p, centroids):\n    # p = [x, y]\n    # centroids = [[x1, y1], [x2, y2]...]\n    return 0",
        solution_code="import numpy as np\nimport math\n\ndef find_closest(p, centroids):\n    distances = [math.sqrt((p[0]-c[0])**2 + (p[1]-c[1])**2) for c in centroids]\n    return distances.index(min(distances))",
        test_input={"p": [0,0], "centroids": [[10,10], [1,1]]},
        expected_output=1
    )

    print("✅ Успешно! Задания добавлены в базу данных.")

if __name__ == "__main__":
    create_tasks()
