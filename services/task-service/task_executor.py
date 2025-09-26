"""
Исполнитель задач для Task Service
Выполнение различных типов задач и команд
"""
import asyncio
import os
import subprocess
import shutil
import json
import time
import psutil
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging
import tempfile
import zipfile
import tarfile
from datetime import datetime, timedelta

from utils.config import JarvisConfig
from utils.logger import get_logger

logger = get_logger("task-executor")

class TaskExecutor:
    """Исполнитель задач"""
    
    def __init__(self, config: JarvisConfig):
        self.config = config
        self.workspace_path = Path("/app/workspace")
        self.workspace_path.mkdir(exist_ok=True)
        
        # Регистр доступных задач
        self.task_handlers = {
            "file_create": self._handle_file_create,
            "file_read": self._handle_file_read,
            "file_write": self._handle_file_write,
            "file_delete": self._handle_file_delete,
            "file_copy": self._handle_file_copy,
            "file_move": self._handle_file_move,
            "file_list": self._handle_file_list,
            "directory_create": self._handle_directory_create,
            "directory_delete": self._handle_directory_delete,
            "system_info": self._handle_system_info,
            "process_list": self._handle_process_list,
            "process_kill": self._handle_process_kill,
            "web_request": self._handle_web_request,
            "web_scrape": self._handle_web_scrape,
            "command_execute": self._handle_command_execute,
            "text_process": self._handle_text_process,
            "data_convert": self._handle_data_convert,
            "backup_create": self._handle_backup_create,
            "backup_restore": self._handle_backup_restore,
            "archive_create": self._handle_archive_create,
            "archive_extract": self._handle_archive_extract,
            "search_files": self._handle_search_files,
            "monitor_system": self._handle_monitor_system,
            "cleanup_temp": self._handle_cleanup_temp,
            "general": self._handle_general_task
        }
        
        logger.info("Task executor initialized")
    
    async def initialize(self):
        """Инициализация исполнителя задач"""
        try:
            # Создание необходимых директорий
            self._create_workspace_directories()
            
            # Инициализация системных ресурсов
            await self._initialize_system_resources()
            
            logger.info("Task executor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize task executor: {e}")
            raise
    
    def _create_workspace_directories(self):
        """Создание директорий рабочего пространства"""
        directories = [
            "temp",
            "downloads",
            "backups",
            "archives",
            "logs",
            "data"
        ]
        
        for directory in directories:
            dir_path = self.workspace_path / directory
            dir_path.mkdir(exist_ok=True)
    
    async def _initialize_system_resources(self):
        """Инициализация системных ресурсов"""
        # Проверка доступности системных команд
        required_commands = ["curl", "wget", "git", "unzip", "tar"]
        
        for command in required_commands:
            try:
                result = await self._run_command(f"which {command}")
                if result["returncode"] != 0:
                    logger.warning(f"Command {command} not found")
            except Exception as e:
                logger.warning(f"Failed to check command {command}: {e}")
    
    async def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение задачи"""
        try:
            if task_type not in self.task_handlers:
                raise ValueError(f"Unknown task type: {task_type}")
            
            logger.info(f"Executing task: {task_type}")
            
            # Выполнение задачи
            result = await self.task_handlers[task_type](task_data)
            
            logger.info(f"Task {task_type} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "task_type": task_type
            }
    
    async def _handle_file_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание файла"""
        file_path = data.get("file_path")
        content = data.get("content", "")
        encoding = data.get("encoding", "utf-8")
        
        if not file_path:
            raise ValueError("file_path is required")
        
        # Создание директории если не существует
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Запись файла
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return {
            "status": "success",
            "file_path": str(file_path),
            "size": file_path.stat().st_size,
            "created": True
        }
    
    async def _handle_file_read(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Чтение файла"""
        file_path = data.get("file_path")
        encoding = data.get("encoding", "utf-8")
        max_size = data.get("max_size", 1024 * 1024)  # 1MB по умолчанию
        
        if not file_path:
            raise ValueError("file_path is required")
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.stat().st_size > max_size:
            raise ValueError(f"File too large: {file_path.stat().st_size} bytes")
        
        # Чтение файла
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        return {
            "status": "success",
            "file_path": str(file_path),
            "content": content,
            "size": len(content),
            "encoding": encoding
        }
    
    async def _handle_file_write(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Запись в файл"""
        file_path = data.get("file_path")
        content = data.get("content", "")
        mode = data.get("mode", "w")  # w, a, x
        encoding = data.get("encoding", "utf-8")
        
        if not file_path:
            raise ValueError("file_path is required")
        
        file_path = Path(file_path)
        
        # Создание директории если не существует
        if mode in ["w", "a", "x"]:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Запись файла
        with open(file_path, mode, encoding=encoding) as f:
            f.write(content)
        
        return {
            "status": "success",
            "file_path": str(file_path),
            "size": file_path.stat().st_size,
            "mode": mode
        }
    
    async def _handle_file_delete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Удаление файла"""
        file_path = data.get("file_path")
        force = data.get("force", False)
        
        if not file_path:
            raise ValueError("file_path is required")
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            if force:
                return {"status": "success", "file_path": str(file_path), "deleted": False}
            else:
                raise FileNotFoundError(f"File not found: {file_path}")
        
        # Удаление файла
        file_path.unlink()
        
        return {
            "status": "success",
            "file_path": str(file_path),
            "deleted": True
        }
    
    async def _handle_file_copy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Копирование файла"""
        source_path = data.get("source_path")
        destination_path = data.get("destination_path")
        
        if not source_path or not destination_path:
            raise ValueError("source_path and destination_path are required")
        
        source_path = Path(source_path)
        destination_path = Path(destination_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Создание директории назначения
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Копирование файла
        shutil.copy2(source_path, destination_path)
        
        return {
            "status": "success",
            "source_path": str(source_path),
            "destination_path": str(destination_path),
            "size": destination_path.stat().st_size
        }
    
    async def _handle_file_move(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Перемещение файла"""
        source_path = data.get("source_path")
        destination_path = data.get("destination_path")
        
        if not source_path or not destination_path:
            raise ValueError("source_path and destination_path are required")
        
        source_path = Path(source_path)
        destination_path = Path(destination_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Создание директории назначения
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Перемещение файла
        shutil.move(str(source_path), str(destination_path))
        
        return {
            "status": "success",
            "source_path": str(source_path),
            "destination_path": str(destination_path),
            "moved": True
        }
    
    async def _handle_file_list(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Список файлов в директории"""
        directory_path = data.get("directory_path", ".")
        recursive = data.get("recursive", False)
        pattern = data.get("pattern", "*")
        
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        # Получение списка файлов
        if recursive:
            files = list(directory_path.rglob(pattern))
        else:
            files = list(directory_path.glob(pattern))
        
        # Информация о файлах
        file_info = []
        for file_path in files:
            if file_path.is_file():
                stat = file_path.stat()
                file_info.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "is_file": True
                })
            elif file_path.is_dir():
                file_info.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "is_file": False
                })
        
        return {
            "status": "success",
            "directory": str(directory_path),
            "files": file_info,
            "count": len(file_info)
        }
    
    async def _handle_directory_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание директории"""
        directory_path = data.get("directory_path")
        parents = data.get("parents", True)
        
        if not directory_path:
            raise ValueError("directory_path is required")
        
        directory_path = Path(directory_path)
        
        # Создание директории
        directory_path.mkdir(parents=parents, exist_ok=True)
        
        return {
            "status": "success",
            "directory_path": str(directory_path),
            "created": True
        }
    
    async def _handle_directory_delete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Удаление директории"""
        directory_path = data.get("directory_path")
        recursive = data.get("recursive", False)
        force = data.get("force", False)
        
        if not directory_path:
            raise ValueError("directory_path is required")
        
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            if force:
                return {"status": "success", "directory_path": str(directory_path), "deleted": False}
            else:
                raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Удаление директории
        if recursive:
            shutil.rmtree(directory_path)
        else:
            directory_path.rmdir()
        
        return {
            "status": "success",
            "directory_path": str(directory_path),
            "deleted": True
        }
    
    async def _handle_system_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Получение информации о системе"""
        return await self.get_system_info()
    
    async def _handle_process_list(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Список процессов"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            "status": "success",
            "processes": processes,
            "count": len(processes)
        }
    
    async def _handle_process_kill(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Завершение процесса"""
        pid = data.get("pid")
        signal = data.get("signal", "SIGTERM")
        
        if not pid:
            raise ValueError("pid is required")
        
        try:
            process = psutil.Process(pid)
            process.terminate()
            
            return {
                "status": "success",
                "pid": pid,
                "killed": True
            }
        except psutil.NoSuchProcess:
            raise ValueError(f"Process {pid} not found")
        except psutil.AccessDenied:
            raise PermissionError(f"Access denied to process {pid}")
    
    async def _handle_web_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение веб-запроса"""
        url = data.get("url")
        method = data.get("method", "GET")
        headers = data.get("headers", {})
        data_payload = data.get("data")
        timeout = data.get("timeout", 30)
        
        if not url:
            raise ValueError("url is required")
        
        # Выполнение запроса
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=data_payload,
            timeout=timeout
        )
        
        return {
            "status": "success",
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text[:1000],  # Ограничение размера
            "size": len(response.content)
        }
    
    async def _handle_web_scrape(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Веб-скрапинг"""
        url = data.get("url")
        selector = data.get("selector")
        timeout = data.get("timeout", 30)
        
        if not url:
            raise ValueError("url is required")
        
        # Выполнение запроса
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        # Простой парсинг (в реальном приложении можно использовать BeautifulSoup)
        content = response.text
        
        if selector:
            # Простой поиск по селектору
            import re
            if selector.startswith("."):
                # Поиск по классу
                pattern = rf'class="{selector[1:]}"[^>]*>([^<]+)'
                matches = re.findall(pattern, content)
            elif selector.startswith("#"):
                # Поиск по ID
                pattern = rf'id="{selector[1:]}"[^>]*>([^<]+)'
                matches = re.findall(pattern, content)
            else:
                # Поиск по тегу
                pattern = rf'<{selector}[^>]*>([^<]+)</{selector}>'
                matches = re.findall(pattern, content)
        else:
            matches = [content[:1000]]  # Первые 1000 символов
        
        return {
            "status": "success",
            "url": url,
            "selector": selector,
            "matches": matches,
            "count": len(matches)
        }
    
    async def _handle_command_execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение системной команды"""
        command = data.get("command")
        timeout = data.get("timeout", 60)
        cwd = data.get("cwd")
        
        if not command:
            raise ValueError("command is required")
        
        return await self._run_command(command, timeout=timeout, cwd=cwd)
    
    async def _handle_text_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка текста"""
        text = data.get("text", "")
        operation = data.get("operation", "count")
        
        if not text:
            raise ValueError("text is required")
        
        result = {}
        
        if operation == "count":
            result = {
                "characters": len(text),
                "words": len(text.split()),
                "lines": len(text.splitlines())
            }
        elif operation == "uppercase":
            result = {"processed_text": text.upper()}
        elif operation == "lowercase":
            result = {"processed_text": text.lower()}
        elif operation == "reverse":
            result = {"processed_text": text[::-1]}
        elif operation == "strip":
            result = {"processed_text": text.strip()}
        
        return {
            "status": "success",
            "operation": operation,
            "result": result
        }
    
    async def _handle_data_convert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Конвертация данных"""
        input_data = data.get("input_data")
        input_format = data.get("input_format", "json")
        output_format = data.get("output_format", "json")
        
        if not input_data:
            raise ValueError("input_data is required")
        
        # Простая конвертация
        if input_format == "json" and output_format == "yaml":
            import yaml
            result = yaml.dump(input_data, default_flow_style=False)
        elif input_format == "yaml" and output_format == "json":
            import yaml
            result = json.dumps(yaml.safe_load(input_data), indent=2)
        else:
            result = input_data
        
        return {
            "status": "success",
            "input_format": input_format,
            "output_format": output_format,
            "result": result
        }
    
    async def _handle_backup_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание резервной копии"""
        source_path = data.get("source_path")
        backup_path = data.get("backup_path")
        
        if not source_path:
            raise ValueError("source_path is required")
        
        source_path = Path(source_path)
        
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.workspace_path / "backups" / f"{source_path.name}_{timestamp}.tar.gz"
        
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Создание архива
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(source_path, arcname=source_path.name)
        
        return {
            "status": "success",
            "source_path": str(source_path),
            "backup_path": str(backup_path),
            "size": backup_path.stat().st_size
        }
    
    async def _handle_backup_restore(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Восстановление из резервной копии"""
        backup_path = data.get("backup_path")
        destination_path = data.get("destination_path")
        
        if not backup_path:
            raise ValueError("backup_path is required")
        
        backup_path = Path(backup_path)
        
        if not destination_path:
            destination_path = backup_path.parent / "restored"
        
        destination_path = Path(destination_path)
        destination_path.mkdir(parents=True, exist_ok=True)
        
        # Извлечение архива
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(destination_path)
        
        return {
            "status": "success",
            "backup_path": str(backup_path),
            "destination_path": str(destination_path),
            "restored": True
        }
    
    async def _handle_archive_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание архива"""
        source_path = data.get("source_path")
        archive_path = data.get("archive_path")
        archive_format = data.get("format", "zip")
        
        if not source_path:
            raise ValueError("source_path is required")
        
        source_path = Path(source_path)
        
        if not archive_path:
            archive_path = source_path.with_suffix(f".{archive_format}")
        
        archive_path = Path(archive_path)
        
        # Создание архива
        if archive_format == "zip":
            with zipfile.ZipFile(archive_path, 'w') as zipf:
                if source_path.is_file():
                    zipf.write(source_path, source_path.name)
                else:
                    for file_path in source_path.rglob('*'):
                        if file_path.is_file():
                            zipf.write(file_path, file_path.relative_to(source_path.parent))
        
        return {
            "status": "success",
            "source_path": str(source_path),
            "archive_path": str(archive_path),
            "format": archive_format,
            "size": archive_path.stat().st_size
        }
    
    async def _handle_archive_extract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение архива"""
        archive_path = data.get("archive_path")
        destination_path = data.get("destination_path")
        
        if not archive_path:
            raise ValueError("archive_path is required")
        
        archive_path = Path(archive_path)
        
        if not destination_path:
            destination_path = archive_path.parent / "extracted"
        
        destination_path = Path(destination_path)
        destination_path.mkdir(parents=True, exist_ok=True)
        
        # Извлечение архива
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(destination_path)
        elif archive_path.suffix in [".tar", ".tar.gz", ".tgz"]:
            with tarfile.open(archive_path, "r:*") as tar:
                tar.extractall(destination_path)
        
        return {
            "status": "success",
            "archive_path": str(archive_path),
            "destination_path": str(destination_path),
            "extracted": True
        }
    
    async def _handle_search_files(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Поиск файлов"""
        directory_path = data.get("directory_path", ".")
        pattern = data.get("pattern", "*")
        name_pattern = data.get("name_pattern")
        content_pattern = data.get("content_pattern")
        
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Поиск файлов
        files = list(directory_path.rglob(pattern))
        
        # Фильтрация по имени
        if name_pattern:
            import re
            name_regex = re.compile(name_pattern)
            files = [f for f in files if name_regex.search(f.name)]
        
        # Фильтрация по содержимому
        if content_pattern:
            import re
            content_regex = re.compile(content_pattern)
            matching_files = []
            
            for file_path in files:
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if content_regex.search(content):
                                matching_files.append(file_path)
                    except Exception:
                        continue
            
            files = matching_files
        
        # Информация о найденных файлах
        file_info = []
        for file_path in files:
            if file_path.is_file():
                stat = file_path.stat()
                file_info.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return {
            "status": "success",
            "directory": str(directory_path),
            "pattern": pattern,
            "files": file_info,
            "count": len(file_info)
        }
    
    async def _handle_monitor_system(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Мониторинг системы"""
        return await self.get_system_info()
    
    async def _handle_cleanup_temp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Очистка временных файлов"""
        temp_dir = self.workspace_path / "temp"
        max_age_hours = data.get("max_age_hours", 24)
        
        if not temp_dir.exists():
            return {"status": "success", "cleaned_files": 0}
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_files = 0
        
        for file_path in temp_dir.rglob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        cleaned_files += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file {file_path}: {e}")
        
        return {
            "status": "success",
            "cleaned_files": cleaned_files,
            "max_age_hours": max_age_hours
        }
    
    async def _handle_general_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка общей задачи"""
        task_description = data.get("description", "General task")
        
        # Простая обработка общей задачи
        return {
            "status": "success",
            "description": task_description,
            "result": "Task completed successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _run_command(self, command: str, timeout: int = 60, cwd: str = None) -> Dict[str, Any]:
        """Выполнение системной команды"""
        try:
            # Выполнение команды
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "status": "success",
                "command": command,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "timeout": timeout
            }
            
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "command": command,
                "error": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            return {
                "status": "error",
                "command": command,
                "error": str(e)
            }
    
    async def execute_file_operation(self, operation: str, file_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение операции с файлом"""
        operation_data = {
            "file_path": file_path,
            **data
        }
        
        return await self.execute_task(f"file_{operation}", operation_data)
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Получение информации о системе"""
        try:
            # Информация о системе
            system_info = {
                "platform": os.name,
                "system": os.uname().sysname if hasattr(os, 'uname') else "unknown",
                "release": os.uname().release if hasattr(os, 'uname') else "unknown",
                "version": os.uname().version if hasattr(os, 'uname') else "unknown",
                "machine": os.uname().machine if hasattr(os, 'uname') else "unknown",
                "processor": os.uname().nodename if hasattr(os, 'uname') else "unknown"
            }
            
            # Информация о CPU
            cpu_info = {
                "count": psutil.cpu_count(),
                "percent": psutil.cpu_percent(interval=1),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            }
            
            # Информация о памяти
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            }
            
            # Информация о диске
            disk = psutil.disk_usage('/')
            disk_info = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
            
            # Информация о сети
            network = psutil.net_io_counters()
            network_info = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            return {
                "status": "success",
                "system": system_info,
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": network_info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_available_tasks(self) -> List[Dict[str, Any]]:
        """Получение списка доступных задач"""
        tasks = []
        
        for task_type, handler in self.task_handlers.items():
            tasks.append({
                "type": task_type,
                "name": task_type.replace("_", " ").title(),
                "description": f"Execute {task_type} task"
            })
        
        return tasks
    
    async def cleanup(self):
        """Очистка ресурсов"""
        try:
            # Очистка временных файлов
            await self._handle_cleanup_temp({"max_age_hours": 0})
            
            logger.info("Task executor cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")