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

# REMEMBER HERE EXAMPLES WILL ALSO COME WHICH WILL BE DYNAMICALLY FETCHED BASED ON THE USER.
def categorize_note(note_text: str) -> str:

    prompt = (
        "You are a specialist note taker and can instantly recognize in which topic you should put the text, i.e given a text you should be intelligent enough to note it in a particular category."
        "You should list all the probable categories where it can belong with their score along with it between 0 and 1 and dont give same points to two categories , every category must have different points"
        "You should provide the output strictly in JSON format with no other thing. i.e output should only consist of JSON which will contain a list of categories with their corresponding score."
        "You should always try to return a subtopic as deep it is from the main topic"
        
        "ex : input text : Gesturio is a modern web application built with Next.js, React, and TypeScript, designed to help users learn and practice American Sign Language (ASL)."
        "output : {'Web app': 0.7, 'Technology': 0.3, 'Sign Language': 0.4, 'Frontend development': 0.9, 'Software': 0.5}"

        "ex : The majority of those killed or injured in Israeli strikes on Iran are women and children, the country's health minister Mohammad-Reza Zafarghand was quoted on state media as saying."
        "output : {'News': 0.2, 'Middle East Conflict': 0.4, 'Politics': 0.35, 'Human Rights': 0.1, 'Isreal Iran War': 0.9}"
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
