"""
Обработчик речи для Voice Service
Интеграция Whisper (распознавание) и TTS (синтез)
"""
import asyncio
import io
import tempfile
import os
from typing import Dict, List, Optional, Any
import numpy as np
import torch
import whisper
from TTS.api import TTS
import librosa
import soundfile as sf
from pathlib import Path
import logging

from utils.config import ModelConfig
from utils.logger import get_logger

logger = get_logger("voice-processor")

class VoiceProcessor:
    """Обработчик речи с поддержкой Whisper и TTS"""
    
    def __init__(self, model_config: ModelConfig):
        self.config = model_config
        self.whisper_model = None
        self.tts_model = None
        self.device = "cuda" if torch.cuda.is_available() and model_config.device == "cuda" else "cpu"
        
        # Поддерживаемые форматы аудио
        self.supported_formats = ['.wav', '.mp3', '.flac', '.m4a', '.ogg']
        
        # Кэш для моделей
        self._model_cache = {}
        
        logger.info(f"Voice processor initialized with device: {self.device}")
    
    async def initialize(self):
        """Инициализация моделей"""
        try:
            # Создание директории для моделей
            os.makedirs(self.config.model_path, exist_ok=True)
            
            # Загрузка Whisper модели
            await self._load_whisper_model()
            
            # Загрузка TTS модели
            await self._load_tts_model()
            
            logger.info("Voice processor models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize voice processor: {e}")
            raise
    
    async def _load_whisper_model(self):
        """Загрузка модели Whisper"""
        try:
            logger.info(f"Loading Whisper model: {self.config.whisper_model}")
            
            # Загрузка модели в отдельном потоке
            loop = asyncio.get_event_loop()
            self.whisper_model = await loop.run_in_executor(
                None, 
                lambda: whisper.load_model(self.config.whisper_model, device=self.device)
            )
            
            logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    async def _load_tts_model(self):
        """Загрузка TTS модели"""
        try:
            logger.info(f"Loading TTS model: {self.config.tts_model}")
            
            # Загрузка модели в отдельном потоке
            loop = asyncio.get_event_loop()
            self.tts_model = await loop.run_in_executor(
                None,
                lambda: TTS(model_name=self.config.tts_model, progress_bar=False).to(self.device)
            )
            
            logger.info("TTS model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}")
            raise
    
    async def recognize_speech(self, audio_data: bytes) -> Dict[str, Any]:
        """Распознавание речи из аудио данных"""
        if not self.whisper_model:
            raise RuntimeError("Whisper model not loaded")
        
        try:
            # Сохранение аудио во временный файл
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # Обработка аудио
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self._process_audio_with_whisper,
                    temp_path
                )
                
                return result
                
            finally:
                # Удаление временного файла
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Speech recognition failed: {e}")
            raise
    
    def _process_audio_with_whisper(self, audio_path: str) -> Dict[str, Any]:
        """Обработка аудио с помощью Whisper"""
        try:
            # Загрузка и предобработка аудио
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Распознавание речи
            result = self.whisper_model.transcribe(
                audio,
                language="ru",  # Русский язык
                task="transcribe",
                verbose=False
            )
            
            # Извлечение информации
            text = result["text"].strip()
            segments = result.get("segments", [])
            
            # Расчет средней уверенности
            confidences = [seg.get("avg_logprob", 0) for seg in segments if "avg_logprob" in seg]
            avg_confidence = np.exp(np.mean(confidences)) if confidences else 0.0
            
            # Длительность аудио
            duration = len(audio) / sr
            
            return {
                "text": text,
                "confidence": float(avg_confidence),
                "language": "ru",
                "duration": duration,
                "segments": segments
            }
            
        except Exception as e:
            logger.error(f"Whisper processing failed: {e}")
            raise
    
    async def synthesize_speech(self, text: str, voice: str = "default") -> bytes:
        """Синтез речи из текста"""
        if not self.tts_model:
            raise RuntimeError("TTS model not loaded")
        
        try:
            # Очистка текста
            cleaned_text = self._clean_text_for_tts(text)
            
            if not cleaned_text:
                raise ValueError("Empty text after cleaning")
            
            # Синтез речи
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_with_tts,
                cleaned_text,
                voice
            )
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            raise
    
    def _synthesize_with_tts(self, text: str, voice: str) -> bytes:
        """Синтез речи с помощью TTS"""
        try:
            # Создание временного файла для вывода
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                output_path = temp_file.name
            
            try:
                # Синтез речи
                self.tts_model.tts_to_file(
                    text=text,
                    file_path=output_path,
                    speaker=voice if voice != "default" else None
                )
                
                # Чтение сгенерированного аудио
                with open(output_path, 'rb') as f:
                    audio_data = f.read()
                
                return audio_data
                
            finally:
                # Удаление временного файла
                if os.path.exists(output_path):
                    os.unlink(output_path)
                    
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Очистка текста для TTS"""
        # Удаление лишних символов
        cleaned = text.strip()
        
        # Замена специальных символов
        replacements = {
            '&': 'и',
            '@': 'собака',
            '#': 'решетка',
            '$': 'доллар',
            '%': 'процент',
            '^': 'крышка',
            '*': 'звездочка',
            '+': 'плюс',
            '=': 'равно',
            '|': 'вертикальная черта',
            '\\': 'обратный слеш',
            '/': 'слеш',
            '<': 'меньше',
            '>': 'больше',
            '?': 'вопрос',
            '!': 'восклицание',
            '.': 'точка',
            ',': 'запятая',
            ';': 'точка с запятой',
            ':': 'двоеточие',
            '"': 'кавычки',
            "'": 'апостроф',
            '`': 'обратная кавычка',
            '~': 'тильда',
            '[': 'открывающая скобка',
            ']': 'закрывающая скобка',
            '{': 'открывающая фигурная скобка',
            '}': 'закрывающая фигурная скобка',
            '(': 'открывающая круглая скобка',
            ')': 'закрывающая круглая скобка',
        }
        
        for char, replacement in replacements.items():
            cleaned = cleaned.replace(char, f' {replacement} ')
        
        # Удаление множественных пробелов
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Получение списка доступных голосов"""
        if not self.tts_model:
            return []
        
        try:
            # Получение доступных спикеров
            speakers = getattr(self.tts_model, 'speakers', [])
            
            voices = []
            for i, speaker in enumerate(speakers):
                voices.append({
                    "id": speaker,
                    "name": speaker,
                    "language": "ru",
                    "gender": "unknown"
                })
            
            # Добавление голоса по умолчанию
            voices.insert(0, {
                "id": "default",
                "name": "По умолчанию",
                "language": "ru",
                "gender": "unknown"
            })
            
            return voices
            
        except Exception as e:
            logger.error(f"Failed to get available voices: {e}")
            return [{
                "id": "default",
                "name": "По умолчанию",
                "language": "ru",
                "gender": "unknown"
            }]
    
    async def process_audio_stream(self, audio_stream: bytes) -> Dict[str, Any]:
        """Обработка аудио потока в реальном времени"""
        try:
            # Конвертация потока в аудио данные
            audio_data = self._convert_stream_to_audio(audio_stream)
            
            # Распознавание речи
            result = await self.recognize_speech(audio_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Audio stream processing failed: {e}")
            raise
    
    def _convert_stream_to_audio(self, stream_data: bytes) -> bytes:
        """Конвертация потока в аудио данные"""
        try:
            # Простая конвертация - в реальном приложении может потребоваться
            # более сложная обработка в зависимости от формата потока
            return stream_data
            
        except Exception as e:
            logger.error(f"Stream conversion failed: {e}")
            raise
    
    async def cleanup(self):
        """Очистка ресурсов"""
        try:
            # Очистка моделей
            if self.whisper_model:
                del self.whisper_model
                self.whisper_model = None
            
            if self.tts_model:
                del self.tts_model
                self.tts_model = None
            
            # Очистка кэша
            self._model_cache.clear()
            
            # Очистка GPU памяти
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("Voice processor cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о моделях"""
        return {
            "whisper_model": self.config.whisper_model,
            "tts_model": self.config.tts_model,
            "device": self.device,
            "whisper_loaded": self.whisper_model is not None,
            "tts_loaded": self.tts_model is not None,
            "supported_formats": self.supported_formats
        }