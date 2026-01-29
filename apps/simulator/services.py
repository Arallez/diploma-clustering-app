import math
import json
import numpy as np

class SolutionValidator:
    """
    Сервис для проверки решений пользователей.
    Изолирует логику проверки от HTTP-представлений.
    """

    @staticmethod
    def validate(task, user_input):
        """
        Главный метод. Определяет тип задачи и вызывает нужный валидатор.
        Возвращает кортеж: (success, message, error, details)
        """
        if task.task_type == 'choice':
            return SolutionValidator._validate_quiz(task, user_input)
        else:
            return SolutionValidator._validate_code(task, user_input)

    @staticmethod
    def _validate_quiz(task, user_input):
        expected = task.expected_output
        is_correct = False
        message = ""
        error_msg = None
        details = {}

        # 1. Нормализация типов (Multi-question vs Single)
        if isinstance(user_input, list) and isinstance(expected, list):
            # Сравнение списков (для составных тестов)
            is_correct = (user_input == expected)
            message = "Ответы приняты"
            
            # Детальная статистика по вопросам
            correctness_array = []
            for i in range(len(expected)):
                if i < len(user_input):
                    correctness_array.append(user_input[i] == expected[i])
                else:
                    correctness_array.append(False)
            details = {'quiz_results': correctness_array}
            
            if not is_correct:
                error_msg = "Некоторые ответы неверны."

        else:
            # Сравнение строк (для одиночных вопросов)
            expected_str = str(expected).strip()
            submitted_str = str(user_input).strip()
            is_correct = (submitted_str == expected_str)
            message = submitted_str
            
            if not is_correct:
                error_msg = f"Выбрано: {user_input}. Попробуйте еще раз."

        return is_correct, message, error_msg, details

    @staticmethod
    def _validate_code(task, user_code):
        """
        Выполняет код пользователя в ограниченном контексте.
        """
        # 1. Статический анализ (Basic Security)
        forbidden_keywords = ['import os', 'import sys', 'import subprocess', 'open(', 'eval(', 'exec(']
        if any(bad in user_code for bad in forbidden_keywords):
            return False, "", "Security Error: Использование системных библиотек запрещено!", {}

        # 2. Подготовка песочницы (Restricted Globals)
        # Разрешаем только безопасные встроенные функции
        safe_builtins = {
            'abs': abs, 'len': len, 'range': range, 'sum': sum, 
            'min': min, 'max': max, 'int': int, 'float': float, 'str': str,
            'list': list, 'dict': dict, 'set': set, 'tuple': tuple, 'bool': bool,
            'sorted': sorted, 'zip': zip, 'map': map, 'filter': filter, 
            'enumerate': enumerate, 'print': print, 'round': round
        }
        
        execution_context = {
            '__builtins__': safe_builtins, # Запрещаем __import__ и прочее
            'np': np, 
            'math': math,
        }

        # 3. Выполнение кода
        try:
            exec(user_code, execution_context)
        except Exception as e:
            return False, "", f"Syntax/Runtime Error: {e}", {}

        # 4. Поиск целевой функции
        func_name = task.function_name
        if func_name not in execution_context:
            return False, "", f"Функция '{func_name}' не найдена в коде.", {}

        user_func = execution_context[func_name]
        
        # 5. Тестирование функции
        test_input = task.test_input
        expected = task.expected_output
        
        try:
            # Определение способа вызова (kwargs, args или single arg)
            if isinstance(test_input, dict):
                result = user_func(**test_input)
            elif isinstance(test_input, list):
                try:
                    result = user_func(*test_input)
                except TypeError:
                    result = user_func(test_input)
            else:
                result = user_func(test_input)
        except Exception as e:
            return False, "", f"Ошибка при вызове функции: {e}", {}

        # 6. Сравнение результатов
        # Приводим numpy типы к стандартным для сравнения
        if isinstance(result, np.ndarray): result = result.tolist()
        if isinstance(expected, np.ndarray): expected = expected.tolist()

        is_correct = False
        # Сложное сравнение (списки, словари, числа с плавающей точкой)
        if isinstance(expected, (list, dict)):
            if str(result) == str(expected):
                is_correct = True
            else:
                # Попытка сравнить float с допуском
                try: 
                    is_correct = np.allclose(result, expected, atol=1e-2)
                except: 
                    is_correct = False
        else:
            is_correct = (result == expected)

        message = str(result)
        error_msg = None if is_correct else f"Ожидалось: {expected}, Получено: {result}"

        return is_correct, message, error_msg, {}
