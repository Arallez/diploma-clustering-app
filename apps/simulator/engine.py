import numpy as np
from sklearn.cluster import KMeans

class KMeansEngine:
    """
    Класс-обертка над scikit-learn для эмуляции пошагового выполнения K-Means.
    Использует параметр max_iter для остановки алгоритма на нужном шаге.
    """
    
    def __init__(self, n_clusters=3, random_state=42):
        self.n_clusters = n_clusters
        self.random_state = random_state

    def run_step_by_step(self, X_data, max_steps=20):
        """
        Запускает K-Means итеративно, возвращая историю изменений.
        
        Args:
            X_data (list of lists): Список координат точек [[x1, y1], [x2, y2], ...]
            max_steps (int): Максимальное количество итераций для проверки сходимости.
            
        Returns:
            list of dicts: История шагов. Каждый элемент содержит:
                - step (int): Номер шага (0 - инициализация)
                - centroids (list): Координаты центроидов
                - labels (list): Метки кластеров для каждой точки
                - inertia (float): Сумма квадратов расстояний (для графика ошибок)
                - converged (bool): Сошелся ли алгоритм
        """
        X = np.array(X_data)
        history = []
        
        # Шаг 0: Инициализация (max_iter=1, init='random', n_init=1)
        # Мы фиксируем random_state, чтобы инициализация была воспроизводимой
        # Примечание: sklearn не дает просто "инициализировать" без одного шага.
        # Поэтому мы используем трюк: 
        # 1. Генерируем центроиды вручную или через kmeans init
        # 2. Передаем их как явный параметр init в цикле
        
        # Генерация начальных центроидов (случайный выбор из данных)
        rng = np.random.RandomState(self.random_state)
        idx = rng.permutation(X.shape[0])[:self.n_clusters]
        initial_centers = X[idx]
        
        current_centers = initial_centers
        
        # Записываем состояние "Шаг 0" (до первой пересборки кластеров, просто центры)
        # Метки считаем по ближайшему центру
        model_dummy = KMeans(n_clusters=self.n_clusters, init=current_centers, n_init=1, max_iter=1)
        model_dummy.fit(X)
        
        history.append({
            "step": 0,
            "centroids": current_centers.tolist(),
            "labels": model_dummy.predict(X).tolist(), # Метки на основе начальных центров
            "inertia": float(model_dummy.inertia_),
            "converged": False
        })

        # Цикл по шагам
        for i in range(1, max_steps + 1):
            # Запускаем KMeans с фиксированными начальными центрами, но ограничиваем итерации
            # В sklearn max_iter=1 делает ОДНУ итерацию (E-шаг + M-шаг)
            # Чтобы получить "следующий" шаг, мы берем центры из ПРЕДЫДУЩЕГО шага и делаем 1 итерацию от них.
            
            model = KMeans(
                n_clusters=self.n_clusters,
                init=current_centers, # Начинаем с центров предыдущего шага
                n_init=1,             # Делаем ровно 1 прогон
                max_iter=1,           # Делаем ровно 1 итерацию
                random_state=self.random_state
            )
            
            model.fit(X)
            
            new_centers = model.cluster_centers_
            labels = model.labels_
            inertia = model.inertia_
            
            # Проверка на сходимость: если центры не сдвинулись
            is_converged = np.allclose(current_centers, new_centers, atol=1e-4)
            
            history.append({
                "step": i,
                "centroids": new_centers.tolist(),
                "labels": labels.tolist(),
                "inertia": float(inertia),
                "converged": bool(is_converged)
            })
            
            current_centers = new_centers
            
            if is_converged:
                break
                
        return history
