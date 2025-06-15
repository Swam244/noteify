from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct,PayloadSchemaType
from app.core.cohereClient import get_embeddings
import os
from app.config import settings
import uuid
import logging

logger = logging.getLogger(__name__)

QDRANT_URL = settings.QDRANT_URL
QDRANT_API_KEY = settings.QDRANT_API_KEY

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

DATA_COLLECTION_NAME = "test"
EMBEDDING_DIM = 384


def initDataCollection():
    if not qdrant_client.collection_exists(DATA_COLLECTION_NAME):
        qdrant_client.recreate_collection(
            collection_name=DATA_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE
            )
        )
        
        qdrant_client.create_payload_index(
            collection_name=DATA_COLLECTION_NAME,
            field_name="user_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        
        qdrant_client.create_payload_index(
            collection_name=DATA_COLLECTION_NAME,
            field_name="category", 
            field_schema=PayloadSchemaType.KEYWORD
        )
        
        logger.info(f"Collection '{DATA_COLLECTION_NAME}' created with user_id and category indexes")
    else:
        logger.info(f"Collection '{DATA_COLLECTION_NAME}' already exists")

def similarityDataSearch(text: str, user_id: str, threshold: float = 0.9):
    logger.info(f"Performing similarity search for user_id: {user_id} with threshold: {threshold}")
    embedding = get_embeddings(text)
    hits = qdrant_client.search(
        collection_name=DATA_COLLECTION_NAME,
        query_vector=embedding,
        limit=1,
        query_filter={"must": [{"key": "user_id", "match": {"value": user_id}}]},   # must means AND operation (here it means find a point  which belongs to the user with user_id = user_id)
        score_threshold=threshold
    )
    result = hits[0].payload if hits else None
    logger.info(f"Similarity search result: {result}")
    return result


def saveHighlightData(text: str, user_id: int, category: str, enrichment: str):
    logger.info(f"Saving highlight for user_id: {user_id}, category: {category}")
    embedding = get_embeddings(text)
    qdrant_client.upsert(
        collection_name=DATA_COLLECTION_NAME,
        points=[PointStruct(
            id=uuid.uuid4().hex,
            vector=embedding,
            payload={
                "highlight": text,
                "user_id": str(user_id),
                "category": category,
                "enrichment": enrichment
            }
        )]
    )
    logger.info("Highlight saved successfully")

def listUserDataHighlights(user_id: str):
    logger.info(f"Listing highlights for user_id: {user_id}")
    highlights = qdrant_client.scroll(
        collection_name=DATA_COLLECTION_NAME,
        scroll_filter={"must": [{"key": "user_id", "match": {"value": user_id}}]},
        limit=100
    )[0]
    logger.info(f"Found {len(highlights)} highlights for user_id: {user_id}")
    return highlights

def similaritySearchCategory(text: str, user_id: int, threshold: float = 0.5):
    logger.info(f"Performing category similarity search for user_id: {user_id} ")
    embedding = get_embeddings(text)
    print(len(embedding))
    user_id = str(user_id)

    hits = qdrant_client.search(
        collection_name=DATA_COLLECTION_NAME,
        query_vector=embedding,
        limit=1,
        query_filter={"must": [{"key": "user_id", "match": {"value": user_id}}]},   
        score_threshold=threshold
    )

    result = hits
    logger.info(f"Similarity search result: {result}")
    return result