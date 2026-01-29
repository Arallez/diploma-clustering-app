import math
import json
import ast
import numpy as np
import random
import collections
import itertools
import functools
from typing import List, Dict, Any, Tuple, Union, Optional

# Try to import timeout protection, fallback if missing
try:
    from func_timeout import func_timeout, FunctionTimedOut
    HAS_TIMEOUT_LIB = True
except ImportError:
    HAS_TIMEOUT_LIB = False
    print("Warning: 'func_timeout' library not found. Code execution timeout protection is DISABLED.")

class SolutionValidator:
    """
    Сервис для проверки решений пользователей.
    Изолирует логику проверки от HTTP-представлений.
    """

    # Расширенный список разрешенных библиотек для Data Science
    ALLOWED_MODULES = {
        # Стандартные
        'math', 'random', 'collections', 'itertools', 'functools', 
        'datetime', 're', 'copy', 'operator', 'string',
        
        # Научные и ML
        'numpy', 'scikit-learn', 'sklearn', 'scipy', 'pandas'
    }

    @staticmethod
    def validate(task: Any, user_input: Union[str, List[Any], Dict[str, Any]]) -> Tuple[bool, str, Optional[str], Dict[str, Any]]:
        """
        Главный метод валидации.
        
        Args:
            task: Объект задачи (Model instance)
            user_input: Ввод пользователя (код или ответы теста)
            
        Returns:
            Tuple[is_correct, message, error_msg, details]
        """
        if task.task_type == 'choice':
            return SolutionValidator._validate_quiz(task, user_input)
        else:
            return SolutionValidator._validate_code(task, user_input)

    @staticmethod
    def _validate_quiz(task: Any, user_input: Any) -> Tuple[bool, str, Optional[str], Dict[str, Any]]:
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
    def _check_imports(user_code: str) -> Tuple[bool, str]:
        """
        Проверяет код на наличие запрещенных импортов через AST.
        """
        try:
            tree = ast.parse(user_code)
        except SyntaxError as e:
            return False, f"Синтаксическая ошибка: {e.msg} (line {e.lineno})"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_module = alias.name.split('.')[0]
                    if root_module not in SolutionValidator.ALLOWED_MODULES:
                        return False, f"Security Error: Импорт модуля '{root_module}' запрещен. Разрешены: {', '.join(sorted(SolutionValidator.ALLOWED_MODULES))}"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_module = node.module.split('.')[0]
                    if root_module not in SolutionValidator.ALLOWED_MODULES:
                         return False, f"Security Error: Импорт из модуля '{root_module}' запрещен."
        
        return True, ""

    @staticmethod
    def _safe_import(name: str, globals: Any = None, locals: Any = None, fromlist: Tuple = (), level: int = 0) -> Any:
        """
        Безопасная обертка для __import__. 
        """
        root = name.split('.')[0]
        if root in SolutionValidator.ALLOWED_MODULES:
            return __import__(name, globals, locals, fromlist, level)
        raise ImportError(f"Security: Import of '{name}' is restricted.")

    @staticmethod
    def _validate_code(task: Any, user_code: str) -> Tuple[bool, str, Optional[str], Dict[str, Any]]:
        """
        Выполняет код пользователя в безопасном контексте с тайм-аутом.
        """
        # 1. Проверка импортов через AST
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
            'pow': pow, 'reversed': reversed, 'divmod': divmod, 'all': all, 'any': any,
            '__import__': SolutionValidator._safe_import
        }
        
        execution_context = {
            '__builtins__': safe_builtins,
            'np': np,
        }

        # 3. Выполнение кода с защитой от бесконечных циклов (Timeout)
        try:
            def run_user_code():
                exec(user_code, execution_context)
            
            # Если библиотека установлена - используем защиту, если нет - просто запускаем
            if HAS_TIMEOUT_LIB:
                func_timeout(3.0, run_user_code)
            else:
                run_user_code()
            
        except NameError: 
             return False, "", "Timeout Error (Lib Missing): Execution failed.", {}
        except Exception as e:
            # Перехват FunctionTimedOut (если он есть) или других ошибок
            if HAS_TIMEOUT_LIB and type(e).__name__ == 'FunctionTimedOut':
                return False, "", "Timeout Error: Выполнение кода заняло слишком много времени ( > 3с ). Проверьте бесконечные циклы.", {}
            return False, "", f"Runtime Error: {e}", {}

        # 4. Поиск функции и проверка
        func_name = task.function_name
        if func_name not in execution_context:
            return False, "", f"Функция '{func_name}' не найдена.", {}

        user_func = execution_context[func_name]
        
        test_input = task.test_input
        expected = task.expected_output
        
        try:
            # Smart call logic
            if isinstance(test_input, dict) and not isinstance(test_input, list): 
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

        # Приведение типов для сравнения
        if hasattr(result, 'tolist'): result = result.tolist()
        if hasattr(expected, 'tolist'): expected = expected.tolist()

        is_correct = False
        if str(result) == str(expected):
            is_correct = True
        else:
            try:
                if isinstance(expected, (int, float)) and isinstance(result, (int, float)):
                    is_correct = math.isclose(result, expected, rel_tol=1e-2)
                elif isinstance(expected, list) and isinstance(result, list):
                    is_correct = np.allclose(result, expected, atol=1e-2)
            except:
                pass

        message = str(result)
        error_msg = None if is_correct else f"Ожидалось: {expected}, Получено: {result}"

        return is_correct, message, error_msg, {}
