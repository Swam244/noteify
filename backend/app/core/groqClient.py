import os
import logging
from groq import Groq
from app.config import settings
import json
import redis

logger = logging.getLogger(__name__)

GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_MODEL = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)

def categorize_note(note_text: str,categories) -> str:

    # json_template = "{\n" + ",\n".join([f'  "{cat}": 0.0' for cat in categories]) + "\n}"
    # prompt = construct_penalizing_prompt(note_text,categories)
    prompt = (
        "You are a specialist note taker and can instantly recognize in which topic you should put the text, i.e given a text you should be intelligent enough to note it in a particular category."
        "You should list all the probable categories where it can belong with their score along with it between 0 and 1"
        "You should provide the output strictly in JSON format with no other thing. i.e output should only consist of JSON which will contain a list of categories with their corresponding score."
        "If the note is about a **very specific or deep topic**, reduce the score of its broader parent categories (e.g., LLM → penalize AI and Technology)."
        "Your goal is to help a note-taking system organize fine-grained notes and identify when a **new category might be needed"

        "ex : input text : Gesturio is a modern web application built with Next.js, React, and TypeScript, designed to help users learn and practice American Sign Language (ASL)."
        "output : {'Education': 0.7, 'Technology': 0.8, 'Language': 0.4, 'Programming': 0.6, 'Software': 0.5}"
        "REMEMBER TO GIVE OUTPUT EXACTLY IN THE FORMAT AS ABOVE ONLY DIFFERENCE BEING THE SINGLE INVERTED SHOULD BE DOUBLE INVERTED"
        f"Text : {note_text}"
    )


    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL,
        )
        logger.debug("Groq categorization response: %s", chat_completion)
        print(chat_completion.choices[0].message.content.strip())
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
