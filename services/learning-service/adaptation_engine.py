#!/usr/bin/env python3
"""
Adaptation Engine - Движок адаптации
Автор: Jarvis AI Assistant
Версия: 1.0.0
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class AdaptationType(Enum):
    """Типы адаптации"""
    BEHAVIORAL = "behavioral"
    PERFORMANCE = "performance"
    PREFERENCE = "preference"
    CONTEXTUAL = "contextual"
    TEMPORAL = "temporal"

class AdaptationTrigger(Enum):
    """Триггеры адаптации"""
    USER_FEEDBACK = "user_feedback"
    PERFORMANCE_DROP = "performance_drop"
    NEW_CONTEXT = "new_context"
    TIME_BASED = "time_based"
    MANUAL = "manual"

@dataclass
class AdaptationContext:
    """Контекст адаптации"""
    user_id: str
    session_id: str
    environment: Dict[str, Any]
    user_preferences: Dict[str, Any]
    historical_data: Dict[str, Any]
    current_metrics: Dict[str, float]
    timestamp: datetime

@dataclass
class AdaptationResult:
    """Результат адаптации"""
    success: bool
    adaptation_type: AdaptationType
    changes_applied: List[Dict[str, Any]]
    performance_impact: float
    confidence: float
    adaptation_time: float
    message: str

class AdaptationEngine:
    """Движок адаптации"""
    
    def __init__(self):
        self.ready = False
        self.adaptation_history = []
        self.user_profiles = {}
        self.performance_baselines = {}
        self.adaptation_rules = {}
        
    async def initialize(self):
        """Инициализация движка адаптации"""
        try:
            logger.info("Инициализация Adaptation Engine...")
            
            # Загрузка правил адаптации
            await self._load_adaptation_rules()
            
            # Инициализация базовых профилей
            await self._initialize_baselines()
            
            self.ready = True
            logger.info("Adaptation Engine инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации Adaptation Engine: {e}")
            raise
    
    async def cleanup(self):
        """Очистка ресурсов"""
        self.ready = False
        logger.info("Adaptation Engine очищен")
    
    def is_ready(self) -> bool:
        """Проверка готовности движка"""
        return self.ready
    
    async def _load_adaptation_rules(self):
        """Загрузка правил адаптации"""
        try:
            # Базовые правила адаптации
            self.adaptation_rules = {
                "performance_drop": {
                    "threshold": 0.8,
                    "action": "optimize_parameters",
                    "priority": "high"
                },
                "user_feedback_negative": {
                    "threshold": 3,
                    "action": "adjust_behavior",
                    "priority": "medium"
                },
                "new_user": {
                    "action": "initialize_profile",
                    "priority": "high"
                },
                "context_change": {
                    "action": "adapt_to_context",
                    "priority": "medium"
                }
            }
            
            logger.info("Правила адаптации загружены")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки правил адаптации: {e}")
    
    async def _initialize_baselines(self):
        """Инициализация базовых показателей"""
        try:
            # Базовые показатели производительности
            self.performance_baselines = {
                "response_time": 1.0,  # секунды
                "accuracy": 0.8,       # точность
                "user_satisfaction": 0.7,  # удовлетворенность
                "task_completion": 0.9,    # выполнение задач
                "error_rate": 0.1          # частота ошибок
            }
            
            logger.info("Базовые показатели инициализированы")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации базовых показателей: {e}")
    
    async def adapt(self, context: Dict[str, Any], adaptation_type: str = "general") -> Dict[str, Any]:
        """Адаптация к контексту"""
        try:
            if not self.ready:
                raise Exception("Adaptation Engine не готов")
            
            start_time = asyncio.get_event_loop().time()
            
            # Создание контекста адаптации
            adaptation_context = AdaptationContext(
                user_id=context.get("user_id", "unknown"),
                session_id=context.get("session_id", "unknown"),
                environment=context.get("environment", {}),
                user_preferences=context.get("user_preferences", {}),
                historical_data=context.get("historical_data", {}),
                current_metrics=context.get("current_metrics", {}),
                timestamp=datetime.now()
            )
            
            # Адаптация в зависимости от типа
            if adaptation_type == "behavioral":
                result = await self._behavioral_adaptation(adaptation_context)
            elif adaptation_type == "performance":
                result = await self._performance_adaptation(adaptation_context)
            elif adaptation_type == "preference":
                result = await self._preference_adaptation(adaptation_context)
            elif adaptation_type == "contextual":
                result = await self._contextual_adaptation(adaptation_context)
            elif adaptation_type == "temporal":
                result = await self._temporal_adaptation(adaptation_context)
            else:
                result = await self._general_adaptation(adaptation_context)
            
            # Сохранение в историю
            self.adaptation_history.append({
                "context": asdict(adaptation_context),
                "result": asdict(result),
                "adaptation_type": adaptation_type,
                "timestamp": datetime.now().isoformat()
            })
            
            # Ограничение размера истории
            if len(self.adaptation_history) > 500:
                self.adaptation_history = self.adaptation_history[-250:]
            
            return {
                "success": result.success,
                "adaptation_type": result.adaptation_type.value,
                "changes_applied": result.changes_applied,
                "performance_impact": result.performance_impact,
                "confidence": result.confidence,
                "adaptation_time": result.adaptation_time,
                "message": result.message
            }
            
        except Exception as e:
            logger.error(f"Ошибка адаптации: {e}")
            return {
                "success": False,
                "error": str(e),
                "adaptation_type": adaptation_type
            }
    
    async def _behavioral_adaptation(self, context: AdaptationContext) -> AdaptationResult:
        """Поведенческая адаптация"""
        try:
            changes_applied = []
            performance_impact = 0.0
            
            # Анализ поведения пользователя
            user_id = context.user_id
            
            if user_id not in self.user_profiles:
                # Создание нового профиля пользователя
                self.user_profiles[user_id] = {
                    "interaction_patterns": {},
                    "preferred_responses": {},
                    "communication_style": "formal",
                    "response_length": "medium",
                    "created_at": datetime.now()
                }
                changes_applied.append({
                    "type": "create_user_profile",
                    "user_id": user_id,
                    "details": "Создан новый профиль пользователя"
                })
                performance_impact = 0.1
            
            # Адаптация стиля общения
            user_profile = self.user_profiles[user_id]
            environment = context.environment
            
            if environment.get("time_of_day") in ["morning", "evening"]:
                user_profile["communication_style"] = "casual"
                changes_applied.append({
                    "type": "adjust_communication_style",
                    "style": "casual",
                    "reason": "Время дня"
                })
                performance_impact += 0.05
            
            # Адаптация длины ответов
            if context.user_preferences.get("detailed_responses", False):
                user_profile["response_length"] = "long"
                changes_applied.append({
                    "type": "adjust_response_length",
                    "length": "long",
                    "reason": "Предпочтения пользователя"
                })
                performance_impact += 0.03
            
            return AdaptationResult(
                success=True,
                adaptation_type=AdaptationType.BEHAVIORAL,
                changes_applied=changes_applied,
                performance_impact=performance_impact,
                confidence=0.8,
                adaptation_time=0.1,
                message="Поведенческая адаптация выполнена"
            )
            
        except Exception as e:
            logger.error(f"Ошибка поведенческой адаптации: {e}")
            return AdaptationResult(
                success=False,
                adaptation_type=AdaptationType.BEHAVIORAL,
                changes_applied=[],
                performance_impact=0.0,
                confidence=0.0,
                adaptation_time=0.0,
                message=f"Ошибка: {str(e)}"
            )
    
    async def _performance_adaptation(self, context: AdaptationContext) -> AdaptationResult:
        """Адаптация производительности"""
        try:
            changes_applied = []
            performance_impact = 0.0
            
            current_metrics = context.current_metrics
            
            # Проверка показателей производительности
            for metric, baseline in self.performance_baselines.items():
                current_value = current_metrics.get(metric, baseline)
                
                if current_value < baseline * 0.8:  # Падение на 20%
                    # Применение оптимизации
                    optimization = await self._apply_performance_optimization(metric, current_value, baseline)
                    changes_applied.append(optimization)
                    performance_impact += 0.1
            
            # Адаптация на основе исторических данных
            historical_data = context.historical_data
            if historical_data.get("avg_response_time", 0) > 2.0:
                changes_applied.append({
                    "type": "optimize_response_time",
                    "action": "reduce_processing_complexity",
                    "expected_improvement": 0.3
                })
                performance_impact += 0.15
            
            return AdaptationResult(
                success=True,
                adaptation_type=AdaptationType.PERFORMANCE,
                changes_applied=changes_applied,
                performance_impact=performance_impact,
                confidence=0.9,
                adaptation_time=0.2,
                message="Адаптация производительности выполнена"
            )
            
        except Exception as e:
            logger.error(f"Ошибка адаптации производительности: {e}")
            return AdaptationResult(
                success=False,
                adaptation_type=AdaptationType.PERFORMANCE,
                changes_applied=[],
                performance_impact=0.0,
                confidence=0.0,
                adaptation_time=0.0,
                message=f"Ошибка: {str(e)}"
            )
    
    async def _preference_adaptation(self, context: AdaptationContext) -> AdaptationResult:
        """Адаптация предпочтений"""
        try:
            changes_applied = []
            performance_impact = 0.0
            
            user_preferences = context.user_preferences
            user_id = context.user_id
            
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = {}
            
            user_profile = self.user_profiles[user_id]
            
            # Адаптация на основе предпочтений
            for preference, value in user_preferences.items():
                if preference == "language":
                    user_profile["language"] = value
                    changes_applied.append({
                        "type": "set_language",
                        "language": value
                    })
                    performance_impact += 0.05
                
                elif preference == "response_format":
                    user_profile["response_format"] = value
                    changes_applied.append({
                        "type": "set_response_format",
                        "format": value
                    })
                    performance_impact += 0.03
                
                elif preference == "notification_frequency":
                    user_profile["notification_frequency"] = value
                    changes_applied.append({
                        "type": "set_notification_frequency",
                        "frequency": value
                    })
                    performance_impact += 0.02
            
            return AdaptationResult(
                success=True,
                adaptation_type=AdaptationType.PREFERENCE,
                changes_applied=changes_applied,
                performance_impact=performance_impact,
                confidence=0.95,
                adaptation_time=0.05,
                message="Адаптация предпочтений выполнена"
            )
            
        except Exception as e:
            logger.error(f"Ошибка адаптации предпочтений: {e}")
            return AdaptationResult(
                success=False,
                adaptation_type=AdaptationType.PREFERENCE,
                changes_applied=[],
                performance_impact=0.0,
                confidence=0.0,
                adaptation_time=0.0,
                message=f"Ошибка: {str(e)}"
            )
    
    async def _contextual_adaptation(self, context: AdaptationContext) -> AdaptationResult:
        """Контекстная адаптация"""
        try:
            changes_applied = []
            performance_impact = 0.0
            
            environment = context.environment
            
            # Адаптация к устройству
            device_type = environment.get("device_type", "desktop")
            if device_type == "mobile":
                changes_applied.append({
                    "type": "optimize_for_mobile",
                    "actions": ["reduce_response_length", "simplify_interface"]
                })
                performance_impact += 0.1
            
            # Адаптация к местоположению
            location = environment.get("location", "unknown")
            if location != "unknown":
                changes_applied.append({
                    "type": "adapt_to_location",
                    "location": location,
                    "actions": ["adjust_timezone", "localize_content"]
                })
                performance_impact += 0.05
            
            # Адаптация к сетевому соединению
            connection_speed = environment.get("connection_speed", "fast")
            if connection_speed == "slow":
                changes_applied.append({
                    "type": "optimize_for_slow_connection",
                    "actions": ["compress_responses", "reduce_data_transfer"]
                })
                performance_impact += 0.15
            
            return AdaptationResult(
                success=True,
                adaptation_type=AdaptationType.CONTEXTUAL,
                changes_applied=changes_applied,
                performance_impact=performance_impact,
                confidence=0.85,
                adaptation_time=0.08,
                message="Контекстная адаптация выполнена"
            )
            
        except Exception as e:
            logger.error(f"Ошибка контекстной адаптации: {e}")
            return AdaptationResult(
                success=False,
                adaptation_type=AdaptationType.CONTEXTUAL,
                changes_applied=[],
                performance_impact=0.0,
                confidence=0.0,
                adaptation_time=0.0,
                message=f"Ошибка: {str(e)}"
            )
    
    async def _temporal_adaptation(self, context: AdaptationContext) -> AdaptationResult:
        """Временная адаптация"""
        try:
            changes_applied = []
            performance_impact = 0.0
            
            current_time = context.timestamp
            time_of_day = current_time.hour
            
            # Адаптация к времени дня
            if 6 <= time_of_day < 12:  # Утро
                changes_applied.append({
                    "type": "morning_adaptation",
                    "actions": ["increase_energy_level", "provide_motivation"]
                })
                performance_impact += 0.05
            
            elif 12 <= time_of_day < 18:  # День
                changes_applied.append({
                    "type": "daytime_adaptation",
                    "actions": ["focus_on_productivity", "provide_efficiency_tips"]
                })
                performance_impact += 0.03
            
            elif 18 <= time_of_day < 22:  # Вечер
                changes_applied.append({
                    "type": "evening_adaptation",
                    "actions": ["relaxed_tone", "summarize_achievements"]
                })
                performance_impact += 0.04
            
            else:  # Ночь
                changes_applied.append({
                    "type": "night_adaptation",
                    "actions": ["quiet_mode", "minimal_interactions"]
                })
                performance_impact += 0.02
            
            # Адаптация к дню недели
            day_of_week = current_time.weekday()
            if day_of_week in [0, 1, 2, 3, 4]:  # Рабочие дни
                changes_applied.append({
                    "type": "workday_adaptation",
                    "actions": ["professional_tone", "focus_on_tasks"]
                })
                performance_impact += 0.06
            
            else:  # Выходные
                changes_applied.append({
                    "type": "weekend_adaptation",
                    "actions": ["casual_tone", "leisure_focus"]
                })
                performance_impact += 0.04
            
            return AdaptationResult(
                success=True,
                adaptation_type=AdaptationType.TEMPORAL,
                changes_applied=changes_applied,
                performance_impact=performance_impact,
                confidence=0.9,
                adaptation_time=0.03,
                message="Временная адаптация выполнена"
            )
            
        except Exception as e:
            logger.error(f"Ошибка временной адаптации: {e}")
            return AdaptationResult(
                success=False,
                adaptation_type=AdaptationType.TEMPORAL,
                changes_applied=[],
                performance_impact=0.0,
                confidence=0.0,
                adaptation_time=0.0,
                message=f"Ошибка: {str(e)}"
            )
    
    async def _general_adaptation(self, context: AdaptationContext) -> AdaptationResult:
        """Общая адаптация"""
        try:
            changes_applied = []
            performance_impact = 0.0
            
            # Комбинированная адаптация
            behavioral_result = await self._behavioral_adaptation(context)
            if behavioral_result.success:
                changes_applied.extend(behavioral_result.changes_applied)
                performance_impact += behavioral_result.performance_impact
            
            contextual_result = await self._contextual_adaptation(context)
            if contextual_result.success:
                changes_applied.extend(contextual_result.changes_applied)
                performance_impact += contextual_result.performance_impact
            
            temporal_result = await self._temporal_adaptation(context)
            if temporal_result.success:
                changes_applied.extend(temporal_result.changes_applied)
                performance_impact += temporal_result.performance_impact
            
            return AdaptationResult(
                success=True,
                adaptation_type=AdaptationType.BEHAVIORAL,
                changes_applied=changes_applied,
                performance_impact=performance_impact,
                confidence=0.8,
                adaptation_time=0.2,
                message="Общая адаптация выполнена"
            )
            
        except Exception as e:
            logger.error(f"Ошибка общей адаптации: {e}")
            return AdaptationResult(
                success=False,
                adaptation_type=AdaptationType.BEHAVIORAL,
                changes_applied=[],
                performance_impact=0.0,
                confidence=0.0,
                adaptation_time=0.0,
                message=f"Ошибка: {str(e)}"
            )
    
    async def _apply_performance_optimization(self, metric: str, current_value: float, baseline: float) -> Dict[str, Any]:
        """Применение оптимизации производительности"""
        try:
            optimization_actions = {
                "response_time": {
                    "action": "optimize_processing",
                    "details": "Оптимизация алгоритмов обработки"
                },
                "accuracy": {
                    "action": "improve_model",
                    "details": "Улучшение модели предсказаний"
                },
                "user_satisfaction": {
                    "action": "adjust_interface",
                    "details": "Настройка пользовательского интерфейса"
                },
                "task_completion": {
                    "action": "simplify_workflow",
                    "details": "Упрощение рабочего процесса"
                },
                "error_rate": {
                    "action": "enhance_error_handling",
                    "details": "Улучшение обработки ошибок"
                }
            }
            
            action = optimization_actions.get(metric, {
                "action": "general_optimization",
                "details": "Общая оптимизация"
            })
            
            return {
                "type": "performance_optimization",
                "metric": metric,
                "current_value": current_value,
                "baseline": baseline,
                "improvement_needed": baseline - current_value,
                "action": action["action"],
                "details": action["details"]
            }
            
        except Exception as e:
            logger.error(f"Ошибка применения оптимизации: {e}")
            return {
                "type": "optimization_error",
                "error": str(e)
            }
    
    async def get_adaptation_history(self, user_id: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Получение истории адаптации"""
        try:
            if not self.ready:
                raise Exception("Adaptation Engine не готов")
            
            # Фильтрация по пользователю
            filtered_history = self.adaptation_history
            if user_id:
                filtered_history = [
                    h for h in self.adaptation_history
                    if h["context"]["user_id"] == user_id
                ]
            
            # Ограничение количества записей
            filtered_history = filtered_history[-limit:]
            
            return {
                "success": True,
                "history": filtered_history,
                "count": len(filtered_history),
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения истории адаптации: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Получение профиля пользователя"""
        try:
            if not self.ready:
                raise Exception("Adaptation Engine не готов")
            
            if user_id not in self.user_profiles:
                return {
                    "success": False,
                    "error": "Профиль пользователя не найден"
                }
            
            profile = self.user_profiles[user_id]
            
            return {
                "success": True,
                "user_id": user_id,
                "profile": profile
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения профиля пользователя: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_adaptation_statistics(self) -> Dict[str, Any]:
        """Получение статистики адаптации"""
        try:
            if not self.ready:
                raise Exception("Adaptation Engine не готов")
            
            # Статистика по типам адаптации
            type_stats = {}
            for record in self.adaptation_history:
                adaptation_type = record["adaptation_type"]
                if adaptation_type not in type_stats:
                    type_stats[adaptation_type] = 0
                type_stats[adaptation_type] += 1
            
            # Статистика по пользователям
            user_stats = {}
            for record in self.adaptation_history:
                user_id = record["context"]["user_id"]
                if user_id not in user_stats:
                    user_stats[user_id] = 0
                user_stats[user_id] += 1
            
            # Средние показатели
            total_adaptations = len(self.adaptation_history)
            successful_adaptations = sum(1 for r in self.adaptation_history if r["result"]["success"])
            avg_confidence = np.mean([r["result"]["confidence"] for r in self.adaptation_history]) if self.adaptation_history else 0
            avg_performance_impact = np.mean([r["result"]["performance_impact"] for r in self.adaptation_history]) if self.adaptation_history else 0
            
            return {
                "success": True,
                "statistics": {
                    "total_adaptations": total_adaptations,
                    "successful_adaptations": successful_adaptations,
                    "success_rate": successful_adaptations / total_adaptations if total_adaptations > 0 else 0,
                    "by_type": type_stats,
                    "by_user": user_stats,
                    "average_confidence": avg_confidence,
                    "average_performance_impact": avg_performance_impact,
                    "total_users": len(self.user_profiles),
                    "active_rules": len(self.adaptation_rules)
                }
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики адаптации: {e}")
            return {
                "success": False,
                "error": str(e)
            }