-- ============================================================
-- МІГРАЦІЯ: Додавання авторизації до існуючих таблиць
-- ============================================================
-- Виконати в Supabase SQL Editor:
-- https://yaeavofxswjkcywnkfvv.supabase.co/project/default/sql/new

-- ============================================================
-- 1. Додати user_id до існуючих таблиць
-- ============================================================

-- Таблиця documents
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Таблиця materials
ALTER TABLE materials
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Таблиця validation_reports
ALTER TABLE validation_reports
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Створити індекси для швидкого пошуку по user_id
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_materials_user_id ON materials(user_id);
CREATE INDEX IF NOT EXISTS idx_validation_reports_user_id ON validation_reports(user_id);

-- ============================================================
-- 2. Налаштувати Row Level Security (RLS)
-- ============================================================

-- ==================== DOCUMENTS ====================
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Політика: користувач бачить тільки свої документи
DROP POLICY IF EXISTS "Users can view own documents" ON documents;
CREATE POLICY "Users can view own documents"
ON documents FOR SELECT
USING (auth.uid() = user_id);

-- Політика: користувач може створювати свої документи
DROP POLICY IF EXISTS "Users can insert own documents" ON documents;
CREATE POLICY "Users can insert own documents"
ON documents FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Політика: користувач може оновлювати свої документи
DROP POLICY IF EXISTS "Users can update own documents" ON documents;
CREATE POLICY "Users can update own documents"
ON documents FOR UPDATE
USING (auth.uid() = user_id);

-- Політика: користувач може видаляти свої документи
DROP POLICY IF EXISTS "Users can delete own documents" ON documents;
CREATE POLICY "Users can delete own documents"
ON documents FOR DELETE
USING (auth.uid() = user_id);

-- ==================== MATERIALS ====================
ALTER TABLE materials ENABLE ROW LEVEL SECURITY;

-- Політика: користувач бачить тільки свої матеріали
DROP POLICY IF EXISTS "Users can view own materials" ON materials;
CREATE POLICY "Users can view own materials"
ON materials FOR SELECT
USING (auth.uid() = user_id);

-- Політика: користувач може створювати свої матеріали
DROP POLICY IF EXISTS "Users can insert own materials" ON materials;
CREATE POLICY "Users can insert own materials"
ON materials FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Політика: користувач може оновлювати свої матеріали
DROP POLICY IF EXISTS "Users can update own materials" ON materials;
CREATE POLICY "Users can update own materials"
ON materials FOR UPDATE
USING (auth.uid() = user_id);

-- Політика: користувач може видаляти свої матеріали
DROP POLICY IF EXISTS "Users can delete own materials" ON materials;
CREATE POLICY "Users can delete own materials"
ON materials FOR DELETE
USING (auth.uid() = user_id);

-- ==================== VALIDATION_REPORTS ====================
ALTER TABLE validation_reports ENABLE ROW LEVEL SECURITY;

-- Політика: користувач бачить тільки свої звіти
DROP POLICY IF EXISTS "Users can view own reports" ON validation_reports;
CREATE POLICY "Users can view own reports"
ON validation_reports FOR SELECT
USING (auth.uid() = user_id);

-- Політика: користувач може створювати свої звіти
DROP POLICY IF EXISTS "Users can insert own reports" ON validation_reports;
CREATE POLICY "Users can insert own reports"
ON validation_reports FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Політика: користувач може оновлювати свої звіти
DROP POLICY IF EXISTS "Users can update own reports" ON validation_reports;
CREATE POLICY "Users can update own reports"
ON validation_reports FOR UPDATE
USING (auth.uid() = user_id);

-- Політика: користувач може видаляти свої звіти
DROP POLICY IF EXISTS "Users can delete own reports" ON validation_reports;
CREATE POLICY "Users can delete own reports"
ON validation_reports FOR DELETE
USING (auth.uid() = user_id);

-- ============================================================
-- 3. Створити таблицю профілів користувачів (опціонально)
-- ============================================================

-- Таблиця для додаткової інформації про користувачів
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT,
  avatar_url TEXT,
  university TEXT,          -- Університет
  faculty TEXT,             -- Факультет
  specialty TEXT,           -- Спеціальність
  student_group TEXT,       -- Група
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS для profiles
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Політика: користувач бачить тільки свій профіль
DROP POLICY IF EXISTS "Users can view own profile" ON user_profiles;
CREATE POLICY "Users can view own profile"
ON user_profiles FOR SELECT
USING (auth.uid() = id);

-- Політика: користувач може оновлювати свій профіль
DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles;
CREATE POLICY "Users can update own profile"
ON user_profiles FOR UPDATE
USING (auth.uid() = id);

-- Політика: користувач може вставити свій профіль
DROP POLICY IF EXISTS "Users can insert own profile" ON user_profiles;
CREATE POLICY "Users can insert own profile"
ON user_profiles FOR INSERT
WITH CHECK (auth.uid() = id);

-- ============================================================
-- 4. Автоматично створювати профіль при реєстрації
-- ============================================================

-- Функція для створення профілю
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_profiles (id, full_name)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email)
  )
  ON CONFLICT (id) DO NOTHING;  -- Якщо вже існує - пропустити
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Тригер для автоматичного створення профілю
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- 5. Функція для оновлення updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Тригер для user_profiles
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================
-- 6. (Опціонально) Таблиця метрик витягування правил - додати user_id
-- ============================================================

-- Якщо у тебе є таблиця extraction_metrics
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'extraction_metrics'
  ) THEN
    -- Додати user_id якщо таблиця існує
    ALTER TABLE extraction_metrics
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

    CREATE INDEX IF NOT EXISTS idx_extraction_metrics_user_id ON extraction_metrics(user_id);

    -- RLS
    ALTER TABLE extraction_metrics ENABLE ROW LEVEL SECURITY;

    DROP POLICY IF EXISTS "Users can view own metrics" ON extraction_metrics;
    CREATE POLICY "Users can view own metrics"
    ON extraction_metrics FOR SELECT
    USING (auth.uid() = user_id);
  END IF;
END $$;

-- ============================================================
-- 7. Перевірка успішності міграції
-- ============================================================

-- Перевірити що всі таблиці мають user_id
SELECT
  table_name,
  column_name,
  data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND column_name = 'user_id'
ORDER BY table_name;

-- Перевірити що RLS увімкнено
SELECT
  schemaname,
  tablename,
  rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('documents', 'materials', 'validation_reports', 'user_profiles')
ORDER BY tablename;

-- Перевірити політики RLS
SELECT
  schemaname,
  tablename,
  policyname,
  cmd
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- ============================================================
-- ГОТОВО! ✅
-- ============================================================
-- Тепер:
-- 1. Увімкни Email Auth в Supabase Dashboard
-- 2. Додай SUPABASE_SERVICE_KEY і SUPABASE_JWT_SECRET в .env
-- 3. Встанови залежності: pip install PyJWT cryptography
-- 4. Запусти бекенд: uvicorn main:app --reload
-- 5. Протестуй /auth/register та /auth/login
-- ============================================================
