from app.core.cohereClient import get_embeddings
from app.config import settings
from app.db.models import NotionBlock
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct,PayloadSchemaType
import uuid
import logging
import random

logger = logging.getLogger(__name__)

QDRANT_URL = settings.QDRANT_URL
QDRANT_API_KEY = settings.QDRANT_API_KEY

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

VECTOR_DB_NAME = settings.VECTOR_DB_NAME
EMBEDDING_DIM = 384


def searchByCategory(user_id: int, category: str):
    logger.info(f"Searching for a random example for user_id: {user_id} in category: {category} where category != llm_top1")
    
    must_conditions = [
        {"key": "user_id", "match": {"value": str(user_id)}},
        {"key": "category", "match": {"value": category}}
    ]
    
    scroll_filter = {
        "must": must_conditions
    }

    highlights = qdrant_client.scroll(
        collection_name=VECTOR_DB_NAME,
        scroll_filter=scroll_filter,
        limit=20
    )[0]

    if not highlights:
        logger.info(f"No highlights found for user_id: {user_id} in category: {category}")
        return None

    payloads = [point.payload for point in highlights]
    filtered_payloads = [p for p in payloads if p.get('category') != p.get('llm_top1')]
    if not filtered_payloads:
        logger.info(f"No highlights found for user_id: {user_id} in category: {category} with category != llm_top1")
        return None
    example = random.choice(filtered_payloads)
    logger.info(f"Returning a random example for user_id: {user_id} in category: {category} where category != llm_top1")
    return example


def initDataCollection():
    if not qdrant_client.collection_exists(VECTOR_DB_NAME):
        qdrant_client.recreate_collection(
            collection_name=VECTOR_DB_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE
            )
        )
        
        qdrant_client.create_payload_index(
            collection_name=VECTOR_DB_NAME,
            field_name="user_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        
        qdrant_client.create_payload_index(
            collection_name=VECTOR_DB_NAME,
            field_name="category", 
            field_schema=PayloadSchemaType.KEYWORD
        )
        
        logger.info(f"Collection '{VECTOR_DB_NAME}' created with user_id and category indexes")
    else:
        logger.info(f"Collection '{VECTOR_DB_NAME}' already exists")




def similarityDataSearch(text: str, user_id: int, threshold: float = 0.9):

    logger.info(f"Performing similarity search for user_id: {user_id} with threshold: {threshold}")
    
    embedding = get_embeddings(text)
    
    hits = qdrant_client.search(
        collection_name=VECTOR_DB_NAME,
        query_vector=embedding,
        limit=1,
        query_filter={
            "must": [
                {
                    "key": "user_id",
                    "match": {"value": str(user_id)}
                }
            ]
        },
        score_threshold=threshold
    )

    if hits:
        result = hits[0].payload
        logger.info(f"Similarity match found: {result}")
        return {
            "payload": hits[0].payload,
            "score": hits[0].score
        }
    else:
        logger.info("No similar match found")
        return None


def deleteHighlightById(point_id: str):

    logger.info(f"Attempting to delete point with ID: {point_id}")
    response = qdrant_client.delete(
        collection_name=VECTOR_DB_NAME,
        points_selector={"points": [point_id]}
    )
    print(response.status)
    if response.status == "acknowledged":
        logger.info(f"Successfully deleted point with ID: {point_id}")
        return True
    else:
        logger.warning(f"Failed to delete point with ID: {point_id}")
        return False




def saveHighlightData(text: str, user_id: int,category: str, block_id : str, page_id : str, destination : str,code : bool, db : Session,llm_predictions = None ,llm_top1 = None):
    logger.info(f"Saving highlight for user_id: {user_id}, category: {category} in vector DB")
    embedding = get_embeddings(text)
    pt_id = uuid.uuid4().hex
    info = qdrant_client.upsert(
        collection_name=VECTOR_DB_NAME,
        points=[PointStruct(
            id=pt_id,
            vector=embedding,
            payload={
                "highlight": text,
                "user_id": str(user_id),
                "category": category,
                "llm_predictions": llm_predictions,
                "llm_top1": llm_top1
            }
        )]
    )
    print(info)
    logger.info("Highlight saved successfully")
    logger.info("Saving Block details in rel.database")

    try:
        block = NotionBlock(
            notion_block_id = block_id,
            notion_page_id = page_id,
            user_id = user_id,
            block_type = "code" if code else "callout",
            plain_text_content = text,
            source_url = destination,
            qdrant_point_id = pt_id
        )

        db.add(block)
        db.commit()
        db.refresh(block)
        logger.info("Saved Successfully")
    except Exception as e:
        logger.info("Error in saving to rel.db .. rolling back saving in vector db")
        resp = deleteHighlightById(pt_id)
        logger.info("deleted successfully" if resp else "error in deletion")
        print(e)
        return e

    return block


def listUserDataHighlights(user_id: str):
    logger.info(f"Listing highlights for user_id: {user_id}")
    highlights = qdrant_client.scroll(
        collection_name=VECTOR_DB_NAME,
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
        collection_name=VECTOR_DB_NAME,
        query_vector=embedding,
        limit=1,
        query_filter={"must": [{"key": "user_id", "match": {"value": user_id}}]},   
        score_threshold=threshold
    )

    result = hits
    logger.info(f"Similarity search result: {result}")
    return result