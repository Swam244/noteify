import logging
from groq import Groq
from app.config import settings
import json
from app.core.prompts import ENRICHMENT_PROMPTS
import redis

logger = logging.getLogger(__name__)

GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_MODEL = settings.GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)

# REMEMBER HERE EXAMPLES WILL ALSO COME WHICH WILL BE DYNAMICALLY FETCHED BASED ON THE USER.
def categorize_note(note_text: str) -> str:

    prompt = ENRICHMENT_PROMPTS['category']
    prompt = prompt + f"Text : {note_text}"

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



def enrich_note(note_text: str, enrichment_type: str) -> str:
    prompt_template = ENRICHMENT_PROMPTS[enrichment_type]
    prompt = prompt_template.replace("{note_text}", note_text)

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL,
        )
        raw_response = chat_completion.choices[0].message.content.strip()
        logger.debug("Groq enrichment raw response: %s", raw_response)

        try:
            response_json = json.loads(raw_response)
            enriched_note = response_json.get("enriched_note", note_text)
        except json.JSONDecodeError:
            logger.warning("LLM response not in expected JSON format.")
            enriched_note = raw_response

        if len(enriched_note) > 2000:
            enriched_note = enriched_note[:1997] + "..."

        return enriched_note

    except Exception as e:
        logger.error("Failed to enrich note: %s", str(e))
        return note_text



def handleCode(text: str):

    prompt = ENRICHMENT_PROMPTS["code"]

    text = json.dumps(text)
    prompt = prompt + "{}".format(text)
    # print(prompt)

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL,
        )
        raw_response = chat_completion.choices[0].message.content.strip()
        logger.debug("Groq enrichment raw response: %s", raw_response)
        # print(raw_response)
        try:

            response_json = json.loads(raw_response)
            # print(response_json)
    
        except json.JSONDecodeError:
            logger.warning("LLM response not in expected JSON format.")
            return {
                "code": False,
                "enriched_text": raw_response[:1997] + "..." if len(raw_response) > 2000 else raw_response
            }

        if response_json.get("code") == True:
            code_language = response_json.get("code_language", "text")
            code_content = response_json.get("code_content", "").strip()

            if len(code_content) > 2000:
                code_content = code_content[:1997] + "..."

            return {
                "code": True,
                "code_language": code_language,
                "code_content": code_content
            }

        else:
            enriched_text = response_json.get("enriched_text", text)
            if len(enriched_text) > 2000:
                enriched_text = enriched_text[:1997] + "..."

            return {
                "code": False,
                "enriched_text": enriched_text
            }

    except Exception as e:
        logger.error("Failed to enrich note: %s", str(e))
        return {
            "code": False,
            "enriched_text": text
        }
