"""
Анализатор команд для Brain Service
Анализ намерений и извлечение параметров из команд пользователя
"""
import re
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

from utils.logger import get_logger
from utils.database import LearningDataManager

logger = get_logger("command-analyzer")

class CommandType(Enum):
    """Типы команд"""
    GENERAL = "general"
    CODE_ANALYSIS = "code_analysis"
    TASK_EXECUTION = "task_execution"
    QUESTION = "question"
    FILE_OPERATION = "file_operation"
    SYSTEM_COMMAND = "system_command"
    WEB_SEARCH = "web_search"
    REMINDER = "reminder"
    CALCULATION = "calculation"

@dataclass
class CommandAnalysis:
    """Результат анализа команды"""
    intent: CommandType
    confidence: float
    parameters: Dict[str, Any]
    entities: List[Dict[str, Any]]
    context_required: bool
    complexity: str  # "simple", "medium", "complex"

class CommandAnalyzer:
    """Анализатор команд пользователя"""
    
    def __init__(self, brain_processor, learning_manager: LearningDataManager):
        self.brain_processor = brain_processor
        self.learning_manager = learning_manager
        
        # Паттерны для распознавания команд
        self.command_patterns = {
            CommandType.CODE_ANALYSIS: [
                r"проанализируй код",
                r"найди ошибку в",
                r"оптимизируй код",
                r"объясни как работает",
                r"напиши код для",
                r"создай функцию",
                r"отлади код"
            ],
            CommandType.TASK_EXECUTION: [
                r"выполни задачу",
                r"сделай",
                r"создай",
                r"удали",
                r"перемести",
                r"скопируй",
                r"открой",
                r"запусти"
            ],
            CommandType.FILE_OPERATION: [
                r"создай файл",
                r"удали файл",
                r"переименуй файл",
                r"скопируй файл",
                r"перемести файл",
                r"открой файл",
                r"сохрани файл"
            ],
            CommandType.SYSTEM_COMMAND: [
                r"перезагрузи систему",
                r"выключи компьютер",
                r"покажи процессы",
                r"освободи память",
                r"проверь диск"
            ],
            CommandType.WEB_SEARCH: [
                r"найди в интернете",
                r"поищи информацию о",
                r"что такое",
                r"как работает",
                r"где найти"
            ],
            CommandType.REMINDER: [
                r"напомни мне",
                r"создай напоминание",
                r"поставь будильник",
                r"запланируй"
            ],
            CommandType.CALCULATION: [
                r"посчитай",
                r"вычисли",
                r"сколько будет",
                r"реши уравнение",
                r"найди корень"
            ],
            CommandType.QUESTION: [
                r"что такое",
                r"как работает",
                r"почему",
                r"зачем",
                r"объясни",
                r"расскажи о"
            ]
        }
        
        # Паттерны для извлечения сущностей
        self.entity_patterns = {
            "file_path": r"(?:файл|папка|директория)\s+([^\s]+)",
            "url": r"(https?://[^\s]+)",
            "time": r"(\d{1,2}:\d{2})",
            "date": r"(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
            "number": r"(\d+(?:\.\d+)?)",
            "email": r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            "phone": r"(\+?[1-9]\d{1,14})"
        }
        
        # Ключевые слова для определения сложности
        self.complexity_keywords = {
            "simple": ["создай", "удали", "открой", "покажи", "найди"],
            "medium": ["проанализируй", "оптимизируй", "настрой", "настройка"],
            "complex": ["разработай", "спроектируй", "реализуй", "интегрируй"]
        }
        
        logger.info("Command analyzer initialized")
    
    async def analyze_command(self, command: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Анализ команды пользователя"""
        try:
            # Нормализация команды
            normalized_command = self._normalize_command(command)
            
            # Определение намерения
            intent_analysis = await self._analyze_intent(normalized_command)
            
            # Извлечение сущностей
            entities = self._extract_entities(normalized_command)
            
            # Извлечение параметров
            parameters = self._extract_parameters(normalized_command, entities)
            
            # Определение сложности
            complexity = self._determine_complexity(normalized_command)
            
            # Определение необходимости контекста
            context_required = self._requires_context(intent_analysis.intent, parameters)
            
            # Создание результата анализа
            analysis = CommandAnalysis(
                intent=intent_analysis.intent,
                confidence=intent_analysis.confidence,
                parameters=parameters,
                entities=entities,
                context_required=context_required,
                complexity=complexity
            )
            
            # Сохранение в память для обучения
            await self._store_analysis_for_learning(command, analysis, context)
            
            return {
                "intent": analysis.intent.value,
                "confidence": analysis.confidence,
                "parameters": analysis.parameters,
                "entities": analysis.entities,
                "context_required": analysis.context_required,
                "complexity": analysis.complexity,
                "normalized_command": normalized_command
            }
            
        except Exception as e:
            logger.error(f"Command analysis failed: {e}")
            return {
                "intent": "general",
                "confidence": 0.0,
                "parameters": {},
                "entities": [],
                "context_required": False,
                "complexity": "simple",
                "error": str(e)
            }
    
    async def analyze_intent(self, command: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Анализ намерения пользователя"""
        try:
            normalized_command = self._normalize_command(command)
            intent_analysis = await self._analyze_intent(normalized_command)
            
            return {
                "intent": intent_analysis.intent.value,
                "confidence": intent_analysis.confidence,
                "command": normalized_command
            }
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return {
                "intent": "general",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _normalize_command(self, command: str) -> str:
        """Нормализация команды"""
        # Приведение к нижнему регистру
        normalized = command.lower().strip()
        
        # Удаление лишних пробелов
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Удаление знаков препинания в конце
        normalized = re.sub(r'[.!?]+$', '', normalized)
        
        return normalized
    
    async def _analyze_intent(self, command: str) -> Tuple[CommandType, float]:
        """Анализ намерения команды"""
        best_match = CommandType.GENERAL
        best_confidence = 0.0
        
        # Проверка паттернов
        for intent_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    confidence = 0.8  # Базовая уверенность
                    
                    # Увеличение уверенности при точном совпадении
                    if re.match(pattern, command, re.IGNORECASE):
                        confidence = 0.95
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = intent_type
        
        # Если не найдено совпадений, используем AI для анализа
        if best_confidence < 0.5:
            ai_analysis = await self._ai_intent_analysis(command)
            if ai_analysis["confidence"] > best_confidence:
                best_match = CommandType(ai_analysis["intent"])
                best_confidence = ai_analysis["confidence"]
        
        return best_match, best_confidence
    
    async def _ai_intent_analysis(self, command: str) -> Dict[str, Any]:
        """Анализ намерения с помощью AI"""
        try:
            # Создание промпта для анализа намерения
            prompt = f"""
            Проанализируй намерение пользователя в следующей команде и определи тип команды.
            
            Команда: "{command}"
            
            Возможные типы:
            - general: общий вопрос или просьба
            - code_analysis: анализ, написание или отладка кода
            - task_execution: выполнение конкретной задачи
            - file_operation: работа с файлами
            - system_command: системные команды
            - web_search: поиск в интернете
            - reminder: создание напоминаний
            - calculation: вычисления и расчеты
            - question: вопрос, требующий объяснения
            
            Ответь в формате JSON:
            {{"intent": "тип_команды", "confidence": 0.0-1.0, "reasoning": "объяснение"}}
            """
            
            # Генерация ответа с помощью AI
            response = await self.brain_processor.generate_response(prompt, {})
            
            # Парсинг ответа
            try:
                result = json.loads(response["text"])
                return {
                    "intent": result.get("intent", "general"),
                    "confidence": float(result.get("confidence", 0.5)),
                    "reasoning": result.get("reasoning", "")
                }
            except json.JSONDecodeError:
                # Если не удалось распарсить JSON, используем простой анализ
                return self._fallback_intent_analysis(command)
                
        except Exception as e:
            logger.error(f"AI intent analysis failed: {e}")
            return self._fallback_intent_analysis(command)
    
    def _fallback_intent_analysis(self, command: str) -> Dict[str, Any]:
        """Резервный анализ намерения"""
        # Простой анализ на основе ключевых слов
        if any(word in command for word in ["код", "функция", "программа", "алгоритм"]):
            return {"intent": "code_analysis", "confidence": 0.6}
        elif any(word in command for word in ["создай", "сделай", "выполни"]):
            return {"intent": "task_execution", "confidence": 0.6}
        elif any(word in command for word in ["файл", "папка", "директория"]):
            return {"intent": "file_operation", "confidence": 0.6}
        elif any(word in command for word in ["что", "как", "почему", "объясни"]):
            return {"intent": "question", "confidence": 0.6}
        else:
            return {"intent": "general", "confidence": 0.5}
    
    def _extract_entities(self, command: str) -> List[Dict[str, Any]]:
        """Извлечение сущностей из команды"""
        entities = []
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, command, re.IGNORECASE)
            for match in matches:
                entities.append({
                    "type": entity_type,
                    "value": match.group(1),
                    "start": match.start(),
                    "end": match.end()
                })
        
        return entities
    
    def _extract_parameters(self, command: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Извлечение параметров из команды"""
        parameters = {}
        
        # Извлечение параметров на основе сущностей
        for entity in entities:
            entity_type = entity["type"]
            entity_value = entity["value"]
            
            if entity_type == "file_path":
                parameters["file_path"] = entity_value
            elif entity_type == "url":
                parameters["url"] = entity_value
            elif entity_type == "time":
                parameters["time"] = entity_value
            elif entity_type == "date":
                parameters["date"] = entity_value
            elif entity_type == "number":
                parameters["number"] = float(entity_value)
            elif entity_type == "email":
                parameters["email"] = entity_value
            elif entity_type == "phone":
                parameters["phone"] = entity_value
        
        # Извлечение дополнительных параметров
        parameters.update(self._extract_additional_parameters(command))
        
        return parameters
    
    def _extract_additional_parameters(self, command: str) -> Dict[str, Any]:
        """Извлечение дополнительных параметров"""
        parameters = {}
        
        # Поиск параметров в кавычках
        quoted_params = re.findall(r'"([^"]*)"', command)
        if quoted_params:
            parameters["quoted_text"] = quoted_params
        
        # Поиск числовых параметров
        numbers = re.findall(r'\d+(?:\.\d+)?', command)
        if numbers:
            parameters["numbers"] = [float(n) for n in numbers]
        
        # Поиск булевых параметров
        if re.search(r'\b(да|нет|true|false|включить|выключить)\b', command, re.IGNORECASE):
            parameters["boolean"] = re.search(r'\b(да|true|включить)\b', command, re.IGNORECASE) is not None
        
        return parameters
    
    def _determine_complexity(self, command: str) -> str:
        """Определение сложности команды"""
        # Подсчет ключевых слов сложности
        complexity_scores = {"simple": 0, "medium": 0, "complex": 0}
        
        for complexity, keywords in self.complexity_keywords.items():
            for keyword in keywords:
                if keyword in command:
                    complexity_scores[complexity] += 1
        
        # Определение максимального балла
        max_complexity = max(complexity_scores, key=complexity_scores.get)
        
        # Если нет явных индикаторов, определяем по длине и структуре
        if complexity_scores[max_complexity] == 0:
            if len(command.split()) > 10:
                return "complex"
            elif len(command.split()) > 5:
                return "medium"
            else:
                return "simple"
        
        return max_complexity
    
    def _requires_context(self, intent: CommandType, parameters: Dict[str, Any]) -> bool:
        """Определение необходимости контекста"""
        # Команды, которые всегда требуют контекста
        context_required_intents = {
            CommandType.CODE_ANALYSIS,
            CommandType.TASK_EXECUTION,
            CommandType.SYSTEM_COMMAND
        }
        
        if intent in context_required_intents:
            return True
        
        # Проверка наличия неопределенных параметров
        if not parameters and intent != CommandType.GENERAL:
            return True
        
        return False
    
    async def _store_analysis_for_learning(self, command: str, analysis: CommandAnalysis, 
                                         context: Dict[str, Any] = None):
        """Сохранение анализа для обучения"""
        try:
            # Сохранение в память для будущего обучения
            await self.learning_manager.store_interaction(
                interaction_type="command_analysis",
                input_data={
                    "command": command,
                    "context": context or {}
                },
                output_data={
                    "intent": analysis.intent.value,
                    "confidence": analysis.confidence,
                    "parameters": analysis.parameters,
                    "entities": analysis.entities,
                    "complexity": analysis.complexity
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to store analysis for learning: {e}")
    
    def get_supported_commands(self) -> Dict[str, List[str]]:
        """Получение списка поддерживаемых команд"""
        return {
            intent_type.value: patterns 
            for intent_type, patterns in self.command_patterns.items()
        }
    
    def get_entity_types(self) -> List[str]:
        """Получение типов извлекаемых сущностей"""
        return list(self.entity_patterns.keys())