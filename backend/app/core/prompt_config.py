import json
from pathlib import Path
from typing import Dict


def load_prompts() -> Dict[str, str]:
    config_path = Path(__file__).parent / "prompt_config.json"
    with open(config_path, 'r') as f:
        return json.load(f)


prompts = load_prompts()


ENRICHMENT_PROMPTS: Dict[str, str] = {
    "definitions": prompts["ENRICHMENT_DEFINITIONS_PROMPT"],
    "grammar": prompts["ENRICHMENT_GRAMMAR_PROMPT"],
    "summarize": prompts["ENRICHMENT_SUMMARIZE_PROMPT"],
    "examples": prompts["ENRICHMENT_EXAMPLES_PROMPT"],
    "code":prompts['CODE'],
    "category":prompts['CATEGORY_PREDICTION']
} 