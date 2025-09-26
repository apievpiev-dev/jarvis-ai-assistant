"""
Планировщик задач для Task Service
Планирование и выполнение задач по расписанию
"""
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import croniter

from utils.logger import get_logger
from utils.database import CommandLogger

logger = get_logger("task-scheduler")

class TaskStatus(Enum):
    """Статусы задач"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ScheduledTask:
    """Запланированная задача"""
    id: str
    task_type: str
    task_data: Dict[str, Any]
    schedule_time: Optional[datetime]
    cron_expression: Optional[str]
    user_id: str
    status: TaskStatus
    created_at: datetime
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    max_runs: Optional[int]
    retry_count: int
    max_retries: int
    error_message: Optional[str]

class TaskScheduler:
    """Планировщик задач"""
    
    def __init__(self, task_executor, command_logger: CommandLogger):
        self.task_executor = task_executor
        self.command_logger = command_logger
        
        # Хранилище запланированных задач
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        
        # Активные задачи
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # Флаг работы планировщика
        self.is_running = False
        
        # Задача планировщика
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # Интервал проверки (в секундах)
        self.check_interval = 10
        
        logger.info("Task scheduler initialized")
    
    async def initialize(self):
        """Инициализация планировщика"""
        try:
            # Загрузка сохраненных задач из базы данных
            await self._load_scheduled_tasks()
            
            # Запуск планировщика
            await self.start()
            
            logger.info("Task scheduler initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize task scheduler: {e}")
            raise
    
    async def start(self):
        """Запуск планировщика"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        logger.info("Task scheduler started")
    
    async def stop(self):
        """Остановка планировщика"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        # Отмена всех активных задач
        for task_id, task in self.running_tasks.items():
            task.cancel()
        
        logger.info("Task scheduler stopped")
    
    async def schedule_task(self, task_type: str, task_data: Dict[str, Any], 
                           schedule_time: Optional[str] = None,
                           cron_expression: Optional[str] = None,
                           user_id: str = "default_user",
                           max_runs: Optional[int] = None,
                           max_retries: int = 3) -> str:
        """Планирование задачи"""
        try:
            # Генерация ID задачи
            task_id = str(uuid.uuid4())
            
            # Парсинг времени выполнения
            parsed_schedule_time = None
            if schedule_time:
                try:
                    parsed_schedule_time = datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
                except ValueError:
                    raise ValueError(f"Invalid schedule_time format: {schedule_time}")
            
            # Валидация cron выражения
            if cron_expression:
                try:
                    croniter.croniter(cron_expression)
                except Exception as e:
                    raise ValueError(f"Invalid cron expression: {cron_expression}")
            
            # Вычисление времени следующего выполнения
            next_run = self._calculate_next_run(parsed_schedule_time, cron_expression)
            
            # Создание задачи
            scheduled_task = ScheduledTask(
                id=task_id,
                task_type=task_type,
                task_data=task_data,
                schedule_time=parsed_schedule_time,
                cron_expression=cron_expression,
                user_id=user_id,
                status=TaskStatus.SCHEDULED,
                created_at=datetime.now(),
                last_run=None,
                next_run=next_run,
                run_count=0,
                max_runs=max_runs,
                retry_count=0,
                max_retries=max_retries,
                error_message=None
            )
            
            # Сохранение задачи
            self.scheduled_tasks[task_id] = scheduled_task
            await self._save_scheduled_task(scheduled_task)
            
            logger.info(f"Task scheduled: {task_id} ({task_type})")
            
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to schedule task: {e}")
            raise
    
    async def cancel_task(self, task_id: str) -> bool:
        """Отмена задачи"""
        try:
            if task_id not in self.scheduled_tasks:
                return False
            
            task = self.scheduled_tasks[task_id]
            
            # Отмена активной задачи
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                del self.running_tasks[task_id]
            
            # Обновление статуса
            task.status = TaskStatus.CANCELLED
            await self._save_scheduled_task(task)
            
            logger.info(f"Task cancelled: {task_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel task: {e}")
            return False
    
    async def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """Получение списка запланированных задач"""
        tasks = []
        
        for task in self.scheduled_tasks.values():
            task_dict = asdict(task)
            # Конвертация datetime в строки
            for key, value in task_dict.items():
                if isinstance(value, datetime):
                    task_dict[key] = value.isoformat()
                elif isinstance(value, TaskStatus):
                    task_dict[key] = value.value
            
            tasks.append(task_dict)
        
        return sorted(tasks, key=lambda x: x['created_at'], reverse=True)
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Получение статуса задачи"""
        if task_id not in self.scheduled_tasks:
            return None
        
        task = self.scheduled_tasks[task_id]
        task_dict = asdict(task)
        
        # Конвертация datetime в строки
        for key, value in task_dict.items():
            if isinstance(value, datetime):
                task_dict[key] = value.isoformat()
            elif isinstance(value, TaskStatus):
                task_dict[key] = value.value
        
        return task_dict
    
    async def _scheduler_loop(self):
        """Основной цикл планировщика"""
        while self.is_running:
            try:
                await self._check_and_execute_tasks()
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_and_execute_tasks(self):
        """Проверка и выполнение готовых к выполнению задач"""
        current_time = datetime.now()
        
        for task_id, task in self.scheduled_tasks.items():
            try:
                # Проверка условий выполнения
                if (task.status == TaskStatus.SCHEDULED and 
                    task.next_run and 
                    current_time >= task.next_run):
                    
                    # Проверка максимального количества выполнений
                    if task.max_runs and task.run_count >= task.max_runs:
                        task.status = TaskStatus.COMPLETED
                        await self._save_scheduled_task(task)
                        continue
                    
                    # Запуск задачи
                    await self._execute_scheduled_task(task)
                    
            except Exception as e:
                logger.error(f"Error checking task {task_id}: {e}")
    
    async def _execute_scheduled_task(self, task: ScheduledTask):
        """Выполнение запланированной задачи"""
        try:
            # Обновление статуса
            task.status = TaskStatus.RUNNING
            task.last_run = datetime.now()
            task.run_count += 1
            
            await self._save_scheduled_task(task)
            
            # Создание задачи выполнения
            execution_task = asyncio.create_task(
                self._run_task_execution(task)
            )
            
            # Сохранение активной задачи
            self.running_tasks[task.id] = execution_task
            
            # Ожидание завершения
            await execution_task
            
            # Удаление из активных задач
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
            
            # Обновление времени следующего выполнения
            task.next_run = self._calculate_next_run(
                task.schedule_time, 
                task.cron_expression
            )
            
            # Определение статуса
            if task.next_run:
                task.status = TaskStatus.SCHEDULED
            else:
                task.status = TaskStatus.COMPLETED
            
            await self._save_scheduled_task(task)
            
            logger.info(f"Task executed: {task.id} ({task.task_type})")
            
        except Exception as e:
            logger.error(f"Failed to execute scheduled task {task.id}: {e}")
            
            # Обработка ошибки
            await self._handle_task_error(task, str(e))
    
    async def _run_task_execution(self, task: ScheduledTask):
        """Выполнение задачи"""
        try:
            # Логирование команды
            command_id = await self.command_logger.log_command(
                user_id=task.user_id,
                session_id=f"scheduled_{task.id}",
                command_text=f"Scheduled task: {task.task_type}",
                command_type="scheduled_task"
            )
            
            # Создание задачи
            task_log_id = await self.command_logger.log_task(
                command_id=command_id,
                task_type=task.task_type,
                task_data=task.task_data
            )
            
            # Выполнение задачи
            result = await self.task_executor.execute_task(
                task.task_type, 
                task.task_data
            )
            
            # Обновление статуса задачи
            await self.command_logger.update_task_status(
                task_log_id,
                "completed",
                result
            )
            
            # Обновление статуса команды
            await self.command_logger.update_command_status(
                command_id,
                "completed",
                {
                    "task_id": task_log_id,
                    "task_type": task.task_type,
                    "result": result
                }
            )
            
            # Сброс счетчика ошибок
            task.retry_count = 0
            task.error_message = None
            
        except Exception as e:
            # Увеличение счетчика ошибок
            task.retry_count += 1
            task.error_message = str(e)
            
            # Проверка максимального количества попыток
            if task.retry_count >= task.max_retries:
                task.status = TaskStatus.FAILED
                logger.error(f"Task {task.id} failed after {task.max_retries} retries")
            else:
                # Планирование повторного выполнения
                retry_delay = min(300, 60 * (2 ** task.retry_count))  # Экспоненциальная задержка
                task.next_run = datetime.now() + timedelta(seconds=retry_delay)
                task.status = TaskStatus.SCHEDULED
                logger.warning(f"Task {task.id} failed, retrying in {retry_delay} seconds")
            
            raise
    
    async def _handle_task_error(self, task: ScheduledTask, error_message: str):
        """Обработка ошибки задачи"""
        task.error_message = error_message
        task.retry_count += 1
        
        if task.retry_count >= task.max_retries:
            task.status = TaskStatus.FAILED
        else:
            # Планирование повторного выполнения
            retry_delay = min(300, 60 * (2 ** task.retry_count))
            task.next_run = datetime.now() + timedelta(seconds=retry_delay)
            task.status = TaskStatus.SCHEDULED
        
        await self._save_scheduled_task(task)
    
    def _calculate_next_run(self, schedule_time: Optional[datetime], 
                           cron_expression: Optional[str]) -> Optional[datetime]:
        """Вычисление времени следующего выполнения"""
        if cron_expression:
            # Вычисление следующего времени по cron
            try:
                cron = croniter.croniter(cron_expression, datetime.now())
                return cron.get_next(datetime)
            except Exception as e:
                logger.error(f"Error calculating next run from cron: {e}")
                return None
        
        elif schedule_time:
            # Одноразовое выполнение
            if schedule_time > datetime.now():
                return schedule_time
            else:
                return None
        
        else:
            # Немедленное выполнение
            return datetime.now()
    
    async def _load_scheduled_tasks(self):
        """Загрузка сохраненных задач из базы данных"""
        try:
            # В реальном приложении здесь будет загрузка из базы данных
            # Пока что просто инициализируем пустой список
            logger.info("Loading scheduled tasks from database")
            
        except Exception as e:
            logger.error(f"Failed to load scheduled tasks: {e}")
    
    async def _save_scheduled_task(self, task: ScheduledTask):
        """Сохранение задачи в базу данных"""
        try:
            # В реальном приложении здесь будет сохранение в базу данных
            # Пока что просто логируем
            logger.debug(f"Saving scheduled task: {task.id}")
            
        except Exception as e:
            logger.error(f"Failed to save scheduled task: {e}")
    
    async def cleanup(self):
        """Очистка ресурсов"""
        try:
            # Остановка планировщика
            await self.stop()
            
            # Очистка задач
            self.scheduled_tasks.clear()
            self.running_tasks.clear()
            
            logger.info("Task scheduler cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики планировщика"""
        stats = {
            "total_tasks": len(self.scheduled_tasks),
            "running_tasks": len(self.running_tasks),
            "scheduled_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0
        }
        
        for task in self.scheduled_tasks.values():
            if task.status == TaskStatus.SCHEDULED:
                stats["scheduled_tasks"] += 1
            elif task.status == TaskStatus.COMPLETED:
                stats["completed_tasks"] += 1
            elif task.status == TaskStatus.FAILED:
                stats["failed_tasks"] += 1
            elif task.status == TaskStatus.CANCELLED:
                stats["cancelled_tasks"] += 1
        
        return stats