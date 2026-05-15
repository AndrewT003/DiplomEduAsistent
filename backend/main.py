import uuid
import hashlib
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form, Depends
from typing import Optional, List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from config import supabase, groq_client, supabase_admin, get_user_supabase
from document_parser import extract_text, extract_text_with_formatting, detect_document_structure
from rag_engine import index_document, index_document_with_structure, search_context
from docx_exporter import export_to_docx, export_validation_to_docx
from generators import generate_material, chat_with_document, SYSTEM_PROMPT
from validator import validate_document
from validation_report import format_report_for_api, format_report_for_chat
from auth import get_current_user, get_optional_user
from auth_routes import router as auth_router


def calculate_file_hash(content: bytes) -> str:
    """Обчислює SHA256 хеш файлу"""
    return hashlib.sha256(content).hexdigest()


def verify_document_access(doc_id: str, user: dict) -> dict:
    """Перевіряє що документ належить користувачу і повертає його"""
    # Використовуємо клієнт з токеном користувача для RLS
    user_supabase = get_user_supabase(user["access_token"])
    doc_result = user_supabase.table("documents").select("*").eq("id", doc_id).execute()

    if not doc_result.data:
        raise HTTPException(status_code=404, detail="Документ не знайдено")

    doc = doc_result.data[0]
    if doc.get("user_id") != user["user_id"]:
        raise HTTPException(status_code=403, detail="Немає доступу до цього документа")

    return doc


def extract_rules_background(doc_id: str, filename: str):
    """Витягує правила у фоновому режимі"""
    print(f"🔄 [Background] Початок витягування правил для {filename}...")

    try:
        # Оновлюємо статус на "extracting" (використовуємо admin для bypass RLS)
        supabase_admin.table("documents").update({
            "extraction_status": "extracting"
        }).eq("id", doc_id).execute()

        from validator import extract_regulatory_rules
        rules = extract_regulatory_rules(doc_id, filename)

        # Оновлюємо статус на "completed" (використовуємо admin для bypass RLS)
        supabase_admin.table("documents").update({
            "extraction_status": "completed"
        }).eq("id", doc_id).execute()

        print(f"✅ [Background] Витягнуто {len(rules)} правил для {filename}")

    except Exception as e:
        import traceback
        print(f"❌ [Background] Помилка при витягуванні правил: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")

        # Оновлюємо статус на "failed" (використовуємо admin для bypass RLS)
        supabase_admin.table("documents").update({
            "extraction_status": "failed"
        }).eq("id", doc_id).execute()

app = FastAPI()

# CORS налаштування для development і Docker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Дозволяємо всі origins для розробки
    allow_credentials=False,  # При allow_origins=["*"] credentials мають бути False
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключаємо auth роутер
app.include_router(auth_router)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/documents")
def get_documents(user: dict = Depends(get_current_user)):
    # Використовуємо клієнт з токеном користувача для RLS
    user_supabase = get_user_supabase(user["access_token"])

    # Користувач бачить тільки свої документи
    result = user_supabase.table("documents").select("*").eq(
        "user_id", user["user_id"]
    ).order("created_at", desc=True).execute()
    return result.data

@app.get("/documents/regulatory")
def get_regulatory_documents(
    category: Optional[str] = None,
    tags: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Отримати список нормативних документів з фільтрацією

    category: фільтр по категорії (content/formatting/structure/references)
    tags: фільтр по тегах (через кому)
    """
    # Використовуємо клієнт з токеном користувача для RLS
    user_supabase = get_user_supabase(user["access_token"])

    query = user_supabase.table("documents").select("*").eq(
        "document_type", "regulatory"
    ).eq("user_id", user["user_id"])

    # Фільтр по категорії
    if category:
        query = query.eq("regulatory_category", category)

    # Фільтр по тегах (якщо потрібно)
    # Примітка: PostgreSQL array containment
    if tags:
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        # Використовуємо overlaps (&&) для перевірки перетину масивів
        for tag in tags_list:
            query = query.contains("tags", [tag])

    result = query.execute()
    return result.data

@app.get("/documents/{doc_id}")
def get_document(doc_id: str, user: dict = Depends(get_current_user)):
    """Отримати один документ за ID"""
    doc = verify_document_access(doc_id, user)
    return doc

@app.patch("/documents/{doc_id}")
def update_document(doc_id: str, body: dict, user: dict = Depends(get_current_user)):
    """Оновити назву або метадані документа"""
    # Перевіряємо доступ
    verify_document_access(doc_id, user)

    # Дозволені поля для оновлення
    allowed_fields = ["filename", "regulatory_category", "tags"]
    update_data = {k: v for k, v in body.items() if k in allowed_fields}

    if not update_data:
        raise HTTPException(status_code=400, detail="Немає полів для оновлення")

    # Оновлюємо документ
    result = supabase_admin.table("documents").update(update_data).eq(
        "id", doc_id
    ).execute()

    return result.data[0] if result.data else {}

@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str, user: dict = Depends(get_current_user)):
    """Видалити документ повністю (з storage, БД, Qdrant)"""
    # Перевіряємо доступ
    doc = verify_document_access(doc_id, user)

    try:
        # 1. Видаляємо з Qdrant
        print(f"🗑️ [1/3] Видалення з Qdrant...")
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            from config import qdrant
            results = qdrant.scroll(
                collection_name="edu_docs",
                scroll_filter=Filter(
                    must=[FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id)
                    )]
                ),
                limit=1000
            )
            point_ids = [p.id for p in results[0]]
            if point_ids:
                qdrant.delete(collection_name="edu_docs", points_selector=point_ids)
                print(f"✅ Видалено {len(point_ids)} точок з Qdrant")
        except Exception as e:
            print(f"⚠️ Помилка видалення з Qdrant: {e}")

        # 2. Видаляємо з Storage
        print(f"🗑️ [2/3] Видалення з Storage...")
        if doc.get("storage_url"):
            try:
                supabase.storage.from_("documents").remove([doc["storage_url"]])
                print(f"✅ Видалено файл з Storage")
            except Exception as e:
                print(f"⚠️ Помилка видалення з Storage: {e}")

        # 3. Видаляємо з БД (це також видалить materials та validation_reports через CASCADE)
        print(f"🗑️ [3/3] Видалення з БД...")
        supabase_admin.table("documents").delete().eq("id", doc_id).execute()
        print(f"✅ Документ видалено")

        return {"message": "Документ успішно видалено", "id": doc_id}

    except Exception as e:
        import traceback
        print(f"❌ Помилка при видаленні: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Помилка видалення: {str(e)}")

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    content = await file.read()

    # Обчислюємо хеш файлу для виявлення дублікатів
    file_hash = calculate_file_hash(content)
    print(f"🔐 Хеш файлу: {file_hash[:16]}...")

    # Перевіряємо чи документ з таким хешем вже існує (серед документів цього користувача)
    existing_by_hash = supabase.table("documents").select("*").eq(
        "file_hash", file_hash
    ).eq("status", "ready").eq("user_id", user["user_id"]).execute()

    if existing_by_hash.data:
        doc = existing_by_hash.data[0]
        print(f"✅ Документ з таким хешем вже існує (id: {doc['id']})")
        return {
            "id": doc["id"],
            "filename": doc["filename"],
            "status": "exists_by_hash",
            "message": f"Ідентичний документ вже завантажений як '{doc['filename']}'",
            "original_filename": doc["filename"]
        }

    # Перевіряємо чи документ з таким іменем вже існує (для зворотної сумісності, серед документів цього користувача)
    existing_by_name = supabase.table("documents").select("*").eq(
        "filename", file.filename
    ).eq("status", "ready").eq("user_id", user["user_id"]).execute()

    if existing_by_name.data:
        doc = existing_by_name.data[0]
        return {
            "id": doc["id"],
            "filename": doc["filename"],
            "status": "exists",
            "message": "Документ з таким іменем вже завантажений"
        }

    # Новий документ — завантажуємо
    doc_id = str(uuid.uuid4())
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    storage_filename = f"{doc_id}.{file_extension}"

    storage_uploaded = False
    db_inserted = False
    indexed_in_qdrant = False

    try:
        # Крок 1: Завантажуємо в storage
        print(f"📤 [1/4] Завантаження в storage...")
        supabase.storage.from_("documents").upload(
            path=storage_filename,
            file=content,
            file_options={"content-type": file.content_type}
        )
        storage_uploaded = True
        print(f"✅ Storage OK")

        # Крок 2: Зберігаємо метадані в Supabase (використовуємо admin для bypass RLS)
        print(f"💾 [2/4] Збереження в Supabase БД...")
        insert_result = supabase_admin.table("documents").insert({
            "id": doc_id,
            "filename": file.filename,
            "storage_url": storage_filename,
            "status": "processing",
            "file_hash": file_hash,
            "user_id": user["user_id"]  # Додаємо user_id
        }).execute()

        if not insert_result.data:
            raise Exception("Supabase insert повернув порожній результат")

        db_inserted = True
        print(f"✅ Supabase OK (id: {doc_id[:8]}...)")

        # Крок 3: Індексуємо в Qdrant
        print(f"🔍 [3/4] Індексація в Qdrant...")
        try:
            blocks = extract_text_with_formatting(content, file.filename)

            # Перевіряємо чи є блоки
            if not blocks or len(blocks) == 0:
                raise ValueError("Витягнуто 0 блоків з форматуванням - використовую fallback")

            blocks_with_structure = detect_document_structure(blocks)
            index_document_with_structure(blocks_with_structure, doc_id, document_type="user")
            print(f"✅ Qdrant OK ({len(blocks)} блоків з форматуванням)")
        except Exception as e:
            # Fallback на звичайне витягування тексту
            print(f"⚠️ Не вдалося витягнути форматування: {e}")
            print(f"📝 Використовую базове витягування тексту")
            text = extract_text(content, file.filename)

            if not text or len(text.strip()) == 0:
                raise Exception("Документ порожній або не містить текстового вмісту")

            index_document(text, doc_id, document_type="user")
            print(f"✅ Qdrant OK (базове індексування, {len(text)} символів)")

        indexed_in_qdrant = True

        # Крок 4: Оновлюємо статус на ready (використовуємо admin для bypass RLS)
        print(f"✅ [4/4] Оновлення статусу...")
        supabase_admin.table("documents").update(
            {"status": "ready", "document_type": "user"}
        ).eq("id", doc_id).execute()
        print(f"✅ Статус оновлено")

        print(f"🎉 Документ успішно завантажено: {file.filename}")
        return {"id": doc_id, "filename": file.filename, "status": "ready"}

    except Exception as e:
        # ROLLBACK: Відкочуємо всі зміни
        import traceback
        error_msg = f"Помилка при завантаженні документа: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"🔍 Traceback: {traceback.format_exc()}")

        # Відкочуємо в зворотному порядку
        if indexed_in_qdrant:
            print(f"🔄 Rollback: Видаляємо з Qdrant...")
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                from config import qdrant
                results = qdrant.scroll(
                    collection_name="edu_docs",
                    scroll_filter=Filter(
                        must=[FieldCondition(
                            key="doc_id",
                            match=MatchValue(value=doc_id)
                        )]
                    ),
                    limit=1000
                )
                point_ids = [p.id for p in results[0]]
                if point_ids:
                    qdrant.delete(collection_name="edu_docs", points_selector=point_ids)
                    print(f"✅ Видалено {len(point_ids)} точок з Qdrant")
            except Exception as rollback_error:
                print(f"⚠️ Не вдалося відкотити Qdrant: {rollback_error}")

        if db_inserted:
            print(f"🔄 Rollback: Видаляємо з Supabase БД...")
            try:
                supabase_admin.table("documents").delete().eq("id", doc_id).execute()
                print(f"✅ Видалено запис з Supabase")
            except Exception as rollback_error:
                print(f"⚠️ Не вдалося відкотити Supabase: {rollback_error}")

        if storage_uploaded:
            print(f"🔄 Rollback: Видаляємо з Storage...")
            try:
                supabase.storage.from_("documents").remove([storage_filename])
                print(f"✅ Видалено файл з Storage")
            except Exception as rollback_error:
                print(f"⚠️ Не вдалося відкотити Storage: {rollback_error}")

        # Повертаємо помилку
        raise HTTPException(
            status_code=500,
            detail=f"Не вдалося завантажити документ: {str(e)}"
        )

@app.post("/generate/{doc_id}")
def generate(doc_id: str, type: str, user: dict = Depends(get_current_user)):
    # Перевіряємо доступ до документа
    verify_document_access(doc_id, user)

    # Зменшуємо limit до 5 для уникнення перевищення ліміту Groq API
    context = search_context(doc_id, type, limit=5)
    result = generate_material(context, type)

    # Зберігаємо результат (використовуємо admin для bypass RLS)
    supabase_admin.table("materials").insert({
        "document_id": doc_id,
        "type": type,
        "content": result["content"],
        "topic": result.get("topic", "Навчальний матеріал"),  # Зберігаємо тему
        "user_id": user["user_id"]  # Додаємо user_id
    }).execute()

    return {"result": result["content"], "topic": result.get("topic")}

@app.get("/download/{doc_id}/{material_type}")
def download(doc_id: str, material_type: str, user: dict = Depends(get_current_user)):
    # Перевіряємо доступ до документа
    verify_document_access(doc_id, user)

    # Беремо збережений матеріал (фільтруємо по user_id)
    user_supabase = get_user_supabase(user["access_token"])
    result = user_supabase.table("materials").select("*").eq(
        "document_id", doc_id
    ).eq("type", material_type).eq("user_id", user["user_id"]).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Матеріал не знайдено")

    material = result.data[-1]
    content = material["content"]
    topic = material.get("topic", f"Документ {doc_id}")

    docx_bytes = export_to_docx(content, f"Документ {doc_id}", material_type, topic=topic)

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={material_type}.docx"}
    )
@app.post("/chat/general")
def chat_general(body: dict, user: dict | None = Depends(get_optional_user)):
    question = body.get("question")
    history = body.get("history", [])

    # Фільтруємо тільки role і content
    clean_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history
        if msg.get("role") in ["user", "assistant"] and msg.get("content")
    ]

    # Отримуємо список нормативних документів для контексту
    # Якщо користувач авторизований - показуємо його документи, інакше - всі публічні
    if user:
        user_supabase = get_user_supabase(user["access_token"])
        regulatory_docs_result = user_supabase.table("documents").select("filename, regulatory_category").eq(
            "document_type", "regulatory"
        ).eq("user_id", user["user_id"]).execute()
    else:
        # Для неавторизованих користувачів - не показуємо нормативи
        regulatory_docs_result = None

    regulatory_docs = regulatory_docs_result.data if regulatory_docs_result and regulatory_docs_result.data else []

    print(f"📋 [GENERAL CHAT] Передаю асистенту список нормативних документів: {len(regulatory_docs) if regulatory_docs else 0}")

    # Формуємо системний промпт з інформацією про нормативні документи
    regulatory_system_info = ""
    if regulatory_docs and len(regulatory_docs) > 0:
        regulatory_system_info = "\n\n" + "="*50 + "\n"
        regulatory_system_info += "ЗАВАНТАЖЕНІ НОРМАТИВНІ ДОКУМЕНТИ В СИСТЕМІ:\n"
        regulatory_system_info += "="*50 + "\n"
        for idx, doc in enumerate(regulatory_docs, 1):
            category = doc.get('regulatory_category', 'не вказана')
            regulatory_system_info += f"{idx}. {doc['filename']} (категорія: {category})\n"
        regulatory_system_info += "="*50 + "\n"
    else:
        regulatory_system_info = "\n\nНормативні документи: поки не завантажено."

    # Формуємо контекст для питання з ОБОВ'ЯЗКОВИМ списком нормативів
    user_question = question
    if regulatory_docs and len(regulatory_docs) > 0:
        user_question = "🔴"*25 + "\n"
        user_question += "⚠️ СПИСОК НОРМАТИВНИХ ДОКУМЕНТІВ (використовуй ТІЛЬКИ цей список!):\n"
        user_question += "="*50 + "\n"
        for idx, doc in enumerate(regulatory_docs, 1):
            category = doc.get('regulatory_category', 'не вказана')
            user_question += f"{idx}. {doc['filename']} (категорія: {category})\n"
        user_question += "="*50 + "\n"
        user_question += "⚠️ ВАЖЛИВО: Це ПОВНИЙ і ЄДИНИЙ список! НЕ вигадуй інші документи!\n"
        user_question += "🔴"*25 + "\n\n"
        user_question += f"Питання: {question}"

    messages_list = [{"role": "system", "content": SYSTEM_PROMPT + regulatory_system_info}]
    messages_list.extend(clean_history)
    messages_list.append({"role": "user", "content": user_question})

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages_list,
        max_tokens=1000
    )

    return {"answer": response.choices[0].message.content}


@app.post("/chat/{doc_id}")
def chat(doc_id: str, body: dict, user: dict = Depends(get_current_user)):
    # Перевіряємо доступ до документа
    verify_document_access(doc_id, user)

    question = body.get("question")
    history = body.get("history", [])

    # Фільтруємо тільки role і content
    clean_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history
        if msg.get("role") in ["user", "assistant"] and msg.get("content")
    ]

    # Отримуємо список нормативних документів для контексту (тільки свої)
    user_supabase = get_user_supabase(user["access_token"])
    regulatory_docs_result = user_supabase.table("documents").select("filename, regulatory_category").eq(
        "document_type", "regulatory"
    ).eq("user_id", user["user_id"]).execute()

    regulatory_docs = regulatory_docs_result.data if regulatory_docs_result.data else []

    context = search_context(doc_id, question)
    answer = chat_with_document(context, question, clean_history, regulatory_docs)
    return {"answer": answer}


# ========== VALIDATION ENDPOINTS ==========

@app.post("/upload/regulatory")
async def upload_regulatory(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    regulatory_category: Optional[str] = Form(None),  # content/formatting/structure/references
    tags: Optional[str] = Form(None),  # Comma-separated tags
    user: dict = Depends(get_current_user)
):
    """Завантажити нормативний документ з категорією

    regulatory_category:
      - content: змістовні вимоги (закони, положення)
      - formatting: вимоги до оформлення (ДСТУ, шрифти)
      - structure: вимоги до структури (розділи, порядок)
      - references: вимоги до посилань

    tags: додаткові теги через кому (наприклад: "освіта,курсова,2024")
    """
    content = await file.read()

    # Валідація категорії
    valid_categories = ["content", "formatting", "structure", "references"]
    if regulatory_category and regulatory_category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Невалідна категорія. Доступні: {', '.join(valid_categories)}"
        )

    # Парсинг тегів
    tags_list = None
    if tags:
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

    print(f"📂 Категорія: {regulatory_category or 'не вказана'}")
    print(f"🏷️  Теги: {tags_list or 'немає'}")

    # Обчислюємо хеш файлу для виявлення дублікатів
    file_hash = calculate_file_hash(content)
    print(f"🔐 Хеш файлу: {file_hash[:16]}...")

    # Перевіряємо чи документ з таким хешем вже існує (серед документів цього користувача)
    existing_by_hash = supabase.table("documents").select("*").eq(
        "file_hash", file_hash
    ).eq("document_type", "regulatory").eq("status", "ready").eq("user_id", user["user_id"]).execute()

    if existing_by_hash.data:
        doc = existing_by_hash.data[0]
        print(f"✅ Документ з таким хешем вже існує (id: {doc['id']})")
        print(f"💾 Використовуємо закешовані правила (0 токенів!)")
        return {
            "id": doc["id"],
            "filename": doc["filename"],
            "status": "exists_by_hash",
            "message": f"Ідентичний документ вже завантажений як '{doc['filename']}'. Використовуємо існуючі правила.",
            "original_filename": doc["filename"],
            "rules_count": len(doc.get("extracted_rules", []))
        }

    # Перевіряємо чи документ з таким іменем вже існує (для зворотної сумісності, серед документів цього користувача)
    existing_by_name = supabase.table("documents").select("*").eq(
        "filename", file.filename
    ).eq("document_type", "regulatory").eq("status", "ready").eq("user_id", user["user_id"]).execute()

    if existing_by_name.data:
        doc = existing_by_name.data[0]
        return {
            "id": doc["id"],
            "filename": doc["filename"],
            "status": "exists",
            "message": "Нормативний документ з таким іменем вже завантажений"
        }

    # Новий нормативний документ
    doc_id = str(uuid.uuid4())
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    storage_filename = f"{doc_id}.{file_extension}"

    storage_uploaded = False
    db_inserted = False
    indexed_in_qdrant = False

    try:
        # Крок 1: Завантажуємо в storage
        print(f"📤 [1/4] Завантаження в storage...")
        supabase.storage.from_("documents").upload(
            path=storage_filename,
            file=content,
            file_options={"content-type": file.content_type}
        )
        storage_uploaded = True
        print(f"✅ Storage OK")

        # Крок 2: Зберігаємо метадані в Supabase (використовуємо admin для bypass RLS)
        print(f"💾 [2/4] Збереження в Supabase БД...")
        insert_result = supabase_admin.table("documents").insert({
            "id": doc_id,
            "filename": file.filename,
            "storage_url": storage_filename,
            "status": "processing",
            "document_type": "regulatory",
            "file_hash": file_hash,
            "extraction_status": "pending",
            "regulatory_category": regulatory_category,
            "tags": tags_list,
            "user_id": user["user_id"]  # Додаємо user_id
        }).execute()

        if not insert_result.data:
            raise Exception("Supabase insert повернув порожній результат")

        db_inserted = True
        print(f"✅ Supabase OK (id: {doc_id[:8]}...)")

        # Крок 3: Індексуємо в Qdrant
        print(f"🔍 [3/4] Індексація в Qdrant...")
        try:
            blocks = extract_text_with_formatting(content, file.filename)

            # Перевіряємо чи є блоки
            if not blocks or len(blocks) == 0:
                raise ValueError("Витягнуто 0 блоків з форматуванням - використовую fallback")

            blocks_with_structure = detect_document_structure(blocks)
            index_document_with_structure(blocks_with_structure, doc_id, document_type="regulatory")
            print(f"✅ Qdrant OK ({len(blocks)} блоків з форматуванням)")
        except Exception as e:
            # Fallback на звичайне витягування тексту
            print(f"⚠️ Не вдалося витягнути форматування: {e}")
            print(f"📝 Використовую базове витягування тексту")
            text = extract_text(content, file.filename)

            if not text or len(text.strip()) == 0:
                raise Exception("Документ порожній або не містить текстового вмісту")

            index_document(text, doc_id, document_type="regulatory")
            print(f"✅ Qdrant OK (базове індексування, {len(text)} символів)")

        indexed_in_qdrant = True

        # Крок 4: Оновлюємо статус на ready (використовуємо admin для bypass RLS)
        print(f"✅ [4/4] Оновлення статусу...")
        supabase_admin.table("documents").update(
            {"status": "ready"}
        ).eq("id", doc_id).execute()
        print(f"✅ Статус оновлено")

        # Витягуємо правила у фоновому режимі (не блокуємо відповідь!)
        print(f"📋 Додаю завдання на витягування правил у фоновий режим...")
        background_tasks.add_task(extract_rules_background, doc_id, file.filename)

        print(f"🎉 Документ успішно завантажено: {file.filename}")
        return {
            "id": doc_id,
            "filename": file.filename,
            "status": "ready",
            "document_type": "regulatory",
            "extraction_status": "pending",
            "message": "Документ завантажено. Правила витягуються у фоновому режимі."
        }

    except Exception as e:
        # ROLLBACK: Відкочуємо всі зміни
        import traceback
        error_msg = f"Помилка при завантаженні документа: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"🔍 Traceback: {traceback.format_exc()}")

        # Відкочуємо в зворотному порядку
        if indexed_in_qdrant:
            print(f"🔄 Rollback: Видаляємо з Qdrant...")
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                from config import qdrant
                # Знаходимо всі точки для цього документа
                results = qdrant.scroll(
                    collection_name="edu_docs",
                    scroll_filter=Filter(
                        must=[FieldCondition(
                            key="doc_id",
                            match=MatchValue(value=doc_id)
                        )]
                    ),
                    limit=1000
                )
                point_ids = [p.id for p in results[0]]
                if point_ids:
                    qdrant.delete(collection_name="edu_docs", points_selector=point_ids)
                    print(f"✅ Видалено {len(point_ids)} точок з Qdrant")
            except Exception as rollback_error:
                print(f"⚠️ Не вдалося відкотити Qdrant: {rollback_error}")

        if db_inserted:
            print(f"🔄 Rollback: Видаляємо з Supabase БД...")
            try:
                supabase_admin.table("documents").delete().eq("id", doc_id).execute()
                print(f"✅ Видалено запис з Supabase")
            except Exception as rollback_error:
                print(f"⚠️ Не вдалося відкотити Supabase: {rollback_error}")

        if storage_uploaded:
            print(f"🔄 Rollback: Видаляємо з Storage...")
            try:
                supabase.storage.from_("documents").remove([storage_filename])
                print(f"✅ Видалено файл з Storage")
            except Exception as rollback_error:
                print(f"⚠️ Не вдалося відкотити Storage: {rollback_error}")

        # Повертаємо помилку
        raise HTTPException(
            status_code=500,
            detail=f"Не вдалося завантажити документ: {str(e)}"
        )


@app.get("/documents/{doc_id}/extraction-status")
def get_extraction_status(doc_id: str, user: dict = Depends(get_current_user)):
    """Перевірити статус витягування правил"""
    # Перевіряємо доступ до документа
    verify_document_access(doc_id, user)

    user_supabase = get_user_supabase(user["access_token"])
    result = user_supabase.table("documents").select(
        "id, filename, extraction_status, extracted_rules"
    ).eq("id", doc_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Документ не знайдено")

    doc = result.data[0]
    extraction_status = doc.get("extraction_status", "unknown")
    rules_count = len(doc.get("extracted_rules", [])) if doc.get("extracted_rules") else 0

    return {
        "id": doc["id"],
        "filename": doc["filename"],
        "extraction_status": extraction_status,
        "rules_count": rules_count,
        "is_completed": extraction_status == "completed",
        "is_failed": extraction_status == "failed"
    }


@app.get("/documents/{doc_id}/diagnostic")
def get_document_diagnostic(doc_id: str, user: dict = Depends(get_current_user)):
    """Діагностика стану документа (перевірка БД + Qdrant)"""
    # Перевіряємо доступ до документа
    verify_document_access(doc_id, user)

    # Інформація з БД
    user_supabase = get_user_supabase(user["access_token"])
    result = user_supabase.table("documents").select("*").eq("id", doc_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Документ не знайдено")

    doc = result.data[0]

    # Перевірка Qdrant
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    from config import qdrant

    qdrant_chunks = 0
    qdrant_error = None

    try:
        results = qdrant.scroll(
            collection_name="edu_docs",
            scroll_filter=Filter(
                must=[FieldCondition(
                    key="doc_id",
                    match=MatchValue(value=doc_id)
                )]
            ),
            limit=1000
        )
        qdrant_chunks = len(results[0]) if results and len(results) > 0 else 0
    except Exception as e:
        qdrant_error = str(e)

    # Визначаємо чи є проблеми
    issues = []

    if doc.get("status") != "ready":
        issues.append(f"Статус документа: {doc.get('status')} (очікується 'ready')")

    if qdrant_chunks == 0 and not qdrant_error:
        issues.append("Документ не проіндексований у векторній БД (0 чанків)")

    if qdrant_error:
        issues.append(f"Помилка доступу до Qdrant: {qdrant_error}")

    return {
        "id": doc_id,
        "filename": doc.get("filename"),
        "status": doc.get("status"),
        "document_type": doc.get("document_type"),
        "created_at": doc.get("created_at"),
        "storage_url": doc.get("storage_url"),
        "qdrant_chunks": qdrant_chunks,
        "qdrant_error": qdrant_error,
        "has_issues": len(issues) > 0,
        "issues": issues,
        "is_ready_for_validation": doc.get("status") == "ready" and qdrant_chunks > 0
    }


@app.get("/documents/{doc_id}/extraction-metrics")
def get_extraction_metrics(doc_id: str, user: dict = Depends(get_current_user)):
    """Отримати метрики витягування правил для документу"""
    # Перевіряємо доступ до документа
    verify_document_access(doc_id, user)

    user_supabase = get_user_supabase(user["access_token"])
    result = user_supabase.table("extraction_metrics").select("*").eq(
        "document_id", doc_id
    ).order("completed_at", desc=True).limit(5).execute()

    if not result.data:
        return {"message": "Метрики не знайдено", "metrics": []}

    return {"metrics": result.data}


@app.post("/documents/{doc_id}/reindex")
def reindex_document(doc_id: str, user: dict = Depends(get_current_user)):
    """Переіндексувати документ у Qdrant (якщо чанки втрачені)"""
    # Перевіряємо доступ до документа
    doc = verify_document_access(doc_id, user)

    print(f"🔄 Переіндексація документа {doc_id} ({doc.get('filename')})...")

    try:
        # Завантажуємо файл з storage
        storage_url = doc.get("storage_url")
        if not storage_url:
            raise HTTPException(status_code=400, detail="Документ не має файлу у storage")

        print(f"📥 Завантаження файлу з storage: {storage_url}")
        file_data = supabase.storage.from_("documents").download(storage_url)

        if not file_data:
            raise HTTPException(status_code=404, detail="Файл не знайдено у storage")

        # Видаляємо старі чанки з Qdrant (якщо є)
        print(f"🗑️ Видаляю старі чанки з Qdrant...")
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        from config import qdrant

        try:
            results = qdrant.scroll(
                collection_name="edu_docs",
                scroll_filter=Filter(
                    must=[FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id)
                    )]
                ),
                limit=1000
            )
            point_ids = [p.id for p in results[0]]
            if point_ids:
                qdrant.delete(collection_name="edu_docs", points_selector=point_ids)
                print(f"✅ Видалено {len(point_ids)} старих точок")
        except Exception as e:
            print(f"⚠️ Помилка при видаленні старих чанків: {e}")

        # Переіндексуємо документ
        print(f"🔍 Індексація документа...")
        try:
            blocks = extract_text_with_formatting(file_data, doc.get("filename"))

            # Перевіряємо чи є блоки
            if not blocks or len(blocks) == 0:
                raise ValueError("Витягнуто 0 блоків з форматуванням - використовую fallback")

            blocks_with_structure = detect_document_structure(blocks)
            index_document_with_structure(
                blocks_with_structure,
                doc_id,
                document_type=doc.get("document_type", "user")
            )
            print(f"✅ Документ переіндексовано ({len(blocks)} блоків)")
        except Exception as e:
            # Fallback на базове індексування
            print(f"⚠️ Не вдалося витягнути форматування: {e}")
            print(f"📝 Використовую базове індексування")
            text = extract_text(file_data, doc.get("filename"))

            if not text or len(text.strip()) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Документ порожній або не містить текстового вмісту. Перевірте файл."
                )

            index_document(text, doc_id, document_type=doc.get("document_type", "user"))
            print(f"✅ Документ переіндексовано (базове, {len(text)} символів)")

        # Оновлюємо статус
        supabase_admin.table("documents").update(
            {"status": "ready"}
        ).eq("id", doc_id).execute()

        return {
            "message": "Документ успішно переіндексовано",
            "id": doc_id,
            "filename": doc.get("filename")
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ Помилка при переіндексації: {e}")
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Помилка переіндексації: {str(e)}"
        )


@app.post("/validate/{doc_id}")
def validate_doc(doc_id: str, body: dict = None, user: dict = Depends(get_current_user)):
    """Валідувати документ проти вибраних нормативів

    body:
      {
        "categories": ["content", "formatting"],  // Які категорії перевіряти
        "regulatory_doc_ids": ["id1", "id2"],    // Конкретні нормативи (опціонально)
        "severity_filter": ["critical", "major"] // Фільтр по важливості (опціонально)
      }
    """
    # Перевіряємо доступ до документа
    verify_document_access(doc_id, user)

    # Параметри валідації
    categories = body.get("categories", []) if body else []
    regulatory_doc_ids = body.get("regulatory_doc_ids", []) if body else []
    severity_filter = body.get("severity_filter", []) if body else []

    print(f"🎯 Валідація з параметрами:")
    print(f"   - Категорії: {categories or 'всі'}")
    print(f"   - Конкретні нормативи: {len(regulatory_doc_ids) if regulatory_doc_ids else 'всі'}")
    print(f"   - Фільтр важливості: {severity_filter or 'всі'}")

    validation_result = validate_document(
        doc_id,
        categories=categories,
        regulatory_doc_ids=regulatory_doc_ids
    )

    if "error" in validation_result:
        raise HTTPException(status_code=400, detail=validation_result["error"])

    # Фільтруємо issues по severity якщо вказано
    if severity_filter and "issues" in validation_result:
        validation_result["issues"] = [
            issue for issue in validation_result["issues"]
            if issue.get("severity") in severity_filter
        ]
        # Оновлюємо summary
        validation_result["summary"]["total_issues"] = len(validation_result["issues"])

    return format_report_for_api(validation_result)


@app.get("/validate/{doc_id}/report")
def get_validation_report(doc_id: str, user: dict = Depends(get_current_user)):
    """Отримати збережений звіт валідації"""
    # Перевіряємо доступ до документа
    verify_document_access(doc_id, user)

    user_supabase = get_user_supabase(user["access_token"])
    result = user_supabase.table("validation_reports").select("*").eq(
        "user_document_id", doc_id
    ).order("created_at", desc=True).limit(1).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Звіт валідації не знайдено")

    report = result.data[0]
    return {
        "report_id": report["id"],
        "validation_result": report["validation_result"],
        "regulatory_documents": report["regulatory_documents"],
        "created_at": report["created_at"]
    }


@app.get("/validate/{doc_id}/report/download")
def download_validation_report(doc_id: str, user: dict = Depends(get_current_user)):
    """Скачати звіт валідації у DOCX форматі"""
    # Перевіряємо доступ до документа
    verify_document_access(doc_id, user)

    # Отримуємо останній звіт
    user_supabase = get_user_supabase(user["access_token"])
    result = user_supabase.table("validation_reports").select("*").eq(
        "user_document_id", doc_id
    ).order("created_at", desc=True).limit(1).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Звіт валідації не знайдено")

    report = result.data[0]
    validation_result = report["validation_result"]

    # Отримуємо ім'я документа
    user_supabase = get_user_supabase(user["access_token"])
    doc_result = user_supabase.table("documents").select("filename").eq("id", doc_id).execute()
    document_name = doc_result.data[0]["filename"] if doc_result.data else "Документ"

    # Генеруємо DOCX
    docx_bytes = export_validation_to_docx(validation_result, document_name)

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=validation_report_{doc_id}.docx"}
    )


@app.post("/chat/{doc_id}/validate")
def chat_validation(doc_id: str, body: dict, user: dict = Depends(get_current_user)):
    """Чат про результати валідації документа"""
    # Перевіряємо доступ до документа
    verify_document_access(doc_id, user)

    question = body.get("question", "").lower()

    # Отримуємо останній звіт валідації
    user_supabase = get_user_supabase(user["access_token"])
    result = user_supabase.table("validation_reports").select("*").eq(
        "user_document_id", doc_id
    ).order("created_at", desc=True).limit(1).execute()

    if not result.data:
        return {"answer": "❌ Звіт валідації не знайдено. Спочатку виконайте валідацію документа."}

    report = result.data[0]
    validation_result = report["validation_result"]

    # Якщо користувач хоче детальний звіт
    if any(keyword in question for keyword in ["звіт", "детально", "покажи", "результат", "показати"]):
        formatted_report = format_report_for_chat(validation_result)
        return {"answer": formatted_report}

    # Якщо користувач запитує про конкретну severity
    if "критичн" in question or "critical" in question:
        critical = [i for i in validation_result["issues"] if i["severity"] == "critical"]
        if not critical:
            return {"answer": "✅ Критичних проблем не виявлено!"}
        answer = f"🔴 Знайдено {len(critical)} критичних проблем:\n\n"
        for idx, issue in enumerate(critical[:5], 1):
            answer += f"{idx}. {issue['description']}\n"
        return {"answer": answer}

    if "важлив" in question or "major" in question:
        major = [i for i in validation_result["issues"] if i["severity"] == "major"]
        if not major:
            return {"answer": "✅ Важливих проблем не виявлено!"}
        answer = f"🟠 Знайдено {len(major)} важливих проблем:\n\n"
        for idx, issue in enumerate(major[:5], 1):
            answer += f"{idx}. {issue['description']}\n"
        return {"answer": answer}

    # За замовчуванням повертаємо форматований звіт
    formatted_report = format_report_for_chat(validation_result)
    return {"answer": formatted_report}


if __name__ == "__main__":
    import uvicorn
    print("🚀 Запуск EduAssistant Backend...")
    print("📖 Документація: http://localhost:8000/docs")
    # Для reload потрібно передавати app як string import
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)