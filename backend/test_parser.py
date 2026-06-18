"""
Парсер тестів для витягування питань, варіантів відповідей та правильних відповідей
"""

import re
from typing import List, Dict, Optional


def parse_test_document(text: str) -> List[Dict]:
    """Парсить текст тесту та витягує питання з відповідями

    Args:
        text: Текст документа з тестом

    Returns:
        Список питань у форматі:
        [
            {
                "question_number": 1,
                "question_text": "Яка столиця України?",
                "options": {
                    "a": "Львів",
                    "b": "Київ",
                    "c": "Харків"
                },
                "correct_answer": "b"  # або None якщо не знайдено
            }
        ]
    """

    questions = []

    # ФОРМАТ 1: Питання + "Правильна відповідь: X"
    # Приклад: Питання 1: текст... Правильна відповідь: В
    simple_pattern = r'Питання\s*(\d+)\s*:\s*(.*?)\s*Правильна відповідь\s*:\s*([A-ZА-ЯЄІЇҐa-zа-яєіїґ])'

    simple_matches = re.finditer(simple_pattern, text, re.DOTALL | re.IGNORECASE)

    for match in simple_matches:
        question_num = int(match.group(1))
        question_text = match.group(2).strip()
        correct_answer = match.group(3).strip().lower()

        questions.append({
            "question_number": question_num,
            "question_text": question_text,
            "options": {},  # Немає варіантів у цьому форматі
            "correct_answer": correct_answer
        })

    # Якщо знайшли питання у простому форматі, повертаємо їх
    if questions:
        print(f"📝 Розпарсено {len(questions)} питань (формат: Питання + Правильна відповідь)")
        return questions

    # ФОРМАТ 2: Питання з варіантами відповідей
    # Розбиваємо текст на блоки питань
    question_pattern = r'(?:^|\n)\s*(?:Питання\s*)?(\d+)[.:\)]\s*(?:Питання:?\s*)?(.*?)(?=(?:\n\s*(?:Питання\s*)?\d+[.:\)])|$)'

    question_blocks = re.finditer(question_pattern, text, re.DOTALL | re.IGNORECASE | re.MULTILINE)

    for match in question_blocks:
        question_num = int(match.group(1))
        question_block = match.group(2).strip()

        # Парсимо питання та варіанти
        parsed_question = parse_question_block(question_num, question_block)

        if parsed_question:
            questions.append(parsed_question)

    print(f"📝 Розпарсено {len(questions)} питань (формат з варіантами)")
    return questions


def parse_question_block(question_num: int, block: str) -> Optional[Dict]:
    """Парсить окремий блок питання

    Args:
        question_num: Номер питання
        block: Текст блоку з питанням та варіантами

    Returns:
        Словник з питанням та варіантами або None
    """

    lines = block.split('\n')
    question_text = ""
    options = {}
    correct_answer = None

    # Перший рядок (або кілька) - це текст питання
    # Варіанти зазвичай починаються з a), А., 1), тощо
    option_pattern = r'^\s*([a-zа-яєіїґA-ZА-ЯЄІЇҐ]|\d+)[.:\)]\s*(.*?)(\s*[✓✔+*]|\s*\(правильн[аі]\)|\s*\[правильн[аі]\])?$'

    in_options = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Перевіряємо чи це варіант відповіді
        option_match = re.match(option_pattern, line, re.IGNORECASE)

        if option_match:
            in_options = True
            option_letter = option_match.group(1).lower()
            option_text = option_match.group(2).strip()
            marker = option_match.group(3)

            options[option_letter] = option_text

            # Перевіряємо чи це правильна відповідь
            if marker:
                correct_answer = option_letter
        else:
            # Якщо ще не дійшли до варіантів - це текст питання
            if not in_options:
                if question_text:
                    question_text += " " + line
                else:
                    question_text = line

    if not question_text or not options:
        return None

    return {
        "question_number": question_num,
        "question_text": question_text,
        "options": options,
        "correct_answer": correct_answer
    }


def extract_student_answers(text: str, answer_key: List[Dict]) -> List[Dict]:
    """Витягує відповіді студента з документа

    Args:
        text: Текст з відповідями студента
        answer_key: Еталонні питання для співставлення

    Returns:
        Список відповідей студента у форматі:
        [
            {
                "question_number": 1,
                "selected_answer": "b"
            }
        ]
    """

    student_answers = []

    # ФОРМАТ 1: "Питання X: текст... Відповідь: Y" або "Правильна відповідь: Y"
    # Підтримка українського формату
    answer_format_1 = r'(?:Питання\s*(\d+)\s*:.*?)?(?:Правильна\s+відповідь|Відповідь|Відповідь\s+на\s+питання\s+(\d+))\s*:\s*([A-ZА-ЯЄІЇҐa-zа-яєіїґ])'

    matches_1 = re.finditer(answer_format_1, text, re.DOTALL | re.IGNORECASE)

    for match in matches_1:
        q_num = int(match.group(1) or match.group(2) or 0)
        if q_num > 0:
            answer = match.group(3).strip().lower()
            student_answers.append({
                "question_number": q_num,
                "selected_answer": answer
            })

    # Якщо знайшли відповіді у форматі "Відповідь: X", повертаємо їх
    if student_answers:
        print(f"📝 Витягнуто {len(student_answers)} відповідей студента (формат: Відповідь)")
        return student_answers

    # ФОРМАТ 2: "Питання X: текст?\n А) текст відповіді"
    # Студент пише літеру з текстом на наступному рядку після питання
    question_answer_pattern = r'Питання\s*(\d+)\s*:.*?\n\s*([A-ZА-ЯЄІЇҐa-zа-яєіїґ])\)'

    matches_2 = re.finditer(question_answer_pattern, text, re.DOTALL | re.IGNORECASE)

    for match in matches_2:
        q_num = int(match.group(1))
        answer = match.group(2).strip().lower()
        student_answers.append({
            "question_number": q_num,
            "selected_answer": answer
        })

    if student_answers:
        print(f"📝 Витягнуто {len(student_answers)} відповідей студента (формат: Питання + літера варіанту)")
        return student_answers

    # ФОРМАТ 3: Шукаємо формат "1. b)" або "1) b" або "1: b"
    answer_pattern = r'(?:^|\n)\s*(\d+)[.:\)]\s*([a-zа-яєіїґ]|\d+)[.:\)]?'

    matches = re.finditer(answer_pattern, text, re.MULTILINE | re.IGNORECASE)

    for match in matches:
        q_num = int(match.group(1))
        answer = match.group(2).lower()

        student_answers.append({
            "question_number": q_num,
            "selected_answer": answer
        })

    # Якщо не знайшли відповіді таким способом, пробуємо інший підхід
    if not student_answers:
        # Спроба 2: Шукаємо позначки в тексті самих питань (якщо студент позначив відповіді в копії тесту)
        for q in answer_key:
            q_num = q["question_number"]
            # Шукаємо блок цього питання
            question_block_pattern = rf'(?:^|\n)\s*(?:Питання\s*)?{q_num}[.:\)]\s*(.*?)(?=(?:\n\s*(?:Питання\s*)?\d+[.:\)])|$)'
            block_match = re.search(question_block_pattern, text, re.DOTALL | re.IGNORECASE)

            if block_match:
                block = block_match.group(1)
                # Шукаємо позначену відповідь
                for opt_letter in q["options"].keys():
                    # Шукаємо варіант з позначкою
                    marked_pattern = rf'\b{opt_letter}[.:\)]\s*.*?(\s*[✓✔+*Xx]|\s*\(вибран[аі]\))'
                    if re.search(marked_pattern, block, re.IGNORECASE):
                        student_answers.append({
                            "question_number": q_num,
                            "selected_answer": opt_letter
                        })
                        break

    print(f"📝 Витягнуто {len(student_answers)} відповідей студента")
    return student_answers


def validate_test_structure(questions: List[Dict]) -> Dict:
    """Валідує структуру розпарсеного тесту

    Args:
        questions: Список питань

    Returns:
        Словник з результатом валідації:
        {
            "valid": True/False,
            "errors": ["список помилок"],
            "warnings": ["список попереджень"]
        }
    """

    errors = []
    warnings = []

    if not questions:
        errors.append("Не знайдено жодного питання в документі")
        return {"valid": False, "errors": errors, "warnings": warnings}

    # Визначаємо чи це тест БЕЗ варіантів (формат: тільки правильна відповідь)
    has_options = any(q.get("options") and len(q["options"]) > 0 for q in questions)

    # Перевіряємо кожне питання
    for q in questions:
        q_num = q["question_number"]

        # Перевірка наявності тексту питання
        if not q.get("question_text"):
            errors.append(f"Питання {q_num}: відсутній текст питання")

        # Перевірка варіантів (тільки якщо в тесті є варіанти)
        if has_options:
            if not q.get("options") or len(q["options"]) < 2:
                errors.append(f"Питання {q_num}: недостатньо варіантів відповідей (мінімум 2)")

        # Перевірка правильної відповіді (для еталону)
        if q.get("correct_answer") is None:
            warnings.append(f"Питання {q_num}: не знайдено позначки правильної відповіді")
        elif has_options and q["correct_answer"] not in q.get("options", {}):
            errors.append(f"Питання {q_num}: правильна відповідь '{q['correct_answer']}' не знайдена серед варіантів")

    # Перевірка нумерації
    question_numbers = [q["question_number"] for q in questions]
    if question_numbers != list(range(1, len(questions) + 1)):
        warnings.append(f"Нумерація питань не послідовна: {question_numbers}")

    valid = len(errors) == 0

    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings
    }
