from docx import Document
import sys
import re

# Читаємо docx файл
doc_path = r"C:\Users\kaktu\Downloads\summary (7).docx"
doc = Document(doc_path)

print("=" * 80)
print("VMIST DOKUMENTA:")
print("=" * 80)

markdown_count = 0

for i, para in enumerate(doc.paragraphs, 1):
    text = para.text
    if text.strip():  # Пропускаємо порожні параграфи
        # Перевіряємо наявність markdown символів
        has_markdown = False
        markdown_symbols = []

        if re.search(r'^#{1,6}\s', text):
            markdown_symbols.append('# (zagolovok)')
            has_markdown = True
        if '**' in text:
            markdown_symbols.append('** (zhyrnyi)')
            has_markdown = True
        if re.search(r'(?<!\*)\*(?!\*)', text):
            markdown_symbols.append('* (kuryv)')
            has_markdown = True

        if has_markdown:
            markdown_count += 1
            print(f"{i}. [MARKDOWN!] {text[:100]}...")
            print(f"   Symbols: {', '.join(markdown_symbols)}")
        else:
            print(f"{i}. OK: {text[:80]}...")

print("=" * 80)
print(f"Znaideno paragrafiw z markdown: {markdown_count}")
print("Analiz zaversheno")
