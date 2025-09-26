#!/usr/bin/env python3
"""
Knowledge Base - База знаний
Автор: Jarvis AI Assistant
Версия: 1.0.0
"""

import asyncio
import logging
import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import pickle

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    """Типы знаний"""
    FACT = "fact"
    RULE = "rule"
    PATTERN = "pattern"
    EXPERIENCE = "experience"
    PREFERENCE = "preference"
    CONTEXT = "context"

class KnowledgeSource(Enum):
    """Источники знаний"""
    USER_INPUT = "user_input"
    SYSTEM_LEARNING = "system_learning"
    FEEDBACK = "feedback"
    EXTERNAL_API = "external_api"
    DOCUMENTATION = "documentation"

@dataclass
class KnowledgeItem:
    """Элемент базы знаний"""
    id: str
    content: Any
    knowledge_type: KnowledgeType
    source: KnowledgeSource
    confidence: float
    tags: List[str]
    context: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    access_count: int
    last_accessed: datetime

@dataclass
class SearchResult:
    """Результат поиска"""
    item: KnowledgeItem
    relevance_score: float
    match_type: str

class KnowledgeBase:
    """База знаний"""
    
    def __init__(self):
        self.ready = False
        self.db_path = "knowledge_base.db"
        self.connection = None
        self.knowledge_cache = {}
        self.search_index = {}
        
    async def initialize(self):
        """Инициализация базы знаний"""
        try:
            logger.info("Инициализация Knowledge Base...")
            
            # Инициализация базы данных
            await self._init_database()
            
            # Загрузка кэша
            await self._load_cache()
            
            # Построение поискового индекса
            await self._build_search_index()
            
            self.ready = True
            logger.info("Knowledge Base инициализирована")
        except Exception as e:
            logger.error(f"Ошибка инициализации Knowledge Base: {e}")
            raise
    
    async def cleanup(self):
        """Очистка ресурсов"""
        try:
            # Сохранение кэша
            await self._save_cache()
            
            # Закрытие соединения с БД
            if self.connection:
                self.connection.close()
            
            self.ready = False
            logger.info("Knowledge Base очищена")
        except Exception as e:
            logger.error(f"Ошибка очистки Knowledge Base: {e}")
    
    def is_ready(self) -> bool:
        """Проверка готовности базы знаний"""
        return self.ready
    
    async def _init_database(self):
        """Инициализация базы данных"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.connection.cursor()
            
            # Создание таблицы знаний
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    knowledge_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    tags TEXT NOT NULL,
                    context TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT
                )
            ''')
            
            # Создание индексов
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge(knowledge_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON knowledge(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_confidence ON knowledge(confidence)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON knowledge(created_at)')
            
            self.connection.commit()
            logger.info("База данных инициализирована")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise
    
    async def _load_cache(self):
        """Загрузка кэша"""
        try:
            # Загрузка кэша из файла
            try:
                with open("knowledge_cache.pkl", 'rb') as f:
                    self.knowledge_cache = pickle.load(f)
                    logger.info(f"Кэш загружен: {len(self.knowledge_cache)} элементов")
            except FileNotFoundError:
                logger.info("Файл кэша не найден, создаем новый кэш")
                self.knowledge_cache = {}
                
        except Exception as e:
            logger.error(f"Ошибка загрузки кэша: {e}")
            self.knowledge_cache = {}
    
    async def _save_cache(self):
        """Сохранение кэша"""
        try:
            with open("knowledge_cache.pkl", 'wb') as f:
                pickle.dump(self.knowledge_cache, f)
                logger.info("Кэш сохранен")
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша: {e}")
    
    async def _build_search_index(self):
        """Построение поискового индекса"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT id, content, tags FROM knowledge')
            
            self.search_index = {}
            for row in cursor.fetchall():
                item_id, content, tags = row
                
                # Индексация по содержимому
                content_words = str(content).lower().split()
                for word in content_words:
                    if word not in self.search_index:
                        self.search_index[word] = []
                    self.search_index[word].append(item_id)
                
                # Индексация по тегам
                if tags:
                    tag_list = json.loads(tags)
                    for tag in tag_list:
                        if tag not in self.search_index:
                            self.search_index[tag] = []
                        self.search_index[tag].append(item_id)
            
            logger.info(f"Поисковый индекс построен: {len(self.search_index)} ключевых слов")
            
        except Exception as e:
            logger.error(f"Ошибка построения поискового индекса: {e}")
            self.search_index = {}
    
    def _generate_id(self, content: Any) -> str:
        """Генерация уникального ID"""
        content_str = str(content)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    async def store_knowledge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Сохранение знаний"""
        try:
            if not self.ready:
                raise Exception("Knowledge Base не готова")
            
            # Создание элемента знаний
            knowledge_item = KnowledgeItem(
                id=data.get("id") or self._generate_id(data.get("content", "")),
                content=data.get("content"),
                knowledge_type=KnowledgeType(data.get("knowledge_type", "fact")),
                source=KnowledgeSource(data.get("source", "user_input")),
                confidence=data.get("confidence", 1.0),
                tags=data.get("tags", []),
                context=data.get("context", {}),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                access_count=0,
                last_accessed=datetime.now()
            )
            
            # Сохранение в базу данных
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO knowledge 
                (id, content, knowledge_type, source, confidence, tags, context, 
                 created_at, updated_at, access_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                knowledge_item.id,
                json.dumps(knowledge_item.content),
                knowledge_item.knowledge_type.value,
                knowledge_item.source.value,
                knowledge_item.confidence,
                json.dumps(knowledge_item.tags),
                json.dumps(knowledge_item.context),
                knowledge_item.created_at.isoformat(),
                knowledge_item.updated_at.isoformat(),
                knowledge_item.access_count,
                knowledge_item.last_accessed.isoformat()
            ))
            
            self.connection.commit()
            
            # Обновление кэша
            self.knowledge_cache[knowledge_item.id] = knowledge_item
            
            # Обновление поискового индекса
            await self._update_search_index(knowledge_item)
            
            return {
                "success": True,
                "id": knowledge_item.id,
                "message": "Знания сохранены"
            }
            
        except Exception as e:
            logger.error(f"Ошибка сохранения знаний: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_knowledge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Получение знаний"""
        try:
            if not self.ready:
                raise Exception("Knowledge Base не готова")
            
            knowledge_id = data.get("id")
            knowledge_type = data.get("knowledge_type")
            source = data.get("source")
            limit = data.get("limit", 10)
            
            cursor = self.connection.cursor()
            
            # Построение запроса
            query = "SELECT * FROM knowledge WHERE 1=1"
            params = []
            
            if knowledge_id:
                query += " AND id = ?"
                params.append(knowledge_id)
            
            if knowledge_type:
                query += " AND knowledge_type = ?"
                params.append(knowledge_type)
            
            if source:
                query += " AND source = ?"
                params.append(source)
            
            query += " ORDER BY confidence DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Преобразование в объекты знаний
            knowledge_items = []
            for row in rows:
                item = KnowledgeItem(
                    id=row[0],
                    content=json.loads(row[1]),
                    knowledge_type=KnowledgeType(row[2]),
                    source=KnowledgeSource(row[3]),
                    confidence=row[4],
                    tags=json.loads(row[5]),
                    context=json.loads(row[6]),
                    created_at=datetime.fromisoformat(row[7]),
                    updated_at=datetime.fromisoformat(row[8]),
                    access_count=row[9],
                    last_accessed=datetime.fromisoformat(row[10]) if row[10] else datetime.now()
                )
                knowledge_items.append(item)
                
                # Обновление счетчика доступа
                await self._update_access_count(item.id)
            
            return {
                "success": True,
                "knowledge": [asdict(item) for item in knowledge_items],
                "count": len(knowledge_items)
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения знаний: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_knowledge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Поиск знаний"""
        try:
            if not self.ready:
                raise Exception("Knowledge Base не готова")
            
            query = data.get("query", "")
            knowledge_type = data.get("knowledge_type")
            min_confidence = data.get("min_confidence", 0.0)
            limit = data.get("limit", 10)
            
            if not query:
                return {
                    "success": False,
                    "error": "Пустой поисковый запрос"
                }
            
            # Поиск по индексу
            query_words = query.lower().split()
            matching_ids = set()
            
            for word in query_words:
                if word in self.search_index:
                    matching_ids.update(self.search_index[word])
            
            if not matching_ids:
                return {
                    "success": True,
                    "results": [],
                    "count": 0,
                    "message": "Ничего не найдено"
                }
            
            # Получение детальной информации
            cursor = self.connection.cursor()
            placeholders = ','.join(['?' for _ in matching_ids])
            
            search_query = f'''
                SELECT * FROM knowledge 
                WHERE id IN ({placeholders})
            '''
            params = list(matching_ids)
            
            if knowledge_type:
                search_query += " AND knowledge_type = ?"
                params.append(knowledge_type)
            
            search_query += " AND confidence >= ?"
            params.append(min_confidence)
            
            search_query += " ORDER BY confidence DESC, access_count DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(search_query, params)
            rows = cursor.fetchall()
            
            # Создание результатов поиска
            search_results = []
            for row in rows:
                item = KnowledgeItem(
                    id=row[0],
                    content=json.loads(row[1]),
                    knowledge_type=KnowledgeType(row[2]),
                    source=KnowledgeSource(row[3]),
                    confidence=row[4],
                    tags=json.loads(row[5]),
                    context=json.loads(row[6]),
                    created_at=datetime.fromisoformat(row[7]),
                    updated_at=datetime.fromisoformat(row[8]),
                    access_count=row[9],
                    last_accessed=datetime.fromisoformat(row[10]) if row[10] else datetime.now()
                )
                
                # Вычисление релевантности
                relevance_score = await self._calculate_relevance(item, query)
                
                search_result = SearchResult(
                    item=item,
                    relevance_score=relevance_score,
                    match_type="content" if any(word in str(item.content).lower() for word in query_words) else "tag"
                )
                
                search_results.append(search_result)
                
                # Обновление счетчика доступа
                await self._update_access_count(item.id)
            
            # Сортировка по релевантности
            search_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return {
                "success": True,
                "results": [
                    {
                        "item": asdict(result.item),
                        "relevance_score": result.relevance_score,
                        "match_type": result.match_type
                    }
                    for result in search_results
                ],
                "count": len(search_results),
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Ошибка поиска знаний: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _calculate_relevance(self, item: KnowledgeItem, query: str) -> float:
        """Вычисление релевантности"""
        try:
            query_words = query.lower().split()
            content_words = str(item.content).lower().split()
            tag_words = [tag.lower() for tag in item.tags]
            
            # Подсчет совпадений
            content_matches = sum(1 for word in query_words if word in content_words)
            tag_matches = sum(1 for word in query_words if word in tag_words)
            
            # Вычисление релевантности
            content_relevance = content_matches / len(query_words) if query_words else 0
            tag_relevance = tag_matches / len(query_words) if query_words else 0
            
            # Взвешенная релевантность
            relevance = (content_relevance * 0.7 + tag_relevance * 0.3) * item.confidence
            
            return min(1.0, relevance)
            
        except Exception as e:
            logger.error(f"Ошибка вычисления релевантности: {e}")
            return 0.0
    
    async def update_knowledge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление знаний"""
        try:
            if not self.ready:
                raise Exception("Knowledge Base не готова")
            
            knowledge_id = data.get("id")
            if not knowledge_id:
                return {
                    "success": False,
                    "error": "ID знаний не указан"
                }
            
            # Получение существующих знаний
            existing_data = await self.get_knowledge({"id": knowledge_id})
            if not existing_data["success"] or not existing_data["knowledge"]:
                return {
                    "success": False,
                    "error": "Знания не найдены"
                }
            
            existing_item = existing_data["knowledge"][0]
            
            # Обновление полей
            updated_item = KnowledgeItem(
                id=knowledge_id,
                content=data.get("content", existing_item["content"]),
                knowledge_type=KnowledgeType(data.get("knowledge_type", existing_item["knowledge_type"])),
                source=KnowledgeSource(data.get("source", existing_item["source"])),
                confidence=data.get("confidence", existing_item["confidence"]),
                tags=data.get("tags", existing_item["tags"]),
                context=data.get("context", existing_item["context"]),
                created_at=datetime.fromisoformat(existing_item["created_at"]),
                updated_at=datetime.now(),
                access_count=existing_item["access_count"],
                last_accessed=datetime.fromisoformat(existing_item["last_accessed"])
            )
            
            # Сохранение обновленных знаний
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE knowledge SET
                    content = ?, knowledge_type = ?, source = ?, confidence = ?,
                    tags = ?, context = ?, updated_at = ?
                WHERE id = ?
            ''', (
                json.dumps(updated_item.content),
                updated_item.knowledge_type.value,
                updated_item.source.value,
                updated_item.confidence,
                json.dumps(updated_item.tags),
                json.dumps(updated_item.context),
                updated_item.updated_at.isoformat(),
                knowledge_id
            ))
            
            self.connection.commit()
            
            # Обновление кэша
            self.knowledge_cache[knowledge_id] = updated_item
            
            # Обновление поискового индекса
            await self._update_search_index(updated_item)
            
            return {
                "success": True,
                "id": knowledge_id,
                "message": "Знания обновлены"
            }
            
        except Exception as e:
            logger.error(f"Ошибка обновления знаний: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_knowledge(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Удаление знаний"""
        try:
            if not self.ready:
                raise Exception("Knowledge Base не готова")
            
            knowledge_id = data.get("id")
            if not knowledge_id:
                return {
                    "success": False,
                    "error": "ID знаний не указан"
                }
            
            # Удаление из базы данных
            cursor = self.connection.cursor()
            cursor.execute('DELETE FROM knowledge WHERE id = ?', (knowledge_id,))
            
            if cursor.rowcount == 0:
                return {
                    "success": False,
                    "error": "Знания не найдены"
                }
            
            self.connection.commit()
            
            # Удаление из кэша
            if knowledge_id in self.knowledge_cache:
                del self.knowledge_cache[knowledge_id]
            
            # Удаление из поискового индекса
            await self._remove_from_search_index(knowledge_id)
            
            return {
                "success": True,
                "id": knowledge_id,
                "message": "Знания удалены"
            }
            
        except Exception as e:
            logger.error(f"Ошибка удаления знаний: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_access_count(self, knowledge_id: str):
        """Обновление счетчика доступа"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE knowledge 
                SET access_count = access_count + 1, last_accessed = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), knowledge_id))
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Ошибка обновления счетчика доступа: {e}")
    
    async def _update_search_index(self, item: KnowledgeItem):
        """Обновление поискового индекса"""
        try:
            # Удаление старых записей
            await self._remove_from_search_index(item.id)
            
            # Добавление новых записей
            content_words = str(item.content).lower().split()
            for word in content_words:
                if word not in self.search_index:
                    self.search_index[word] = []
                self.search_index[word].append(item.id)
            
            for tag in item.tags:
                tag_lower = tag.lower()
                if tag_lower not in self.search_index:
                    self.search_index[tag_lower] = []
                self.search_index[tag_lower].append(item.id)
            
        except Exception as e:
            logger.error(f"Ошибка обновления поискового индекса: {e}")
    
    async def _remove_from_search_index(self, knowledge_id: str):
        """Удаление из поискового индекса"""
        try:
            for word, ids in self.search_index.items():
                if knowledge_id in ids:
                    ids.remove(knowledge_id)
                    if not ids:
                        del self.search_index[word]
            
        except Exception as e:
            logger.error(f"Ошибка удаления из поискового индекса: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики базы знаний"""
        try:
            if not self.ready:
                raise Exception("Knowledge Base не готова")
            
            cursor = self.connection.cursor()
            
            # Общая статистика
            cursor.execute('SELECT COUNT(*) FROM knowledge')
            total_count = cursor.fetchone()[0]
            
            # Статистика по типам
            cursor.execute('SELECT knowledge_type, COUNT(*) FROM knowledge GROUP BY knowledge_type')
            type_stats = dict(cursor.fetchall())
            
            # Статистика по источникам
            cursor.execute('SELECT source, COUNT(*) FROM knowledge GROUP BY source')
            source_stats = dict(cursor.fetchall())
            
            # Статистика по уверенности
            cursor.execute('SELECT AVG(confidence), MIN(confidence), MAX(confidence) FROM knowledge')
            confidence_stats = cursor.fetchone()
            
            # Статистика по доступу
            cursor.execute('SELECT AVG(access_count), SUM(access_count) FROM knowledge')
            access_stats = cursor.fetchone()
            
            return {
                "success": True,
                "statistics": {
                    "total_knowledge_items": total_count,
                    "by_type": type_stats,
                    "by_source": source_stats,
                    "confidence": {
                        "average": confidence_stats[0] or 0,
                        "minimum": confidence_stats[1] or 0,
                        "maximum": confidence_stats[2] or 0
                    },
                    "access": {
                        "average_access_count": access_stats[0] or 0,
                        "total_access_count": access_stats[1] or 0
                    },
                    "search_index_size": len(self.search_index),
                    "cache_size": len(self.knowledge_cache)
                }
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {
                "success": False,
                "error": str(e)
            }