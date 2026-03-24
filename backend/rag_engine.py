from config import qdrant
from qdrant_client.models import PointStruct, VectorParams, Distance, Filter, FieldCondition, MatchValue
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

COLLECTION = "edu_docs"
model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text: str) -> list:
    return model.encode(text).tolist()


def ensure_collection():
    collections = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION not in collections:
        qdrant.create_collection(
            COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )

    # Створюємо індекс для фільтрації по doc_id
    try:
        qdrant.create_payload_index(
            collection_name=COLLECTION,
            field_name="doc_id",
            field_schema="keyword"
        )
    except:
        pass  # Індекс вже існує

    # Створюємо індекс для document_type
    try:
        qdrant.create_payload_index(
            collection_name=COLLECTION,
            field_name="document_type",
            field_schema="keyword"
        )
    except:
        pass  # Індекс вже існує
def index_document(text: str, doc_id: str, document_type: str = "user", metadata: dict = None):
    """Індексація документа тільки з текстом (для зворотної сумісності)"""
    ensure_collection()

    # Збільшені параметри для кращого аналізу документів
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # Більше контексту в кожному чанку
        chunk_overlap=200     # Більше перекриття для збереження контексту
    )
    chunks = splitter.split_text(text)

    points = []
    for i, chunk in enumerate(chunks):
        vector = get_embedding(chunk)
        payload = {
            "doc_id": doc_id,
            "text": chunk,
            "document_type": document_type,
            "chunk_index": i
        }
        if metadata:
            payload["metadata"] = metadata

        points.append(PointStruct(
            id=abs(hash(f"{doc_id}_{i}")) % (10**9),
            vector=vector,
            payload=payload
        ))

    batch_size = 50
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        qdrant.upsert(collection_name=COLLECTION, points=batch)
        print(f"Завантажено {min(i + batch_size, len(points))}/{len(points)} чанків")

    return len(chunks)


def index_document_with_structure(blocks: list, doc_id: str, document_type: str = "user"):
    """Індексація документа з інформацією про структуру та форматування

    Args:
        blocks: Список блоків з форматуванням від extract_text_with_formatting()
        doc_id: ID документа
        document_type: Тип документа (user/regulatory)
    """
    ensure_collection()

    # Об'єднуємо блоки в чанки по 1000 символів
    chunks_data = []
    current_chunk = []
    current_length = 0
    chunk_index = 0

    for block in blocks:
        block_text = block.get("text", "")
        block_length = len(block_text)

        # Якщо додавання цього блоку перевищить ліміт - створюємо новий чанк
        if current_length + block_length > 1000 and current_chunk:
            # Зберігаємо поточний чанк
            chunks_data.append({
                "blocks": current_chunk.copy(),
                "chunk_index": chunk_index
            })
            chunk_index += 1
            current_chunk = []
            current_length = 0

        current_chunk.append(block)
        current_length += block_length

    # Додаємо останній чанк
    if current_chunk:
        chunks_data.append({
            "blocks": current_chunk.copy(),
            "chunk_index": chunk_index
        })

    # Створюємо points для Qdrant
    points = []
    for chunk_data in chunks_data:
        # Об'єднуємо текст блоків для embedding
        chunk_text = "\n".join([b.get("text", "") for b in chunk_data["blocks"]])
        vector = get_embedding(chunk_text)

        # Витягуємо метадані з першого блоку (для сумісності)
        first_block = chunk_data["blocks"][0] if chunk_data["blocks"] else {}

        payload = {
            "doc_id": doc_id,
            "text": chunk_text,
            "document_type": document_type,
            "chunk_index": chunk_data["chunk_index"],
            # Додаткова інформація про структуру
            "blocks": chunk_data["blocks"],  # Всі блоки з форматуванням
            "section": first_block.get("section", "ПОЧАТОК ДОКУМЕНТА"),
            "has_formatting": True
        }

        points.append(PointStruct(
            id=abs(hash(f"{doc_id}_{chunk_data['chunk_index']}")) % (10**9),
            vector=vector,
            payload=payload
        ))

    # Завантажуємо батчами
    batch_size = 50
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        qdrant.upsert(collection_name=COLLECTION, points=batch)
        print(f"Завантажено {min(i + batch_size, len(points))}/{len(points)} чанків з форматуванням")

    return len(chunks_data)

def search_context(doc_id: str, query: str, limit: int = 10) -> str:
    """
    Пошук релевантних чанків для запиту
    limit=10 для більш детального аналізу (раніше було 5)
    """
    query_vector = get_embedding(query)
    results = qdrant.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        query_filter=Filter(
            must=[FieldCondition(
                key="doc_id",
                match=MatchValue(value=doc_id)
            )]
        ),
        limit=limit
    )
    return "\n\n".join([r.payload["text"] for r in results.points])


def get_all_chunks_for_document(doc_id: str) -> list:
    """Витягнути всі чанки документа, відсортовані по chunk_index

    Повертає чанки з інформацією про структуру (якщо доступна)
    """
    results = qdrant.scroll(
        collection_name=COLLECTION,
        scroll_filter=Filter(
            must=[FieldCondition(
                key="doc_id",
                match=MatchValue(value=doc_id)
            )]
        ),
        limit=1000
    )

    chunks = []
    for point in results[0]:
        chunk = {
            "text": point.payload["text"],
            "chunk_index": point.payload.get("chunk_index", 0),
            "metadata": point.payload.get("metadata", {}),
        }

        # Додаємо інформацію про структуру якщо вона є
        if point.payload.get("has_formatting"):
            chunk["section"] = point.payload.get("section", "N/A")
            chunk["blocks"] = point.payload.get("blocks", [])
            chunk["has_formatting"] = True

        chunks.append(chunk)

    # Сортуємо по chunk_index
    chunks.sort(key=lambda x: x["chunk_index"])
    return chunks


def search_regulatory_context(query: str, limit: int = 10) -> str:
    """Пошук контексту тільки по нормативних документах"""
    query_vector = get_embedding(query)
    results = qdrant.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        query_filter=Filter(
            must=[FieldCondition(
                key="document_type",
                match=MatchValue(value="regulatory")
            )]
        ),
        limit=limit
    )
    return "\n\n".join([r.payload["text"] for r in results.points])