import cohere
from app.config import settings

co = cohere.Client(settings.COHERE_API_KEY)

def get_embeddings(text : str)-> str:
    response = co.embed(
      model='embed-english-light-v3.0',
      texts=[text],
      input_type='classification',
      truncate='NONE'
    )
    return response.embeddings[0]
