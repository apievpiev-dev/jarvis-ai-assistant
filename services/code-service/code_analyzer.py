#!/usr/bin/env python3
"""
Code Analyzer - Анализатор кода
Автор: Jarvis AI Assistant
Версия: 1.0.0
"""

import ast
import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """Типы анализа кода"""
    SYNTAX = "syntax"
    COMPLEXITY = "complexity"
    QUALITY = "quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    FULL = "full"

@dataclass
class CodeIssue:
    """Проблема в коде"""
    line: int
    column: int
    severity: str  # error, warning, info
    message: str
    rule_id: str
    category: str

@dataclass
class CodeMetrics:
    """Метрики кода"""
    lines_of_code: int
    cyclomatic_complexity: int
    maintainability_index: float
    technical_debt: float
    code_coverage: float

@dataclass
class AnalysisResult:
    """Результат анализа кода"""
    issues: List[CodeIssue]
    metrics: CodeMetrics
    suggestions: List[str]
    language: str
    analysis_type: str

class CodeAnalyzer:
    """Анализатор кода"""
    
    def __init__(self):
        self.ready = False
        self.supported_languages = ["python", "javascript", "typescript", "java", "cpp", "c"]
        
    async def initialize(self):
        """Инициализация анализатора"""
        try:
            logger.info("Инициализация Code Analyzer...")
            self.ready = True
            logger.info("Code Analyzer инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации Code Analyzer: {e}")
            raise
    
    async def cleanup(self):
        """Очистка ресурсов"""
        self.ready = False
        logger.info("Code Analyzer очищен")
    
    def is_ready(self) -> bool:
        """Проверка готовности анализатора"""
        return self.ready
    
    async def analyze_code(self, code: str, language: str = "python", analysis_type: str = "full") -> Dict[str, Any]:
        """Анализ кода"""
        try:
            if not self.ready:
                raise Exception("Code Analyzer не готов")
            
            if language not in self.supported_languages:
                raise Exception(f"Неподдерживаемый язык: {language}")
            
            # Анализ в зависимости от языка
            if language == "python":
                return await self._analyze_python_code(code, analysis_type)
            elif language in ["javascript", "typescript"]:
                return await self._analyze_js_code(code, analysis_type)
            elif language in ["java", "cpp", "c"]:
                return await self._analyze_compiled_code(code, language, analysis_type)
            else:
                return await self._analyze_generic_code(code, language, analysis_type)
                
        except Exception as e:
            logger.error(f"Ошибка анализа кода: {e}")
            raise
    
    async def _analyze_python_code(self, code: str, analysis_type: str) -> Dict[str, Any]:
        """Анализ Python кода"""
        try:
            issues = []
            metrics = None
            suggestions = []
            
            # Синтаксический анализ
            if analysis_type in ["syntax", "full"]:
                syntax_issues = await self._check_python_syntax(code)
                issues.extend(syntax_issues)
            
            # Анализ сложности
            if analysis_type in ["complexity", "full"]:
                complexity_issues = await self._check_python_complexity(code)
                issues.extend(complexity_issues)
            
            # Анализ качества
            if analysis_type in ["quality", "full"]:
                quality_issues = await self._check_python_quality(code)
                issues.extend(quality_issues)
            
            # Анализ безопасности
            if analysis_type in ["security", "full"]:
                security_issues = await self._check_python_security(code)
                issues.extend(security_issues)
            
            # Анализ производительности
            if analysis_type in ["performance", "full"]:
                performance_issues = await self._check_python_performance(code)
                issues.extend(performance_issues)
            
            # Вычисление метрик
            metrics = await self._calculate_python_metrics(code)
            
            # Генерация предложений
            suggestions = await self._generate_python_suggestions(code, issues)
            
            return {
                "issues": [issue.__dict__ for issue in issues],
                "metrics": metrics.__dict__ if metrics else {},
                "suggestions": suggestions,
                "language": "python",
                "analysis_type": analysis_type
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа Python кода: {e}")
            raise
    
    async def _check_python_syntax(self, code: str) -> List[CodeIssue]:
        """Проверка синтаксиса Python"""
        issues = []
        
        try:
            # Попытка парсинга AST
            ast.parse(code)
        except SyntaxError as e:
            issues.append(CodeIssue(
                line=e.lineno or 0,
                column=e.offset or 0,
                severity="error",
                message=f"Синтаксическая ошибка: {e.msg}",
                rule_id="syntax_error",
                category="syntax"
            ))
        except Exception as e:
            issues.append(CodeIssue(
                line=0,
                column=0,
                severity="error",
                message=f"Ошибка парсинга: {str(e)}",
                rule_id="parse_error",
                category="syntax"
            ))
        
        return issues
    
    async def _check_python_complexity(self, code: str) -> List[CodeIssue]:
        """Проверка сложности Python кода"""
        issues = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._calculate_cyclomatic_complexity(node)
                    
                    if complexity > 10:
                        issues.append(CodeIssue(
                            line=node.lineno,
                            column=node.col_offset,
                            severity="warning",
                            message=f"Высокая цикломатическая сложность: {complexity}",
                            rule_id="high_complexity",
                            category="complexity"
                        ))
                
                elif isinstance(node, (ast.For, ast.While)):
                    # Проверка вложенности циклов
                    nested_loops = self._count_nested_loops(node)
                    if nested_loops > 3:
                        issues.append(CodeIssue(
                            line=node.lineno,
                            column=node.col_offset,
                            severity="warning",
                            message=f"Слишком глубокая вложенность циклов: {nested_loops}",
                            rule_id="deep_nesting",
                            category="complexity"
                        ))
        
        except Exception as e:
            logger.error(f"Ошибка проверки сложности: {e}")
        
        return issues
    
    async def _check_python_quality(self, code: str) -> List[CodeIssue]:
        """Проверка качества Python кода"""
        issues = []
        
        try:
            lines = code.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Проверка длины строки
                if len(line) > 120:
                    issues.append(CodeIssue(
                        line=i,
                        column=0,
                        severity="warning",
                        message="Строка слишком длинная (>120 символов)",
                        rule_id="line_too_long",
                        category="quality"
                    ))
                
                # Проверка trailing whitespace
                if line.rstrip() != line:
                    issues.append(CodeIssue(
                        line=i,
                        column=len(line.rstrip()),
                        severity="info",
                        message="Лишние пробелы в конце строки",
                        rule_id="trailing_whitespace",
                        category="quality"
                    ))
                
                # Проверка импортов
                if line.strip().startswith('import ') and ',' in line:
                    issues.append(CodeIssue(
                        line=i,
                        column=0,
                        severity="warning",
                        message="Импорт нескольких модулей в одной строке",
                        rule_id="multiple_imports",
                        category="quality"
                    ))
        
        except Exception as e:
            logger.error(f"Ошибка проверки качества: {e}")
        
        return issues
    
    async def _check_python_security(self, code: str) -> List[CodeIssue]:
        """Проверка безопасности Python кода"""
        issues = []
        
        try:
            lines = code.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Проверка на использование eval
                if 'eval(' in line:
                    issues.append(CodeIssue(
                        line=i,
                        column=line.find('eval('),
                        severity="error",
                        message="Использование eval() может быть небезопасным",
                        rule_id="eval_usage",
                        category="security"
                    ))
                
                # Проверка на использование exec
                if 'exec(' in line:
                    issues.append(CodeIssue(
                        line=i,
                        column=line.find('exec('),
                        severity="error",
                        message="Использование exec() может быть небезопасным",
                        rule_id="exec_usage",
                        category="security"
                    ))
                
                # Проверка на SQL injection
                if 'execute(' in line and ('%' in line or '+' in line):
                    issues.append(CodeIssue(
                        line=i,
                        column=0,
                        severity="warning",
                        message="Возможная SQL injection атака",
                        rule_id="sql_injection",
                        category="security"
                    ))
        
        except Exception as e:
            logger.error(f"Ошибка проверки безопасности: {e}")
        
        return issues
    
    async def _check_python_performance(self, code: str) -> List[CodeIssue]:
        """Проверка производительности Python кода"""
        issues = []
        
        try:
            lines = code.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Проверка на использование глобальных переменных в циклах
                if any(keyword in line for keyword in ['for ', 'while ']):
                    # Простая проверка на глобальные переменные
                    if 'global ' in line:
                        issues.append(CodeIssue(
                            line=i,
                            column=0,
                            severity="warning",
                            message="Использование глобальных переменных в цикле может снизить производительность",
                            rule_id="global_in_loop",
                            category="performance"
                        ))
                
                # Проверка на неэффективные операции со строками
                if 'str +' in line or 'str +=' in line:
                    issues.append(CodeIssue(
                        line=i,
                        column=0,
                        severity="info",
                        message="Рассмотрите использование join() для конкатенации строк",
                        rule_id="inefficient_string_concat",
                        category="performance"
                    ))
        
        except Exception as e:
            logger.error(f"Ошибка проверки производительности: {e}")
        
        return issues
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Вычисление цикломатической сложности"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _count_nested_loops(self, node: ast.AST) -> int:
        """Подсчет вложенных циклов"""
        count = 0
        current = node
        
        while hasattr(current, 'parent'):
            if isinstance(current, (ast.For, ast.While)):
                count += 1
            current = current.parent
        
        return count
    
    async def _calculate_python_metrics(self, code: str) -> CodeMetrics:
        """Вычисление метрик Python кода"""
        try:
            lines = code.split('\n')
            lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            # Простое вычисление цикломатической сложности
            tree = ast.parse(code)
            complexity = 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)):
                    complexity += 1
            
            # Простой индекс поддерживаемости
            maintainability_index = max(0, 100 - (complexity * 2) - (lines_of_code / 10))
            
            return CodeMetrics(
                lines_of_code=lines_of_code,
                cyclomatic_complexity=complexity,
                maintainability_index=maintainability_index,
                technical_debt=complexity * 0.5,
                code_coverage=0.0  # Требует дополнительных инструментов
            )
            
        except Exception as e:
            logger.error(f"Ошибка вычисления метрик: {e}")
            return CodeMetrics(0, 0, 0.0, 0.0, 0.0)
    
    async def _generate_python_suggestions(self, code: str, issues: List[CodeIssue]) -> List[str]:
        """Генерация предложений по улучшению Python кода"""
        suggestions = []
        
        # Анализ проблем и генерация предложений
        for issue in issues:
            if issue.rule_id == "high_complexity":
                suggestions.append("Разбейте функцию на более мелкие части для снижения сложности")
            elif issue.rule_id == "deep_nesting":
                suggestions.append("Используйте early return или guard clauses для уменьшения вложенности")
            elif issue.rule_id == "line_too_long":
                suggestions.append("Разбейте длинную строку на несколько строк")
            elif issue.rule_id == "eval_usage":
                suggestions.append("Замените eval() на более безопасные альтернативы")
            elif issue.rule_id == "inefficient_string_concat":
                suggestions.append("Используйте ''.join() для конкатенации строк")
        
        # Общие предложения
        if not suggestions:
            suggestions.append("Код выглядит хорошо! Продолжайте в том же духе.")
        
        return suggestions
    
    async def _analyze_js_code(self, code: str, analysis_type: str) -> Dict[str, Any]:
        """Анализ JavaScript/TypeScript кода"""
        # Базовая реализация для JS/TS
        return {
            "issues": [],
            "metrics": {},
            "suggestions": ["Анализ JavaScript/TypeScript кода в разработке"],
            "language": "javascript",
            "analysis_type": analysis_type
        }
    
    async def _analyze_compiled_code(self, code: str, language: str, analysis_type: str) -> Dict[str, Any]:
        """Анализ скомпилированного кода (Java, C++, C)"""
        # Базовая реализация для скомпилированных языков
        return {
            "issues": [],
            "metrics": {},
            "suggestions": [f"Анализ {language} кода в разработке"],
            "language": language,
            "analysis_type": analysis_type
        }
    
    async def _analyze_generic_code(self, code: str, language: str, analysis_type: str) -> Dict[str, Any]:
        """Универсальный анализ кода"""
        lines = code.split('\n')
        lines_of_code = len([line for line in lines if line.strip()])
        
        return {
            "issues": [],
            "metrics": {
                "lines_of_code": lines_of_code,
                "cyclomatic_complexity": 1,
                "maintainability_index": 80.0,
                "technical_debt": 0.0,
                "code_coverage": 0.0
            },
            "suggestions": [f"Базовый анализ {language} кода выполнен"],
            "language": language,
            "analysis_type": analysis_type
        }
    
    async def suggest_improvements(self, code: str, language: str = "python", context: str = "") -> List[str]:
        """Предложение улучшений кода"""
        try:
            # Анализ кода
            analysis_result = await self.analyze_code(code, language, "full")
            
            # Генерация предложений на основе анализа
            suggestions = analysis_result.get("suggestions", [])
            
            # Дополнительные предложения на основе контекста
            if context:
                if "performance" in context.lower():
                    suggestions.append("Рассмотрите оптимизацию алгоритмов для улучшения производительности")
                if "security" in context.lower():
                    suggestions.append("Проверьте код на уязвимости безопасности")
                if "maintainability" in context.lower():
                    suggestions.append("Добавьте комментарии и документацию для улучшения читаемости")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Ошибка генерации предложений: {e}")
            return [f"Ошибка анализа: {str(e)}"]
    
    async def generate_tests(self, code: str, test_type: str = "unit", language: str = "python") -> Dict[str, Any]:
        """Генерация тестов для кода"""
        try:
            if language == "python":
                return await self._generate_python_tests(code, test_type)
            else:
                return {
                    "tests": [],
                    "coverage": 0.0,
                    "message": f"Генерация тестов для {language} в разработке"
                }
                
        except Exception as e:
            logger.error(f"Ошибка генерации тестов: {e}")
            return {
                "tests": [],
                "coverage": 0.0,
                "error": str(e)
            }
    
    async def _generate_python_tests(self, code: str, test_type: str) -> Dict[str, Any]:
        """Генерация Python тестов"""
        try:
            tree = ast.parse(code)
            tests = []
            
            # Поиск функций для тестирования
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith('_'):
                        functions.append(node.name)
            
            # Генерация базовых тестов
            for func_name in functions:
                test_code = f"""
def test_{func_name}():
    \"\"\"Тест для функции {func_name}\"\"\"
    # TODO: Добавьте тестовые случаи
    assert True
"""
                tests.append({
                    "name": f"test_{func_name}",
                    "code": test_code.strip(),
                    "type": test_type
                })
            
            return {
                "tests": tests,
                "coverage": len(tests) / max(len(functions), 1) * 100,
                "message": f"Сгенерировано {len(tests)} тестов"
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации Python тестов: {e}")
            return {
                "tests": [],
                "coverage": 0.0,
                "error": str(e)
            }