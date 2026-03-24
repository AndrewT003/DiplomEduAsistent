-- Міграція: Додавання поля topic до таблиці materials
-- Дата: 2026-03-23
-- Опис: Додає поле для зберігання теми/назви заняття витягнутої з документа

-- Додаємо колонку topic
ALTER TABLE materials
ADD COLUMN IF NOT EXISTS topic TEXT DEFAULT 'Навчальний матеріал';

-- Оновлюємо існуючі записи без теми
UPDATE materials
SET topic = 'Навчальний матеріал'
WHERE topic IS NULL;

-- Коментар для поля
COMMENT ON COLUMN materials.topic IS 'Тема/назва заняття витягнута з документа';
