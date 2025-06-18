from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct,PayloadSchemaType
from app.core.cohereClient import get_embeddings
from app.config import settings
import uuid
import logging
from sqlalchemy.orm import Session
from app.db.models import NotionBlock

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




def similarityDataSearch(text: str, user_id: int, threshold: float = 0.9):

    logger.info(f"Performing similarity search for user_id: {user_id} with threshold: {threshold}")
    
    embedding = get_embeddings(text)
    
    hits = qdrant_client.search(
        collection_name=DATA_COLLECTION_NAME,
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
        collection_name=DATA_COLLECTION_NAME,
        points_selector={"points": [point_id]}
    )
    print(response.status)
    if response.status == "acknowledged":
        logger.info(f"Successfully deleted point with ID: {point_id}")
        return True
    else:
        logger.warning(f"Failed to delete point with ID: {point_id}")
        return False




def saveHighlightData(text: str, user_id: int, category: str, block_id : str, page_id : str, destination : str,code : bool, db : Session):
    logger.info(f"Saving highlight for user_id: {user_id}, category: {category} in vector DB")
    embedding = get_embeddings(text)
    pt_id = uuid.uuid4().hex
    info = qdrant_client.upsert(
        collection_name=DATA_COLLECTION_NAME,
        points=[PointStruct(
            id=pt_id,
            vector=embedding,
            payload={
                "highlight": text,
                "user_id": str(user_id),
                "category": category,
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