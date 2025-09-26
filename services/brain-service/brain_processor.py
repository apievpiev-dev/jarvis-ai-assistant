"""
AI процессор для Brain Service
Интеграция Phi-2 и других моделей для обработки команд
"""
import asyncio
import time
import torch
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    pipeline,
    BitsAndBytesConfig
)
from sentence_transformers import SentenceTransformer
import logging
import json
import re

from utils.config import ModelConfig
from utils.logger import get_logger

logger = get_logger("brain-processor")

class BrainProcessor:
    """AI процессор с поддержкой Phi-2 и других моделей"""
    
    def __init__(self, model_config: ModelConfig):
        self.config = model_config
        self.device = "cuda" if torch.cuda.is_available() and model_config.device == "cuda" else "cpu"
        
        # Модели
        self.phi2_model = None
        self.phi2_tokenizer = None
        self.embedding_model = None
        self.classification_pipeline = None
        
        # Кэш для эмбеддингов
        self._embedding_cache = {}
        
        # Системные промпты
        self.system_prompts = {
            "assistant": """Ты - Jarvis, умный AI-ассистент. Ты помогаешь пользователю с различными задачами.
Твои возможности:
- Выполнение команд и задач
- Анализ и генерация кода
- Ответы на вопросы
- Помощь в работе с компьютером
- Обучение и адаптация

Отвечай на русском языке, будь полезным и дружелюбным.""",
            
            "code_assistant": """Ты - эксперт по программированию. Помогаешь с:
- Анализом кода
- Написанием кода
- Отладкой
- Оптимизацией
- Объяснением алгоритмов

Отвечай на русском языке, давай четкие и практичные советы.""",
            
            "task_planner": """Ты - планировщик задач. Разбиваешь сложные команды на простые шаги.
Анализируй команду и создавай план выполнения с четкими шагами.
Отвечай в формате JSON с массивом шагов."""
        }
        
        logger.info(f"Brain processor initialized with device: {self.device}")
    
    async def initialize(self):
        """Инициализация моделей"""
        try:
            # Создание директории для моделей
            import os
            os.makedirs(self.config.model_path, exist_ok=True)
            
            # Загрузка моделей
            await self._load_phi2_model()
            await self._load_embedding_model()
            await self._load_classification_pipeline()
            
            logger.info("Brain processor models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize brain processor: {e}")
            raise
    
    async def _load_phi2_model(self):
        """Загрузка модели Phi-2"""
        try:
            logger.info(f"Loading Phi-2 model: {self.config.phi2_model}")
            
            # Конфигурация для CPU
            model_kwargs = {
                "torch_dtype": torch.float32,
                "device_map": "auto" if self.device == "cuda" else None,
                "trust_remote_code": True
            }
            
            # Загрузка в отдельном потоке
            loop = asyncio.get_event_loop()
            
            # Загрузка токенизатора
            self.phi2_tokenizer = await loop.run_in_executor(
                None,
                lambda: AutoTokenizer.from_pretrained(
                    self.config.phi2_model,
                    trust_remote_code=True
                )
            )
            
            # Загрузка модели
            self.phi2_model = await loop.run_in_executor(
                None,
                lambda: AutoModelForCausalLM.from_pretrained(
                    self.config.phi2_model,
                    **model_kwargs
                )
            )
            
            # Настройка токенизатора
            if self.phi2_tokenizer.pad_token is None:
                self.phi2_tokenizer.pad_token = self.phi2_tokenizer.eos_token
            
            logger.info("Phi-2 model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Phi-2 model: {e}")
            raise
    
    async def _load_embedding_model(self):
        """Загрузка модели эмбеддингов"""
        try:
            logger.info(f"Loading embedding model: {self.config.embedding_model}")
            
            loop = asyncio.get_event_loop()
            self.embedding_model = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer(self.config.embedding_model)
            )
            
            logger.info("Embedding model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    async def _load_classification_pipeline(self):
        """Загрузка пайплайна классификации"""
        try:
            logger.info("Loading classification pipeline")
            
            # Используем простую модель для классификации
            loop = asyncio.get_event_loop()
            self.classification_pipeline = await loop.run_in_executor(
                None,
                lambda: pipeline(
                    "text-classification",
                    model="cointegrated/rubert-tiny2-cedr-emotion-detection",
                    device=0 if self.device == "cuda" else -1
                )
            )
            
            logger.info("Classification pipeline loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load classification pipeline: {e}")
            # Не критично, продолжаем без классификации
            self.classification_pipeline = None
    
    async def process_command(self, command: str, analysis: Dict[str, Any], 
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка команды пользователя"""
        try:
            start_time = time.time()
            
            # Определение типа команды
            command_type = analysis.get("intent", "general")
            
            # Обработка в зависимости от типа
            if command_type == "code_analysis":
                result = await self._process_code_command(command, context)
            elif command_type == "task_execution":
                result = await self._process_task_command(command, analysis, context)
            elif command_type == "question":
                result = await self._process_question_command(command, context)
            else:
                result = await self._process_general_command(command, context)
            
            processing_time = time.time() - start_time
            
            return {
                **result,
                "processing_time": processing_time,
                "command_type": command_type
            }
            
        except Exception as e:
            logger.error(f"Command processing failed: {e}")
            return {
                "error": str(e),
                "response": "Извините, произошла ошибка при обработке команды.",
                "processing_time": 0
            }
    
    async def _process_general_command(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка общей команды"""
        try:
            # Создание промпта
            prompt = self._create_prompt(command, context, "assistant")
            
            # Генерация ответа
            response = await self._generate_text(prompt)
            
            return {
                "response": response,
                "type": "general_response"
            }
            
        except Exception as e:
            logger.error(f"General command processing failed: {e}")
            raise
    
    async def _process_code_command(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка команды, связанной с кодом"""
        try:
            # Создание промпта для анализа кода
            prompt = self._create_prompt(command, context, "code_assistant")
            
            # Генерация ответа
            response = await self._generate_text(prompt)
            
            # Извлечение кода из ответа
            code_blocks = self._extract_code_blocks(response)
            
            return {
                "response": response,
                "code_blocks": code_blocks,
                "type": "code_response"
            }
            
        except Exception as e:
            logger.error(f"Code command processing failed: {e}")
            raise
    
    async def _process_task_command(self, command: str, analysis: Dict[str, Any], 
                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка команды выполнения задачи"""
        try:
            # Создание плана выполнения
            plan_prompt = self._create_prompt(command, context, "task_planner")
            plan_response = await self._generate_text(plan_prompt)
            
            # Парсинг плана
            task_plan = self._parse_task_plan(plan_response)
            
            return {
                "response": f"Понял! Выполню задачу: {command}",
                "task_plan": task_plan,
                "type": "task_response"
            }
            
        except Exception as e:
            logger.error(f"Task command processing failed: {e}")
            raise
    
    async def _process_question_command(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка вопроса"""
        try:
            # Создание промпта для ответа на вопрос
            prompt = self._create_prompt(command, context, "assistant")
            
            # Генерация ответа
            response = await self._generate_text(prompt)
            
            return {
                "response": response,
                "type": "question_response"
            }
            
        except Exception as e:
            logger.error(f"Question processing failed: {e}")
            raise
    
    async def generate_response(self, prompt: str, context: Dict[str, Any], 
                              max_tokens: int = None, temperature: float = None) -> Dict[str, Any]:
        """Генерация ответа на основе промпта"""
        try:
            start_time = time.time()
            
            # Параметры по умолчанию
            max_tokens = max_tokens or self.config.max_tokens
            temperature = temperature or self.config.temperature
            
            # Создание полного промпта
            full_prompt = self._create_prompt(prompt, context, "assistant")
            
            # Генерация текста
            response = await self._generate_text(full_prompt, max_tokens, temperature)
            
            generation_time = time.time() - start_time
            
            return {
                "text": response,
                "tokens_used": len(response.split()),
                "generation_time": generation_time
            }
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise
    
    async def _generate_text(self, prompt: str, max_tokens: int = None, 
                           temperature: float = None) -> str:
        """Генерация текста с помощью Phi-2"""
        if not self.phi2_model or not self.phi2_tokenizer:
            raise RuntimeError("Phi-2 model not loaded")
        
        try:
            # Параметры по умолчанию
            max_tokens = max_tokens or self.config.max_tokens
            temperature = temperature or self.config.temperature
            
            # Токенизация
            inputs = self.phi2_tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048
            )
            
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Генерация
            with torch.no_grad():
                outputs = self.phi2_model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.phi2_tokenizer.eos_token_id,
                    eos_token_id=self.phi2_tokenizer.eos_token_id
                )
            
            # Декодирование
            generated_text = self.phi2_tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )
            
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise
    
    def _create_prompt(self, command: str, context: Dict[str, Any], 
                      prompt_type: str = "assistant") -> str:
        """Создание промпта для модели"""
        system_prompt = self.system_prompts.get(prompt_type, self.system_prompts["assistant"])
        
        # Добавление контекста
        context_str = ""
        if context:
            context_str = f"\nКонтекст: {json.dumps(context, ensure_ascii=False)}"
        
        # Создание полного промпта
        prompt = f"{system_prompt}{context_str}\n\nПользователь: {command}\n\nJarvis:"
        
        return prompt
    
    def _extract_code_blocks(self, text: str) -> List[str]:
        """Извлечение блоков кода из текста"""
        code_blocks = []
        
        # Поиск блоков кода в markdown формате
        pattern = r'```(?:python|py|javascript|js|html|css|json|sql)?\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for match in matches:
            code_blocks.append(match.strip())
        
        return code_blocks
    
    def _parse_task_plan(self, plan_text: str) -> List[Dict[str, Any]]:
        """Парсинг плана выполнения задач"""
        try:
            # Попытка парсинга JSON
            if plan_text.strip().startswith('{') or plan_text.strip().startswith('['):
                return json.loads(plan_text)
            
            # Простой парсинг текстового плана
            steps = []
            lines = plan_text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line and not line.startswith('#'):
                    steps.append({
                        "step": i + 1,
                        "description": line,
                        "status": "pending"
                    })
            
            return steps
            
        except Exception as e:
            logger.error(f"Failed to parse task plan: {e}")
            return [{
                "step": 1,
                "description": "Выполнить команду",
                "status": "pending"
            }]
    
    async def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Получение эмбеддингов для текстов"""
        if not self.embedding_model:
            raise RuntimeError("Embedding model not loaded")
        
        try:
            # Проверка кэша
            cache_key = hash(tuple(texts))
            if cache_key in self._embedding_cache:
                return self._embedding_cache[cache_key]
            
            # Генерация эмбеддингов
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.embedding_model.encode(texts)
            )
            
            # Сохранение в кэш
            self._embedding_cache[cache_key] = embeddings
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to get embeddings: {e}")
            raise
    
    async def classify_text(self, text: str) -> Dict[str, Any]:
        """Классификация текста"""
        if not self.classification_pipeline:
            return {"label": "unknown", "score": 0.0}
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.classification_pipeline(text)
            )
            
            return result[0] if result else {"label": "unknown", "score": 0.0}
            
        except Exception as e:
            logger.error(f"Text classification failed: {e}")
            return {"label": "unknown", "score": 0.0}
    
    async def cleanup(self):
        """Очистка ресурсов"""
        try:
            # Очистка моделей
            if self.phi2_model:
                del self.phi2_model
                self.phi2_model = None
            
            if self.phi2_tokenizer:
                del self.phi2_tokenizer
                self.phi2_tokenizer = None
            
            if self.embedding_model:
                del self.embedding_model
                self.embedding_model = None
            
            if self.classification_pipeline:
                del self.classification_pipeline
                self.classification_pipeline = None
            
            # Очистка кэша
            self._embedding_cache.clear()
            
            # Очистка GPU памяти
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("Brain processor cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о моделях"""
        return {
            "phi2_model": self.config.phi2_model,
            "embedding_model": self.config.embedding_model,
            "device": self.device,
            "phi2_loaded": self.phi2_model is not None,
            "embedding_loaded": self.embedding_model is not None,
            "classification_loaded": self.classification_pipeline is not None,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }