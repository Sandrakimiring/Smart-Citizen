"""
LLM-based signal analyzer for Nyayo Sentinel.

Extracts topic, tension score, and county from citizen questions
using OpenAI GPT-4o-mini with structured JSON output.
"""

import json
import os
import logging
from typing import Optional

from openai import OpenAI

from .models import SignalExtraction, TOPIC_TAXONOMY, KENYA_COUNTIES

logger = logging.getLogger(__name__)

# ── Extraction prompt ─────────────────────────────────────────────────
_SYSTEM_PROMPT = f"""You are a signal analyzer for Kenyan citizen questions about government policies and laws.

Given a citizen's question, extract:
1. **topic** — The main topic. MUST be exactly one of: {json.dumps(TOPIC_TAXONOMY)}
2. **tension_score** — A float from 0.0 to 1.0 measuring the citizen's frustration or confusion level:
   - 0.0–0.3 = neutral/informational (e.g., "What does Article 73 say?")
   - 0.3–0.6 = mild concern or confusion (e.g., "Is the housing levy mandatory?")
   - 0.6–0.8 = frustration or worry (e.g., "Why are land rates increasing?")
   - 0.8–1.0 = strong frustration or anger (e.g., "This tax is unconstitutional!")
3. **county** — The Kenya county if mentioned or implied. Must be one of: {json.dumps(KENYA_COUNTIES)}. If no county is mentioned, set to null.

Respond with ONLY a JSON object, no markdown, no explanation:
{{"topic": "...", "tension_score": 0.XX, "county": "..." or null}}"""

_USER_TEMPLATE = "Citizen question: {question}"


class SentinelAnalyzer:
    """Extracts structured signals from citizen questions using GPT-4o-mini."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for Sentinel analyzer")
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"

    def analyze(self, question: str) -> SignalExtraction:
        """
        Analyze a citizen question and extract topic, tension, and county.

        Args:
            question: The citizen's original question text.

        Returns:
            SignalExtraction with topic, tension_score, and optional county.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": _USER_TEMPLATE.format(question=question)},
                ],
                temperature=0.1,  # low temp for consistent classification
                max_tokens=100,
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content.strip()
            data = json.loads(raw)

            # Validate topic is in taxonomy
            topic = data.get("topic", "governance")
            if topic not in TOPIC_TAXONOMY:
                logger.warning(f"LLM returned unknown topic '{topic}', defaulting to 'governance'")
                topic = "governance"

            # Validate tension score range
            tension = float(data.get("tension_score", 0.5))
            tension = max(0.0, min(1.0, tension))

            # Validate county
            county = data.get("county")
            if county and county not in KENYA_COUNTIES:
                logger.warning(f"LLM returned unknown county '{county}', setting to None")
                county = None

            return SignalExtraction(
                topic=topic,
                tension_score=round(tension, 2),
                county=county,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            return self._fallback_extraction(question)
        except Exception as e:
            logger.error(f"Analyzer error: {e}")
            return self._fallback_extraction(question)

    def _fallback_extraction(self, question: str) -> SignalExtraction:
        """Simple keyword-based fallback if LLM fails."""
        q = question.lower()

        # Topic detection via keywords
        topic_keywords = {
            "tax": ["tax", "levy", "duty", "vat", "revenue", "finance bill"],
            "land": ["land", "plot", "title deed", "survey", "rates"],
            "employment": ["job", "employ", "salary", "wage", "labour", "work"],
            "education": ["school", "university", "education", "student", "teacher"],
            "security": ["police", "security", "crime", "terrorism", "safety"],
            "health": ["hospital", "health", "doctor", "medicine", "clinic"],
            "governance": ["president", "parliament", "senator", "governor", "election"],
            "rights": ["right", "freedom", "constitutional", "bill of rights"],
            "environment": ["environment", "climate", "pollution", "forest", "water"],
            "infrastructure": ["road", "bridge", "railway", "sgr", "airport"],
        }

        topic = "governance"  # default
        for t, keywords in topic_keywords.items():
            if any(kw in q for kw in keywords):
                topic = t
                break

        # Tension: higher if question marks, exclamation, "why" patterns
        tension = 0.4  # default mild
        if "why" in q or "how come" in q:
            tension = 0.6
        if "!" in question:
            tension = 0.7
        if any(w in q for w in ["unfair", "illegal", "unconstitutional", "corruption"]):
            tension = 0.8

        return SignalExtraction(topic=topic, tension_score=tension, county=None)
