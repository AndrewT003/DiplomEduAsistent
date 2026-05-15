"""
Тестовий скрипт для перевірки чанків документа у Qdrant
"""
from config import qdrant
from qdrant_client.models import Filter, FieldCondition, MatchValue

# ID документа, який ви намагаєтеся валідувати
doc_id = "4d9953ff-e68f-4943-9a90-2682d786ff32"

print(f"🔍 Перевірка документа: {doc_id}")
print("=" * 60)

try:
    # Отримуємо чанки з Qdrant
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

    points = results[0] if results and len(results) > 0 else []

    print(f"📊 Знайдено чанків у Qdrant: {len(points)}")

    if points:
        print(f"\n✅ Документ проіндексований!")
        print(f"Перший чанк (приклад):")
        print(f"  - Text (перші 100 символів): {points[0].payload.get('text', '')[:100]}")
        print(f"  - Document type: {points[0].payload.get('document_type')}")
        print(f"  - Chunk index: {points[0].payload.get('chunk_index')}")
    else:
        print(f"\n❌ ПРОБЛЕМА: Документ НЕ проіндексований у Qdrant!")
        print(f"   Це означає, що при завантаженні документа виникла помилка.")
        print(f"\n   Рішення:")
        print(f"   1. Перевірте логи при завантаженні документа")
        print(f"   2. Спробуйте завантажити документ заново")
        print(f"   3. Або використайте POST /documents/{doc_id}/reindex")

except Exception as e:
    print(f"❌ Помилка при перевірці Qdrant: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)

# Перевіряємо також БД
from config import supabase

print(f"\n🔍 Перевірка документа в БД...")
result = supabase.table("documents").select("*").eq("id", doc_id).execute()

if result.data:
    doc = result.data[0]
    print(f"✅ Документ знайдено в БД:")
    print(f"  - Filename: {doc.get('filename')}")
    print(f"  - Status: {doc.get('status')}")
    print(f"  - Document type: {doc.get('document_type')}")
    print(f"  - Storage URL: {doc.get('storage_url')}")
    print(f"  - Created at: {doc.get('created_at')}")
else:
    print(f"❌ Документ НЕ знайдено в БД!")

print("=" * 60)