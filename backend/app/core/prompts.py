from .prompt_config import ENRICHMENT_PROMPTS
from app.db.models import UserCategories
from app.core.qdrantClient import searchByCategory
from sqlalchemy.orm import Session
import random
import json

__all__ = ['ENRICHMENT_PROMPTS']


def getUserSpecificPromptExamples(user_id : int, db : Session):
    try:
        categories = db.query(UserCategories).filter(UserCategories.user_id == user_id).all()
        category_names = [cat.category_name for cat in categories]
        
        if len(category_names) == 0:
            return []
        
        selected_categories = random.sample(category_names, min(5,len(category_names)))
        
        examples = []
        
        for cat in selected_categories:
            example = searchByCategory(user_id, cat)
            example_str = ""
            if example:
                predictions = dict(example['llm_predictions'])
                predictions[f"{cat}"] = 1.0

                example_str += f'input text : {example['highlight']}'
                example_str += "\n"
                example_str += f'output : {predictions}'

            examples.append(example_str)

        return examples
    
    finally:
        db.close()