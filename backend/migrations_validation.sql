-- Міграції для системи валідації документів
-- Виконати в Supabase SQL Editor

-- 1. Додати колонку document_type до таблиці documents
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS document_type VARCHAR(50) DEFAULT 'user';

-- Оновити існуючі записи (якщо потрібно)
UPDATE documents
SET document_type = 'user'
WHERE document_type IS NULL;

-- Створити індекс для document_type
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);

-- 2. Створити таблицю validation_reports
CREATE TABLE IF NOT EXISTS validation_reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  regulatory_documents JSONB NOT NULL,
  validation_result JSONB NOT NULL,
  status VARCHAR(20) DEFAULT 'completed',
  created_at TIMESTAMP DEFAULT NOW()
);

-- Створити індекси для швидкого пошуку
CREATE INDEX IF NOT EXISTS idx_validation_user_doc ON validation_reports(user_document_id);
CREATE INDEX IF NOT EXISTS idx_validation_created_at ON validation_reports(created_at DESC);

-- 3. Додати коментарі до таблиць та колонок
COMMENT ON TABLE validation_reports IS 'Звіти валідації користувацьких документів проти нормативних';
COMMENT ON COLUMN documents.document_type IS 'Тип документа: user (користувацький) або regulatory (нормативний)';
COMMENT ON COLUMN validation_reports.user_document_id IS 'ID користувацького документа, який валідується';
COMMENT ON COLUMN validation_reports.regulatory_documents IS 'Масив нормативних документів використаних для валідації';
COMMENT ON COLUMN validation_reports.validation_result IS 'JSON результат валідації з issues, summary, compliance';

-- 4. (Опціонально) Створити view для швидкого доступу до останніх звітів
CREATE OR REPLACE VIEW latest_validation_reports AS
SELECT DISTINCT ON (user_document_id)
  vr.id,
  vr.user_document_id,
  d.filename as document_name,
  vr.validation_result,
  vr.regulatory_documents,
  vr.created_at
FROM validation_reports vr
JOIN documents d ON vr.user_document_id = d.id
ORDER BY vr.user_document_id, vr.created_at DESC;

COMMENT ON VIEW latest_validation_reports IS 'Останні звіти валідації для кожного документа';

-- 5. Додати колонку для зберігання витягнутих правил (економія токенів)
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS extracted_rules JSONB DEFAULT NULL;

COMMENT ON COLUMN documents.extracted_rules IS 'Витягнуті правила з нормативного документа (кешовані для економії токенів)';

-- Індекс видалено, бо JSONB може бути занадто великим для btree індексу
-- Пошук завжди відбувається по id (primary key), тому додатковий індекс не потрібен

-- 6. Додати колонку для хешу файлу (економія токенів через дедуплікацію)
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64) DEFAULT NULL;

COMMENT ON COLUMN documents.file_hash IS 'SHA256 хеш файлу для виявлення дублікатів';

-- Створити індекс для швидкого пошуку по хешу
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash) WHERE file_hash IS NOT NULL;

-- 7. Додати колонку для статусу витягування правил (background task)
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS extraction_status VARCHAR(20) DEFAULT NULL;

COMMENT ON COLUMN documents.extraction_status IS 'Статус витягування правил: pending/extracting/completed/failed';

-- Можливі значення: pending (в черзі), extracting (в процесі), completed (завершено), failed (помилка)

-- 7.1. Додати колонку для категорії нормативного документу
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS regulatory_category VARCHAR(50) DEFAULT NULL;

COMMENT ON COLUMN documents.regulatory_category IS 'Категорія нормативного документу: content (зміст), formatting (оформлення), structure (структура), references (посилання)';

-- Створити індекс для швидкого пошуку по категорії
CREATE INDEX IF NOT EXISTS idx_documents_regulatory_category ON documents(regulatory_category) WHERE regulatory_category IS NOT NULL;

-- Додати колонку для тегів (множинні категорії)
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT NULL;

COMMENT ON COLUMN documents.tags IS 'Теги для класифікації документів (масив рядків)';

CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN(tags) WHERE tags IS NOT NULL;

-- 8. Створити таблицю для метрик витягування правил
CREATE TABLE IF NOT EXISTS extraction_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  started_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  duration_seconds FLOAT,
  total_chunks INT,
  chunks_processed INT,
  rules_extracted INT,
  rules_after_deduplication INT,
  rules_after_quality_filter INT,
  model_name VARCHAR(100),
  success BOOLEAN DEFAULT true,
  error_message TEXT
);

-- Створити індекси
CREATE INDEX IF NOT EXISTS idx_extraction_metrics_document ON extraction_metrics(document_id);
CREATE INDEX IF NOT EXISTS idx_extraction_metrics_date ON extraction_metrics(completed_at DESC);

COMMENT ON TABLE extraction_metrics IS 'Метрики процесу витягування правил для аналізу та оптимізації';

-- Перевірка структури
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'documents' AND column_name = 'document_type';

-- SELECT table_name, column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'validation_reports'
-- ORDER BY ordinal_position;
