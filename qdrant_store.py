"""
qdrant_store.py
───────────────
Handles all vector-storage operations using Qdrant Cloud.

Collection schema
  name    : gisul_questions
  size    : 384  (all-MiniLM-L6-v2 output dimension)
  distance: Cosine

Point payload
  user_id       : int   – owner of the question (used as a filter)
  question_text : str   – original question string
  topic_tag     : str   – topic assigned by assign_tag()
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
)

# ─── Client ───────────────────────────────────────────────────────────────────

load_dotenv()

QDRANT_URL  = os.environ["QDRANT_URL"]
QDRANT_KEY  = os.environ["QDRANT_API_KEY"]
COLLECTION  = os.getenv("QDRANT_COLLECTION", "gisul_questions")
VECTOR_SIZE = 384   # matches all-MiniLM-L6-v2

qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY)


# ─── Collection bootstrap ─────────────────────────────────────────────────────

def init_collection() -> None:
    """Create the Qdrant collection and required payload indexes."""
    existing = {c.name for c in qdrant.get_collections().collections}
    if COLLECTION not in existing:
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"[Qdrant] Collection '{COLLECTION}' created.")
    else:
        print(f"[Qdrant] Collection '{COLLECTION}' ready.")

    # Create payload index on user_id so filtered searches work
    qdrant.create_payload_index(
        collection_name=COLLECTION,
        field_name="user_id",
        field_schema=PayloadSchemaType.INTEGER,
    )
    print("[Qdrant] Payload index on 'user_id' ensured.")


# ─── Write ────────────────────────────────────────────────────────────────────

def store_vector(
    question_id: int,
    user_id: int,
    embedding: list,
    text: str,
    tag: str,
) -> None:
    """
    Upsert a single question embedding into Qdrant.
    Uses the SQLite question.id as the Qdrant point id (must be int or UUID).
    """
    qdrant.upsert(
        collection_name=COLLECTION,
        points=[
            PointStruct(
                id=question_id,
                vector=embedding,
                payload={
                    "user_id":       user_id,
                    "question_text": text,
                    "topic_tag":     tag,
                },
            )
        ],
    )


# ─── Read / Search ────────────────────────────────────────────────────────────

def search_similar(
    user_id: int,
    embedding: list,
    top_n: int = 5,
    min_score: float = 0.3,
) -> list:
    """
    Return the top-N most similar questions for this user.
    Filters by user_id so users only see their own history.
    """
    response = qdrant.query_points(
        collection_name=COLLECTION,
        query=embedding,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id),
                )
            ]
        ),
        limit=top_n,
        score_threshold=min_score,
    )

    return [
        {
            "text":  hit.payload["question_text"],
            "tag":   hit.payload["topic_tag"],
            "score": round(hit.score, 3),
        }
        for hit in response.points
    ]
