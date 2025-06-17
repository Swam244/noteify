from .prompt_config import ENRICHMENT_PROMPTS

__all__ = ['ENRICHMENT_PROMPTS']

text = "from django.contrib.auth.decorators import login_required\nfrom django.utils.decorators import method_decorator\nfrom django.views.generic import View\n\n\n@login_required(login_url=\"/books/login/\", redirect_field_name=\"redirect_to\")\ndef book_dashboard(request): ...\n\n\n@method_decorator(\n    login_required(login_url=\"/books/login/\", redirect_field_name=\"redirect_to\"),\n    name=\"dispatch\",\n)\nclass BookMetrics(View):\n    pass"

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
prompt = prompt + "{}".format(text)

# print(prompt)