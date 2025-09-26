#!/usr/bin/env python3
"""
Скрипт загрузки AI моделей для Jarvis AI Assistant
"""
import os
import sys
import subprocess
import asyncio
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Проверка зависимостей"""
    required_packages = [
        'torch',
        'transformers',
        'openai-whisper',
        'TTS',
        'sentence-transformers'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"✓ {package} установлен")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"✗ {package} не установлен")
    
    if missing_packages:
        logger.error(f"Отсутствуют пакеты: {', '.join(missing_packages)}")
        logger.info("Установите их командой: pip install " + " ".join(missing_packages))
        return False
    
    return True

def download_whisper_model():
    """Загрузка модели Whisper"""
    logger.info("Загрузка модели Whisper...")
    try:
        import whisper
        model = whisper.load_model("base")
        logger.info("✓ Whisper модель 'base' загружена")
        
        # Проверка доступности других размеров
        sizes = ["tiny", "small", "medium", "large"]
        for size in sizes:
            try:
                whisper.load_model(size)
                logger.info(f"✓ Whisper модель '{size}' доступна")
            except Exception as e:
                logger.warning(f"✗ Whisper модель '{size}' недоступна: {e}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Ошибка загрузки Whisper: {e}")
        return False

def download_tts_model():
    """Загрузка TTS модели"""
    logger.info("Загрузка TTS модели...")
    try:
        from TTS.api import TTS
        
        # Загрузка русской модели
        tts = TTS(model_name="tts_models/ru/ruslan")
        logger.info("✓ TTS модель 'ruslan' загружена")
        
        # Проверка других доступных моделей
        available_models = TTS.list_models()
        russian_models = [model for model in available_models if 'ru' in model]
        
        logger.info(f"Доступные русские TTS модели: {len(russian_models)}")
        for model in russian_models[:5]:  # Показываем первые 5
            logger.info(f"  - {model}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Ошибка загрузки TTS: {e}")
        return False

def download_embedding_model():
    """Загрузка модели эмбеддингов"""
    logger.info("Загрузка модели эмбеддингов...")
    try:
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        logger.info("✓ Модель эмбеддингов 'paraphrase-multilingual-MiniLM-L12-v2' загружена")
        
        # Тест модели
        test_texts = ["Привет, мир!", "Hello, world!"]
        embeddings = model.encode(test_texts)
        logger.info(f"✓ Тест эмбеддингов прошел успешно (размер: {embeddings.shape})")
        
        return True
    except Exception as e:
        logger.error(f"✗ Ошибка загрузки эмбеддингов: {e}")
        return False

def download_phi2_model():
    """Загрузка модели Phi-2"""
    logger.info("Загрузка модели Phi-2...")
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        model_name = "microsoft/phi-2"
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            trust_remote_code=True
        )
        
        logger.info("✓ Модель Phi-2 загружена")
        
        # Тест модели
        test_prompt = "Привет! Как дела?"
        inputs = tokenizer(test_prompt, return_tensors="pt")
        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=50, do_sample=True)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"✓ Тест Phi-2 прошел успешно")
        
        return True
    except Exception as e:
        logger.error(f"✗ Ошибка загрузки Phi-2: {e}")
        return False

def download_classification_model():
    """Загрузка модели классификации"""
    logger.info("Загрузка модели классификации...")
    try:
        from transformers import pipeline
        
        classifier = pipeline(
            "text-classification",
            model="cointegrated/rubert-tiny2-cedr-emotion-detection"
        )
        
        logger.info("✓ Модель классификации 'rubert-tiny2' загружена")
        
        # Тест модели
        test_text = "Я очень рад!"
        result = classifier(test_text)
        logger.info(f"✓ Тест классификации прошел успешно: {result}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Ошибка загрузки модели классификации: {e}")
        return False

def create_model_info():
    """Создание файла с информацией о моделях"""
    logger.info("Создание файла информации о моделях...")
    
    model_info = {
        "whisper": {
            "model": "base",
            "size": "~140MB",
            "languages": ["ru", "en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh"],
            "description": "Модель распознавания речи OpenAI Whisper"
        },
        "tts": {
            "model": "tts_models/ru/ruslan",
            "size": "~50MB",
            "languages": ["ru"],
            "description": "Модель синтеза русской речи"
        },
        "embedding": {
            "model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "size": "~120MB",
            "languages": ["ru", "en", "es", "fr", "de", "it", "pt", "nl", "pl", "tr"],
            "description": "Многоязычная модель эмбеддингов"
        },
        "phi2": {
            "model": "microsoft/phi-2",
            "size": "~2.7GB",
            "languages": ["en", "ru"],
            "description": "Малая языковая модель Microsoft Phi-2"
        },
        "classification": {
            "model": "cointegrated/rubert-tiny2-cedr-emotion-detection",
            "size": "~30MB",
            "languages": ["ru"],
            "description": "Модель классификации эмоций на русском языке"
        }
    }
    
    import json
    with open("shared/models/model_info.json", "w", encoding="utf-8") as f:
        json.dump(model_info, f, ensure_ascii=False, indent=2)
    
    logger.info("✓ Файл информации о моделях создан")

def check_disk_space():
    """Проверка свободного места на диске"""
    import shutil
    
    total, used, free = shutil.disk_usage(".")
    free_gb = free // (1024**3)
    
    logger.info(f"Свободное место на диске: {free_gb} GB")
    
    if free_gb < 5:
        logger.warning("⚠️  Мало свободного места на диске (< 5GB)")
        logger.warning("Рекомендуется освободить место перед загрузкой моделей")
        return False
    
    return True

def main():
    """Основная функция"""
    print("=" * 50)
    print("  Jarvis AI Assistant - Загрузка моделей")
    print("=" * 50)
    print()
    
    # Проверка зависимостей
    if not check_dependencies():
        logger.error("Не все зависимости установлены. Установите их и попробуйте снова.")
        sys.exit(1)
    
    # Проверка места на диске
    if not check_disk_space():
        response = input("Продолжить загрузку? (y/N): ")
        if response.lower() != 'y':
            logger.info("Загрузка отменена")
            sys.exit(0)
    
    # Создание директории для моделей
    os.makedirs("shared/models", exist_ok=True)
    
    # Загрузка моделей
    success_count = 0
    total_models = 5
    
    if download_whisper_model():
        success_count += 1
    
    if download_tts_model():
        success_count += 1
    
    if download_embedding_model():
        success_count += 1
    
    if download_phi2_model():
        success_count += 1
    
    if download_classification_model():
        success_count += 1
    
    # Создание информации о моделях
    create_model_info()
    
    print()
    print("=" * 50)
    print(f"  Загрузка завершена: {success_count}/{total_models} моделей")
    print("=" * 50)
    
    if success_count == total_models:
        logger.info("🎉 Все модели загружены успешно!")
        logger.info("Jarvis готов к работе!")
    else:
        logger.warning(f"⚠️  Загружено {success_count} из {total_models} моделей")
        logger.warning("Некоторые функции могут быть недоступны")
    
    print()
    print("Информация о моделях сохранена в: shared/models/model_info.json")
    print("Модели готовы к использованию!")

if __name__ == "__main__":
    main()