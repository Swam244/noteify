import os
import logging
from groq import Groq
from app.config import settings

logger = logging.getLogger(__name__)

GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_MODEL = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)

def categorize_note(note_text: str) -> str:
    prompt = (
        "You are a helpful assistant that classifies user notes into predefined categories.\n"
        "Categories: Productivity, Technology, Health, Education, Finance, Philosophy, Entertainment, Science, Business, Personal Development.\n\n"
        f"Note: \"{note_text}\"\n\n"
        "Respond with only the most relevant category from the list."
    )
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL,
        )
        logger.debug("Groq categorization response: %s", chat_completion)
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Failed to categorize note: %s", str(e))
        return "Uncategorized"



def enrich_note(note_text: str) -> str:
    prompt = (
        "You are an intelligent assistant. Given a short note or text snippet, enrich it by adding useful context, definitions for key terms, and any helpful related info. Keep it concise and relevant.\n\n"
        f"Note: \"{note_text}\"\n\n"
        "Enriched Version:"
    )
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL,
        )
        logger.debug("Groq enrichment response: %s", chat_completion)
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Failed to enrich note: %s", str(e))
        return note_text
