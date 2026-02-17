"""Language detection and multilingual output (English, Kiswahili, Sheng)."""

# Fallback when Sheng is unclear
SHENG_FALLBACK_PREFIX = "Sheng beta: switched to Kiswahili for clarity.\n\n"


def detect_language(text: str) -> str:
    """
    Detect input language. Returns 'en', 'sw', or 'sheng'.
    """
    try:
        import langdetect
        lang = langdetect.detect(text)
        if lang == "sw":
            return "sw"
        text_lower = text.lower()
        sheng_markers = ["sasa", "sema", "buana", "msee", "noma", "poa", "vipi", "namna", "mzito"]
        if any(m in text_lower for m in sheng_markers):
            return "sheng"
        return "en"
    except Exception:
        return "en"


def translate_answer(
    answer_en: str,
    target_lang: str,
    question: str,
    llm=None,
) -> str:
    """
    Translate an English answer to Kiswahili or Sheng using OpenAI.
    Falls back to Kiswahili if Sheng is unclear.
    """
    from .config import OPENAI_API_KEY

    if target_lang == "en":
        return answer_en

    if not OPENAI_API_KEY:
        return answer_en

    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    if target_lang == "sw":
        prompt = f"""Translate this answer about Kenyan law from English to Kiswahili.
Use simple, clear Kiswahili that citizens can understand.

English: {answer_en}

Kiswahili:"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    elif target_lang == "sheng":
        prompt = f"""Translate this answer about Kenyan law from English to Sheng (Kenyan youth slang).
Keep it respectful and clear. Use common Sheng words that Nairobi youth would understand.

IMPORTANT: If you are unsure how to translate this safely or clearly in Sheng, respond with EXACTLY: FALLBACK_TO_KISWAHILI

English: {answer_en}

Sheng (or FALLBACK_TO_KISWAHILI if unclear):"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        sheng_result = response.choices[0].message.content.strip()

        if "FALLBACK_TO_KISWAHILI" in sheng_result.upper():
            kisw = translate_answer(answer_en, "sw", question, llm)
            return SHENG_FALLBACK_PREFIX + kisw

        return sheng_result

    return answer_en