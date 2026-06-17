import json
import time
import os
from datetime import datetime
from typing import Dict, List
from config import supabase, supabase_admin, groq_client
from rag_engine import get_all_chunks_for_document, search_regulatory_context

# Імпортуємо спеціалізовані валідатори
try:
    from formatting_validator import FormattingValidator, StructureValidator, ReferencesValidator
    SPECIALIZED_VALIDATORS_AVAILABLE = True
except ImportError:
    print("⚠️ Спеціалізовані валідатори недоступні (потрібен python-docx)")
    SPECIALIZED_VALIDATORS_AVAILABLE = False


def retry_on_api_error(max_attempts=3, delay=1.0, backoff=2.0):
    """Decorator для повторних спроб при помилках API"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay

            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e)

                    # Якщо помилка rate limit або тимчасова проблема
                    if any(keyword in error_msg.lower() for keyword in ['rate_limit', 'timeout', '5', 'temporarily']):
                        if attempt < max_attempts:
                            print(f"⚠️ Спроба {attempt}/{max_attempts} не вдалася: {error_msg}")
                            print(f"⏳ Очікування {current_delay:.1f}с перед наступною спробою...")
                            time.sleep(current_delay)
                            current_delay *= backoff
                            attempt += 1
                        else:
                            print(f"❌ Всі {max_attempts} спроб вичерпано")
                            raise
                    else:
                        # Для інших помилок не ретраїмо
                        raise

            return None
        return wrapper
    return decorator


# Кеш для витягнутих правил (щоб не викликати LLM повторно)
_rules_cache = {}


def save_extraction_metrics(doc_id: str, metrics: Dict):
    """Зберігає метрики витягування правил у БД"""
    try:
        supabase_admin.table("extraction_metrics").insert(metrics).execute()
        print(f"📊 Метрики збережено для документу {doc_id}")
    except Exception as e:
        print(f"⚠️ Не вдалося зберегти метрики: {e}")


def validate_rule_quality(rule: Dict) -> bool:
    """Перевіряє якість витягнутого правила"""

    # Перевіряємо обов'язкові поля
    requirement = rule.get("requirement", "").strip()
    check_criteria = rule.get("check_criteria", "").strip()
    category = rule.get("category", "").strip()

    # Фільтруємо порожні правила
    if not requirement or not check_criteria or not category:
        return False

    # Фільтруємо занадто короткі правила
    if len(requirement) < 20 or len(check_criteria) < 15:
        return False

    # Фільтруємо загальні фрази (низька специфічність)
    generic_phrases = [
        "документ має",
        "слід дотримуватись",
        "необхідно враховувати",
        "рекомендується",
        "має відповідати",
        "загальна відповідність",
        "general compliance",
        "should comply",
        "must follow"
    ]

    requirement_lower = requirement.lower()
    criteria_lower = check_criteria.lower()

    for phrase in generic_phrases:
        if phrase in requirement_lower and len(requirement) < 60:
            # Якщо фраза загальна І правило коротке - відкидаємо
            return False
        if phrase in criteria_lower and len(check_criteria) < 40:
            return False

    return True


@retry_on_api_error(max_attempts=3, delay=2.0, backoff=2.0)
def extract_rules_from_chunks(
    chunks: List[Dict],
    regulatory_doc_name: str,
    regulatory_category: str = None,
    start_idx: int = 0,
    chunk_limit: int = 15
) -> List[Dict]:
    """Витягує правила з певної частини чанків (з автоматичним retry при помилках API)

    Args:
        regulatory_category: content/formatting/structure/references - впливає на промпт
    """
    selected_chunks = chunks[start_idx:start_idx + chunk_limit]
    if not selected_chunks:
        return []

    context = "\n\n".join([chunk["text"] for chunk in selected_chunks])
    print(f"📝 Частина {start_idx//chunk_limit + 1}: {len(selected_chunks)} чанків, {len(context)} символів")

    # Різні промпти залежно від категорії
    if regulatory_category == "formatting":
        # Промпт для оформлення (ДСТУ, стандарти)
        prompt = f"""Ти — експерт з технічних стандартів оформлення документів. Витягни найважливіші вимоги до ОФОРМЛЕННЯ з цього фрагменту (максимум 10-15 вимог).

ФОКУС на технічних параметрах:
- Шрифти (тип, розмір, накреслення)
- Відступи та інтервали (рядки, абзаци, поля)
- Розміри сторінок та полів
- Нумерація та позначення
- Таблиці, рисунки, формули
- Кольори та графіка

Для кожної вимоги вкажи:
1. category - ЗАВЖДИ "formatting"
2. section - розділ стандарту (якщо вказаний)
3. requirement - технічний параметр (наприклад: "Шрифт основного тексту Times New Roman 14pt")
4. check_criteria - як перевірити (наприклад: "Перевірити шрифт та розмір основного тексту")

ВАЖЛИВО:
- Відповідай ТІЛЬКИ у JSON форматі
- ОБОВ'ЯЗКОВО закрий всі дужки та лапки!
- Формат: [{{"category": "formatting", "section": "...", "requirement": "...", "check_criteria": "..."}}]

Документ "{regulatory_doc_name}":
{context}"""

    elif regulatory_category == "content":
        # Промпт для змісту (закони, положення)
        prompt = f"""Ти — аналітик нормативних документів. Витягни найважливіші вимоги до ЗМІСТУ документа (максимум 10-15 вимог).

ФОКУС на змістовних вимогах:
- Які розділи/пункти мають ОБОВ'ЯЗКОВО бути
- Яка інформація має бути включена
- Які дані/показники мають бути наведені
- Які теми мають бути розкриті

Для кожної вимоги вкажи:
1. category - ЗАВЖДИ "content"
2. section - розділ документа (якщо вказаний)
3. requirement - змістовна вимога (що має бути)
4. check_criteria - як перевірити наявність

ВАЖЛИВО:
- Відповідай ТІЛЬКИ у JSON форматі
- ОБОВ'ЯЗКОВО закрий всі дужки та лапки!
- Формат: [{{"category": "content", "section": "...", "requirement": "...", "check_criteria": "..."}}]

Документ "{regulatory_doc_name}":
{context}"""

    else:
        # Універсальний промпт
        prompt = f"""Ти — аналітик нормативних документів. Витягни найважливіші вимоги з цього фрагменту документа (максимум 10-15 вимог).

Для кожної вимоги вкажи:
1. category - категорію (formatting/structure/content/references)
2. section - розділ документа (якщо вказаний)
3. requirement - КОРОТКО опиши вимогу (максимум 100 символів)
4. check_criteria - КОРОТКО вкажи критерій перевірки (максимум 100 символів)

ВАЖЛИВО:
- Відповідай ТІЛЬКИ у JSON форматі (масив об'єктів)
- ОБОВ'ЯЗКОВО закрий всі дужки та лапки!
- Формат: [{{"category": "...", "section": "...", "requirement": "...", "check_criteria": "..."}}]

Документ "{regulatory_doc_name}":
{context}"""

    try:
        print(f"🤖 Відправляю запит до LLM...")
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Ти експерт з аналізу нормативних документів. Відповідай тільки валідним JSON масивом. ЗАВЖДИ закривай всі дужки та лапки!"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4500
        )
        print(f"✅ Отримано відповідь від LLM")

        content = response.choices[0].message.content.strip()

        # Видаляємо markdown форматування
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # Витягуємо тільки JSON масив (від [ до ]) - ігноруємо текст після
        if content.startswith("["):
            bracket_count = 0
            json_end = -1
            for i, char in enumerate(content):
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        json_end = i + 1
                        break
            if json_end > 0 and json_end < len(content):
                original_len = len(content)
                content = content[:json_end]
                print(f"🔧 Обрізано зайвий текст: {original_len} → {json_end} символів")

        # Спроба парсингу JSON з автовиправленням
        try:
            rules = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"⚠️ Невалідний JSON, спроба автовиправлення...")
            if not content.endswith("]"):
                content = content.rstrip(",") + "]"
                try:
                    rules = json.loads(content)
                    print(f"✅ JSON виправлено автоматично")
                except:
                    last_valid_bracket = content.rfind("}")
                    if last_valid_bracket > 0:
                        content = content[:last_valid_bracket + 1] + "]"
                        try:
                            rules = json.loads(content)
                            print(f"✅ JSON виправлено (обрізано до останнього валідного об'єкта)")
                        except:
                            raise e
                    else:
                        raise e
            else:
                raise e

        print(f"📊 Витягнуто {len(rules)} правил з частини {start_idx//chunk_limit + 1}")
        return rules

    except Exception as e:
        import traceback
        print(f"❌ Помилка при витягуванні правил з частини {start_idx//chunk_limit + 1}: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return []


def extract_regulatory_rules(regulatory_doc_id: str, regulatory_doc_name: str) -> List[Dict]:
    """Витягує структуровані правила з нормативного документа через LLM"""

    print(f"🚀 extract_regulatory_rules викликано для: {regulatory_doc_name} (id: {regulatory_doc_id})")

    # Перевіряємо кеш у пам'яті
    if regulatory_doc_id in _rules_cache:
        print(f"✅ Використовую закешовані правила з пам'яті для {regulatory_doc_name} ({len(_rules_cache[regulatory_doc_id])} правил)")
        return _rules_cache[regulatory_doc_id]

    # Перевіряємо чи є правила в БД та отримуємо категорію
    print(f"🔍 Перевіряю БД на наявність правил для {regulatory_doc_name}...")
    doc_result = supabase_admin.table("documents").select("extracted_rules, regulatory_category").eq("id", regulatory_doc_id).execute()

    regulatory_category = None
    if doc_result.data:
        regulatory_category = doc_result.data[0].get("regulatory_category")
        print(f"📂 Категорія документу: {regulatory_category or 'не вказана'}")

        if doc_result.data[0].get("extracted_rules"):
            rules = doc_result.data[0]["extracted_rules"]
            _rules_cache[regulatory_doc_id] = rules  # Кешуємо у пам'яті
            print(f"✅ Завантажено правила з БД для {regulatory_doc_name} ({len(rules)} правил, 0 токенів!)")
            return rules

    print(f"🔄 Правил у БД немає. Витягую правила з нормативу через LLM: {regulatory_doc_name}")

    # Початок збору метрик
    start_time = datetime.now()
    metrics = {
        "document_id": regulatory_doc_id,
        "started_at": start_time.isoformat(),
        "model_name": "llama-3.1-8b-instant",
        "success": False
    }

    # Отримуємо всі чанки нормативного документа
    print(f"📄 Отримую чанки документа з векторної БД...")
    chunks = get_all_chunks_for_document(regulatory_doc_id)
    total_chunks = len(chunks)
    print(f"📄 Отримано {total_chunks} чанків")

    # === РОЗГАЛУЖЕННЯ: структуровані правила для форматування ===
    if regulatory_category == "formatting":
        print(f"🎨 Категорія 'formatting' - використовую структуроване витягування правил")

        # Об'єднуємо всі чанки в один текст
        full_text = "\n".join([chunk["text"] for chunk in chunks])
        print(f"📝 Об'єднано текст: {len(full_text)} символів")

        # Використовуємо спеціалізоване витягування структурованих правил
        from formatting_rules_extractor import extract_formatting_rules_structured

        all_rules = extract_formatting_rules_structured(
            text=full_text,
            document_name=regulatory_doc_name
        )

        print(f"✅ Витягнуто {len(all_rules)} структурованих правил форматування")

        # Для структурованих правил не потрібна дедуплікація, вони вже унікальні
        unique_rules = all_rules

    else:
        # === ТЕКСТОВІ ПРАВИЛА для інших категорій (content, structure, references) ===
        print(f"📚 Категорія '{regulatory_category or 'general'}' - використовую текстове витягування правил")

        # Обробляємо документ частинами по 15 чанків
        chunk_size = 15
        all_rules = []
        num_parts = (total_chunks + chunk_size - 1) // chunk_size  # Округлення вгору

        print(f"📚 Розділяю документ на {num_parts} частин по {chunk_size} чанків")

        for part_idx in range(num_parts):
            start_idx = part_idx * chunk_size
            print(f"\n--- Частина {part_idx + 1}/{num_parts} ---")

            # Додаємо затримку між запитами (крім першого) щоб не перевищити rate limit
            if part_idx > 0:
                delay_seconds = 2
                print(f"⏳ Затримка {delay_seconds}с перед наступним запитом...")
                time.sleep(delay_seconds)

            part_rules = extract_rules_from_chunks(
                chunks,
                regulatory_doc_name,
                regulatory_category,  # Передаємо категорію для адаптації промпту
                start_idx,
                chunk_size
            )
            if part_rules:
                all_rules.extend(part_rules)
                print(f"✅ Додано {len(part_rules)} правил з частини {part_idx + 1}")

        print(f"\n📊 Всього витягнуто {len(all_rules)} правил з усіх частин")

        # Дедуплікація правил (видаляємо однакові)
        unique_rules = []
        seen = set()
        for rule in all_rules:
            # Створюємо унікальний ключ на основі вимоги та критерію
            key = (rule.get("requirement", ""), rule.get("check_criteria", ""))
            if key not in seen and key != ("", ""):  # Пропускаємо порожні
                seen.add(key)
                unique_rules.append(rule)

        if len(unique_rules) < len(all_rules):
            print(f"🧹 Видалено {len(all_rules) - len(unique_rules)} дублікатів правил")

    print(f"📊 Унікальних правил після дедуплікації: {len(unique_rules)}")

    # Валідація якості правил (фільтруємо погані)
    quality_rules = []
    for rule in unique_rules:
        if validate_rule_quality(rule):
            quality_rules.append(rule)

    if len(quality_rules) < len(unique_rules):
        print(f"🎯 Відфільтровано {len(unique_rules) - len(quality_rules)} низькоякісних правил")

    rules = quality_rules
    print(f"✅ Високоякісних правил після валідації: {len(rules)}")

    # Зберігаємо в БД для майбутнього використання (економія токенів!)
    try:
        print(f"💾 Зберігаю правила в БД...")
        supabase_admin.table("documents").update({
            "extracted_rules": rules
        }).eq("id", regulatory_doc_id).execute()
        print(f"✅ Витягнуто {len(rules)} правил з {regulatory_doc_name} та збережено в БД")
    except Exception as e:
        import traceback
        print(f"⚠️ Не вдалося зберегти правила в БД: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")

    # Кешуємо у пам'яті
    _rules_cache[regulatory_doc_id] = rules
    print(f"💾 Правила закешовано у пам'яті")

    # Зберігаємо метрики
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    metrics.update({
        "completed_at": end_time.isoformat(),
        "duration_seconds": duration,
        "total_chunks": total_chunks,
        "chunks_processed": len(all_rules),  # Кількість оброблених чанків (через num_parts * chunk_size)
        "rules_extracted": len(all_rules),
        "rules_after_deduplication": len(unique_rules),
        "rules_after_quality_filter": len(rules),
        "success": True
    })

    save_extraction_metrics(regulatory_doc_id, metrics)

    return rules


def check_compliance_batch(
    user_text: str,
    rules_batch: List[Dict],
    reg_doc: Dict,
    sections_in_batch: set,
    batch_number: int = 1
) -> List[Dict]:
    """Перевіряє відповідність документа групі правил ОДНИМ запитом (BATCH)

    Args:
        user_text: Текст користувацького документа
        rules_batch: Група правил для перевірки (5-8 правил)
        reg_doc: Інформація про нормативний документ
        sections_in_batch: Розділи документа в цій частині
        batch_number: Номер батчу для логування

    Returns:
        Список знайдених проблем
    """

    if not rules_batch:
        return []

    # Формуємо JSON з правилами
    rules_json = []
    for idx, rule in enumerate(rules_batch):
        rules_json.append({
            "rule_id": idx,
            "category": rule.get("category", "N/A"),
            "section": rule.get("section", "N/A"),
            "requirement": rule.get("requirement", ""),
            "check_criteria": rule.get("check_criteria", "")
        })

    rules_str = json.dumps(rules_json, ensure_ascii=False, indent=2)

    prompt = f"""Перевір користувацький документ на відповідність {len(rules_batch)} вимогам з нормативу "{reg_doc['filename']}".

ВИМОГИ ДЛЯ ПЕРЕВІРКИ:
{rules_str}

КОРИСТУВАЦЬКИЙ ДОКУМЕНТ З ФОРМАТУВАННЯМ:
{user_text[:4500]}

Для КОЖНОЇ вимоги (rule_id від 0 до {len(rules_batch)-1}) визнач чи є порушення.

Відповідай МАСИВОМ JSON об'єктів (для кожного rule_id):
[
  {{
    "rule_id": 0,
    "has_issue": true/false,
    "severity": "critical|major|minor|info",
    "description": "Детальний опис проблеми",
    "user_document_section": "Розділ де знайдено проблему",
    "fragment": "Фрагмент з проблемою (макс 150 символів)",
    "recommendation": "Як виправити"
  }},
  {{
    "rule_id": 1,
    "has_issue": false
  }},
  ...
]

ВАЖЛИВО:
- Відповідай ТІЛЬКИ валідним JSON масивом
- Для КОЖНОГО rule_id має бути об'єкт
- Якщо порушення немає: {{"rule_id": N, "has_issue": false}}
- Якщо є порушення: вкажи всі поля

Відповідай JSON масивом:"""

    try:
        print(f"  🔍 Batch {batch_number}: перевіряю {len(rules_batch)} правил одним запитом...")

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "Ти експерт з валідації документів. Аналізуй текст та форматування. Відповідай ТІЛЬКИ валідним JSON масивом. Для кожного rule_id поверни об'єкт."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=3500  # Більше токенів для групової валідації
        )

        content = response.choices[0].message.content.strip()

        # Очищаємо markdown
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # Парсимо JSON
        results = json.loads(content)

        if not isinstance(results, list):
            print(f"  ⚠️ Очікувався масив, отримано: {type(results)}")
            return []

        # Обробляємо результати
        issues = []
        for result in results:
            if not isinstance(result, dict):
                continue

            rule_id = result.get("rule_id")
            if rule_id is None or rule_id >= len(rules_batch):
                continue

            if result.get("has_issue"):
                rule = rules_batch[rule_id]

                # Визначаємо розділ користувацького документа
                user_section = result.get("user_document_section", "")
                if not user_section and sections_in_batch:
                    user_section = list(sections_in_batch)[0]

                issues.append({
                    "severity": result.get("severity", "minor"),
                    "category": rule.get("category", "N/A"),
                    "regulatory_doc_id": reg_doc["id"],
                    "regulatory_doc_name": reg_doc["filename"],
                    "regulatory_section": rule.get("section", "N/A"),
                    "user_document_section": user_section,
                    "description": result.get("description", "Виявлено невідповідність"),
                    "user_doc_fragment": result.get("fragment", "")[:200],
                    "recommendation": result.get("recommendation", "Перевірте документ на відповідність нормативу")
                })

        print(f"  ✅ Batch {batch_number}: знайдено {len(issues)} проблем")
        return issues

    except json.JSONDecodeError as e:
        print(f"  ❌ Помилка парсингу JSON у batch {batch_number}: {e}")
        print(f"  📄 Відповідь LLM: {content[:200]}...")
        return []
    except Exception as e:
        print(f"  ❌ Помилка при batch-валідації {batch_number}: {e}")
        import traceback
        print(f"  🔍 Traceback: {traceback.format_exc()}")
        return []


def check_compliance_for_chunk_batch(
    user_chunks: List[Dict],
    rules: List[Dict],
    reg_doc: Dict,
    start_chunk_idx: int = 0,
    chunk_limit: int = 40,
    start_rule_idx: int = 0,
    rule_limit: int = 20
) -> List[Dict]:
    """Перевіряє відповідність частини користувацького документа частині правил нормативу

    ОНОВЛЕНО: Використовує batch-валідацію (кілька правил за один запит)

    Args:
        user_chunks: Всі чанки користувацького документа
        rules: Всі правила нормативу
        reg_doc: Інформація про нормативний документ
        start_chunk_idx: З якого чанку починати
        chunk_limit: Скільки чанків обробляти
        start_rule_idx: З якого правила починати
        rule_limit: Скільки правил перевіряти
    """

    # Вибираємо частину чанків для аналізу
    selected_chunks = user_chunks[start_chunk_idx:start_chunk_idx + chunk_limit]
    if not selected_chunks:
        return []

    # Визначаємо розділи документа в цій частині
    sections_in_batch = set()
    for chunk in selected_chunks:
        if chunk.get("section"):
            sections_in_batch.add(chunk["section"])

    # Форматуємо текст з інформацією про форматування (якщо є)
    formatted_text_parts = []
    for chunk in selected_chunks:
        if chunk.get("has_formatting") and chunk.get("blocks"):
            # Є інформація про форматування
            section = chunk.get("section", "N/A")
            formatted_text_parts.append(f"\n--- {section} ---")

            for block in chunk["blocks"][:10]:  # Перші 10 блоків з чанку
                alignment = block.get("alignment", "left")
                font_size = block.get("font_size", 0)
                bold = "BOLD" if block.get("bold") else "normal"
                text = block.get("text", "")[:200]

                formatted_text_parts.append(
                    f"[{alignment.upper()}|{font_size}pt|{bold}] {text}"
                )
        else:
            # Немає форматування - звичайний текст
            formatted_text_parts.append(chunk["text"])

    user_text = "\n".join(formatted_text_parts)

    # Вибираємо частину правил для перевірки
    selected_rules = rules[start_rule_idx:start_rule_idx + rule_limit]
    if not selected_rules:
        return []

    sections_str = ", ".join(list(sections_in_batch)[:3]) if sections_in_batch else "N/A"
    print(f"  📄 Чанки {start_chunk_idx+1}-{start_chunk_idx+len(selected_chunks)} | Розділи: {sections_str}")
    print(f"  📋 Правила {start_rule_idx+1}-{start_rule_idx+len(selected_rules)} ({len(selected_rules)} правил)")

    # === НОВА ЛОГІКА: BATCH-ВАЛІДАЦІЯ ===
    # Розбиваємо правила на батчі по 3 правила (зменшено для відповідності ліміту Groq API)
    batch_size = 3
    all_issues = []
    num_batches = (len(selected_rules) + batch_size - 1) // batch_size

    print(f"  🚀 Використовую batch-валідацію: {len(selected_rules)} правил → {num_batches} батчів")

    for batch_idx in range(num_batches):
        batch_start = batch_idx * batch_size
        batch_end = min(batch_start + batch_size, len(selected_rules))
        rules_batch = selected_rules[batch_start:batch_end]

        # Додаємо затримку між батчами для уникнення перевищення rate limit (крім першого)
        if batch_idx > 0:
            time.sleep(2.0)  # Збільшено з 0.5 до 2 секунд

        # Перевіряємо batch правил одним запитом
        batch_issues = check_compliance_batch(
            user_text=user_text,
            rules_batch=rules_batch,
            reg_doc=reg_doc,
            sections_in_batch=sections_in_batch,
            batch_number=batch_idx + 1
        )

        all_issues.extend(batch_issues)

    print(f"  📊 Загалом знайдено {len(all_issues)} проблем у {num_batches} батчах")

    return all_issues


def run_specialized_validators(
    user_doc_id: str,
    user_chunks: List[Dict],
    categories: List[str] = None,
    regulatory_doc_ids: List[str] = None
) -> List[Dict]:
    """Запускає спеціалізовані валідатори (без LLM) для швидкої перевірки

    Args:
        user_doc_id: ID документа користувача
        user_chunks: Чанки документа
        categories: Категорії для перевірки
        regulatory_doc_ids: ID нормативних документів для отримання правил

    Returns:
        Список проблем знайдених спеціалізованими валідаторами
    """

    if not SPECIALIZED_VALIDATORS_AVAILABLE:
        print("  ⚠️ Спеціалізовані валідатори недоступні, пропускаю...")
        return []

    issues = []

    # Отримуємо інформацію про документ
    doc_result = supabase_admin.table("documents").select("storage_url").eq("id", user_doc_id).execute()
    if not doc_result.data:
        return []

    storage_url = doc_result.data[0]["storage_url"]

    # Завантажуємо файл з storage (якщо це DOCX)
    if not storage_url.endswith('.docx'):
        print(f"  ℹ️ Документ не є DOCX ({storage_url}), спеціалізовані валідатори недоступні")
        return []

    try:
        # Завантажуємо файл
        print(f"  📥 Завантажую файл з storage: {storage_url}")
        file_data = supabase.storage.from_("documents").download(storage_url)

        # Зберігаємо тимчасово
        temp_path = f"/tmp/{user_doc_id}.docx"
        with open(temp_path, 'wb') as f:
            f.write(file_data)

        print(f"  ✅ Файл завантажено: {len(file_data)} байт")

        # === ВАЛІДАЦІЯ ФОРМАТУВАННЯ ===
        if not categories or "formatting" in categories:
            try:
                print(f"\n  🎨 Запуск валідатора форматування...")
                formatting_validator = FormattingValidator(temp_path)

                # Якщо є нормативні документи з категорією "formatting" - використовуємо їх правила
                if regulatory_doc_ids:
                    print(f"  📋 Отримую структуровані правила форматування з нормативів...")

                    for reg_doc_id in regulatory_doc_ids:
                        # Отримуємо правила та категорію документа
                        reg_doc = supabase_admin.table("documents").select(
                            "extracted_rules, regulatory_category, filename"
                        ).eq("id", reg_doc_id).execute()

                        if not reg_doc.data:
                            continue

                        doc_data = reg_doc.data[0]
                        reg_category = doc_data.get("regulatory_category")

                        # Використовуємо тільки документи категорії "formatting"
                        if reg_category != "formatting":
                            continue

                        structured_rules = doc_data.get("extracted_rules", [])
                        if not structured_rules:
                            print(f"  ⚠️ Немає витягнутих правил у {doc_data.get('filename')}")
                            continue

                        print(f"  ✅ Знайдено {len(structured_rules)} структурованих правил у {doc_data.get('filename')}")

                        # Застосовуємо структуровані правила до валідатора
                        from formatting_rules_extractor import apply_structured_rules_to_validator

                        formatting_issues = apply_structured_rules_to_validator(
                            structured_rules=structured_rules,
                            validator=formatting_validator,
                            regulatory_doc_name=doc_data.get('filename')
                        )

                        issues.extend(formatting_issues)
                        print(f"  📊 Знайдено {len(formatting_issues)} проблем за правилами з {doc_data.get('filename')}")
                else:
                    # Якщо немає нормативів - використовуємо стандартну валідацію
                    print(f"  ℹ️ Нормативні документи не вказані, використовую стандартні параметри ДСТУ")
                    formatting_issues = formatting_validator.validate_all()

                    # Додаємо метадані до кожного issue
                    for issue in formatting_issues:
                        if "regulatory_doc_name" not in issue:
                            issue["regulatory_doc_name"] = "Стандартні вимоги ДСТУ"
                        if "section" not in issue:
                            # Якщо є user_document_section, використовуємо його як section
                            issue["section"] = issue.get("user_document_section", "N/A")

                    issues.extend(formatting_issues)

                print(f"  ✅ Форматування: {len(issues)} проблем загалом")
            except Exception as e:
                import traceback
                print(f"  ⚠️ Помилка при валідації форматування: {e}")
                print(f"  🔍 Traceback: {traceback.format_exc()}")

        # === ВАЛІДАЦІЯ СТРУКТУРИ ===
        if not categories or "structure" in categories:
            try:
                print(f"\n  📚 Запуск валідатора структури...")
                structure_validator = StructureValidator(user_chunks)

                # Стандартні обов'язкові розділи для курсової/дипломної роботи
                required_sections = [
                    "ВСТУП",
                    "РОЗДІЛ 1",
                    "РОЗДІЛ 2",
                    "ВИСНОВКИ",
                    "СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ"
                ]

                structure_issues = structure_validator.validate_required_sections(required_sections)

                # Додаємо метадані до кожного issue
                for issue in structure_issues:
                    if "regulatory_doc_name" not in issue:
                        issue["regulatory_doc_name"] = "Стандартні вимоги до структури"
                    if "section" not in issue:
                        issue["section"] = "Структура документа"

                issues.extend(structure_issues)
                print(f"  ✅ Структура: {len(structure_issues)} проблем")
            except Exception as e:
                print(f"  ⚠️ Помилка при валідації структури: {e}")

        # === ВАЛІДАЦІЯ ПОСИЛАНЬ ===
        if not categories or "references" in categories:
            try:
                print(f"\n  🔗 Запуск валідатора посилань...")

                # Об'єднуємо весь текст
                full_text = "\n".join([chunk["text"] for chunk in user_chunks])

                references_validator = ReferencesValidator(full_text)
                references_issues = references_validator.validate_citations()

                # Додаємо метадані до кожного issue
                for issue in references_issues:
                    if "regulatory_doc_name" not in issue:
                        issue["regulatory_doc_name"] = "Стандартні вимоги до посилань"
                    if "section" not in issue:
                        issue["section"] = "Список використаних джерел"

                issues.extend(references_issues)
                print(f"  ✅ Посилання: {len(references_issues)} проблем")
            except Exception as e:
                print(f"  ⚠️ Помилка при валідації посилань: {e}")

        # Видаляємо тимчасовий файл
        try:
            os.remove(temp_path)
        except:
            pass

        print(f"\n  📊 Спеціалізовані валідатори: загалом {len(issues)} проблем")

    except Exception as e:
        print(f"  ❌ Помилка при роботі спеціалізованих валідаторів: {e}")
        import traceback
        print(f"  🔍 Traceback: {traceback.format_exc()}")

    return issues


def check_compliance_full_document(user_chunks: List[Dict], rules: List[Dict], reg_doc: Dict) -> List[Dict]:
    """Перевіряє відповідність ВСЬОГО користувацького документа ВСІМ правилам нормативу

    Розбиває документ і правила на частини та обробляє їх послідовно
    """

    all_issues = []
    total_chunks = len(user_chunks)
    total_rules = len(rules)

    # Параметри розбиття (зменшено для відповідності ліміту Groq API)
    chunk_batch_size = 30  # Чанків за один запит (зменшено з 40)
    rule_batch_size = 10   # Правил за один запит (зменшено з 20)

    num_chunk_batches = (total_chunks + chunk_batch_size - 1) // chunk_batch_size
    num_rule_batches = (total_rules + rule_batch_size - 1) // rule_batch_size

    print(f"\n🔍 Повна валідація проти {reg_doc['filename']}")
    print(f"  📊 Документ: {total_chunks} чанків → {num_chunk_batches} частин по {chunk_batch_size} чанків")
    print(f"  📊 Правила: {total_rules} правил → {num_rule_batches} частин по {rule_batch_size} правил")
    print(f"  📊 Загалом: {num_chunk_batches * num_rule_batches} комбінацій для перевірки\n")

    request_count = 0

    # Перебираємо всі частини документа
    for chunk_batch_idx in range(num_chunk_batches):
        start_chunk_idx = chunk_batch_idx * chunk_batch_size

        print(f"📄 Частина документа {chunk_batch_idx + 1}/{num_chunk_batches}")

        # Для кожної частини документа перевіряємо всі правила (теж частинами)
        for rule_batch_idx in range(num_rule_batches):
            start_rule_idx = rule_batch_idx * rule_batch_size

            print(f"  🔎 Перевірка правил {rule_batch_idx + 1}/{num_rule_batches}...")

            # Додаємо затримку між запитами (крім першого)
            if request_count > 0:
                delay = 1.5
                print(f"  ⏳ Затримка {delay}с...")
                time.sleep(delay)

            # Перевіряємо цю комбінацію частин
            batch_issues = check_compliance_for_chunk_batch(
                user_chunks=user_chunks,
                rules=rules,
                reg_doc=reg_doc,
                start_chunk_idx=start_chunk_idx,
                chunk_limit=chunk_batch_size,
                start_rule_idx=start_rule_idx,
                rule_limit=rule_batch_size
            )

            if batch_issues:
                all_issues.extend(batch_issues)
                print(f"  ⚠️ Знайдено {len(batch_issues)} проблем у цій частині")
            else:
                print(f"  ✅ Проблем не виявлено у цій частині")

            request_count += 1

    # Дедуплікація проблем (видаляємо дублікати)
    unique_issues = []
    seen = set()

    for issue in all_issues:
        # Створюємо ключ на основі опису та категорії
        key = (issue.get("description", ""), issue.get("category", ""), issue.get("section", ""))
        if key not in seen and key[0]:  # Пропускаємо порожні
            seen.add(key)
            unique_issues.append(issue)

    if len(unique_issues) < len(all_issues):
        print(f"  🧹 Видалено {len(all_issues) - len(unique_issues)} дублікатів проблем")

    print(f"\n✅ Валідація завершена: знайдено {len(unique_issues)} унікальних проблем\n")

    return unique_issues


def aggregate_validation_results(all_issues: List[Dict]) -> Dict:
    """Агрегує результати валідації та обчислює метрики"""

    if not all_issues:
        return {
            "overall_compliance": "pass",
            "compliance_score": 1.0,
            "issues": [],
            "summary": {
                "total_issues": 0,
                "critical": 0,
                "major": 0,
                "minor": 0,
                "info": 0
            }
        }

    # Підрахунок по severity
    severity_counts = {
        "critical": 0,
        "major": 0,
        "minor": 0,
        "info": 0
    }

    for issue in all_issues:
        severity = issue.get("severity", "minor")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    # Обчислення compliance score
    total_issues = len(all_issues)
    weight_map = {"critical": 10, "major": 5, "minor": 2, "info": 1}

    weighted_issues = sum(
        severity_counts[sev] * weight_map[sev]
        for sev in severity_counts
    )

    # Нормалізація (припускаємо максимум 100 зважених проблем = 0 балів)
    max_weighted = 100
    compliance_score = max(0.0, 1.0 - (weighted_issues / max_weighted))

    # Визначення overall_compliance
    if severity_counts["critical"] > 0:
        overall_compliance = "fail"
    elif severity_counts["major"] > 2:
        overall_compliance = "fail"
    elif total_issues > 5:
        overall_compliance = "partial"
    else:
        overall_compliance = "partial" if total_issues > 0 else "pass"

    return {
        "overall_compliance": overall_compliance,
        "compliance_score": round(compliance_score, 2),
        "issues": all_issues,
        "summary": {
            "total_issues": total_issues,
            "critical": severity_counts["critical"],
            "major": severity_counts["major"],
            "minor": severity_counts["minor"],
            "info": severity_counts["info"]
        }
    }


def get_validation_cache_key(user_doc_id: str, categories: List[str] = None, regulatory_doc_ids: List[str] = None) -> str:
    """Генерує ключ для кешування валідації"""
    import hashlib

    # Сортуємо для консистентності
    cats = sorted(categories) if categories else []
    reg_ids = sorted(regulatory_doc_ids) if regulatory_doc_ids else []

    # Створюємо ключ
    key_parts = [user_doc_id] + cats + reg_ids
    key_string = "|".join(key_parts)

    # Хешуємо для компактності
    return hashlib.sha256(key_string.encode()).hexdigest()


def validate_document(
    user_doc_id: str,
    categories: List[str] = None,
    regulatory_doc_ids: List[str] = None,
    use_cache: bool = True
) -> Dict:
    """Головна функція валідації документа з вибірковою валідацією та кешуванням

    Args:
        user_doc_id: ID документа для валідації
        categories: Список категорій нормативів для перевірки (content/formatting/structure/references)
        regulatory_doc_ids: Конкретні ID нормативних документів (якщо не вказано - всі)
        use_cache: Використовувати кеш (за замовчуванням True)
    """

    print(f"\n=== Початок валідації документа {user_doc_id} ===")
    print(f"🎯 Категорії: {categories or 'всі'}")
    print(f"📋 Конкретні нормативи: {len(regulatory_doc_ids) if regulatory_doc_ids else 'всі'}")

    # === КЕШУВАННЯ: Перевіряємо чи є збережений результат ===
    if use_cache:
        cache_key = get_validation_cache_key(user_doc_id, categories, regulatory_doc_ids)
        print(f"🔍 Перевіряю кеш валідації (ключ: {cache_key[:16]}...)")

        try:
            # Шукаємо в останньому звіті валідації
            cache_result = supabase_admin.table("validation_reports").select("*").eq(
                "user_document_id", user_doc_id
            ).order("created_at", desc=True).limit(1).execute()

            if cache_result.data:
                cached_report = cache_result.data[0]
                cached_result = cached_report.get("validation_result", {})

                # Перевіряємо чи це той самий запит (ті самі нормативи)
                cached_reg_docs = cached_report.get("regulatory_documents", [])
                cached_reg_ids = set(doc["id"] for doc in cached_reg_docs)
                requested_reg_ids = set(regulatory_doc_ids) if regulatory_doc_ids else None

                # Якщо запит ідентичний або запитуються всі нормативи
                is_same_request = (
                    requested_reg_ids is None or
                    cached_reg_ids == requested_reg_ids
                )

                if is_same_request and cached_result:
                    # Перевіряємо свіжість кешу (менше 24 годин)
                    from datetime import datetime, timedelta
                    created_at = datetime.fromisoformat(cached_report["created_at"].replace('Z', '+00:00'))
                    age = datetime.now(created_at.tzinfo) - created_at

                    if age < timedelta(hours=24):
                        print(f"✅ Знайдено свіжий кеш ({age.total_seconds()/60:.0f}хв тому)")
                        print(f"📊 Повертаю закешований результат (0 API запитів!)")
                        cached_result["from_cache"] = True
                        cached_result["cache_age_minutes"] = age.total_seconds() / 60
                        return cached_result
                    else:
                        print(f"⚠️ Кеш застарілий ({age.days}д тому), виконую нову валідацію")
                else:
                    print(f"⚠️ Кеш не підходить (інші параметри), виконую нову валідацію")
        except Exception as e:
            print(f"⚠️ Помилка при перевірці кешу: {e}")
            print(f"📝 Продовжую звичайну валідацію...")

    # === ЗВИЧАЙНА ВАЛІДАЦІЯ (якщо кешу немає) ===

    # ПРИМІТКА: Використовуємо supabase_admin для bypass RLS,
    # оскільки доступ вже перевірено через verify_document_access у main.py

    # Перевіряємо чи документ існує
    doc_result = supabase_admin.table("documents").select("*").eq("id", user_doc_id).execute()
    if not doc_result.data:
        return {"error": "Документ не знайдено"}

    user_doc = doc_result.data[0]
    print(f"📄 Документ: {user_doc.get('filename')} (статус: {user_doc.get('status')})")

    # Перевіряємо статус документа
    if user_doc.get("status") != "ready":
        return {
            "error": f"Документ ще обробляється (статус: {user_doc.get('status')}). "
                    f"Зачекайте поки завантаження завершиться."
        }

    # Перевіряємо чи це не нормативний документ
    if user_doc.get("document_type") == "regulatory":
        return {"error": "Не можна валідувати нормативний документ"}

    # Отримуємо нормативні документи з фільтрацією
    # ПРИМІТКА: Використовуємо supabase_admin для отримання нормативів,
    # оскільки користувач має доступ до своїх нормативів через user_id фільтр
    query = supabase_admin.table("documents").select("*").eq(
        "document_type", "regulatory"
    ).eq("status", "ready").eq("user_id", user_doc.get("user_id"))

    # Фільтр по конкретних ID
    if regulatory_doc_ids:
        query = query.in_("id", regulatory_doc_ids)

    # Фільтр по категоріях
    if categories:
        query = query.in_("regulatory_category", categories)

    regulatory_docs_result = query.execute()

    if not regulatory_docs_result.data:
        # Перевіряємо чи взагалі є нормативні документи для цього користувача
        all_regulatory = supabase_admin.table("documents").select("id, filename, regulatory_category").eq(
            "document_type", "regulatory"
        ).eq("status", "ready").eq("user_id", user_doc.get("user_id")).execute()

        if not all_regulatory.data:
            return {"error": "Немає завантажених нормативних документів для валідації"}

        # Є документи, але без потрібних категорій
        without_category = [doc for doc in all_regulatory.data if not doc.get("regulatory_category")]
        if without_category:
            return {
                "error": f"Знайдено {len(without_category)} нормативних документів БЕЗ категорії. "
                         f"Завантажте нормативні документи заново з вибором категорії або "
                         f"видаліть старі документи без категорій."
            }

        return {"error": f"Немає нормативних документів з категоріями: {', '.join(categories)}"}

    regulatory_docs = regulatory_docs_result.data
    print(f"✅ Знайдено {len(regulatory_docs)} нормативних документів для валідації")

    # Отримуємо чанки користувацького документа
    print(f"📥 Отримую чанки документа з Qdrant...")
    user_chunks = get_all_chunks_for_document(user_doc_id)

    if not user_chunks:
        error_msg = (
            f"❌ Документ не містить проіндексованого вмісту у векторній БД. "
            f"Можливо документ не був повністю завантажений або сталася помилка при індексації. "
            f"Спробуйте завантажити документ заново."
        )
        print(error_msg)
        return {"error": error_msg}

    print(f"✅ Документ містить {len(user_chunks)} чанків")

    # === КРОК 1: СПЕЦІАЛІЗОВАНІ ВАЛІДАТОРИ (БЕЗ LLM) ===
    print(f"\n{'='*60}")
    print(f"🚀 КРОК 1: Спеціалізовані валідатори (форматування, структура, посилання)")
    print(f"{'='*60}\n")

    specialized_issues = run_specialized_validators(
        user_doc_id=user_doc_id,
        user_chunks=user_chunks,
        categories=categories,
        regulatory_doc_ids=regulatory_doc_ids
    )

    print(f"\n✅ Спеціалізовані валідатори завершено: {len(specialized_issues)} проблем\n")

    # === КРОК 2: LLM-ВАЛІДАЦІЯ ЗМІСТУ ===
    print(f"\n{'='*60}")
    print(f"🤖 КРОК 2: LLM-валідація змісту проти нормативів")
    print(f"{'='*60}\n")

    # Валідація проти кожного нормативу
    all_issues = list(specialized_issues)  # Починаємо з проблем від спеціалізованих валідаторів
    regulatory_docs_used = []

    for idx, reg_doc in enumerate(regulatory_docs):
        print(f"\n{'='*60}")
        print(f"📋 Нормативний документ {idx + 1}/{len(regulatory_docs)}: {reg_doc['filename']}")
        print(f"{'='*60}")

        # Витягуємо правила з нормативу
        rules = extract_regulatory_rules(reg_doc["id"], reg_doc["filename"])

        if not rules:
            print(f"⚠️ Не вдалося витягти правила з {reg_doc['filename']}, пропускаю...")
            continue

        # Перевіряємо відповідність ВСЬОГО документа ВСІМ правилам
        issues = check_compliance_full_document(user_chunks, rules, reg_doc)

        if issues:
            all_issues.extend(issues)
            print(f"📊 Підсумок для {reg_doc['filename']}: знайдено {len(issues)} проблем")
        else:
            print(f"✅ Підсумок для {reg_doc['filename']}: проблем не виявлено")

        regulatory_docs_used.append({
            "id": reg_doc["id"],
            "filename": reg_doc["filename"]
        })

    print(f"\n{'='*60}")
    print(f"📊 ЗАГАЛЬНИЙ ПІДСУМОК: {len(all_issues)} проблем з усіх нормативів")
    print(f"{'='*60}\n")

    # Агрегуємо результати
    validation_result = aggregate_validation_results(all_issues)

    print(f"\n=== Валідація завершена ===")
    print(f"Загальна відповідність: {validation_result['overall_compliance']}")
    print(f"Знайдено проблем: {validation_result['summary']['total_issues']}")

    # Зберігаємо звіт у БД
    try:
        report = supabase_admin.table("validation_reports").insert({
            "user_document_id": user_doc_id,
            "regulatory_documents": regulatory_docs_used,
            "validation_result": validation_result,
            "validation_categories": categories or [],  # Зберігаємо категорії валідації
            "status": "completed",
            "user_id": user_doc.get("user_id")  # Додаємо user_id для RLS
        }).execute()

        validation_result["report_id"] = report.data[0]["id"]
    except Exception as e:
        print(f"Помилка при збереженні звіту: {e}")

    return validation_result
