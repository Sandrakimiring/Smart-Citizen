"""Language detection and multilingual output (English, Kiswahili, Sheng)."""

from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLLM

# Fallback when Sheng is unclear
SHENG_FALLBACK_PREFIX = "Sheng beta: switched to Kiswahili for clarity.\n\n"

TRANSLATE_SWAHILI = """Translate the following answer from English to Kiswahili. The answer is about official Kenyan documents (Constitution, Finance Bill). Keep the same meaning and tone. Use simple, clear Kiswahili that citizens can understand. Do not add or remove information.

Original answer in English:
{answer}

Translated answer in Kiswahili:"""

TRANSLATE_SHENG = """Translate the following answer from English to Sheng. Sheng is everyday Kenyan youth-friendly slang. Keep it respectful and clear. If you are unsure how to phrase something safely or clearly in Sheng, respond ONLY with the exact phrase: FALLBACK_TO_KISWAHILI

Original answer in English:
{answer}

Translated answer in Sheng (or FALLBACK_TO_KISWAHILI if unclear):"""


def detect_language(text: str) -> str:
    """
    Detect input language. Returns 'en', 'sw', or 'sheng'.
    Sheng is hard to detect automatically; we treat common Sheng markers as hints.
    """
    try:
        import langdetect
        lang = langdetect.detect(text)
        if lang == "sw":
            return "sw"
        # Simple heuristics for Sheng (mix of English/Swahili + youth slang markers)
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
    llm: BaseLLM,
) -> str:
    """
    Translate an English answer to Kiswahili or Sheng.
    Uses OpenAI for better quality during hackathon demo.
    Falls back to Kiswahili if Sheng is unclear.
    """
    from .config import USE_OPENAI_FOR_TRANSLATION, OPENAI_API_KEY
    
    if target_lang == "en":
        return answer_en

    # Use OpenAI for better translation quality
    if USE_OPENAI_FOR_TRANSLATION and OPENAI_API_KEY:
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

IMPORTANT: If you are unsure how to translate this safely or clearly in Sheng, respond with EXACTLY this phrase and nothing else: "FALLBACK_TO_KISWAHILI"

English: {answer_en}

Sheng (or FALLBACK_TO_KISWAHILI if unclear):"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,  # Slightly higher for creative Sheng
            )
            sheng_result = response.choices[0].message.content.strip()
            
            # Check if OpenAI requested fallback
            if "FALLBACK_TO_KISWAHILI" in sheng_result.upper():
                # Fallback: translate to Kiswahili instead
                kisw = translate_answer(answer_en, "sw", question, llm)
                return SHENG_FALLBACK_PREFIX + kisw
            
            return sheng_result
        
        else:
            return answer_en
    
    # Fallback to Ollama (original code)
    if target_lang == "sw":
        prompt = PromptTemplate(template=TRANSLATE_SWAHILI, input_variables=["answer"])
        return (prompt | llm).invoke({"answer": answer_en}).strip()

    if target_lang == "sheng":
        prompt = PromptTemplate(template=TRANSLATE_SHENG, input_variables=["answer"])
        out = (prompt | llm).invoke({"answer": answer_en}).strip()
        if "FALLBACK_TO_KISWAHILI" in out.upper():
            kisw = translate_answer(answer_en, "sw", question, llm)
            return SHENG_FALLBACK_PREFIX + kisw
        return out

    return answer_en
