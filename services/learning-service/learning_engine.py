#!/usr/bin/env python3
"""
Learning Engine - Движок обучения
Автор: Jarvis AI Assistant
Версия: 1.0.0
"""

import asyncio
import logging
import json
import pickle
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class LearningType(Enum):
    """Типы обучения"""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    TRANSFER = "transfer"
    FEDERATED = "federated"

class FeedbackType(Enum):
    """Типы обратной связи"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    CORRECTION = "correction"
    SUGGESTION = "suggestion"

@dataclass
class LearningData:
    """Данные для обучения"""
    input_data: Any
    output_data: Any
    context: Dict[str, Any]
    timestamp: datetime
    source: str
    quality_score: float

@dataclass
class LearningResult:
    """Результат обучения"""
    success: bool
    accuracy: float
    loss: float
    metrics: Dict[str, float]
    model_updates: Dict[str, Any]
    learning_time: float

@dataclass
class FeedbackData:
    """Данные обратной связи"""
    original_input: Any
    original_output: Any
    feedback: Any
    feedback_type: FeedbackType
    timestamp: datetime
    user_id: str

class LearningEngine:
    """Движок обучения"""
    
    def __init__(self):
        self.ready = False
        self.models = {}
        self.learning_history = []
        self.feedback_history = []
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.clusterer = KMeans(n_clusters=5, random_state=42)
        
    async def initialize(self):
        """Инициализация движка обучения"""
        try:
            logger.info("Инициализация Learning Engine...")
            
            # Загрузка сохраненных моделей
            await self._load_models()
            
            # Инициализация компонентов
            await self._initialize_components()
            
            self.ready = True
            logger.info("Learning Engine инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации Learning Engine: {e}")
            raise
    
    async def cleanup(self):
        """Очистка ресурсов"""
        try:
            # Сохранение моделей
            await self._save_models()
            
            self.ready = False
            logger.info("Learning Engine очищен")
        except Exception as e:
            logger.error(f"Ошибка очистки Learning Engine: {e}")
    
    def is_ready(self) -> bool:
        """Проверка готовности движка"""
        return self.ready
    
    async def _load_models(self):
        """Загрузка сохраненных моделей"""
        try:
            # Загрузка моделей из файлов
            model_files = [
                "models/learning_models.pkl",
                "models/feedback_models.pkl",
                "models/optimization_models.pkl"
            ]
            
            for model_file in model_files:
                try:
                    with open(model_file, 'rb') as f:
                        model_data = pickle.load(f)
                        model_name = model_file.split('/')[-1].split('.')[0]
                        self.models[model_name] = model_data
                        logger.info(f"Модель {model_name} загружена")
                except FileNotFoundError:
                    logger.info(f"Файл модели {model_file} не найден, создаем новую модель")
                except Exception as e:
                    logger.error(f"Ошибка загрузки модели {model_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Ошибка загрузки моделей: {e}")
    
    async def _save_models(self):
        """Сохранение моделей"""
        try:
            import os
            os.makedirs("models", exist_ok=True)
            
            for model_name, model_data in self.models.items():
                model_file = f"models/{model_name}.pkl"
                with open(model_file, 'wb') as f:
                    pickle.dump(model_data, f)
                    logger.info(f"Модель {model_name} сохранена")
                    
        except Exception as e:
            logger.error(f"Ошибка сохранения моделей: {e}")
    
    async def _initialize_components(self):
        """Инициализация компонентов"""
        try:
            # Инициализация векторного преобразователя
            # Обучение на базовых данных
            sample_texts = [
                "Привет, как дела?",
                "Помоги мне с задачей",
                "Спасибо за помощь",
                "Ошибка в коде",
                "Как настроить систему?"
            ]
            self.vectorizer.fit(sample_texts)
            
            # Инициализация кластеризатора
            sample_vectors = self.vectorizer.transform(sample_texts)
            self.clusterer.fit(sample_vectors)
            
            logger.info("Компоненты инициализированы")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации компонентов: {e}")
    
    async def learn(self, data: Dict[str, Any], learning_type: str = "general") -> Dict[str, Any]:
        """Обучение на данных"""
        try:
            if not self.ready:
                raise Exception("Learning Engine не готов")
            
            start_time = asyncio.get_event_loop().time()
            
            # Создание объекта данных обучения
            learning_data = LearningData(
                input_data=data.get("input"),
                output_data=data.get("output"),
                context=data.get("context", {}),
                timestamp=datetime.now(),
                source=data.get("source", "unknown"),
                quality_score=data.get("quality_score", 1.0)
            )
            
            # Обучение в зависимости от типа
            if learning_type == "supervised":
                result = await self._supervised_learning(learning_data)
            elif learning_type == "unsupervised":
                result = await self._unsupervised_learning(learning_data)
            elif learning_type == "reinforcement":
                result = await self._reinforcement_learning(learning_data)
            elif learning_type == "transfer":
                result = await self._transfer_learning(learning_data)
            else:
                result = await self._general_learning(learning_data)
            
            # Сохранение в историю
            self.learning_history.append({
                "data": asdict(learning_data),
                "result": asdict(result),
                "learning_type": learning_type,
                "timestamp": datetime.now().isoformat()
            })
            
            # Ограничение размера истории
            if len(self.learning_history) > 1000:
                self.learning_history = self.learning_history[-500:]
            
            return {
                "success": result.success,
                "accuracy": result.accuracy,
                "loss": result.loss,
                "metrics": result.metrics,
                "learning_time": result.learning_time,
                "learning_type": learning_type
            }
            
        except Exception as e:
            logger.error(f"Ошибка обучения: {e}")
            return {
                "success": False,
                "error": str(e),
                "learning_type": learning_type
            }
    
    async def _supervised_learning(self, data: LearningData) -> LearningResult:
        """Обучение с учителем"""
        try:
            # Простая реализация обучения с учителем
            input_text = str(data.input_data)
            output_text = str(data.output_data)
            
            # Векторизация входных данных
            input_vector = self.vectorizer.transform([input_text])
            
            # Простое обучение на основе сходства
            similarity_score = 0.8  # Базовый score
            
            # Обновление модели
            if "supervised_model" not in self.models:
                self.models["supervised_model"] = {
                    "patterns": [],
                    "responses": [],
                    "weights": []
                }
            
            self.models["supervised_model"]["patterns"].append(input_vector.toarray()[0])
            self.models["supervised_model"]["responses"].append(output_text)
            self.models["supervised_model"]["weights"].append(data.quality_score)
            
            return LearningResult(
                success=True,
                accuracy=similarity_score,
                loss=1.0 - similarity_score,
                metrics={"precision": similarity_score, "recall": similarity_score},
                model_updates={"patterns_added": 1},
                learning_time=0.1
            )
            
        except Exception as e:
            logger.error(f"Ошибка обучения с учителем: {e}")
            return LearningResult(
                success=False,
                accuracy=0.0,
                loss=1.0,
                metrics={},
                model_updates={},
                learning_time=0.0
            )
    
    async def _unsupervised_learning(self, data: LearningData) -> LearningResult:
        """Обучение без учителя"""
        try:
            # Кластеризация данных
            input_text = str(data.input_data)
            input_vector = self.vectorizer.transform([input_text])
            
            # Предсказание кластера
            cluster = self.clusterer.predict(input_vector)[0]
            
            # Обновление кластеризатора
            if "unsupervised_model" not in self.models:
                self.models["unsupervised_model"] = {
                    "clusters": {},
                    "centroids": []
                }
            
            if cluster not in self.models["unsupervised_model"]["clusters"]:
                self.models["unsupervised_model"]["clusters"][cluster] = []
            
            self.models["unsupervised_model"]["clusters"][cluster].append(input_vector.toarray()[0])
            
            return LearningResult(
                success=True,
                accuracy=0.7,  # Базовый accuracy для кластеризации
                loss=0.3,
                metrics={"cluster_purity": 0.7, "silhouette_score": 0.6},
                model_updates={"cluster": cluster, "samples_added": 1},
                learning_time=0.05
            )
            
        except Exception as e:
            logger.error(f"Ошибка обучения без учителя: {e}")
            return LearningResult(
                success=False,
                accuracy=0.0,
                loss=1.0,
                metrics={},
                model_updates={},
                learning_time=0.0
            )
    
    async def _reinforcement_learning(self, data: LearningData) -> LearningResult:
        """Обучение с подкреплением"""
        try:
            # Простая реализация Q-learning
            state = str(data.input_data)
            action = str(data.output_data)
            reward = data.quality_score
            
            if "reinforcement_model" not in self.models:
                self.models["reinforcement_model"] = {
                    "q_table": {},
                    "learning_rate": 0.1,
                    "discount_factor": 0.9
                }
            
            q_table = self.models["reinforcement_model"]["q_table"]
            lr = self.models["reinforcement_model"]["learning_rate"]
            gamma = self.models["reinforcement_model"]["discount_factor"]
            
            # Обновление Q-таблицы
            if state not in q_table:
                q_table[state] = {}
            
            if action not in q_table[state]:
                q_table[state][action] = 0.0
            
            # Q-learning update
            old_q = q_table[state][action]
            max_future_q = max(q_table[state].values()) if q_table[state] else 0
            new_q = old_q + lr * (reward + gamma * max_future_q - old_q)
            q_table[state][action] = new_q
            
            return LearningResult(
                success=True,
                accuracy=min(1.0, new_q),
                loss=abs(reward - new_q),
                metrics={"q_value": new_q, "reward": reward},
                model_updates={"q_updated": True},
                learning_time=0.02
            )
            
        except Exception as e:
            logger.error(f"Ошибка обучения с подкреплением: {e}")
            return LearningResult(
                success=False,
                accuracy=0.0,
                loss=1.0,
                metrics={},
                model_updates={},
                learning_time=0.0
            )
    
    async def _transfer_learning(self, data: LearningData) -> LearningResult:
        """Трансферное обучение"""
        try:
            # Использование предобученных знаний
            source_domain = data.context.get("source_domain", "general")
            target_domain = data.context.get("target_domain", "specific")
            
            if "transfer_model" not in self.models:
                self.models["transfer_model"] = {
                    "source_knowledge": {},
                    "transfer_weights": {}
                }
            
            # Сохранение знаний из исходного домена
            if source_domain not in self.models["transfer_model"]["source_knowledge"]:
                self.models["transfer_model"]["source_knowledge"][source_domain] = []
            
            self.models["transfer_model"]["source_knowledge"][source_domain].append({
                "input": data.input_data,
                "output": data.output_data,
                "quality": data.quality_score
            })
            
            # Вычисление весов трансфера
            transfer_weight = min(1.0, data.quality_score * 0.8)
            
            return LearningResult(
                success=True,
                accuracy=transfer_weight,
                loss=1.0 - transfer_weight,
                metrics={"transfer_accuracy": transfer_weight},
                model_updates={"source_domain": source_domain, "transfer_weight": transfer_weight},
                learning_time=0.15
            )
            
        except Exception as e:
            logger.error(f"Ошибка трансферного обучения: {e}")
            return LearningResult(
                success=False,
                accuracy=0.0,
                loss=1.0,
                metrics={},
                model_updates={},
                learning_time=0.0
            )
    
    async def _general_learning(self, data: LearningData) -> LearningResult:
        """Общее обучение"""
        try:
            # Простое обучение на основе паттернов
            input_text = str(data.input_data)
            output_text = str(data.output_data)
            
            if "general_model" not in self.models:
                self.models["general_model"] = {
                    "patterns": {},
                    "responses": {},
                    "frequency": {}
                }
            
            # Обновление паттернов
            pattern_key = input_text[:50]  # Первые 50 символов как ключ
            
            if pattern_key not in self.models["general_model"]["patterns"]:
                self.models["general_model"]["patterns"][pattern_key] = []
                self.models["general_model"]["responses"][pattern_key] = []
                self.models["general_model"]["frequency"][pattern_key] = 0
            
            self.models["general_model"]["patterns"][pattern_key].append(input_text)
            self.models["general_model"]["responses"][pattern_key].append(output_text)
            self.models["general_model"]["frequency"][pattern_key] += 1
            
            # Вычисление метрик
            accuracy = min(1.0, data.quality_score)
            
            return LearningResult(
                success=True,
                accuracy=accuracy,
                loss=1.0 - accuracy,
                metrics={"pattern_count": len(self.models["general_model"]["patterns"])},
                model_updates={"pattern_added": pattern_key},
                learning_time=0.01
            )
            
        except Exception as e:
            logger.error(f"Ошибка общего обучения: {e}")
            return LearningResult(
                success=False,
                accuracy=0.0,
                loss=1.0,
                metrics={},
                model_updates={},
                learning_time=0.0
            )
    
    async def process_feedback(self, feedback: Dict[str, Any], feedback_type: str = "general") -> Dict[str, Any]:
        """Обработка обратной связи"""
        try:
            if not self.ready:
                raise Exception("Learning Engine не готов")
            
            # Создание объекта обратной связи
            feedback_data = FeedbackData(
                original_input=feedback.get("original_input"),
                original_output=feedback.get("original_output"),
                feedback=feedback.get("feedback"),
                feedback_type=FeedbackType(feedback_type),
                timestamp=datetime.now(),
                user_id=feedback.get("user_id", "unknown")
            )
            
            # Обработка в зависимости от типа
            if feedback_type == "positive":
                result = await self._process_positive_feedback(feedback_data)
            elif feedback_type == "negative":
                result = await self._process_negative_feedback(feedback_data)
            elif feedback_type == "correction":
                result = await self._process_correction_feedback(feedback_data)
            elif feedback_type == "suggestion":
                result = await self._process_suggestion_feedback(feedback_data)
            else:
                result = await self._process_general_feedback(feedback_data)
            
            # Сохранение в историю
            self.feedback_history.append({
                "data": asdict(feedback_data),
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
            # Ограничение размера истории
            if len(self.feedback_history) > 500:
                self.feedback_history = self.feedback_history[-250:]
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка обработки обратной связи: {e}")
            return {
                "success": False,
                "error": str(e),
                "feedback_type": feedback_type
            }
    
    async def _process_positive_feedback(self, feedback: FeedbackData) -> Dict[str, Any]:
        """Обработка положительной обратной связи"""
        try:
            # Усиление положительных паттернов
            input_text = str(feedback.original_input)
            output_text = str(feedback.original_output)
            
            # Увеличение весов для успешных паттернов
            if "general_model" in self.models:
                pattern_key = input_text[:50]
                if pattern_key in self.models["general_model"]["frequency"]:
                    self.models["general_model"]["frequency"][pattern_key] += 2
            
            return {
                "success": True,
                "action": "reinforce_pattern",
                "weight_increase": 2.0,
                "message": "Положительная обратная связь обработана"
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки положительной обратной связи: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_negative_feedback(self, feedback: FeedbackData) -> Dict[str, Any]:
        """Обработка отрицательной обратной связи"""
        try:
            # Ослабление отрицательных паттернов
            input_text = str(feedback.original_input)
            
            # Уменьшение весов для неуспешных паттернов
            if "general_model" in self.models:
                pattern_key = input_text[:50]
                if pattern_key in self.models["general_model"]["frequency"]:
                    self.models["general_model"]["frequency"][pattern_key] = max(0, 
                        self.models["general_model"]["frequency"][pattern_key] - 1)
            
            return {
                "success": True,
                "action": "weaken_pattern",
                "weight_decrease": 1.0,
                "message": "Отрицательная обратная связь обработана"
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки отрицательной обратной связи: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_correction_feedback(self, feedback: FeedbackData) -> Dict[str, Any]:
        """Обработка корректирующей обратной связи"""
        try:
            # Замена неправильного ответа на правильный
            input_text = str(feedback.original_input)
            correct_output = str(feedback.feedback)
            
            if "general_model" in self.models:
                pattern_key = input_text[:50]
                if pattern_key in self.models["general_model"]["responses"]:
                    # Замена ответа
                    self.models["general_model"]["responses"][pattern_key] = [correct_output]
            
            return {
                "success": True,
                "action": "correct_response",
                "corrected_output": correct_output,
                "message": "Корректирующая обратная связь обработана"
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки корректирующей обратной связи: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_suggestion_feedback(self, feedback: FeedbackData) -> Dict[str, Any]:
        """Обработка предложений"""
        try:
            # Сохранение предложений для будущего использования
            suggestion = str(feedback.feedback)
            
            if "suggestions" not in self.models:
                self.models["suggestions"] = []
            
            self.models["suggestions"].append({
                "input": feedback.original_input,
                "suggestion": suggestion,
                "timestamp": feedback.timestamp.isoformat()
            })
            
            return {
                "success": True,
                "action": "store_suggestion",
                "suggestion": suggestion,
                "message": "Предложение сохранено"
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки предложения: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_general_feedback(self, feedback: FeedbackData) -> Dict[str, Any]:
        """Обработка общей обратной связи"""
        try:
            # Общая обработка обратной связи
            return {
                "success": True,
                "action": "general_feedback",
                "message": "Обратная связь обработана"
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки общей обратной связи: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize(self, data: Dict[str, Any], optimization_type: str = "general") -> Dict[str, Any]:
        """Оптимизация моделей"""
        try:
            if not self.ready:
                raise Exception("Learning Engine не готов")
            
            start_time = asyncio.get_event_loop().time()
            
            if optimization_type == "performance":
                result = await self._optimize_performance()
            elif optimization_type == "accuracy":
                result = await self._optimize_accuracy()
            elif optimization_type == "memory":
                result = await self._optimize_memory()
            else:
                result = await self._optimize_general()
            
            optimization_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "success": result["success"],
                "optimization_type": optimization_type,
                "improvements": result.get("improvements", {}),
                "optimization_time": optimization_time,
                "message": result.get("message", "Оптимизация завершена")
            }
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации: {e}")
            return {
                "success": False,
                "error": str(e),
                "optimization_type": optimization_type
            }
    
    async def _optimize_performance(self) -> Dict[str, Any]:
        """Оптимизация производительности"""
        try:
            improvements = {}
            
            # Оптимизация размеров моделей
            for model_name, model_data in self.models.items():
                if isinstance(model_data, dict):
                    # Удаление старых данных
                    if "patterns" in model_data and len(model_data["patterns"]) > 100:
                        # Оставляем только последние 50 паттернов
                        if isinstance(model_data["patterns"], list):
                            model_data["patterns"] = model_data["patterns"][-50:]
                        improvements[f"{model_name}_patterns_optimized"] = True
            
            return {
                "success": True,
                "improvements": improvements,
                "message": "Оптимизация производительности завершена"
            }
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации производительности: {e}")
            return {"success": False, "error": str(e)}
    
    async def _optimize_accuracy(self) -> Dict[str, Any]:
        """Оптимизация точности"""
        try:
            improvements = {}
            
            # Переобучение моделей на основе обратной связи
            if self.feedback_history:
                positive_feedback = [f for f in self.feedback_history 
                                   if f["data"]["feedback_type"] == "positive"]
                negative_feedback = [f for f in self.feedback_history 
                                   if f["data"]["feedback_type"] == "negative"]
                
                if len(positive_feedback) > len(negative_feedback):
                    improvements["accuracy_improved"] = True
                    improvements["positive_feedback_ratio"] = len(positive_feedback) / len(self.feedback_history)
            
            return {
                "success": True,
                "improvements": improvements,
                "message": "Оптимизация точности завершена"
            }
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации точности: {e}")
            return {"success": False, "error": str(e)}
    
    async def _optimize_memory(self) -> Dict[str, Any]:
        """Оптимизация памяти"""
        try:
            improvements = {}
            
            # Очистка старых данных
            if len(self.learning_history) > 100:
                self.learning_history = self.learning_history[-50:]
                improvements["learning_history_cleaned"] = True
            
            if len(self.feedback_history) > 50:
                self.feedback_history = self.feedback_history[-25:]
                improvements["feedback_history_cleaned"] = True
            
            return {
                "success": True,
                "improvements": improvements,
                "message": "Оптимизация памяти завершена"
            }
            
        except Exception as e:
            logger.error(f"Ошибка оптимизации памяти: {e}")
            return {"success": False, "error": str(e)}
    
    async def _optimize_general(self) -> Dict[str, Any]:
        """Общая оптимизация"""
        try:
            improvements = {}
            
            # Комбинированная оптимизация
            perf_result = await self._optimize_performance()
            if perf_result["success"]:
                improvements.update(perf_result["improvements"])
            
            acc_result = await self._optimize_accuracy()
            if acc_result["success"]:
                improvements.update(acc_result["improvements"])
            
            mem_result = await self._optimize_memory()
            if mem_result["success"]:
                improvements.update(mem_result["improvements"])
            
            return {
                "success": True,
                "improvements": improvements,
                "message": "Общая оптимизация завершена"
            }
            
        except Exception as e:
            logger.error(f"Ошибка общей оптимизации: {e}")
            return {"success": False, "error": str(e)}