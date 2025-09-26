#!/usr/bin/env python3
"""
Code Modifier - Модификатор кода
Автор: Jarvis AI Assistant
Версия: 1.0.0
"""

import ast
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class RefactorType(Enum):
    """Типы рефакторинга"""
    EXTRACT_METHOD = "extract_method"
    RENAME_VARIABLE = "rename_variable"
    SIMPLIFY_CONDITION = "simplify_condition"
    REMOVE_DUPLICATE = "remove_duplicate"
    OPTIMIZE_IMPORTS = "optimize_imports"
    ADD_TYPE_HINTS = "add_type_hints"
    GENERAL = "general"

@dataclass
class CodeModification:
    """Модификация кода"""
    line_start: int
    line_end: int
    old_code: str
    new_code: str
    description: str
    type: str

@dataclass
class ModificationResult:
    """Результат модификации кода"""
    original_code: str
    modified_code: str
    modifications: List[CodeModification]
    success: bool
    message: str

class CodeModifier:
    """Модификатор кода"""
    
    def __init__(self):
        self.ready = False
        self.supported_languages = ["python", "javascript", "typescript"]
        
    async def initialize(self):
        """Инициализация модификатора"""
        try:
            logger.info("Инициализация Code Modifier...")
            self.ready = True
            logger.info("Code Modifier инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации Code Modifier: {e}")
            raise
    
    async def cleanup(self):
        """Очистка ресурсов"""
        self.ready = False
        logger.info("Code Modifier очищен")
    
    def is_ready(self) -> bool:
        """Проверка готовности модификатора"""
        return self.ready
    
    async def modify_code(self, code: str, modifications: List[Dict], language: str = "python") -> Dict[str, Any]:
        """Модификация кода"""
        try:
            if not self.ready:
                raise Exception("Code Modifier не готов")
            
            if language not in self.supported_languages:
                raise Exception(f"Неподдерживаемый язык: {language}")
            
            if language == "python":
                return await self._modify_python_code(code, modifications)
            else:
                return await self._modify_generic_code(code, modifications, language)
                
        except Exception as e:
            logger.error(f"Ошибка модификации кода: {e}")
            raise
    
    async def _modify_python_code(self, code: str, modifications: List[Dict]) -> Dict[str, Any]:
        """Модификация Python кода"""
        try:
            lines = code.split('\n')
            applied_modifications = []
            
            # Применение модификаций
            for mod in modifications:
                mod_type = mod.get("type")
                mod_data = mod.get("data", {})
                
                if mod_type == "replace":
                    result = await self._apply_replace_modification(lines, mod_data)
                    if result:
                        applied_modifications.append(result)
                elif mod_type == "insert":
                    result = await self._apply_insert_modification(lines, mod_data)
                    if result:
                        applied_modifications.append(result)
                elif mod_type == "delete":
                    result = await self._apply_delete_modification(lines, mod_data)
                    if result:
                        applied_modifications.append(result)
                elif mod_type == "refactor":
                    result = await self._apply_refactor_modification(lines, mod_data)
                    if result:
                        applied_modifications.extend(result)
            
            modified_code = '\n'.join(lines)
            
            return {
                "original_code": code,
                "modified_code": modified_code,
                "modifications": [mod.__dict__ for mod in applied_modifications],
                "success": True,
                "message": f"Применено {len(applied_modifications)} модификаций"
            }
            
        except Exception as e:
            logger.error(f"Ошибка модификации Python кода: {e}")
            return {
                "original_code": code,
                "modified_code": code,
                "modifications": [],
                "success": False,
                "message": f"Ошибка модификации: {str(e)}"
            }
    
    async def _apply_replace_modification(self, lines: List[str], data: Dict) -> Optional[CodeModification]:
        """Применение модификации замены"""
        try:
            line_num = data.get("line", 1) - 1
            old_text = data.get("old_text", "")
            new_text = data.get("new_text", "")
            
            if 0 <= line_num < len(lines):
                if old_text in lines[line_num]:
                    lines[line_num] = lines[line_num].replace(old_text, new_text)
                    return CodeModification(
                        line_start=line_num + 1,
                        line_end=line_num + 1,
                        old_code=old_text,
                        new_code=new_text,
                        description=f"Замена '{old_text}' на '{new_text}'",
                        type="replace"
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка применения замены: {e}")
            return None
    
    async def _apply_insert_modification(self, lines: List[str], data: Dict) -> Optional[CodeModification]:
        """Применение модификации вставки"""
        try:
            line_num = data.get("line", 1) - 1
            text = data.get("text", "")
            position = data.get("position", "after")  # before, after, replace
            
            if 0 <= line_num < len(lines):
                if position == "before":
                    lines.insert(line_num, text)
                    return CodeModification(
                        line_start=line_num + 1,
                        line_end=line_num + 1,
                        old_code="",
                        new_code=text,
                        description=f"Вставка перед строкой {line_num + 1}",
                        type="insert"
                    )
                elif position == "after":
                    lines.insert(line_num + 1, text)
                    return CodeModification(
                        line_start=line_num + 2,
                        line_end=line_num + 2,
                        old_code="",
                        new_code=text,
                        description=f"Вставка после строки {line_num + 1}",
                        type="insert"
                    )
                elif position == "replace":
                    old_line = lines[line_num]
                    lines[line_num] = text
                    return CodeModification(
                        line_start=line_num + 1,
                        line_end=line_num + 1,
                        old_code=old_line,
                        new_code=text,
                        description=f"Замена строки {line_num + 1}",
                        type="insert"
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка применения вставки: {e}")
            return None
    
    async def _apply_delete_modification(self, lines: List[str], data: Dict) -> Optional[CodeModification]:
        """Применение модификации удаления"""
        try:
            line_num = data.get("line", 1) - 1
            
            if 0 <= line_num < len(lines):
                deleted_line = lines[line_num]
                del lines[line_num]
                return CodeModification(
                    line_start=line_num + 1,
                    line_end=line_num + 1,
                    old_code=deleted_line,
                    new_code="",
                    description=f"Удаление строки {line_num + 1}",
                    type="delete"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка применения удаления: {e}")
            return None
    
    async def _apply_refactor_modification(self, lines: List[str], data: Dict) -> List[CodeModification]:
        """Применение модификации рефакторинга"""
        try:
            refactor_type = data.get("refactor_type", "general")
            modifications = []
            
            if refactor_type == "extract_method":
                modifications.extend(await self._extract_method_refactor(lines, data))
            elif refactor_type == "rename_variable":
                modifications.extend(await self._rename_variable_refactor(lines, data))
            elif refactor_type == "simplify_condition":
                modifications.extend(await self._simplify_condition_refactor(lines, data))
            elif refactor_type == "optimize_imports":
                modifications.extend(await self._optimize_imports_refactor(lines, data))
            elif refactor_type == "add_type_hints":
                modifications.extend(await self._add_type_hints_refactor(lines, data))
            
            return modifications
            
        except Exception as e:
            logger.error(f"Ошибка применения рефакторинга: {e}")
            return []
    
    async def _extract_method_refactor(self, lines: List[str], data: Dict) -> List[CodeModification]:
        """Рефакторинг извлечения метода"""
        modifications = []
        
        try:
            # Простая реализация извлечения метода
            start_line = data.get("start_line", 1) - 1
            end_line = data.get("end_line", 1) - 1
            method_name = data.get("method_name", "extracted_method")
            
            if 0 <= start_line <= end_line < len(lines):
                # Извлечение кода
                extracted_code = lines[start_line:end_line + 1]
                
                # Создание нового метода
                method_code = [
                    f"def {method_name}():",
                    "    \"\"\"Извлеченный метод\"\"\""
                ]
                for line in extracted_code:
                    method_code.append(f"    {line}")
                
                # Замена исходного кода на вызов метода
                lines[start_line:end_line + 1] = [f"    {method_name}()"]
                
                # Добавление метода в конец
                lines.extend(method_code)
                
                modifications.append(CodeModification(
                    line_start=start_line + 1,
                    line_end=end_line + 1,
                    old_code='\n'.join(extracted_code),
                    new_code=f"{method_name}()",
                    description=f"Извлечение метода '{method_name}'",
                    type="extract_method"
                ))
        
        except Exception as e:
            logger.error(f"Ошибка извлечения метода: {e}")
        
        return modifications
    
    async def _rename_variable_refactor(self, lines: List[str], data: Dict) -> List[CodeModification]:
        """Рефакторинг переименования переменной"""
        modifications = []
        
        try:
            old_name = data.get("old_name", "")
            new_name = data.get("new_name", "")
            
            if old_name and new_name:
                for i, line in enumerate(lines):
                    if old_name in line:
                        old_line = line
                        new_line = re.sub(r'\b' + re.escape(old_name) + r'\b', new_name, line)
                        lines[i] = new_line
                        
                        modifications.append(CodeModification(
                            line_start=i + 1,
                            line_end=i + 1,
                            old_code=old_line,
                            new_code=new_line,
                            description=f"Переименование '{old_name}' в '{new_name}'",
                            type="rename_variable"
                        ))
        
        except Exception as e:
            logger.error(f"Ошибка переименования переменной: {e}")
        
        return modifications
    
    async def _simplify_condition_refactor(self, lines: List[str], data: Dict) -> List[CodeModification]:
        """Рефакторинг упрощения условий"""
        modifications = []
        
        try:
            line_num = data.get("line", 1) - 1
            
            if 0 <= line_num < len(lines):
                line = lines[line_num]
                
                # Простые упрощения условий
                if 'if True:' in line:
                    new_line = line.replace('if True:', 'if True:  # Упрощено')
                    lines[line_num] = new_line
                    modifications.append(CodeModification(
                        line_start=line_num + 1,
                        line_end=line_num + 1,
                        old_code=line,
                        new_code=new_line,
                        description="Упрощение условия",
                        type="simplify_condition"
                    ))
                elif 'if False:' in line:
                    new_line = line.replace('if False:', 'if False:  # Упрощено')
                    lines[line_num] = new_line
                    modifications.append(CodeModification(
                        line_start=line_num + 1,
                        line_end=line_num + 1,
                        old_code=line,
                        new_code=new_line,
                        description="Упрощение условия",
                        type="simplify_condition"
                    ))
        
        except Exception as e:
            logger.error(f"Ошибка упрощения условия: {e}")
        
        return modifications
    
    async def _optimize_imports_refactor(self, lines: List[str], data: Dict) -> List[CodeModification]:
        """Рефакторинг оптимизации импортов"""
        modifications = []
        
        try:
            # Поиск импортов
            import_lines = []
            for i, line in enumerate(lines):
                if line.strip().startswith(('import ', 'from ')):
                    import_lines.append((i, line))
            
            # Группировка и сортировка импортов
            if import_lines:
                # Простая сортировка
                import_lines.sort(key=lambda x: x[1])
                
                # Замена импортов
                for i, (line_num, _) in enumerate(import_lines):
                    old_line = lines[line_num]
                    new_line = import_lines[i][1]
                    lines[line_num] = new_line
                    
                    if old_line != new_line:
                        modifications.append(CodeModification(
                            line_start=line_num + 1,
                            line_end=line_num + 1,
                            old_code=old_line,
                            new_code=new_line,
                            description="Оптимизация импортов",
                            type="optimize_imports"
                        ))
        
        except Exception as e:
            logger.error(f"Ошибка оптимизации импортов: {e}")
        
        return modifications
    
    async def _add_type_hints_refactor(self, lines: List[str], data: Dict) -> List[CodeModification]:
        """Рефакторинг добавления типов"""
        modifications = []
        
        try:
            for i, line in enumerate(lines):
                # Поиск определений функций без типов
                if re.match(r'def\s+\w+\([^)]*\):', line) and '->' not in line:
                    # Простое добавление типов
                    new_line = line.replace('):', ') -> None:')
                    lines[i] = new_line
                    
                    modifications.append(CodeModification(
                        line_start=i + 1,
                        line_end=i + 1,
                        old_code=line,
                        new_code=new_line,
                        description="Добавление типов",
                        type="add_type_hints"
                    ))
        
        except Exception as e:
            logger.error(f"Ошибка добавления типов: {e}")
        
        return modifications
    
    async def _modify_generic_code(self, code: str, modifications: List[Dict], language: str) -> Dict[str, Any]:
        """Универсальная модификация кода"""
        try:
            lines = code.split('\n')
            applied_modifications = []
            
            # Простые модификации для любого языка
            for mod in modifications:
                mod_type = mod.get("type")
                mod_data = mod.get("data", {})
                
                if mod_type == "replace":
                    result = await self._apply_replace_modification(lines, mod_data)
                    if result:
                        applied_modifications.append(result)
                elif mod_type == "insert":
                    result = await self._apply_insert_modification(lines, mod_data)
                    if result:
                        applied_modifications.append(result)
                elif mod_type == "delete":
                    result = await self._apply_delete_modification(lines, mod_data)
                    if result:
                        applied_modifications.append(result)
            
            modified_code = '\n'.join(lines)
            
            return {
                "original_code": code,
                "modified_code": modified_code,
                "modifications": [mod.__dict__ for mod in applied_modifications],
                "success": True,
                "message": f"Применено {len(applied_modifications)} модификаций для {language}"
            }
            
        except Exception as e:
            logger.error(f"Ошибка универсальной модификации: {e}")
            return {
                "original_code": code,
                "modified_code": code,
                "modifications": [],
                "success": False,
                "message": f"Ошибка модификации: {str(e)}"
            }
    
    async def refactor_code(self, code: str, refactor_type: str = "general", language: str = "python") -> Dict[str, Any]:
        """Рефакторинг кода"""
        try:
            if not self.ready:
                raise Exception("Code Modifier не готов")
            
            if language == "python":
                return await self._refactor_python_code(code, refactor_type)
            else:
                return {
                    "original_code": code,
                    "refactored_code": code,
                    "refactor_type": refactor_type,
                    "success": False,
                    "message": f"Рефакторинг {language} в разработке"
                }
                
        except Exception as e:
            logger.error(f"Ошибка рефакторинга: {e}")
            return {
                "original_code": code,
                "refactored_code": code,
                "refactor_type": refactor_type,
                "success": False,
                "message": f"Ошибка рефакторинга: {str(e)}"
            }
    
    async def _refactor_python_code(self, code: str, refactor_type: str) -> Dict[str, Any]:
        """Рефакторинг Python кода"""
        try:
            lines = code.split('\n')
            modifications = []
            
            if refactor_type == "general":
                # Общий рефакторинг
                modifications.extend(await self._general_python_refactor(lines))
            elif refactor_type == "extract_method":
                modifications.extend(await self._extract_method_refactor(lines, {}))
            elif refactor_type == "optimize_imports":
                modifications.extend(await self._optimize_imports_refactor(lines, {}))
            elif refactor_type == "add_type_hints":
                modifications.extend(await self._add_type_hints_refactor(lines, {}))
            
            refactored_code = '\n'.join(lines)
            
            return {
                "original_code": code,
                "refactored_code": refactored_code,
                "refactor_type": refactor_type,
                "modifications": [mod.__dict__ for mod in modifications],
                "success": True,
                "message": f"Применено {len(modifications)} рефакторингов"
            }
            
        except Exception as e:
            logger.error(f"Ошибка рефакторинга Python кода: {e}")
            return {
                "original_code": code,
                "refactored_code": code,
                "refactor_type": refactor_type,
                "success": False,
                "message": f"Ошибка рефакторинга: {str(e)}"
            }
    
    async def _general_python_refactor(self, lines: List[str]) -> List[CodeModification]:
        """Общий рефакторинг Python кода"""
        modifications = []
        
        try:
            # Оптимизация импортов
            modifications.extend(await self._optimize_imports_refactor(lines, {}))
            
            # Добавление типов
            modifications.extend(await self._add_type_hints_refactor(lines, {}))
            
            # Упрощение условий
            for i, line in enumerate(lines):
                if 'if True:' in line or 'if False:' in line:
                    modifications.extend(await self._simplify_condition_refactor(lines, {"line": i + 1}))
        
        except Exception as e:
            logger.error(f"Ошибка общего рефакторинга: {e}")
        
        return modifications