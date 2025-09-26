-- Jarvis AI Assistant Database Schema

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Таблица пользователей
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    settings JSONB DEFAULT '{}'
);

-- Таблица сессий
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Таблица команд
CREATE TABLE commands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    command_text TEXT NOT NULL,
    command_type VARCHAR(50) NOT NULL, -- 'voice', 'text', 'system'
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Таблица задач
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    command_id UUID REFERENCES commands(id) ON DELETE CASCADE,
    task_type VARCHAR(100) NOT NULL,
    task_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Таблица обучения
CREATE TABLE learning_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interaction_type VARCHAR(50) NOT NULL, -- 'command', 'feedback', 'reflection'
    input_data JSONB NOT NULL,
    output_data JSONB,
    feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5),
    learning_vector vector(384), -- Для векторного поиска
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица памяти агента
CREATE TABLE agent_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_type VARCHAR(50) NOT NULL, -- 'fact', 'skill', 'preference', 'context'
    content TEXT NOT NULL,
    importance_score FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Таблица метрик
CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_labels JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица логов
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    log_level VARCHAR(20) NOT NULL, -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    message TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для оптимизации
CREATE INDEX idx_commands_user_id ON commands(user_id);
CREATE INDEX idx_commands_created_at ON commands(created_at);
CREATE INDEX idx_commands_status ON commands(status);
CREATE INDEX idx_tasks_command_id ON tasks(command_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_learning_data_type ON learning_data(interaction_type);
CREATE INDEX idx_learning_data_created_at ON learning_data(created_at);
CREATE INDEX idx_agent_memory_type ON agent_memory(memory_type);
CREATE INDEX idx_agent_memory_importance ON agent_memory(importance_score);
CREATE INDEX idx_metrics_service_timestamp ON metrics(service_name, timestamp);
CREATE INDEX idx_logs_service_level ON logs(service_name, log_level);
CREATE INDEX idx_logs_timestamp ON logs(timestamp);

-- Векторный индекс для поиска по сходству
CREATE INDEX idx_learning_vector ON learning_data USING ivfflat (learning_vector vector_cosine_ops);

-- Триггеры для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Функция для очистки старых данных
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Удаление старых сессий
    DELETE FROM sessions WHERE expires_at < NOW() - INTERVAL '30 days';
    
    -- Удаление старых логов
    DELETE FROM logs WHERE timestamp < NOW() - INTERVAL '90 days';
    
    -- Удаление старых метрик
    DELETE FROM metrics WHERE timestamp < NOW() - INTERVAL '30 days';
    
    -- Удаление истекшей памяти
    DELETE FROM agent_memory WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Создание пользователя по умолчанию
INSERT INTO users (username, email, settings) VALUES 
('jarvis', 'jarvis@localhost', '{"voice_enabled": true, "language": "ru", "auto_learning": true}');

-- Создание индексов для полнотекстового поиска
CREATE INDEX idx_commands_text_search ON commands USING gin(to_tsvector('russian', command_text));
CREATE INDEX idx_agent_memory_content_search ON agent_memory USING gin(to_tsvector('russian', content));