from typing import Dict


def format_report_for_api(validation_result: Dict) -> Dict:
    """Форматує звіт для API відповіді (JSON)"""
    return {
        "overall_compliance": validation_result.get("overall_compliance", "unknown"),
        "compliance_score": validation_result.get("compliance_score", 0.0),
        "summary": validation_result.get("summary", {}),
        "issues": validation_result.get("issues", []),
        "report_id": validation_result.get("report_id")
    }


def format_report_for_chat(validation_result: Dict) -> str:
    """Форматує звіт у markdown для чату з emoji"""

    compliance = validation_result.get("overall_compliance", "unknown")
    score = validation_result.get("compliance_score", 0.0)
    summary = validation_result.get("summary", {})
    issues = validation_result.get("issues", [])

    # Emoji для статусу
    status_emoji = {
        "pass": "✅",
        "partial": "⚠️",
        "fail": "❌",
        "unknown": "❓"
    }

    # Emoji для severity
    severity_emoji = {
        "critical": "🔴",
        "major": "🟠",
        "minor": "🟡",
        "info": "🔵"
    }

    report_lines = [
        f"# {status_emoji.get(compliance, '❓')} Звіт валідації документа\n",
        f"**Загальна відповідність:** {compliance.upper()}",
        f"**Оцінка відповідності:** {score * 100:.1f}%\n",
        "## 📊 Підсумок\n"
    ]

    # Підсумок проблем
    total = summary.get("total_issues", 0)
    if total == 0:
        report_lines.append("✅ Проблем не виявлено! Документ відповідає всім нормативним вимогам.\n")
    else:
        report_lines.extend([
            f"**Загальна кількість проблем:** {total}",
            f"- {severity_emoji['critical']} Критичні: {summary.get('critical', 0)}",
            f"- {severity_emoji['major']} Важливі: {summary.get('major', 0)}",
            f"- {severity_emoji['minor']} Незначні: {summary.get('minor', 0)}",
            f"- {severity_emoji['info']} Інформаційні: {summary.get('info', 0)}\n"
        ])

    # Детальний список проблем
    if issues:
        report_lines.append("## 🔍 Виявлені проблеми\n")

        # Групуємо по severity
        for severity in ["critical", "major", "minor", "info"]:
            severity_issues = [i for i in issues if i.get("severity") == severity]

            if severity_issues:
                severity_label = {
                    "critical": "Критичні проблеми",
                    "major": "Важливі проблеми",
                    "minor": "Незначні проблеми",
                    "info": "Інформаційні зауваження"
                }
                report_lines.append(f"### {severity_emoji[severity]} {severity_label[severity]}\n")

                for idx, issue in enumerate(severity_issues, 1):
                    # Заголовок з розділом документа
                    user_section = issue.get('user_document_section', '')
                    if user_section and user_section != 'N/A':
                        report_lines.append(f"**{idx}. РОЗДІЛ '{user_section[:60]}...' - {issue.get('description', 'Невідома проблема')}**")
                    else:
                        report_lines.append(f"**{idx}. {issue.get('description', 'Невідома проблема')}**")

                    report_lines.extend([
                        f"- **Нормативний документ:** {issue.get('regulatory_doc_name', 'N/A')}",
                        f"- **Розділ нормативу:** {issue.get('regulatory_section', issue.get('section', 'N/A'))}",
                        f"- **Категорія:** {issue.get('category', 'N/A')}",
                    ])

                    fragment = issue.get('user_doc_fragment', '')
                    if fragment:
                        report_lines.append(f"- **Фрагмент документа:** \"{fragment[:150]}...\"")

                    recommendation = issue.get('recommendation', '')
                    if recommendation:
                        report_lines.append(f"- **Рекомендація:** {recommendation}")

                    report_lines.append("")  # Порожній рядок між проблемами

    # Фінальні рекомендації
    report_lines.extend([
        "## 💡 Загальні рекомендації\n"
    ])

    if compliance == "pass":
        report_lines.append("Документ повністю відповідає нормативним вимогам. Чудова робота! 🎉")
    elif compliance == "partial":
        report_lines.append("Документ частково відповідає вимогам. Рекомендується виправити виявлені проблеми для повної відповідності.")
    elif compliance == "fail":
        report_lines.append("Документ має значні невідповідності. Необхідно терміново виправити критичні та важливі проблеми перед поданням.")
    else:
        report_lines.append("Не вдалося визначити рівень відповідності. Перевірте звіт детально.")

    return "\n".join(report_lines)


def format_issue_summary(issues: list) -> str:
    """Коротке форматування списку проблем для швидкого перегляду"""

    if not issues:
        return "✅ Проблем не виявлено"

    lines = ["Виявлені проблеми:\n"]

    severity_emoji = {
        "critical": "🔴",
        "major": "🟠",
        "minor": "🟡",
        "info": "🔵"
    }

    for idx, issue in enumerate(issues[:10], 1):  # Показуємо перші 10
        emoji = severity_emoji.get(issue.get("severity"), "⚪")
        desc = issue.get("description", "Невідома проблема")
        lines.append(f"{emoji} {idx}. {desc}")

    if len(issues) > 10:
        lines.append(f"\n... та ще {len(issues) - 10} проблем")

    return "\n".join(lines)
