import math
import json
import ast
import numpy as np
import random
import collections
import itertools
import functools

class SolutionValidator:
    """
    Сервис для проверки решений пользователей.
    Изолирует логику проверки от HTTP-представлений.
    """

    # Список разрешенных библиотек
    ALLOWED_MODULES = {
        'math', 'numpy', 'random', 'collections', 
        'itertools', 'functools', 'datetime', 're'
    }

    @staticmethod
    def validate(task, user_input):
        """
        Главный метод. Определяет тип задачи и вызывает нужный валидатор.
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

        if isinstance(user_input, list) and isinstance(expected, list):
            is_correct = (user_input == expected)
            message = "Ответы приняты"
            
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
            expected_str = str(expected).strip()
            submitted_str = str(user_input).strip()
            is_correct = (submitted_str == expected_str)
            message = submitted_str
            
            if not is_correct:
                error_msg = f"Выбрано: {user_input}. Попробуйте еще раз."

        return is_correct, message, error_msg, details

    @staticmethod
    def _check_imports(user_code):
        """
        Проверяет код на наличие запрещенных импортов через AST.
        """
        try:
            tree = ast.parse(user_code)
        except SyntaxError as e:
            return False, f"Синтаксическая ошибка: {e.msg} (line {e.lineno})"

        for node in ast.walk(tree):
            # Проверка 'import x'
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Берем корневой модуль (например, из 'os.path' берем 'os')
                    root_module = alias.name.split('.')[0]
                    if root_module not in SolutionValidator.ALLOWED_MODULES:
                        return False, f"Security Error: Импорт модуля '{root_module}' запрещен. Разрешены: {', '.join(SolutionValidator.ALLOWED_MODULES)}"
            
            # Проверка 'from x import y'
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_module = node.module.split('.')[0]
                    if root_module not in SolutionValidator.ALLOWED_MODULES:
                         return False, f"Security Error: Импорт из модуля '{root_module}' запрещен."
        
        return True, ""

    @staticmethod
    def _validate_code(task, user_code):
        """
        Выполняет код пользователя в безопасном контексте.
        """
        # 1. Проверка импортов через Белый список (Whitelist)
        is_safe, error_msg = SolutionValidator._check_imports(user_code)
        if not is_safe:
            return False, "", error_msg, {}

        # 2. Подготовка песочницы
        safe_builtins = {
            'abs': abs, 'len': len, 'range': range, 'sum': sum, 
            'min': min, 'max': max, 'int': int, 'float': float, 'str': str,
            'list': list, 'dict': dict, 'set': set, 'tuple': tuple, 'bool': bool,
            'sorted': sorted, 'zip': zip, 'map': map, 'filter': filter, 
            'enumerate': enumerate, 'print': print, 'round': round,
            'pow': pow, 'reversed': reversed
        }
        
        # Разрешаем использование этих модулей внутри exec, если пользователь их импортирует
        execution_context = {
            '__builtins__': safe_builtins,
            'np': np, # Предоставляем np сразу для удобства, даже если нет импорта
        }

        # 3. Выполнение кода
        try:
            exec(user_code, execution_context)
        except Exception as e:
            return False, "", f"Runtime Error: {e}", {}

        # 4. Поиск функции и проверка (остальная логика без изменений)
        func_name = task.function_name
        if func_name not in execution_context:
            return False, "", f"Функция '{func_name}' не найдена.", {}

        user_func = execution_context[func_name]
        
        test_input = task.test_input
        expected = task.expected_output
        
        try:
            # Smart call (args vs kwargs)
            if isinstance(test_input, dict) and not isinstance(test_input, list): 
                # Простая эвристика: если это dict, но задача не ждет dict как аргумент, 
                # то разворачиваем как kwargs.
                # (В идеале можно анализировать сигнатуру функции, но для MVP хватит try-except)
                try:
                    result = user_func(**test_input)
                except TypeError:
                    result = user_func(test_input)
            elif isinstance(test_input, list):
                try:
                    result = user_func(*test_input)
                except TypeError:
                    result = user_func(test_input)
            else:
                result = user_func(test_input)
        except Exception as e:
            return False, "", f"Ошибка при вызове функции: {e}", {}

        # Приведение типов для numpy
        if hasattr(result, 'tolist'): result = result.tolist()
        if hasattr(expected, 'tolist'): expected = expected.tolist()

        is_correct = False
        if str(result) == str(expected):
            is_correct = True
        else:
            try:
                # Мягкое сравнение для чисел
                if isinstance(expected, (int, float)) and isinstance(result, (int, float)):
                    is_correct = math.isclose(result, expected, rel_tol=1e-2)
                elif isinstance(expected, list) and isinstance(result, list):
                    is_correct = np.allclose(result, expected, atol=1e-2)
            except:
                pass

        message = str(result)
        error_msg = None if is_correct else f"Ожидалось: {expected}, Получено: {result}"

        return is_correct, message, error_msg, {}
