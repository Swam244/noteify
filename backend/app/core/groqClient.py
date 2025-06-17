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
    prompt = f"""
        You are a code enrichment assistant.
        Your job is to determine whether the given input contains code. If it does, extract the code and append helpful explanations as **comments at the bottom of the code block**, using the appropriate comment syntax.
        Return only a **pure JSON object** at the top level. Do **not** embed the JSON inside a string or wrap it in another object.
        ---
        If the input contains code, return:
        {{
        "code": true,
        "code_language": "<language_name>",
        "code_content": "<original_code_with_explanation_as_comments_at_bottom>"
        }}

        If the input does NOT contain code, return:
        {{
        "code": false,
        "enriched_text": "<summarized_or_enriched_text>"
        }}
        ---
        Formatting rules:
        - Add the explanation **only at the bottom** as comments.
        - Use appropriate syntax: `#` for Python, `//` for JS, etc.
        - Consider all programming languages as code ex. JSON, HTML,CSS, Javascript, Python, C, C++, TypeScript,bash, etc.
        - Do not use markdown or wrap with triple backticks (```) — return as plain text.
        - Keep the total output under 2000 characters.
        - Ensure the entire response is valid JSON.
        ---
        Example with code:
        Input:
        def add(a, b):
            return a + b
        Output:
        {{
        "code": true,
        "code_language": "python",
        "code_content": "def add(a, b):\\n    return a + b\\n\\n# This function adds two numbers and returns the result."
        }}
        ---
        Example without code:
        Input:
        Photosynthesis is a process used by plants to convert light into energy.
        Output:
        {{
        "code": false,
        "enriched_text": "Photosynthesis helps plants convert light into energy using chloroplasts, water, and CO₂."
        }}
        ---
        Input:
        """


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
