-- ============================================
-- Инициализация PostgreSQL для бота
-- Выполняется только при первом запуске
-- ============================================

-- Включаем расширения PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Для быстрого поиска по тексту

-- Устанавливаем часовой пояс UTC
SET timezone = 'UTC';

-- Настройки производительности
ALTER DATABASE cute_bot SET random_page_cost = 1.1;
ALTER DATABASE cute_bot SET effective_cache_size = '1GB';

-- Комментарий к БД
COMMENT ON DATABASE cute_bot IS 'TelegramBotCuteForCuteV4 - Production database';

-- Вывод версии PostgreSQL
SELECT version();
