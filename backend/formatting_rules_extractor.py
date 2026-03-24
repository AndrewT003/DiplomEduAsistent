"""
Витягування СТРУКТУРОВАНИХ правил форматування з нормативних документів
Використовує LLM для витягування + парсинг в структуровані параметри
"""

import re
import json
from typing import List, Dict, Optional
from config import groq_client


def extract_formatting_rules_structured(
    text: str,
    document_name: str
) -> List[Dict]:
    """Витягує структуровані правила форматування з нормативного документа

    Args:
        text: Текст нормативного документа
        document_name: Назва документа

    Returns:
        Список структурованих правил з параметрами
    """

    prompt = f"""Ти — експерт з технічних стандартів оформлення документів (ДСТУ, стандарти).

Витягни СТРУКТУРОВАНІ правила оформлення з цього фрагменту.

ВАЖЛИВО: Для КОЖНОГО правила витягуй ТОЧНІ ЧИСЛОВІ ПАРАМЕТРИ!

Формат відповіді (JSON масив):
[
  {{
    "parameter_type": "font|margins|spacing|indent|page_size|alignment",
    "description": "Опис правила",
    "values": {{
      // Для font:
      "font_name": "Times New Roman",
      "font_size": 14,
      "unit": "pt"
    }},
    "section": "Розділ документа"
  }},
  {{
    "parameter_type": "margins",
    "description": "Поля сторінки",
    "values": {{
      "top": 2.0,
      "bottom": 2.0,
      "left": 3.0,
      "right": 1.5,
      "unit": "cm"
    }},
    "section": "Розділ 3.2"
  }},
  {{
    "parameter_type": "spacing",
    "description": "Міжрядковий інтервал",
    "values": {{
      "line_spacing": 1.5,
      "spacing_type": "multiple"
    }},
    "section": "Розділ 3.3"
  }},
  {{
    "parameter_type": "indent",
    "description": "Абзацний відступ",
    "values": {{
      "first_line": 1.25,
      "unit": "cm"
    }},
    "section": "Розділ 3.4"
  }},
  {{
    "parameter_type": "page_size",
    "description": "Розмір сторінки",
    "values": {{
      "width": 21.0,
      "height": 29.7,
      "unit": "cm",
      "standard": "A4"
    }},
    "section": "Розділ 3.1"
  }},
  {{
    "parameter_type": "alignment",
    "description": "Вирівнювання тексту",
    "values": {{
      "alignment": "justify"  // left|center|right|justify
    }},
    "section": "Розділ 3.5"
  }}
]

ТЕКСТ НОРМАТИВНОГО ДОКУМЕНТА "{document_name}":
{text[:12000]}

ВАЖЛИВО: Відповідай ТІЛЬКИ валідним JSON масивом! Без додаткового тексту!
Якщо правил багато - витягни найважливіші (шрифт, поля, інтервали, відступи)."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "Ти експерт з витягування структурованих правил форматування. "
                               "Відповідай ТІЛЬКИ валідним JSON з точними числовими параметрами."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=8000  # Збільшено для великих документів
        )

        content = response.choices[0].message.content
        print(f"🔍 RAW відповідь LLM ({len(content) if content else 0} символів):")
        print(f"   '{content[:200] if content else 'ПОРОЖНЯ ВІДПОВІДЬ'}'...")

        if not content or not content.strip():
            print(f"❌ LLM повернув порожню відповідь!")
            return []

        content = content.strip()

        # Очищаємо markdown та зайвий текст
        # Якщо є ```json - витягуємо тільки JSON між ```json та ```
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                content = content[start:end].strip()
        # Якщо є просто ``` - витягуємо між ними
        elif content.startswith("```"):
            content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        # Якщо є просто текст перед JSON - видаляємо все до [
        elif not content.startswith("[") and "[" in content:
            start = content.find("[")
            content = content[start:].strip()

        print(f"🔍 Після очищення ({len(content)} символів):")
        print(f"   '{content[:200]}'...")

        try:
            rules = json.loads(content)
            return rules
        except json.JSONDecodeError as e:
            print(f"⚠️ Спроба виправити неповний JSON...")

            # Якщо JSON обрізаний - спробуємо виправити
            # Знаходимо останній повний об'єкт
            last_complete_brace = content.rfind("}")
            if last_complete_brace > 0:
                # Обрізаємо до останнього повного об'єкта
                truncated = content[:last_complete_brace + 1]

                # Додаємо закриваючу дужку масиву якщо потрібно
                if not truncated.rstrip().endswith("]"):
                    truncated = truncated.rstrip()
                    # Видаляємо останню кому якщо є
                    if truncated.endswith(","):
                        truncated = truncated[:-1]
                    truncated += "\n]"

                try:
                    rules = json.loads(truncated)
                    print(f"✅ JSON виправлено! Витягнуто {len(rules)} правил (частина була обрізана)")
                    return rules
                except:
                    pass

            # Якщо виправлення не допомогло
            print(f"❌ Не вдалося виправити JSON")
            raise e

    except json.JSONDecodeError as e:
        print(f"❌ Помилка парсингу JSON: {e}")
        print(f"   Контент: '{content[:500] if 'content' in locals() else 'N/A'}'")
        return []
    except Exception as e:
        print(f"❌ Помилка витягування структурованих правил: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return []


def parse_text_rule_to_params(rule: Dict) -> Optional[Dict]:
    """Парсить текстове правило в структуровані параметри

    Args:
        rule: Текстове правило з полями requirement, check_criteria

    Returns:
        Структуроване правило або None
    """

    requirement = rule.get("requirement", "").lower()

    # === ШРИФТ ===
    if "шрифт" in requirement or "font" in requirement:
        # Шукаємо назву шрифту
        font_patterns = [
            r"times new roman",
            r"arial",
            r"calibri",
            r"courier new"
        ]

        font_name = None
        for pattern in font_patterns:
            if pattern in requirement:
                font_name = pattern.title()
                break

        # Шукаємо розмір (14pt, 14 pt, 14)
        size_match = re.search(r'(\d+\.?\d*)\s*(?:pt|пт|пунктів)?', requirement)
        font_size = float(size_match.group(1)) if size_match else None

        if font_name or font_size:
            return {
                "parameter_type": "font",
                "description": rule.get("requirement", ""),
                "values": {
                    "font_name": font_name,
                    "font_size": font_size,
                    "unit": "pt"
                },
                "section": rule.get("section", "N/A")
            }

    # === ПОЛЯ ===
    if "поля" in requirement or "поле" in requirement or "margin" in requirement:
        # Шукаємо числа (верхнє 2см, ліве 3см тощо)
        margins = {}

        top_match = re.search(r'верхн[єьня]+\s*[:\-]?\s*(\d+\.?\d*)\s*см', requirement)
        if top_match:
            margins["top"] = float(top_match.group(1))

        bottom_match = re.search(r'нижн[єьня]+\s*[:\-]?\s*(\d+\.?\d*)\s*см', requirement)
        if bottom_match:
            margins["bottom"] = float(bottom_match.group(1))

        left_match = re.search(r'лів[еоі]+\s*[:\-]?\s*(\d+\.?\d*)\s*см', requirement)
        if left_match:
            margins["left"] = float(left_match.group(1))

        right_match = re.search(r'прав[еоі]+\s*[:\-]?\s*(\d+\.?\d*)\s*см', requirement)
        if right_match:
            margins["right"] = float(right_match.group(1))

        if margins:
            margins["unit"] = "cm"
            return {
                "parameter_type": "margins",
                "description": rule.get("requirement", ""),
                "values": margins,
                "section": rule.get("section", "N/A")
            }

    # === МІЖРЯДКОВИЙ ІНТЕРВАЛ ===
    if "інтервал" in requirement or "spacing" in requirement:
        spacing_match = re.search(r'(\d+\.?\d*)', requirement)
        if spacing_match:
            return {
                "parameter_type": "spacing",
                "description": rule.get("requirement", ""),
                "values": {
                    "line_spacing": float(spacing_match.group(1)),
                    "spacing_type": "multiple"
                },
                "section": rule.get("section", "N/A")
            }

    # === АБЗАЦНИЙ ВІДСТУП ===
    if "відступ" in requirement or "indent" in requirement:
        indent_match = re.search(r'(\d+\.?\d*)\s*см', requirement)
        if indent_match:
            return {
                "parameter_type": "indent",
                "description": rule.get("requirement", ""),
                "values": {
                    "first_line": float(indent_match.group(1)),
                    "unit": "cm"
                },
                "section": rule.get("section", "N/A")
            }

    # === РОЗМІР СТОРІНКИ ===
    if "a4" in requirement or "а4" in requirement:
        return {
            "parameter_type": "page_size",
            "description": rule.get("requirement", ""),
            "values": {
                "width": 21.0,
                "height": 29.7,
                "unit": "cm",
                "standard": "A4"
            },
            "section": rule.get("section", "N/A")
        }

    # === ВИРІВНЮВАННЯ ===
    alignment_map = {
        "по ширині": "justify",
        "по лівому краю": "left",
        "по центру": "center",
        "по правому краю": "right",
        "justify": "justify",
        "left": "left",
        "center": "center",
        "right": "right"
    }

    for key, value in alignment_map.items():
        if key in requirement:
            return {
                "parameter_type": "alignment",
                "description": rule.get("requirement", ""),
                "values": {
                    "alignment": value
                },
                "section": rule.get("section", "N/A")
            }

    return None


def convert_text_rules_to_structured(text_rules: List[Dict]) -> List[Dict]:
    """Конвертує текстові правила в структуровані

    Args:
        text_rules: Список текстових правил з LLM

    Returns:
        Список структурованих правил
    """

    structured_rules = []

    for rule in text_rules:
        if rule.get("category") != "formatting":
            continue

        structured = parse_text_rule_to_params(rule)
        if structured:
            structured_rules.append(structured)

    return structured_rules


def apply_structured_rules_to_validator(
    structured_rules: List[Dict],
    validator,
    regulatory_doc_name: str = None
) -> List[Dict]:
    """Застосовує структуровані правила до спеціалізованого валідатора

    Args:
        structured_rules: Список структурованих правил
        validator: Екземпляр FormattingValidator
        regulatory_doc_name: Назва нормативного документа

    Returns:
        Список знайдених проблем
    """

    all_issues = []

    for rule in structured_rules:
        param_type = rule.get("parameter_type")
        values = rule.get("values", {})
        rule_section = rule.get("section", "N/A")
        rule_description = rule.get("description", "")

        try:
            issues = []

            if param_type == "font":
                if values.get("font_name") and values.get("font_size"):
                    issues = validator.validate_font(
                        expected_font=values["font_name"],
                        expected_size=int(values["font_size"])
                    )

            elif param_type == "margins":
                margin_params = {}
                if "top" in values:
                    margin_params["top_cm"] = values["top"]
                if "bottom" in values:
                    margin_params["bottom_cm"] = values["bottom"]
                if "left" in values:
                    margin_params["left_cm"] = values["left"]
                if "right" in values:
                    margin_params["right_cm"] = values["right"]

                if margin_params:
                    issues = validator.validate_margins(**margin_params)

            elif param_type == "spacing":
                if "line_spacing" in values:
                    issues = validator.validate_line_spacing(
                        expected_spacing=values["line_spacing"]
                    )

            elif param_type == "indent":
                if "first_line" in values:
                    issues = validator.validate_paragraph_indent(
                        expected_indent_cm=values["first_line"]
                    )

            elif param_type == "page_size":
                if "width" in values and "height" in values:
                    issues = validator.validate_page_size(
                        expected_width_cm=values["width"],
                        expected_height_cm=values["height"]
                    )

            elif param_type == "alignment":
                if "alignment" in values:
                    issues = validator.validate_alignment(
                        expected_alignment=values["alignment"]
                    )

            # Додаємо метадані нормативу до кожного issue
            for issue in issues:
                if regulatory_doc_name:
                    issue["regulatory_doc_name"] = regulatory_doc_name
                issue["section"] = rule_section

                # Якщо у валідатора не було опису правила, додаємо з rule
                if not issue.get("rule_description") and rule_description:
                    issue["rule_description"] = rule_description

            all_issues.extend(issues)

        except Exception as e:
            print(f"⚠️ Помилка застосування правила {param_type}: {e}")
            continue

    return all_issues
