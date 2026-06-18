"""
Перевірка тестів студентів проти еталонних відповідей
Генерує звіти у форматі validation_result
"""

from typing import List, Dict


def compare_test_answers(
    student_answers: List[Dict],
    answer_key: List[Dict],
    student_doc_name: str = "Тест студента",
    answer_key_name: str = "Еталон відповідей"
) -> Dict:
    """Порівнює відповіді студента з еталонними та генерує звіт у форматі validation_result

    Args:
        student_answers: Відповіді студента у форматі:
            [{"question_number": 1, "selected_answer": "b"}]
        answer_key: Еталонні питання з правильними відповідями
        student_doc_name: Назва документа студента
        answer_key_name: Назва еталону

    Returns:
        Словник у форматі validation_result:
        {
            "overall_compliance": "pass|partial|fail",
            "compliance_score": 0.0-1.0,
            "issues": [...],
            "summary": {...},
            "test_details": {
                "total_questions": X,
                "correct_answers": X,
                "incorrect_answers": X,
                "unanswered": X,
                "percentage": X
            }
        }
    """

    issues = []
    total_questions = len(answer_key)
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0

    # Створюємо мапу відповідей студента для швидкого доступу
    student_answer_map = {
        ans["question_number"]: ans["selected_answer"]
        for ans in student_answers
    }

    # Перевіряємо кожне питання
    for question in answer_key:
        q_num = question["question_number"]
        correct_answer = question.get("correct_answer")
        question_text = question.get("question_text", f"Питання {q_num}")
        options = question.get("options", {})

        # Отримуємо відповідь студента
        student_answer = student_answer_map.get(q_num)

        # Якщо студент не відповів
        if student_answer is None:
            unanswered_count += 1
            issues.append({
                "severity": "major",
                "category": "test_answer",
                "description": f"Питання {q_num}: Відповідь відсутня",
                "location": f"Питання №{q_num}",
                "question_number": q_num,
                "question_text": question_text,
                "expected": f"{correct_answer}) {options.get(correct_answer, 'N/A')}" if correct_answer else "Не вказано",
                "actual": "Немає відповіді",
                "regulatory_doc_name": answer_key_name
            })
            continue

        # Якщо відповідь неправильна
        if student_answer != correct_answer:
            incorrect_count += 1

            # Формуємо детальний опис
            expected_text = options.get(correct_answer, "N/A") if correct_answer else "Не вказано в еталоні"
            actual_text = options.get(student_answer, student_answer)

            issues.append({
                "severity": "major",
                "category": "test_answer",
                "description": f"Питання {q_num}: Неправильна відповідь. Правильна: {correct_answer}) {expected_text}",
                "location": f"Питання №{q_num}",
                "question_number": q_num,
                "question_text": question_text,
                "expected": f"{correct_answer}) {expected_text}",
                "actual": f"{student_answer}) {actual_text}",
                "regulatory_doc_name": answer_key_name
            })
        else:
            # Відповідь правильна
            correct_count += 1

    # Обчислюємо метрики
    percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
    compliance_score = correct_count / total_questions if total_questions > 0 else 0

    # Визначаємо загальний статус
    if percentage >= 90:
        overall_compliance = "pass"
    elif percentage >= 60:
        overall_compliance = "partial"
    else:
        overall_compliance = "fail"

    # Формуємо summary у форматі validation_result
    summary = {
        "total_issues": len(issues),
        "critical": 0,  # Для тестів не використовуємо critical
        "major": incorrect_count + unanswered_count,  # Неправильні та пропущені
        "minor": 0,
        "info": 0
    }

    # Детальна інформація про тест
    test_details = {
        "total_questions": total_questions,
        "correct_answers": correct_count,
        "incorrect_answers": incorrect_count,
        "unanswered": unanswered_count,
        "percentage": round(percentage, 2)
    }

    print(f"\n📊 Результати перевірки тесту:")
    print(f"   Всього питань: {total_questions}")
    print(f"   Правильних: {correct_count} ✅")
    print(f"   Неправильних: {incorrect_count} ❌")
    print(f"   Без відповіді: {unanswered_count} ⚠️")
    print(f"   Відсоток: {percentage:.1f}%")
    print(f"   Статус: {overall_compliance}")

    return {
        "overall_compliance": overall_compliance,
        "compliance_score": compliance_score,
        "issues": issues,
        "summary": summary,
        "test_details": test_details
    }


def generate_test_report_text(validation_result: Dict) -> str:
    """Генерує текстовий звіт про результати тестування

    Args:
        validation_result: Результат перевірки тесту

    Returns:
        Форматований текстовий звіт
    """

    test_details = validation_result.get("test_details", {})
    issues = validation_result.get("issues", [])

    report = []
    report.append("=" * 60)
    report.append("ЗВІТ ПРО РЕЗУЛЬТАТИ ТЕСТУВАННЯ")
    report.append("=" * 60)
    report.append("")

    # Загальна статистика
    report.append("📊 ЗАГАЛЬНА СТАТИСТИКА:")
    report.append(f"   Всього питань: {test_details.get('total_questions', 0)}")
    report.append(f"   Правильних відповідей: {test_details.get('correct_answers', 0)} ✅")
    report.append(f"   Неправильних відповідей: {test_details.get('incorrect_answers', 0)} ❌")
    report.append(f"   Без відповіді: {test_details.get('unanswered', 0)} ⚠️")
    report.append(f"   Відсоток правильних: {test_details.get('percentage', 0):.1f}%")
    report.append("")

    # Оцінка
    percentage = test_details.get('percentage', 0)
    if percentage >= 90:
        grade = "Відмінно"
        emoji = "🌟"
    elif percentage >= 75:
        grade = "Добре"
        emoji = "👍"
    elif percentage >= 60:
        grade = "Задовільно"
        emoji = "📝"
    else:
        grade = "Незадовільно"
        emoji = "📉"

    report.append(f"{emoji} ОЦІНКА: {grade}")
    report.append("")

    # Детальний розбір помилок
    if issues:
        report.append("=" * 60)
        report.append("❌ ДЕТАЛЬНИЙ РОЗБІР ПОМИЛОК:")
        report.append("=" * 60)
        report.append("")

        for idx, issue in enumerate(issues, 1):
            q_num = issue.get("question_number", "?")
            q_text = issue.get("question_text", "N/A")
            expected = issue.get("expected", "N/A")
            actual = issue.get("actual", "N/A")

            report.append(f"{idx}. Питання №{q_num}:")
            report.append(f"   Текст: {q_text}")
            report.append(f"   Правильна відповідь: {expected}")
            report.append(f"   Відповідь студента: {actual}")
            report.append("")
    else:
        report.append("✅ ПОМИЛОК НЕ ВИЯВЛЕНО!")
        report.append("")

    report.append("=" * 60)

    return "\n".join(report)


def calculate_grade(percentage: float) -> Dict:
    """Розраховує оцінку на основі відсотка правильних відповідей

    Args:
        percentage: Відсоток правильних відповідей (0-100)

    Returns:
        Словник з оцінкою:
        {
            "numeric": 5,  # За 5-бальною шкалою
            "ects": "A",   # За шкалою ECTS
            "text": "Відмінно"
        }
    """

    if percentage >= 90:
        return {"numeric": 5, "ects": "A", "text": "Відмінно"}
    elif percentage >= 82:
        return {"numeric": 5, "ects": "B", "text": "Відмінно"}
    elif percentage >= 75:
        return {"numeric": 4, "ects": "C", "text": "Добре"}
    elif percentage >= 67:
        return {"numeric": 4, "ects": "D", "text": "Добре"}
    elif percentage >= 60:
        return {"numeric": 3, "ects": "E", "text": "Задовільно"}
    elif percentage >= 35:
        return {"numeric": 2, "ects": "FX", "text": "Незадовільно з можливістю повторного складання"}
    else:
        return {"numeric": 2, "ects": "F", "text": "Незадовільно з обов'язковим повторним вивченням"}
