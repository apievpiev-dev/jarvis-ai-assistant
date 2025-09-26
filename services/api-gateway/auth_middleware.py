"""
Middleware аутентификации для API Gateway
Обработка JWT токенов и аутентификации пользователей
"""
import jwt
import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from passlib.context import CryptContext
from dataclasses import dataclass

from utils.logger import get_logger

logger = get_logger("auth-middleware")

@dataclass
class SecurityConfig:
    """Конфигурация безопасности"""
    secret_key: str
    jwt_expire_hours: int
    allowed_origins: list
    rate_limit_per_minute: int

class AuthMiddleware:
    """Middleware аутентификации"""
    
    def __init__(self, security_config: SecurityConfig):
        self.config = security_config
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.algorithm = "HS256"
        
        # Временное хранилище пользователей (в реальном приложении - база данных)
        self.users = {
            "admin": {
                "username": "admin",
                "password_hash": self.pwd_context.hash("admin123"),
                "role": "admin",
                "permissions": ["read", "write", "admin"]
            },
            "user": {
                "username": "user",
                "password_hash": self.pwd_context.hash("user123"),
                "role": "user",
                "permissions": ["read"]
            }
        }
        
        logger.info("Auth middleware initialized")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Хеширование пароля"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Создание JWT токена"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=self.config.jwt_expire_hours)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(to_encode, self.config.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверка JWT токена"""
        try:
            payload = jwt.decode(token, self.config.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"JWT error: {e}")
            return None
    
    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Аутентификация пользователя"""
        try:
            if username not in self.users:
                return {"success": False, "error": "Invalid username or password"}
            
            user = self.users[username]
            
            if not self.verify_password(password, user["password_hash"]):
                return {"success": False, "error": "Invalid username or password"}
            
            # Создание токена
            access_token = self.create_access_token(
                data={"sub": username, "role": user["role"], "permissions": user["permissions"]}
            )
            
            logger.info(f"User authenticated: {username}")
            
            return {
                "success": True,
                "access_token": access_token,
                "user": {
                    "username": username,
                    "role": user["role"],
                    "permissions": user["permissions"]
                }
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {"success": False, "error": "Authentication failed"}
    
    async def authenticate_request(self, request) -> Dict[str, Any]:
        """Аутентификация HTTP запроса"""
        try:
            # Получение токена из заголовка Authorization
            authorization = request.headers.get("Authorization")
            
            if not authorization:
                return {"authenticated": False, "error": "Authorization header missing"}
            
            # Проверка формата Bearer token
            if not authorization.startswith("Bearer "):
                return {"authenticated": False, "error": "Invalid authorization format"}
            
            token = authorization.split(" ")[1]
            
            # Проверка токена
            payload = self.verify_token(token)
            if not payload:
                return {"authenticated": False, "error": "Invalid or expired token"}
            
            # Получение информации о пользователе
            username = payload.get("sub")
            if not username or username not in self.users:
                return {"authenticated": False, "error": "User not found"}
            
            user = self.users[username]
            
            return {
                "authenticated": True,
                "user": {
                    "username": username,
                    "role": user["role"],
                    "permissions": user["permissions"]
                },
                "payload": payload
            }
            
        except Exception as e:
            logger.error(f"Request authentication error: {e}")
            return {"authenticated": False, "error": "Authentication error"}
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Обновление токена"""
        try:
            # Проверка refresh токена
            payload = self.verify_token(refresh_token)
            if not payload:
                return {"success": False, "error": "Invalid refresh token"}
            
            # Проверка типа токена
            if payload.get("type") != "refresh":
                return {"success": False, "error": "Invalid token type"}
            
            username = payload.get("sub")
            if not username or username not in self.users:
                return {"success": False, "error": "User not found"}
            
            user = self.users[username]
            
            # Создание нового access токена
            access_token = self.create_access_token(
                data={"sub": username, "role": user["role"], "permissions": user["permissions"]}
            )
            
            logger.info(f"Token refreshed for user: {username}")
            
            return {
                "success": True,
                "access_token": access_token
            }
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return {"success": False, "error": "Token refresh failed"}
    
    def check_permission(self, user: Dict[str, Any], required_permission: str) -> bool:
        """Проверка разрешения пользователя"""
        try:
            user_permissions = user.get("permissions", [])
            return required_permission in user_permissions or "admin" in user_permissions
            
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False
    
    def check_role(self, user: Dict[str, Any], required_role: str) -> bool:
        """Проверка роли пользователя"""
        try:
            user_role = user.get("role")
            return user_role == required_role or user_role == "admin"
            
        except Exception as e:
            logger.error(f"Role check error: {e}")
            return False
    
    async def create_user(self, username: str, password: str, role: str = "user", permissions: list = None) -> Dict[str, Any]:
        """Создание нового пользователя"""
        try:
            if username in self.users:
                return {"success": False, "error": "User already exists"}
            
            if permissions is None:
                permissions = ["read"] if role == "user" else ["read", "write"]
            
            password_hash = self.get_password_hash(password)
            
            self.users[username] = {
                "username": username,
                "password_hash": password_hash,
                "role": role,
                "permissions": permissions
            }
            
            logger.info(f"User created: {username} with role: {role}")
            
            return {
                "success": True,
                "user": {
                    "username": username,
                    "role": role,
                    "permissions": permissions
                }
            }
            
        except Exception as e:
            logger.error(f"User creation error: {e}")
            return {"success": False, "error": "User creation failed"}
    
    async def update_user(self, username: str, **kwargs) -> Dict[str, Any]:
        """Обновление пользователя"""
        try:
            if username not in self.users:
                return {"success": False, "error": "User not found"}
            
            user = self.users[username]
            
            # Обновление полей
            if "password" in kwargs:
                user["password_hash"] = self.get_password_hash(kwargs["password"])
            
            if "role" in kwargs:
                user["role"] = kwargs["role"]
            
            if "permissions" in kwargs:
                user["permissions"] = kwargs["permissions"]
            
            logger.info(f"User updated: {username}")
            
            return {
                "success": True,
                "user": {
                    "username": username,
                    "role": user["role"],
                    "permissions": user["permissions"]
                }
            }
            
        except Exception as e:
            logger.error(f"User update error: {e}")
            return {"success": False, "error": "User update failed"}
    
    async def delete_user(self, username: str) -> Dict[str, Any]:
        """Удаление пользователя"""
        try:
            if username not in self.users:
                return {"success": False, "error": "User not found"}
            
            del self.users[username]
            
            logger.info(f"User deleted: {username}")
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"User deletion error: {e}")
            return {"success": False, "error": "User deletion failed"}
    
    def get_all_users(self) -> Dict[str, Dict[str, Any]]:
        """Получение всех пользователей (без паролей)"""
        users = {}
        for username, user_data in self.users.items():
            users[username] = {
                "username": user_data["username"],
                "role": user_data["role"],
                "permissions": user_data["permissions"]
            }
        return users
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Получение статистики пользователей"""
        total_users = len(self.users)
        admin_users = sum(1 for user in self.users.values() if user["role"] == "admin")
        regular_users = total_users - admin_users
        
        return {
            "total_users": total_users,
            "admin_users": admin_users,
            "regular_users": regular_users
        }