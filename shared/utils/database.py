"""
Database utilities for Jarvis AI Assistant
"""
import asyncio
import asyncpg
import redis.asyncio as redis
from typing import Optional, Dict, Any, List
import json
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер для работы с базами данных"""
    
    def __init__(self, postgres_url: str, redis_url: str):
        self.postgres_url = postgres_url
        self.redis_url = redis_url
        self._postgres_pool: Optional[asyncpg.Pool] = None
        self._redis_pool: Optional[redis.ConnectionPool] = None
    
    async def initialize(self):
        """Инициализация подключений к базам данных"""
        try:
            # PostgreSQL pool
            self._postgres_pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            # Redis pool
            self._redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=20
            )
            
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    async def close(self):
        """Закрытие подключений"""
        if self._postgres_pool:
            await self._postgres_pool.close()
        if self._redis_pool:
            await self._redis_pool.disconnect()
    
    @asynccontextmanager
    async def get_postgres_connection(self):
        """Контекстный менеджер для PostgreSQL подключения"""
        if not self._postgres_pool:
            raise RuntimeError("Database not initialized")
        
        async with self._postgres_pool.acquire() as connection:
            yield connection
    
    @asynccontextmanager
    async def get_redis_connection(self):
        """Контекстный менеджер для Redis подключения"""
        if not self._redis_pool:
            raise RuntimeError("Redis not initialized")
        
        redis_client = redis.Redis(connection_pool=self._redis_pool)
        try:
            yield redis_client
        finally:
            await redis_client.close()
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Выполнение SQL запроса"""
        async with self.get_postgres_connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def execute_command(self, command: str, *args) -> str:
        """Выполнение SQL команды"""
        async with self.get_postgres_connection() as conn:
            return await conn.execute(command, *args)
    
    async def redis_set(self, key: str, value: Any, expire: Optional[int] = None):
        """Установка значения в Redis"""
        async with self.get_redis_connection() as redis_client:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            await redis_client.set(key, value, ex=expire)
    
    async def redis_get(self, key: str) -> Optional[Any]:
        """Получение значения из Redis"""
        async with self.get_redis_connection() as redis_client:
            value = await redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value.decode('utf-8')
            return None
    
    async def redis_delete(self, key: str):
        """Удаление ключа из Redis"""
        async with self.get_redis_connection() as redis_client:
            await redis_client.delete(key)
    
    async def redis_publish(self, channel: str, message: Any):
        """Публикация сообщения в Redis канал"""
        async with self.get_redis_connection() as redis_client:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            await redis_client.publish(channel, message)
    
    async def redis_subscribe(self, channels: List[str]):
        """Подписка на Redis каналы"""
        async with self.get_redis_connection() as redis_client:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(*channels)
            try:
                async for message in pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                        except json.JSONDecodeError:
                            data = message['data'].decode('utf-8')
                        yield message['channel'], data
            finally:
                await pubsub.unsubscribe()
                await pubsub.close()

class CommandLogger:
    """Логгер команд для отслеживания выполнения"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def log_command(self, user_id: str, session_id: str, command_text: str, 
                         command_type: str) -> str:
        """Логирование новой команды"""
        query = """
        INSERT INTO commands (user_id, session_id, command_text, command_type, status)
        VALUES ($1, $2, $3, $4, 'pending')
        RETURNING id
        """
        result = await self.db_manager.execute_query(query, user_id, session_id, command_text, command_type)
        return result[0]['id']
    
    async def update_command_status(self, command_id: str, status: str, 
                                   result: Optional[Dict] = None, error: Optional[str] = None):
        """Обновление статуса команды"""
        query = """
        UPDATE commands 
        SET status = $2, result = $3, error_message = $4, completed_at = NOW()
        WHERE id = $1
        """
        await self.db_manager.execute_command(query, command_id, status, result, error)
    
    async def log_task(self, command_id: str, task_type: str, task_data: Dict) -> str:
        """Логирование задачи"""
        query = """
        INSERT INTO tasks (command_id, task_type, task_data, status)
        VALUES ($1, $2, $3, 'pending')
        RETURNING id
        """
        result = await self.db_manager.execute_query(query, command_id, task_type, task_data)
        return result[0]['id']
    
    async def update_task_status(self, task_id: str, status: str, 
                                result: Optional[Dict] = None, error: Optional[str] = None):
        """Обновление статуса задачи"""
        query = """
        UPDATE tasks 
        SET status = $2, result = $3, error_message = $4, 
            started_at = CASE WHEN $2 = 'processing' AND started_at IS NULL THEN NOW() ELSE started_at END,
            completed_at = CASE WHEN $2 IN ('completed', 'failed') THEN NOW() ELSE completed_at END
        WHERE id = $1
        """
        await self.db_manager.execute_command(query, task_id, status, result, error)

class LearningDataManager:
    """Менеджер данных обучения"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def store_interaction(self, interaction_type: str, input_data: Dict, 
                               output_data: Optional[Dict] = None, 
                               feedback_score: Optional[int] = None,
                               learning_vector: Optional[List[float]] = None):
        """Сохранение данных взаимодействия"""
        query = """
        INSERT INTO learning_data (interaction_type, input_data, output_data, feedback_score, learning_vector)
        VALUES ($1, $2, $3, $4, $5)
        """
        await self.db_manager.execute_command(
            query, interaction_type, input_data, output_data, feedback_score, learning_vector
        )
    
    async def get_learning_data(self, interaction_type: Optional[str] = None, 
                               limit: int = 100) -> List[Dict]:
        """Получение данных обучения"""
        if interaction_type:
            query = """
            SELECT * FROM learning_data 
            WHERE interaction_type = $1 
            ORDER BY created_at DESC 
            LIMIT $2
            """
            return await self.db_manager.execute_query(query, interaction_type, limit)
        else:
            query = """
            SELECT * FROM learning_data 
            ORDER BY created_at DESC 
            LIMIT $1
            """
            return await self.db_manager.execute_query(query, limit)
    
    async def store_memory(self, memory_type: str, content: str, 
                          importance_score: float = 0.5,
                          expires_at: Optional[str] = None):
        """Сохранение в память агента"""
        query = """
        INSERT INTO agent_memory (memory_type, content, importance_score, expires_at)
        VALUES ($1, $2, $3, $4)
        """
        await self.db_manager.execute_command(query, memory_type, content, importance_score, expires_at)
    
    async def get_memory(self, memory_type: Optional[str] = None, 
                        min_importance: float = 0.0) -> List[Dict]:
        """Получение памяти агента"""
        if memory_type:
            query = """
            SELECT * FROM agent_memory 
            WHERE memory_type = $1 AND importance_score >= $2
            ORDER BY importance_score DESC, last_accessed DESC
            """
            return await self.db_manager.execute_query(query, memory_type, min_importance)
        else:
            query = """
            SELECT * FROM agent_memory 
            WHERE importance_score >= $1
            ORDER BY importance_score DESC, last_accessed DESC
            """
            return await self.db_manager.execute_query(query, min_importance)
    
    async def update_memory_access(self, memory_id: str):
        """Обновление времени доступа к памяти"""
        query = """
        UPDATE agent_memory 
        SET access_count = access_count + 1, last_accessed = NOW()
        WHERE id = $1
        """
        await self.db_manager.execute_command(query, memory_id)