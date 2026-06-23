import os
import math
import socket
from dotenv import load_dotenv

load_dotenv()

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")
API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}

TOPICS = {
    "Biology":          ["photosynthesis", "cell", "DNA", "evolution", "respiration", "protein", "organism"],
    "Physics":          ["force", "gravity", "energy", "motion", "light", "wave", "electron", "velocity"],
    "Chemistry":        ["reaction", "molecule", "element", "acid", "bond", "compound", "atom"],
    "Mathematics":      ["equation", "integral", "derivative", "geometry", "probability", "function"],
    "History":          ["war", "civilization", "empire", "revolution", "century", "government", "treaty"],
    "Computer Science": ["algorithm", "data structure", "network", "program", "database", "recursion"],
    "General":          []
}

topic_sentences = {
    topic: " ".join(keywords)
    for topic, keywords in TOPICS.items() if keywords
}

import json
import urllib.request
import urllib.error

def query_huggingface(texts):
    """Query the Hugging Face Inference API."""
    data = json.dumps({"inputs": texts, "options": {"wait_for_model": True}}).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers=headers)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise Exception(f"Hugging Face API error: {e.read().decode('utf-8')}")
    except Exception as e:
        # Fallback error for DNS or connection issues
        raise Exception(f"Network error querying Hugging Face: {str(e)}")

# Pre-compute topic embeddings once at startup
topic_embeddings = {}
if topic_sentences:
    topics_list = list(topic_sentences.keys())
    sentences_list = [topic_sentences[t] for t in topics_list]
    try:
        embeddings = query_huggingface(sentences_list)
        for i, topic in enumerate(topics_list):
            topic_embeddings[topic] = embeddings[i]
        print("[Embedding] Loaded topic embeddings from Hugging Face API.")
    except Exception as e:
        print(f"[Embedding] Warning: Failed to pre-compute topic embeddings from Hugging Face API: {e}")

def cosine_similarity(vec1: list, vec2: list) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def get_embedding(text: str) -> list:
    """Return embedding as a plain Python list (JSON-serialisable)."""
    result = query_huggingface([text])
    return result[0]

def assign_tag(question: str) -> str:
    """Classify a question into the closest TOPICS category."""
    if not topic_embeddings:
        return "General"
    
    q_embedding = get_embedding(question)
    best_topic = "General"
    best_score = 0.0
    for topic, t_emb in topic_embeddings.items():
        score = cosine_similarity(q_embedding, t_emb)
        if score > best_score:
            best_score = score
            best_topic = topic
    return best_topic
