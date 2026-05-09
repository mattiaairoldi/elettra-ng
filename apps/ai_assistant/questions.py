import re
import unicodedata


def normalize_diagnostic_question(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = normalized.lower()
    normalized = normalized.replace("\u2019", "'").replace("`", "'").replace("\u2018", "'")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(normalized.split())


def append_unique_diagnostic_questions(existing_questions, new_questions):
    questions = [question for question in existing_questions if isinstance(question, str) and question.strip()]
    seen = {normalize_diagnostic_question(question) for question in questions}
    for question in new_questions:
        if not isinstance(question, str):
            continue
        cleaned_question = question.strip()
        normalized_question = normalize_diagnostic_question(cleaned_question)
        if not cleaned_question or not normalized_question or normalized_question in seen:
            continue
        questions.append(cleaned_question)
        seen.add(normalized_question)
    return questions
